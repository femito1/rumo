# backend/app/budget/workbook_import.py
"""Import the granular monthly budget (Orçado) from the closing workbook's
``DRE 2026`` sheet into ``BudgetEntry`` records.

The workbook's ``DRE 2026`` tab is the stable, planned budget: rows are the
institutional DRE lines, columns C..N are the twelve months (Jan..Dez), each an
Orçado amount. Unlike the hand-built per-lawyer ledger (``Base_Resultado``),
this sheet does not carry per-close manual adjustments, so it is safe to import
verbatim as workbook-granularity ``monthly_amounts``.

This parser is pure (takes the already-extracted cell matrix) so it can be
unit-tested without a spreadsheet. The thin script in ``scripts.import_budget``
does the openpyxl read and persistence.
"""
from __future__ import annotations

from app.budget.models import BudgetEntry
from app.closing.dre import (
    AMORTIZACAO,
    CUSTO_EQUIPE,
    DESPESAS,
    IMPOSTO,
    RECEBIMENTO,
    RESERVA_BONUS,
)

#: 1-based ``DRE 2026`` row -> (area, canonical line_key). Verified against
#: "Copy of Fechamento MBC 02.2026.xlsx" (2026-07 audit): row 3 Faturamento,
#: 5 Custos Diretos, 6/7/8 per-area Custo equipe, 9 Despesas Indiretas,
#: 23 Impostos, 24 Amortização, 27 Reserva bônus.
DRE_ROW_MAP: dict[int, tuple[str, str]] = {
    3: ("institucional", RECEBIMENTO),
    5: ("institucional", CUSTO_EQUIPE),
    9: ("institucional", DESPESAS),
    23: ("institucional", IMPOSTO),
    24: ("institucional", AMORTIZACAO),
    27: ("institucional", RESERVA_BONUS),
    6: ("Contencioso", CUSTO_EQUIPE),
    7: ("Econômico", CUSTO_EQUIPE),
    8: ("Arbitragem", CUSTO_EQUIPE),
}

#: First month column in ``DRE 2026`` is C (index 3); twelve months through N.
FIRST_MONTH_COL = 3
N_MONTHS = 12


def parse_dre_budget(
    cell: "CellReader", *, client_id: str, ano: int
) -> list[BudgetEntry]:
    """Build BudgetEntry records from a ``DRE 2026`` cell reader.

    ``cell(row, col)`` returns the value at 1-based (row, col); missing/blank
    cells must return ``None``. Blank months coerce to 0.0 so a partially filled
    row still yields a valid 12-length ``monthly_amounts`` tuple.
    """
    entries: list[BudgetEntry] = []
    for row, (area, line_key) in DRE_ROW_MAP.items():
        months: list[float] = []
        for i in range(N_MONTHS):
            v = cell(row, FIRST_MONTH_COL + i)
            months.append(round(float(v), 2) if isinstance(v, (int, float)) else 0.0)
        entries.append(
            BudgetEntry(
                client_id=client_id,
                ano=ano,
                area=area,
                line_key=line_key,
                annual_amount=round(sum(months), 2),
                monthly_amounts=tuple(months),
            )
        )
    return entries


class CellReader:  # pragma: no cover - typing protocol only
    """Callable protocol: ``(row: int, col: int) -> float | int | str | None``."""

    def __call__(self, row: int, col: int) -> float | int | str | None: ...
