# backend/app/sources/fixture.py
from __future__ import annotations
from app.sources.base import SectionKey, DayRange, SectionData
from app.closing.period import Period

class FixtureSource:
    """Minimal, deterministic placeholder data for the demo client.

    Exists only to demonstrate the admin multi-client view. NOT real data.
    """
    name = "fixture"

    def supports(self) -> set[SectionKey]:
        return {SectionKey.META, SectionKey.BASE_RESULTADO}

    def fetch(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        seed = period.month * 1000
        receita = float(120000 + seed)
        faturamento = float(180000 + seed)
        return {
            SectionKey.META: {
                "kpis": {
                    "receita_honorarios": receita,
                    "faturamento_realizado": faturamento,
                    "faturas_emitidas": 5 + period.month,
                },
            },
            SectionKey.BASE_RESULTADO: {
                "lines": [
                    {"row": 4, "label": "Receita de honorários", "value": receita, "origin": "fixture", "indent": 0, "is_total": False},
                ],
            },
        }
