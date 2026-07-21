# backend/tests/test_custo_equipe_deriv.py
"""Tests for SISJURI-derived per-area Custo equipe (no manual ledger).

Validates the fold recipe from docs/SISJURI_QUERIES.md §11 against the 2026-02
component data probed from the live DB: per-lawyer component sums, the Aurelio
50/50 CAD_RATEIO_GRUPO split, home-area fallback, INSS exclusion, and the
per-lawyer override (cap) path.
"""
from __future__ import annotations

import pytest

from app.closing.custo_equipe_deriv import (
    LawyerOverride,
    build_area_splits,
    derive_area_custo_equipe,
)

# Home grupo per lawyer (CAD_PROFISSIONAL.ID_GRUPOJURIDICO -> name), Feb 2026.
HOME_AREA = {
    "AM": "Equipe Direito Econômico",
    "ASG": "Equipe Direito Econômico",
    "BBX": "Equipe Contencioso",
    "BMP": "Equipe Direito Econômico",
    "DC": "Equipe Contencioso",
    "EHF": "Equipe Direito Econômico",
    "EMC": "Arbitragem",
    "FSM": "Arbitragem",
    "IAC": "Equipe Contencioso",
    "JGS": "Arbitragem",
    "JVO": "Equipe Contencioso",
    "MV": "Arbitragem",
    "RB": "Equipe Direito Econômico",
}

# CAD_RATEIO_GRUPO active rows (only AM is multi-area): 50/50.
RATEIO_GRUPO = [
    {"sigla": "AM", "grupo": "Equipe Contencioso", "percentual": 50},
    {"sigla": "AM", "grupo": "Equipe Direito Econômico", "percentual": 50},
]


def _splits():
    return build_area_splits(RATEIO_GRUPO, HOME_AREA)


def test_aurelio_splits_50_50_via_rateio_grupo():
    splits = _splits()
    am = splits["AM"].normalized()
    assert round(am["Contencioso"], 4) == 0.5
    assert round(am["Econômico"], 4) == 0.5


def test_single_area_lawyer_falls_back_to_home_grupo():
    splits = _splits()
    assert splits["DC"].normalized() == {"Contencioso": 1.0}
    assert splits["MV"].normalized() == {"Arbitragem": 1.0}
    assert splits["RB"].normalized() == {"Econômico": 1.0}


def test_inss_account_is_excluded():
    rows = [
        {"sigla": "DC", "id_conta": "030.010.0010", "valor": 23379.0},
        {"sigla": "DC", "id_conta": "030.010.0050", "valor": 324.20},  # INSS
    ]
    out = derive_area_custo_equipe(rows, _splits())
    # INSS dropped -> only the 23.379 distribuição lands in Contencioso.
    assert out["Contencioso"] == 23379.0


def test_aurelio_amount_splits_across_two_areas():
    rows = [{"sigla": "AM", "id_conta": "030.010.0010", "valor": 23379.0}]
    out = derive_area_custo_equipe(rows, _splits())
    assert out["Contencioso"] == 11689.5
    assert out["Econômico"] == 11689.5


def test_full_feb_reconciles_to_the_centavo():
    """The complete Feb 2026 component set + the documented per-lawyer override
    map must reproduce the client dashboard's per-area Custo equipe exactly.

    Components (docs/SISJURI_QUERIES.md §11): 0010 gross ex-Bônus/Excedente,
    0130 gross pró-labore, 0110 net convênio, 0140 bolsa; INSS 0050 excluded.
    Overrides: EHF/RB convênio hand-net, AM/DC monthly AASP, JGS negotiated cap.
    """
    c0010 = {
        "AM": 23379, "ASG": 4099 + 3018 + 520, "BBX": 7537.4 + 518.4,
        "BMP": 8037.88 + 1034.38, "DC": 23379, "EHF": 11879 + 1000, "EMC": 4699,
        "FSM": 13409.4 + 1610.4, "IAC": 15605 + 1566, "JGS": 9379, "MV": 23379,
        "RB": 23379,
    }
    c0110 = {
        "AM": 3182.83, "ASG": 564.92, "BBX": 1269.46, "BMP": 564.92, "DC": 1736.14,
        "EHF": 2122.30, "EMC": 1269.46, "FSM": 1564.08, "IAC": 1564.08,
        "JGS": 1911.95, "RB": 3427.58,
    }
    rows: list[dict] = []
    for s, v in c0010.items():
        rows.append({"sigla": s, "id_conta": "030.010.0010", "valor": v})
        rows.append({"sigla": s, "id_conta": "030.010.0130", "valor": 1621})
        rows.append({"sigla": s, "id_conta": "030.010.0050", "valor": 324.2})  # INSS
    for s, v in c0110.items():
        rows.append({"sigla": s, "id_conta": "030.010.0110", "valor": v})
    rows.append({"sigla": "JVO", "id_conta": "030.010.0140", "valor": 2800})
    # Area-level Vale (from 500.010.<SIGLA>): JVO Vale = 1.249,40, routed to his
    # home area (Contencioso) by the fold.
    rows.append({"sigla": "JVO", "id_conta": "030.010.0100/0220", "valor": 1249.40})

    overrides = {
        "AM": LawyerOverride(add=108.70),   # monthly AASP (54,35 x2 across halves)
        "DC": LawyerOverride(add=108.70),   # monthly AASP
        "EHF": LawyerOverride(set_account={"030.010.0110": 1564.10}),  # hand-net
        "RB": LawyerOverride(set_account={"030.010.0110": 2526.09}),   # hand-net
        "JGS": LawyerOverride(cap_total=11000.0),  # negotiated round figure
    }
    # JVO home area needed too.
    home = dict(HOME_AREA)
    splits = build_area_splits(RATEIO_GRUPO, home)
    out = derive_area_custo_equipe(rows, splits, overrides=overrides)
    assert out["Contencioso"] == pytest.approx(76342.35, abs=0.05)
    assert out["Econômico"] == pytest.approx(78817.05, abs=0.05)
    assert out["Arbitragem"] == pytest.approx(61794.34, abs=0.05)


def test_reconciles_reconciled_lawyers_to_the_centavo():
    """The 8 lawyers that reconciled exactly (Feb): area totals from their
    component rows must equal the known per-lawyer ledger figures."""
    # (sigla, id_conta, valor) — gross ex-bônus 0010 + gross 0130 + net 0110.
    rows = [
        # ASG -> Econômico 9.822,92
        {"sigla": "ASG", "id_conta": "030.010.0010", "valor": 4099 + 3018 + 520},
        {"sigla": "ASG", "id_conta": "030.010.0130", "valor": 1621},
        {"sigla": "ASG", "id_conta": "030.010.0110", "valor": 564.92},
        # MV -> Arbitragem 25.000,00
        {"sigla": "MV", "id_conta": "030.010.0010", "valor": 23379},
        {"sigla": "MV", "id_conta": "030.010.0130", "valor": 1621},
        # IAC -> Contencioso 20.356,08
        {"sigla": "IAC", "id_conta": "030.010.0010", "valor": 15605 + 1566},
        {"sigla": "IAC", "id_conta": "030.010.0130", "valor": 1621},
        {"sigla": "IAC", "id_conta": "030.010.0110", "valor": 1564.08},
    ]
    out = derive_area_custo_equipe(rows, _splits())
    assert out["Econômico"] == 9822.92
    assert out["Arbitragem"] == 25000.00
    assert out["Contencioso"] == 20356.08


def test_iss_juridico_ties_workbook_via_solicitante():
    """ISS jurídico (030.010.0160, TRIMESTRAL) is a flat per-professional rateio of
    the firm's quarterly ISS. Proven 2026-07-21 (probe_iss_solicitante) that each
    unit's AREA = its LANCSOLICITANTE (requester)'s home area — NOT LANCPROFDEST —
    then folded through the standard AM 50/50 rateio. This reproduces the workbook
    "ISS Trimestral" split (Base_Resultado rows 25/54/79) to the CENTAVO.

    Real Jan 2026 roster (14 units, keyed by solicitante; JGS has 2 postings, one
    solicited by JGS→Arbitragem and one by MAM→Econômico — the DB-derived cross-area
    move that made the earlier "manual residual" verdict WRONG):
        Contencioso 1.719,72 | Econômico 2.101,88 | Arbitragem 1.528,64  (Σ 5.350,24)
    """
    u = 382.16
    # (solicitante_sigla, unit). Extract keys ISS by LANCSOLICITANTE.
    solic = [
        "AM",              # Econômico home, but AM splits 50/50 via rateio
        "BBX", "DC", "IAC", "JCT",           # Contencioso homes (4)
        "BMP", "EHF", "RB", "VC",            # Econômico homes (4)
        "EMC", "FSM", "MV", "JGS",           # Arbitragem homes (4, incl. JGS's own unit)
        "MAM",             # JGS's 2nd ISS unit was solicited by MAM (Econômico home)
    ]
    rows = [{"sigla": s, "id_conta": "030.010.0160", "valor": u} for s in solic]

    # Jan home-area map for every solicitante above (from the live snapshot).
    ECON = "Equipe Direito Econômico"; CONT = "Equipe Contencioso"; ARB = "Arbitragem"
    home = {
        "AM": ECON, "BBX": CONT, "DC": CONT, "IAC": CONT, "JCT": CONT,
        "BMP": ECON, "EHF": ECON, "RB": ECON, "VC": ECON,
        "EMC": ARB, "FSM": ARB, "MV": ARB, "JGS": ARB, "MAM": ECON,
    }
    rateio = [
        {"sigla": "AM", "grupo": ECON, "percentual": 50},
        {"sigla": "AM", "grupo": CONT, "percentual": 50},
    ]
    splits = build_area_splits(rateio, home)
    out = derive_area_custo_equipe(rows, splits)
    assert out["Contencioso"] == pytest.approx(1719.72, abs=0.01)
    assert out["Econômico"] == pytest.approx(2101.88, abs=0.01)
    assert out["Arbitragem"] == pytest.approx(1528.64, abs=0.01)
    assert round(sum(out.values()), 2) == pytest.approx(5350.24, abs=0.01)


def test_per_lawyer_override_caps_total():
    rows = [
        {"sigla": "JGS", "id_conta": "030.010.0010", "valor": 9379},
        {"sigla": "JGS", "id_conta": "030.010.0130", "valor": 1621},
        {"sigla": "JGS", "id_conta": "030.010.0110", "valor": 1911.95},
    ]
    # Without override JGS derives 12.911,95; the negotiated cap is 11.000.
    out = derive_area_custo_equipe(
        rows, _splits(), overrides={"JGS": LawyerOverride(cap_total=11000.0)}
    )
    assert out["Arbitragem"] == 11000.0
    # A bare float is treated as cap_total for convenience.
    out2 = derive_area_custo_equipe(rows, _splits(), overrides={"JGS": 11000.0})
    assert out2["Arbitragem"] == 11000.0


def test_set_account_override_replaces_convenio():
    # EHF convênio: LANCAMENTO books 2.122,30 ("parte MBC" base) but the ledger
    # uses a hand-netted 1.564,10. set_account replaces just that account.
    rows = [
        {"sigla": "EHF", "id_conta": "030.010.0010", "valor": 12879.0},
        {"sigla": "EHF", "id_conta": "030.010.0130", "valor": 1621.0},
        {"sigla": "EHF", "id_conta": "030.010.0110", "valor": 2122.30},
    ]
    out = derive_area_custo_equipe(
        rows,
        _splits(),
        overrides={"EHF": LawyerOverride(set_account={"030.010.0110": 1564.10})},
    )
    # 12879 + 1621 + 1564.10 = 16.064,10 (the ledger EHF total), all Econômico.
    assert out["Econômico"] == 16064.10


def test_add_override_applies_monthly_aasp():
    # AM/DC monthly AASP (54,35) has no DB row; add it. AM's 108,70 splits 50/50.
    rows = [
        {"sigla": "AM", "id_conta": "030.010.0010", "valor": 23379.0},
        {"sigla": "AM", "id_conta": "030.010.0130", "valor": 1621.0},
        {"sigla": "AM", "id_conta": "030.010.0110", "valor": 3182.83},
    ]
    out = derive_area_custo_equipe(
        rows, _splits(), overrides={"AM": LawyerOverride(add=108.70)}
    )
    # (23379 + 1621 + 3182.83 + 108.70) = 28.291,53, split 50/50.
    assert out["Contencioso"] == round(28291.53 / 2, 2)
    assert out["Econômico"] == round(28291.53 / 2, 2)
