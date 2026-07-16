# backend/app/closing/provider.py
from __future__ import annotations
from datetime import datetime, timezone
from app.closing.available import is_closeable
from app.closing.period import Period
from app.closing.tab_layouts import TAB_ORDER
from app.sources.assembler_source import AssemblerSource
from app.sources.base import SectionKey, DayRange, Source, SectionData
from app.sources.budget_source import BudgetSource
from app.sources.fixture import FixtureSource
from app.sources.legaldesk import LegalDeskSource
from app.sources.sisjuri_db import SisjuriDbSource
from app.tenancy.models import Client

class ClosingProvider:
    def __init__(self, sources: list[Source]) -> None:
        self.sources = sources

    def _merge(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        merged: dict[SectionKey, SectionData] = {}
        for src in self.sources:                       # ordered; later overrides earlier
            for key, data in src.fetch(period, day_range).items():
                merged[key] = data
        return merged

    def build_closing(self, *, client: Client, period: Period, day_range: DayRange) -> dict:
        sections = self._merge(period, day_range)
        meta_kpis = dict(sections.get(SectionKey.META, {}).get("kpis", {}))
        meta_kpis.update(_headline_kpis_from_dre(sections.get(SectionKey.INSTITUCIONAL)))
        tabs = {k.value: v for k, v in sections.items()}
        return {
            "client": {"id": client.id, "name": client.name},
            "period": {"ano_mes": period.ano_mes, "label": period.label, "column_letter": period.column_letter},
            "day_range": {"from": day_range.start, "to": day_range.end, "is_full_month": day_range.is_full_month},
            "kpis": meta_kpis,
            "tab_order": [t for t in TAB_ORDER if t in tabs] or list(tabs.keys()),
            "tabs": tabs,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

def _headline_kpis_from_dre(institucional: SectionData | None) -> dict[str, float | None]:
    """Extract headline KPIs from the assembled institucional DRE rows.

    Returns an empty dict when the section is not the assembled DRE (e.g. only
    LegalDesk ran). Keys mirror the canonical line-keys in ``app.closing.dre``.
    """
    if not institucional or not isinstance(institucional, dict):
        return {}
    rows = institucional.get("rows")
    if not isinstance(rows, list):
        return {}
    wanted = {
        "resultado_bruto",
        "margem_bruta",
        "resultado_liquido",
        "margem_liquida",
        "reserva_bonus",
    }
    out: dict[str, float | None] = {}
    for row in rows:
        key = row.get("key")
        if key not in wanted:
            continue
        cell = row.get("Realizado")
        out[key] = cell.get("value") if isinstance(cell, dict) else None
    return out


def _snapshot_store():
    """Indirection so tests can inject a store; imported lazily to avoid cycles."""
    from app.api.providers import get_snapshot_store

    return get_snapshot_store()


def _budget_repo():
    """Lazy budget repo lookup; imported lazily to avoid import cycles."""
    from app.api.providers import get_budget_repo

    return get_budget_repo()


def _transfers_repo():
    """Lazy area-transfers repo lookup; imported lazily to avoid import cycles."""
    from app.api.providers import get_transfers_repo

    return get_transfers_repo()


def build_provider_for(client: Client, *, period: Period | None = None) -> ClosingProvider:
    """Resolve a client's `provider` column to an ordered list of Sources (spec §4)."""
    if client.provider == "legaldesk":
        return ClosingProvider(sources=[LegalDeskSource()])
    if client.provider == "fixture":
        return ClosingProvider(sources=[FixtureSource()])
    if client.provider == "legaldesk+sisjuri":
        # Order matters: later overrides earlier.
        #   1. LegalDesk  -> revenue/rateio/invoices + KPI-bearing META.
        #   2. SisjuriDb  -> raw expense detail (INSTITUCIONAL_ANO) + RATEIO_MENSAL.
        #   3. Budget     -> ORCAMENTO_2026 reference table.
        #   4. Assembler  -> computed DRE (Orcado x Realizado) over institucional
        #      + area blocks + areas_sintetico + dre_2026 + amortizacao.
        sources: list[Source] = [LegalDeskSource()]

        snapshot = None
        if period is not None:
            snapshot = _snapshot_store().get(period.ano_mes, client_id=client.id)
        if snapshot is not None:
            sources.append(SisjuriDbSource.from_snapshot(snapshot, emit_meta=False))

        budget_monthly: dict[str, dict[str, float]] | None = None
        entries = []
        if period is not None:
            try:
                from app.budget.models import monthly_budget

                entries = _budget_repo().get_budget(client.id, period.year)
                budget_monthly = (
                    monthly_budget(entries, month=period.month) if entries else None
                )
            except Exception:  # pragma: no cover - budget is best-effort overlay
                budget_monthly = None
        sources.append(BudgetSource(entries))

        transfers = None
        if period is not None:
            try:
                transfers = _transfers_repo().get_transfers(client.id, period.ano_mes)
            except Exception:  # pragma: no cover - transfers overlay is best-effort
                transfers = None

        # Workbook verification overlay (hard rule): blank any Realizado cell that
        # diverges from the authoritative workbook target by more than R$0,01.
        targets = None
        if period is not None:
            try:
                from app.closing.workbook_targets import targets_for

                targets = targets_for(period)
            except Exception:  # pragma: no cover - targets overlay is best-effort
                targets = None

        # Meta dashboard: per-month realized recebimento for the whole competence
        # year, so the 12-month table fills every CLOSED month (not just the
        # competence one). Future months are absent from the map -> blank.
        ytd_recebimento: dict[int, float] | None = None
        if period is not None:
            try:
                full = _snapshot_store().recebimento_by_year(
                    period.year, client_id=client.id
                )
                ytd_recebimento = {
                    m: v
                    for m, v in full.items()
                    if is_closeable(f"{period.year:04d}-{m:02d}")
                }
            except Exception:  # pragma: no cover - meta YTD is best-effort overlay
                ytd_recebimento = None

        sources.append(
            AssemblerSource(
                snapshot=snapshot,
                budget=budget_monthly,
                transfers=transfers,
                targets=targets,
                ytd_recebimento=ytd_recebimento,
            )
        )
        return ClosingProvider(sources=sources)
    raise ValueError(f"unknown provider: {client.provider}")
