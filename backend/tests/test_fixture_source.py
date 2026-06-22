# backend/tests/test_fixture_source.py
from app.sources.fixture import FixtureSource
from app.sources.base import SectionKey, DayRange
from app.closing.period import Period

def test_fixture_is_deterministic_and_minimal():
    src = FixtureSource()
    p = Period.parse("2026-05")
    dr = DayRange.full_month(p)
    a = src.fetch(p, dr)
    b = src.fetch(p, dr)
    assert a == b
    assert SectionKey.META in src.supports()
    assert SectionKey.META in a
    assert a[SectionKey.META]["kpis"]["receita_honorarios"] >= 0
