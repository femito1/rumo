# backend/app/sources/legaldesk.py
from __future__ import annotations
from app.sources.base import SectionKey, DayRange, SectionData
from app.sources.legaldesk_client import LegalDeskClient, _LegalDeskSettings
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

    def __init__(
        self,
        client: LegalDeskClient | None = None,
        *,
        settings: _LegalDeskSettings | None = None,
        _recorded: dict | None = None,
    ) -> None:
        self._client = client
        #: Per-client credentials (from ``clients.provider_config``). Held rather than
        #: used so the HTTP client is built only if ``fetch`` actually needs it —
        #: ``build_provider_for`` runs on every request and a recorded payload or a
        #: SISJURI snapshot often answers instead.
        self.settings = settings
        self._recorded = _recorded

    @classmethod
    def from_recorded_payload(cls, payload: dict) -> "LegalDeskSource":
        return cls(_recorded=payload)

    def supports(self) -> set[SectionKey]:
        return set(_ALL)

    def _http_client(self) -> LegalDeskClient | None:
        """Build the HTTP client on first real use, with this tenant's credentials."""
        if self._client is None and self.settings is not None:
            self._client = LegalDeskClient(self.settings)
        return self._client

    def fetch(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        # A recorded payload short-circuits before any client is built — which is why
        # the sacred-numbers fixture test never touches credentials.
        payload = (
            self._recorded
            if self._recorded is not None
            else build_payload(period, self._http_client())
        )
        tabs = payload["tabs"]
        out: dict[SectionKey, SectionData] = {}
        for key in SectionKey:
            if key.value in tabs:
                out[key] = tabs[key.value]
        # Carry KPIs alongside META so the provider can assemble headline numbers.
        out[SectionKey.META] = {**out.get(SectionKey.META, {}), "kpis": payload.get("kpis", {})}
        return out
