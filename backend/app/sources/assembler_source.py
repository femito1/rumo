# backend/app/sources/assembler_source.py
"""Source that emits the assembled DRE views (Orcado x Realizado).

Composed LAST in the provider so it overlays the raw institutional/area tabs
with computed Resultado/Margem/Variacao. It reads the SISJURI snapshot and the
budget directly (not from prior sources) because it needs both together.
"""
from __future__ import annotations

from typing import Any

from app.closing.dre import assemble_dre_sections
from app.closing.period import Period
from app.sources.base import DayRange, SectionData, SectionKey

_VALUE_TO_KEY = {k.value: k for k in SectionKey}


class AssemblerSource:
    name = "assembler"

    def __init__(
        self,
        *,
        snapshot: dict[str, Any] | None,
        budget: dict[str, dict[str, float]] | None,
        manual: dict[str, dict[str, float]] | None = None,
    ) -> None:
        self._snapshot = snapshot
        self._budget = budget
        self._manual = manual

    def supports(self) -> set[SectionKey]:
        return {
            SectionKey.INSTITUCIONAL,
            SectionKey.CONTENCIOSO,
            SectionKey.ECONOMICO,
            SectionKey.ARBITRAGEM,
            SectionKey.AREAS_SINTETICO,
            SectionKey.AMORTIZACAO,
            SectionKey.BASE_RESULTADO,
            SectionKey.RATEIO_MENSAL,
            SectionKey.DRE_2026,
            SectionKey.INSTITUCIONAL_ANO,
            SectionKey.FLUXO_CONSOLIDADO,
        }

    def fetch(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        sections = assemble_dre_sections(
            snapshot=self._snapshot,
            budget=self._budget,
            period_label=period.label,
            manual=self._manual,
        )
        out: dict[SectionKey, SectionData] = {}
        for value, data in sections.items():
            key = _VALUE_TO_KEY.get(value)
            if key is not None:
                out[key] = data
        return out
