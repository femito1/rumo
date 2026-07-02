# backend/app/budget/models.py
"""Budget (Orcado) domain: canonical DRE lines and a per-year budget record.

Granularity (product decision): one ANNUAL amount per DRE line per area;
monthly = annual / 12. Areas: 'institucional' plus the three cost centers.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.closing.dre import (
    AMORTIZACAO,
    AREAS,
    CUSTOS_DIRETOS,
    DESPESAS_INDIRETAS,
    FATURAMENTO,
    IMPOSTOS,
    RECEITA,
    RESERVA_BONUS,
)

#: Areas that can hold a budget. 'institucional' is the consolidated view.
BUDGET_AREAS = ("institucional", *AREAS)

#: The DRE lines an admin/client can budget (subtotals/margins are derived, so
#: they are intentionally excluded from manual entry).
BUDGET_LINES: tuple[tuple[str, str], ...] = (
    (FATURAMENTO, "Faturamento"),
    (RECEITA, "Receita (recebimento)"),
    (CUSTOS_DIRETOS, "Custos Diretos"),
    (DESPESAS_INDIRETAS, "Despesas Indiretas"),
    (IMPOSTOS, "Impostos"),
    (AMORTIZACAO, "Amortizacao"),
    (RESERVA_BONUS, "Reserva de Bonus"),
)

_BUDGET_LINE_KEYS = {k for k, _ in BUDGET_LINES}


@dataclass(frozen=True)
class BudgetEntry:
    client_id: str
    ano: int
    area: str
    line_key: str
    annual_amount: float


def is_valid_line(line_key: str) -> bool:
    return line_key in _BUDGET_LINE_KEYS


def is_valid_area(area: str) -> bool:
    return area in BUDGET_AREAS


def monthly_budget(entries: list[BudgetEntry]) -> dict[str, dict[str, float]]:
    """Fold budget entries into {area: {line_key: monthly_amount}}."""
    out: dict[str, dict[str, float]] = {}
    for e in entries:
        area_map = out.setdefault(e.area, {})
        area_map[e.line_key] = round(e.annual_amount / 12.0, 2)
    return out
