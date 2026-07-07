# backend/tests/test_ledger_import.py
"""Parse the hand-built per-lawyer ledger (``Base_Resultado Mensal_V2``) into
per-area monthly figures, and derive the Despesa Institucional rateio.

Values are the verified cached amounts from "Fechamento MBC 05.2026.xlsx"
(2026-07 validation against the client dashboard "MBC Resultado Jan a Mai
2026.pdf"). The parser must locate rows by label (robust to per-month staff
churn / row insertion) and read their cached values, then apply the workbook's
rateio rule:

    desp_inst[area] = (DespesaInstitucional - Sum DespesasArea) * (CE[area] / Sum CE)

Cross-checked to the centavo: summing the derived monthlies Jan..Mai for
Contencioso gives custo_equipe 372_279.42, despesas_equipe 11_996.28 and
despesa_institucional 170_869.75 -- exactly the dashboard's YTD figures.
"""
from app.closing.ledger_import import (
    AREA_ROW_LABELS,
    FIRST_MONTH_COL,
    LedgerMonth,
    despesa_institucional_rateio,
    month_reader_from_matrix,
    parse_ledger_month,
)

# Verified cached anchor values per month (Jan..Mai) for 05.2026.
# custo_equipe subtotal rows (Custo equipe - <area>), comissao (Participação +
# Repasse), despesas_equipe (Despesas Área: <area>), and the institutional total.
_CUSTO_EQUIPE = {
    "Contencioso": {1: 73576.32, 2: 76342.35, 3: 72845.49, 4: 75374.05, 5: 74141.21},
    "Econômico": {1: 75653.19, 2: 78817.05, 3: 76049.97, 4: 79160.08, 5: 79436.24},
    "Arbitragem": {1: 62013.17, 2: 61794.34, 3: 49183.94, 4: 55038.69, 5: 54383.94},
}
_DESPESAS_AREA = {
    "Contencioso": {1: 1060.10, 2: 2129.32, 3: 2346.72, 4: 4183.92, 5: 2276.22},
    "Econômico": {1: 1871.81, 2: 3296.07, 3: 2129.32, 4: 2129.32, 5: 2300.10},
    "Arbitragem": {1: 146.00, 2: 2633.69, 3: 3728.18, 4: 2633.69, 5: 1204.47},
}
_DESP_INST_TOTAL = {1: 100181.41, 2: 95047.39, 3: 101968.90, 4: 110156.11, 5: 105511.43}
_COMISSAO = {  # Feb Econômico had a 1500 Participação; May Econômico 2128.06
    "Contencioso": {m: 0.0 for m in range(1, 6)},
    "Econômico": {1: 0.0, 2: 1500.0, 3: 0.0, 4: 0.0, 5: 2128.06},
    "Arbitragem": {m: 0.0 for m in range(1, 6)},
}


def _reader(month: int):
    """Return a label->value reader for a single competence month."""

    def read(label: str):
        area_key = AREA_ROW_LABELS  # provided by the module (label prefixes)
        # custo equipe subtotal rows
        for area, lbl in area_key["custo_equipe"].items():
            if label == lbl:
                return _CUSTO_EQUIPE[area][month]
        for area, lbls in area_key["comissao"].items():
            if label in lbls:
                # split the area's comissao onto the Participação row; Repasse = 0
                return _COMISSAO[area][month] if label == lbls[0] else 0.0
        for area, lbl in area_key["despesas_area"].items():
            if label == lbl:
                return _DESPESAS_AREA[area][month]
        if label == area_key["despesa_institucional_total"]:
            return _DESP_INST_TOTAL[month]
        return None

    return read


def test_parse_ledger_month_contencioso_feb():
    m = parse_ledger_month(_reader(2), month=2)
    assert isinstance(m, LedgerMonth)
    assert m.custo_equipe["Contencioso"] == 76342.35
    assert m.comissao["Contencioso"] == 0.0
    assert m.despesas_equipe["Contencioso"] == 2129.32
    assert m.despesa_institucional_total == 95047.39


def test_despesa_institucional_rateio_ties_to_workbook_jan():
    m = parse_ledger_month(_reader(1), month=1)
    di = despesa_institucional_rateio(m)
    # ratear = 100181.41 - (1060.10+1871.81+146.00) = 97103.50
    # Contencioso ratio = 73576.32 / 211242.68 -> 0.34830...
    assert round(di["Contencioso"], 2) == 33821.38
    assert round(di["Econômico"], 2) == 34776.07
    assert round(di["Arbitragem"], 2) == 28506.06


def test_ytd_contencioso_matches_dashboard():
    """Summing Jan..Mai must reproduce the dashboard's Contencioso YTD figures."""
    ce = de = di = 0.0
    for month in range(1, 6):
        m = parse_ledger_month(_reader(month), month=month)
        ce += m.custo_equipe["Contencioso"]
        de += m.despesas_equipe["Contencioso"]
        di += despesa_institucional_rateio(m)["Contencioso"]
    assert round(ce, 2) == 372279.42
    assert round(de, 2) == 11996.28
    assert round(di, 2) == 170869.75


def test_comissao_econimico_may_nonzero():
    m = parse_ledger_month(_reader(5), month=5)
    assert m.comissao["Econômico"] == 2128.06


def test_month_reader_from_matrix_resolves_despesas_area_positionally():
    # The "Despesas Área" per-area subtotal rows share bare labels ("Contencioso"
    # etc.) with other blocks, so the importer resolves them by concrete row.
    # Build a tiny matrix: row 5 = Custo equipe Contencioso for month col C.
    ce_labels = AREA_ROW_LABELS["custo_equipe"]
    inst_label = AREA_ROW_LABELS["despesa_institucional_total"]
    label_rows = {ce_labels["Contencioso"]: 5, inst_label: 100}
    matrix = {(5, FIRST_MONTH_COL): 76342.35, (100, FIRST_MONTH_COL): 95047.39,
              (204, FIRST_MONTH_COL): 2129.32}  # 204 = Despesas Área Contencioso row

    def value_at(row, col):
        return matrix.get((row, col))

    read = month_reader_from_matrix(
        label_rows, value_at, month_index=0,
        despesas_area_rows={"Contencioso": 204, "Econômico": 205, "Arbitragem": 206},
    )
    assert read(ce_labels["Contencioso"]) == 76342.35
    assert read(inst_label) == 95047.39
    # bare "Contencioso" (Despesas Área) resolves to row 204, not the custo row.
    assert read("Contencioso") == 2129.32
    assert read("Econômico") is None  # row 205 empty in this matrix
