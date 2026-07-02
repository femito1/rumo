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


def is_valid_line(line_key: str) -> bool:
    # Accept legacy keys on write/validation too, so old clients don't 422.
    return canonical_line_key(line_key) in _BUDGET_LINE_KEYS


def is_valid_area(area: str) -> bool:
    return area in BUDGET_AREAS


def monthly_budget(entries: list[BudgetEntry]) -> dict[str, dict[str, float]]:
    """Fold budget entries into {area: {canonical_line_key: monthly_amount}}.

    Legacy keys are normalized so pre-rework budgets still feed the Orçado
    columns."""
    out: dict[str, dict[str, float]] = {}
    for e in entries:
        area_map = out.setdefault(e.area, {})
        area_map[canonical_line_key(e.line_key)] = round(e.annual_amount / 12.0, 2)
    return out
