# backend/app/closing/provider.py
from __future__ import annotations
from datetime import datetime, timezone
from app.closing.period import Period
from app.closing.tab_layouts import TAB_ORDER
from app.sources.base import SectionKey, DayRange, Source, SectionData
from app.sources.fixture import FixtureSource
from app.sources.legaldesk import LegalDeskSource
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
        meta_kpis = sections.get(SectionKey.META, {}).get("kpis", {})
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

def build_provider_for(client: Client) -> ClosingProvider:
    """Resolve a client's `provider` column to an ordered list of Sources (spec §4)."""
    if client.provider == "legaldesk":
        return ClosingProvider(sources=[LegalDeskSource()])
    if client.provider == "fixture":
        return ClosingProvider(sources=[FixtureSource()])
    raise ValueError(f"unknown provider: {client.provider}")
