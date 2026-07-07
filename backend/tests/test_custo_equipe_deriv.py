# backend/tests/test_custo_equipe_deriv.py
"""Tests for SISJURI-derived per-area Custo equipe (no manual ledger).

Validates the fold recipe from docs/SISJURI_QUERIES.md §11 against the 2026-02
component data probed from the live DB: per-lawyer component sums, the Aurelio
50/50 CAD_RATEIO_GRUPO split, home-area fallback, INSS exclusion, and the
per-lawyer override (cap) path.
"""
from __future__ import annotations

from app.closing.custo_equipe_deriv import (
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


def test_per_lawyer_override_caps_total():
    rows = [
        {"sigla": "JGS", "id_conta": "030.010.0010", "valor": 9379},
        {"sigla": "JGS", "id_conta": "030.010.0130", "valor": 1621},
        {"sigla": "JGS", "id_conta": "030.010.0110", "valor": 1911.95},
    ]
    # Without override JGS derives 12.911,95; the negotiated cap is 11.000.
    out = derive_area_custo_equipe(rows, _splits(), overrides={"JGS": 11000.0})
    assert out["Arbitragem"] == 11000.0
