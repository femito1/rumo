# backend/app/budget/models.py
"""Budget (Orcado) domain: canonical DRE lines and a per-year budget record.

Granularity (product decision): one ANNUAL amount per DRE line per area;
monthly = annual / 12. Areas: 'institucional' plus the three cost centers.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.closing.dre import (
    AMORTIZACAO,
    CUSTO_EQUIPE,
    DESPESAS,
    IMPOSTO,
    RECEBIMENTO,
    RESERVA_BONUS,
)
from app.closing.workbook_layouts import AREAS

#: Areas that can hold a budget. 'institucional' is the consolidated view.
BUDGET_AREAS = ("institucional", *AREAS)

#: The DRE lines an admin/client can budget, in workbook vocabulary
#: (subtotals/margins are derived, so they are excluded from manual entry).
BUDGET_LINES: tuple[tuple[str, str], ...] = (
    (RECEBIMENTO, "Recebimento"),
    (CUSTO_EQUIPE, "Custo equipe"),
    (DESPESAS, "Despesas"),
    (IMPOSTO, "Imposto"),
    (AMORTIZACAO, "Amortização"),
    (RESERVA_BONUS, "Reserva de Bônus"),
)

_BUDGET_LINE_KEYS = {k for k, _ in BUDGET_LINES}

#: Pre-rework line keys → current workbook vocabulary. Lets budgets saved before
#: the Recebimento-base rework keep feeding the Orçado columns without re-entry.
LEGACY_LINE_ALIASES: dict[str, str] = {
    "faturamento": RECEBIMENTO,
    "receita": RECEBIMENTO,
    "custos_diretos": CUSTO_EQUIPE,
    "despesas_indiretas": DESPESAS,
    "impostos": IMPOSTO,
}


def canonical_line_key(line_key: str) -> str:
    """Map a possibly-legacy line key to the current canonical key."""
    return LEGACY_LINE_ALIASES.get(line_key, line_key)


@dataclass(frozen=True)
class BudgetEntry:
    client_id: str
    ano: int
    area: str
    line_key: str
    annual_amount: float
    #: Optional workbook-granularity per-month amounts (Jan..Dez, 12 values).
    #: When present these override the annual/12 even split; the workbook's
    #: Orçado varies month-to-month (Custo equipe, Despesas, etc.).
    monthly_amounts: tuple[float, ...] | None = None

    def month_amount(self, month: int) -> float:
        """Budget for a 1-based month; per-month detail if present else annual/12."""
        if self.monthly_amounts and 1 <= month <= len(self.monthly_amounts):
            return round(self.monthly_amounts[month - 1], 2)
        return round(self.annual_amount / 12.0, 2)

    def effective_annual(self) -> float:
        """Annual total: sum of per-month detail if present, else annual_amount."""
        if self.monthly_amounts:
            return round(sum(self.monthly_amounts), 2)
        return round(self.annual_amount, 2)


def is_valid_line(line_key: str) -> bool:
    # Accept legacy keys on write/validation too, so old clients don't 422.
    return canonical_line_key(line_key) in _BUDGET_LINE_KEYS


def is_valid_area(area: str) -> bool:
    return area in BUDGET_AREAS


def monthly_budget(
    entries: list[BudgetEntry], month: int | None = None
) -> dict[str, dict[str, float]]:
    """Fold budget entries into {area: {canonical_line_key: monthly_amount}}.

    ``month`` (1-based) selects a specific competence month; entries carrying
    workbook-granularity ``monthly_amounts`` then return that month's value,
    otherwise annual/12. When ``month`` is None the even split is used (the
    aggregate/reference behavior). Legacy keys are normalized so pre-rework
    budgets still feed the Orçado columns."""
    out: dict[str, dict[str, float]] = {}
    # Track which (area, line) values came from an entry carrying monthly detail
    # so a legacy annual-only entry can't shadow an imported granular budget
    # when both normalize to the same canonical key (order-independent).
    has_detail: set[tuple[str, str]] = set()
    for e in entries:
        area_map = out.setdefault(e.area, {})
        line = canonical_line_key(e.line_key)
        if (e.area, line) in has_detail and not e.monthly_amounts:
            continue  # keep the detailed value already set
        amount = e.month_amount(month) if month is not None else round(
            e.annual_amount / 12.0, 2
        )
        area_map[line] = amount
        if e.monthly_amounts:
            has_detail.add((e.area, line))
    return out
