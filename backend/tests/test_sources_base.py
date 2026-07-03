# backend/tests/test_sources_base.py
from app.sources.base import SectionKey, DayRange
from app.closing.period import Period

def test_sectionkey_has_the_fifteen_tabs():
    assert SectionKey.META in SectionKey
    assert SectionKey.BASE_RESULTADO in SectionKey
    # 15 workbook tabs + META_DASHBOARD + FATURAS_ANALITICO (derived views).
    assert len(list(SectionKey)) == 17
    assert SectionKey.META_DASHBOARD in SectionKey
    assert SectionKey.FATURAS_ANALITICO in SectionKey

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


def test_period_days_in_month():
    assert Period.parse("2026-02").days_in_month == 28  # non-leap
    assert Period.parse("2024-02").days_in_month == 29  # leap
    assert Period.parse("2026-04").days_in_month == 30
    assert Period.parse("2026-05").days_in_month == 31


def test_dayrange_clamps_to_month_length_february():
    p = Period.parse("2026-02")  # 28 days
    dr = DayRange.within(p, from_day=10, to_day=31)
    assert dr.start == "2026-02-10"
    # to_day clamped to 28 (the last day) -> end rolls to next month's 1st,
    # never the invalid "2026-02-29"/"2026-02-32".
    assert dr.end == "2026-03-01"
    assert dr.is_full_month is False


def test_dayrange_last_day_rolls_to_next_month():
    p = Period.parse("2026-05")  # 31 days
    dr = DayRange.within(p, from_day=20, to_day=31)
    assert dr.start == "2026-05-20"
    assert dr.end == "2026-06-01"


def test_dayrange_full_span_marks_full_month():
    p = Period.parse("2026-04")  # 30 days
    dr = DayRange.within(p, from_day=1, to_day=30)
    assert dr.is_full_month is True
