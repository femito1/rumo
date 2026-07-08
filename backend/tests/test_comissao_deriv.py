# backend/tests/test_comissao_deriv.py
"""Per-area Comissão derivation from SISJURI (docs/SISJURI_QUERIES.md §12a).

Ground truth from the workbook Base_Resultado (test_ledger_import.py):
Comissão is zero every month except Feb Econômico 1.500,00 (020.110.0010,
area-tagged) and Mai Econômico 2.128,06 (030.010.0120, EHF per-lawyer).
"""
from app.closing.comissao_deriv import derive_area_comissao
from app.closing.custo_equipe_deriv import LawyerAreaSplit


def _splits():
    # EHF home area = Econômico; AM split 50/50 (like Custo equipe).
    return {
        "EHF": LawyerAreaSplit({"Econômico": 1.0}),
        "AM": LawyerAreaSplit({"Contencioso": 0.5, "Econômico": 0.5}),
        "BBX": LawyerAreaSplit({"Contencioso": 1.0}),
    }


def test_participacao_externa_area_level_feb():
    # 020.110.0010 tagged to Equipe Direito Econômico = 1.500 → Econômico.
    rows = [{"kind": "area", "area": "Equipe Direito Econômico", "valor": 1500.0}]
    out = derive_area_comissao(rows, _splits())
    assert out["Econômico"] == 1500.0
    assert out["Contencioso"] == 0.0
    assert out["Arbitragem"] == 0.0


def test_participacao_interna_per_lawyer_may():
    # 030.010.0120 EHF 2.128,06 → EHF home area Econômico.
    rows = [{"kind": "lawyer", "sigla": "EHF", "valor": 2128.06}]
    out = derive_area_comissao(rows, _splits())
    assert out["Econômico"] == 2128.06
    assert out["Contencioso"] == 0.0


def test_multi_area_lawyer_splits_comissao():
    # A multi-area lawyer's comissão splits by the same rateio as Custo equipe.
    rows = [{"kind": "lawyer", "sigla": "AM", "valor": 1000.0}]
    out = derive_area_comissao(rows, _splits())
    assert out["Contencioso"] == 500.0
    assert out["Econômico"] == 500.0


def test_zero_month_is_all_zero():
    assert derive_area_comissao([], _splits()) == {
        "Contencioso": 0.0,
        "Econômico": 0.0,
        "Arbitragem": 0.0,
    }


def test_area_and_lawyer_combine():
    rows = [
        {"kind": "area", "area": "Equipe Direito Econômico", "valor": 1500.0},
        {"kind": "lawyer", "sigla": "EHF", "valor": 2128.06},
    ]
    out = derive_area_comissao(rows, _splits())
    assert out["Econômico"] == round(1500.0 + 2128.06, 2)


def test_unknown_lawyer_is_dropped():
    rows = [{"kind": "lawyer", "sigla": "ZZZ", "valor": 999.0}]
    out = derive_area_comissao(rows, _splits())
    assert out == {"Contencioso": 0.0, "Econômico": 0.0, "Arbitragem": 0.0}
