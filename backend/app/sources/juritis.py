# backend/app/sources/juritis.py
from __future__ import annotations
from app.sources.base import SectionKey, DayRange, SectionData
from app.closing.period import Period

class JuritisSource:
    """PLACEHOLDER for the Juritis / TOTVS Backoffice API (not yet accessible).

    When credentials arrive, implement `supports()` to return the institutional-expense
    SectionKeys it can fill and `fetch()` to emit them. Three integration paths are
    documented in docs/superpowers/specs/2026-06-21-rumo-multi-client-platform-design.md §4:
    additive, partial override, or full replacement. Do NOT guess the API shape until we
    have access.
    """
    name = "juritis"

    def supports(self) -> set[SectionKey]:
        return set()

    def fetch(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        raise NotImplementedError("JuritisSource is not wired yet (no API access).")
