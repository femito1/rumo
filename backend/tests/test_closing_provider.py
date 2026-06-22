# backend/tests/test_closing_provider.py
from app.closing.provider import ClosingProvider, build_provider_for
from app.closing.period import Period
from app.sources.base import SectionKey, DayRange
from app.sources.fixture import FixtureSource
from app.tenancy.models import Client

def test_provider_builds_payload_shape():
    p = Period.parse("2026-05")
    provider = ClosingProvider(sources=[FixtureSource()])
    payload = provider.build_closing(client=Client(id="demo", name="Cliente Demonstração", provider="fixture", provider_config={}), period=p, day_range=DayRange.full_month(p))
    assert payload["client"] == {"id": "demo", "name": "Cliente Demonstração"}
    assert payload["period"]["ano_mes"] == "2026-05"
    assert payload["period"]["label"] == "Maio 2026"
    assert payload["day_range"]["is_full_month"] is True
    assert "kpis" in payload and "tabs" in payload and "tab_order" in payload

def test_merge_later_source_overrides_earlier_for_same_section():
    class A:
        name = "a"
        def supports(self): return {SectionKey.META}
        def fetch(self, period, day_range): return {SectionKey.META: {"kpis": {"x": 1}}}
    class B:
        name = "b"
        def supports(self): return {SectionKey.META}
        def fetch(self, period, day_range): return {SectionKey.META: {"kpis": {"x": 2}}}
    p = Period.parse("2026-05")
    provider = ClosingProvider(sources=[A(), B()])  # B later -> wins
    payload = provider.build_closing(client=Client(id="t", name="T", provider="x", provider_config={}), period=p, day_range=DayRange.full_month(p))
    assert payload["kpis"]["x"] == 2

def test_build_provider_for_maps_client_to_sources():
    mbc = Client(id="mbc", name="MBC", provider="legaldesk", provider_config={})
    demo = Client(id="demo", name="Cliente Demonstração", provider="fixture", provider_config={})
    assert build_provider_for(mbc).sources[0].name == "legaldesk"
    assert build_provider_for(demo).sources[0].name == "fixture"
