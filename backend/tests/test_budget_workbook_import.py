# backend/tests/test_budget_workbook_import.py
"""Parse the granular monthly budget from the DRE 2026 cell matrix.

Values below are the verified first-three-months from
"Copy of Fechamento MBC 02.2026.xlsx" (2026-07 audit); the parser must map rows
to (area, line_key) and emit 12-length monthly_amounts.
"""
from app.budget.models import CUSTO_EQUIPE, DESPESAS, RECEBIMENTO
from app.budget.workbook_import import DRE_ROW_MAP, parse_dre_budget

# Minimal fixture: row -> 12 monthly Orçado values (Jan..Dez). Only a few rows
# need realistic values for the assertions; the rest are filled with a constant.
_FIXTURE_ROWS = {
    3: [671666.67] * 12,  # institucional / recebimento (Faturamento)
    5: [213417.59, 208717.59, 196100.61] + [200000.0] * 9,  # inst / custo_equipe
    6: [74354.07, 72754.07, 72754.07] + [72000.0] * 9,  # Contencioso / custo_equipe
    7: [76879.17, 75379.17, 75379.17] + [75000.0] * 9,  # Econômico / custo_equipe
    8: [62184.36, 60584.36, 47967.38] + [48000.0] * 9,  # Arbitragem / custo_equipe
    9: [102906.66, 100790.33, 128651.12] + [110000.0] * 9,  # inst / despesas
    23: [150750.0] * 12,  # imposto
    24: [8117.0] * 12,  # amortizacao
    27: [19647.54, 20329.18, 18804.79] + [20000.0] * 9,  # reserva_bonus
}


def _cell(row: int, col: int):
    vals = _FIXTURE_ROWS.get(row)
    if vals is None:
        return None
    idx = col - 3  # first month col is C (3)
    return vals[idx] if 0 <= idx < 12 else None


def test_parse_dre_budget_maps_all_rows():
    entries = parse_dre_budget(_cell, client_id="mbc", ano=2026)
    assert len(entries) == len(DRE_ROW_MAP)
    by = {(e.area, e.line_key): e for e in entries}

    receb = by[("institucional", RECEBIMENTO)]
    assert receb.monthly_amounts is not None
    assert len(receb.monthly_amounts) == 12
    assert receb.month_amount(1) == 671666.67
    assert receb.effective_annual() == round(671666.67 * 12, 2)

    cont = by[("Contencioso", CUSTO_EQUIPE)]
    assert cont.month_amount(1) == 74354.07
    assert cont.month_amount(2) == 72754.07

    desp = by[("institucional", DESPESAS)]
    assert desp.month_amount(3) == 128651.12


def test_parse_dre_budget_blank_months_coerce_to_zero():
    def cell(row, col):
        # Row 3 present only for Jan; everything else blank.
        if row == 3 and col == 3:
            return 671666.67
        return None

    entries = parse_dre_budget(cell, client_id="mbc", ano=2026)
    by = {(e.area, e.line_key): e for e in entries}
    receb = by[("institucional", RECEBIMENTO)]
    assert receb.monthly_amounts == (671666.67,) + (0.0,) * 11
    assert receb.month_amount(2) == 0.0
