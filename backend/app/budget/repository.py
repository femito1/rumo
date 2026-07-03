# backend/app/budget/repository.py
"""Budget persistence. Mirrors the tenancy repository pattern (supabase-py in
prod, in-memory fixture for USE_FAKE_REPO)."""
from __future__ import annotations

from typing import Protocol

from app.budget.models import BudgetEntry


class BudgetRepository(Protocol):
    def get_budget(self, client_id: str, ano: int) -> list[BudgetEntry]: ...
    def set_budget(self, client_id: str, ano: int, entries: list[BudgetEntry]) -> None: ...


def _row_to_entry(row: dict) -> BudgetEntry:
    raw_months = row.get("monthly_amounts")
    months: tuple[float, ...] | None = None
    if raw_months:
        try:
            vals = [float(x) for x in raw_months]
            if len(vals) == 12:
                months = tuple(vals)
        except (TypeError, ValueError):
            months = None
    return BudgetEntry(
        client_id=str(row["client_id"]),
        ano=int(row["ano"]),
        area=str(row.get("area", "institucional")),
        line_key=str(row["line_key"]),
        annual_amount=float(row.get("annual_amount", 0.0) or 0.0),
        monthly_amounts=months,
    )


class SupabaseBudgetRepository:
    def __init__(self, client) -> None:
        self._c = client

    def get_budget(self, client_id: str, ano: int) -> list[BudgetEntry]:
        res = (
            self._c.table("budgets")
            .select("*")
            .eq("client_id", client_id)
            .eq("ano", ano)
            .execute()
        )
        return [_row_to_entry(r) for r in (res.data or [])]

    def set_budget(self, client_id: str, ano: int, entries: list[BudgetEntry]) -> None:
        payload = [
            {
                "client_id": client_id,
                "ano": ano,
                "area": e.area,
                "line_key": e.line_key,
                "annual_amount": e.effective_annual(),
                "monthly_amounts": list(e.monthly_amounts)
                if e.monthly_amounts
                else None,
            }
            for e in entries
        ]
        if payload:
            self._c.table("budgets").upsert(
                payload, on_conflict="client_id,ano,area,line_key"
            ).execute()


class InMemoryBudgetRepository:
    """Fixture repo. Seeds a placeholder Institucional budget so variance renders
    immediately in demos (workbook Meta = 8.060.000/ano)."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, int], list[BudgetEntry]] = {}

    @classmethod
    def seeded(cls) -> "InMemoryBudgetRepository":
        repo = cls()
        from app.closing.dre import CUSTO_EQUIPE, DESPESAS, IMPOSTO, RECEBIMENTO

        # Workbook Meta 2026: Recebimento meta 8.060.000/ano (671.666,67/mês),
        # custo direto + despesas indiretas + impostos annualized.
        seed = [
            BudgetEntry("mbc", 2026, "institucional", RECEBIMENTO, 8060000.0),
            BudgetEntry("mbc", 2026, "institucional", CUSTO_EQUIPE, 2403882.65),
            BudgetEntry("mbc", 2026, "institucional", DESPESAS, 1331793.81),
            BudgetEntry("mbc", 2026, "institucional", IMPOSTO, 1809000.0),
        ]
        repo._store[("mbc", 2026)] = seed
        return repo

    def get_budget(self, client_id: str, ano: int) -> list[BudgetEntry]:
        return list(self._store.get((client_id, ano), []))

    def set_budget(self, client_id: str, ano: int, entries: list[BudgetEntry]) -> None:
        self._store[(client_id, ano)] = list(entries)
