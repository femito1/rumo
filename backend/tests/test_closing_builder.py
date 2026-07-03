# backend/tests/test_closing_builder.py
"""Regression: build_payload must not crash on assembler-only tabs.

meta_dashboard and faturas_analitico live in TAB_ORDER (display order) but are
produced by the AssemblerSource, not by LegalDesk. build_payload iterates
TAB_ORDER and looks each id up in TAB_LAYOUTS; assembler-only ids have no
LegalDesk layout, so the loop must skip them instead of raising KeyError.
"""
from app.closing.builder import build_payload
from app.closing.period import Period
from app.closing.tab_layouts import TAB_LAYOUTS


class _EmptyClient:
    """Minimal LegalDeskClient stand-in returning no rows for every primitive."""

    def recebimento_rows(self, ano_mes):
        return []

    def faturamento_rows(self, ano_mes):
        return []

    def rateio_profissional_rows(self, start, end):
        return []

    def fatura_rows(self, start, end):
        return []

    def rateio_caso_rows(self, start, end):
        return []

    def tributo_percentuais(self, ano_mes):
        return {}


def test_build_payload_skips_assembler_only_tabs():
    payload = build_payload(Period.parse("2026-05"), _EmptyClient())
    tabs = payload["tabs"]
    # Assembler-only tabs must not appear in the LegalDesk payload...
    assert "meta_dashboard" not in tabs
    assert "faturas_analitico" not in tabs
    # ...and every tab that IS built must have a real layout.
    for tab_id in tabs:
        assert tab_id in TAB_LAYOUTS
