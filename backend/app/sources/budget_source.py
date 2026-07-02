# backend/app/sources/budget_source.py
"""Source that emits the standalone Orcamento (budget) table.

Variance (Orcado x Realizado) is computed in ``app.closing.dre`` where budget
and realizado meet; this Source contributes the ``ORCAMENTO_2026`` reference
tab so the budget is always visible even when no snapshot exists yet.
"""
from __future__ import annotations

from app.budget.models import (
    BUDGET_LINES,
    BudgetEntry,
    canonical_line_key,
    monthly_budget,
)
from app.closing.period import Period
from app.sources.base import DayRange, SectionData, SectionKey


class BudgetSource:
    name = "budget"

    def __init__(self, entries: list[BudgetEntry]) -> None:
        self._entries = entries

    def supports(self) -> set[SectionKey]:
        return {SectionKey.ORCAMENTO_2026}

    def fetch(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        # Annual comes straight from the stored entry (source of truth); monthly
        # is the even split. Avoids annual != monthly*12 rounding drift.
        annual_by_key = {
            canonical_line_key(e.line_key): e.annual_amount
            for e in self._entries
            if e.area == "institucional"
        }
        monthly_by_key = monthly_budget(self._entries).get("institucional", {})
        rows = []
        for key, label in BUDGET_LINES:
            annual = annual_by_key.get(key)
            monthly = monthly_by_key.get(key)
            rows.append(
                {
                    "Linha": label,
                    "Mensal (Orcado)": {"value": monthly, "source": "orcado"},
                    "Anual (Orcado)": {"value": annual, "source": "orcado"},
                }
            )
        return {
            SectionKey.ORCAMENTO_2026: {
                "kind": "rich",
                "name": "Orcamento 2026",
                "columns": ["Linha", "Mensal (Orcado)", "Anual (Orcado)"],
                "rows": rows,
                "source": self.name,
            }
        }
