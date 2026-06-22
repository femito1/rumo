# backend/app/sources/legaldesk.py
from __future__ import annotations
from app.sources.base import SectionKey, DayRange, SectionData
from app.sources.legaldesk_client import LegalDeskClient
from app.closing.builder import build_payload
from app.closing.period import Period

# All 15 SectionKeys are produced by the existing builder payload.
_ALL = set(SectionKey)

class LegalDeskSource:
    """Wraps the verified LegalDeskClient + build_payload behind the Source interface.

    `build_payload` already returns the full tab structure; this source adapts that into
    the SectionKey-keyed dict the ClosingProvider consumes. Behavior of the underlying
    numbers is unchanged and locked by recorded-fixture tests.
    """
    name = "legaldesk"

    def __init__(self, client: LegalDeskClient | None = None, *, _recorded: dict | None = None) -> None:
        self._client = client
        self._recorded = _recorded

    @classmethod
    def from_recorded_payload(cls, payload: dict) -> "LegalDeskSource":
        return cls(_recorded=payload)

    def supports(self) -> set[SectionKey]:
        return set(_ALL)

    def fetch(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        payload = self._recorded if self._recorded is not None else build_payload(period, self._client)
        tabs = payload["tabs"]
        out: dict[SectionKey, SectionData] = {}
        for key in SectionKey:
            if key.value in tabs:
                out[key] = tabs[key.value]
        # Carry KPIs alongside META so the provider can assemble headline numbers.
        out[SectionKey.META] = {**out.get(SectionKey.META, {}), "kpis": payload.get("kpis", {})}
        return out
