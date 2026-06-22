# backend/tests/test_available.py
from datetime import date
from app.closing.available import available_months, is_closeable

def test_past_month_is_closeable():
    assert is_closeable("2026-05", today=date(2026, 6, 21)) is True

def test_current_month_not_closeable():
    assert is_closeable("2026-06", today=date(2026, 6, 21)) is False

def test_future_month_not_closeable():
    assert is_closeable("2026-12", today=date(2026, 6, 21)) is False

def test_available_months_descending_and_bounded():
    months = available_months(today=date(2026, 6, 21), back=3)
    assert months == ["2026-05", "2026-04", "2026-03"]
