# backend/tests/test_sources_base.py
from app.sources.base import SectionKey, DayRange
from app.closing.period import Period

def test_sectionkey_has_the_fifteen_tabs():
    assert SectionKey.META in SectionKey
    assert SectionKey.BASE_RESULTADO in SectionKey
    assert len(list(SectionKey)) == 15

def test_dayrange_full_month_from_period():
    p = Period.parse("2026-05")
    dr = DayRange.full_month(p)
    assert dr.start == "2026-05-01"
    assert dr.end == "2026-06-01"
    assert dr.is_full_month is True

def test_dayrange_partial_within_month():
    p = Period.parse("2026-05")
    dr = DayRange.within(p, from_day=1, to_day=15)
    assert dr.start == "2026-05-01"
    assert dr.end == "2026-05-16"   # end-exclusive
    assert dr.is_full_month is False
