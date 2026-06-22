# backend/tests/test_juritis_placeholder.py
import pytest
from app.sources.juritis import JuritisSource
from app.closing.period import Period
from app.sources.base import DayRange

def test_juritis_supports_nothing_yet():
    assert JuritisSource().supports() == set()

def test_juritis_fetch_not_implemented():
    src = JuritisSource()
    with pytest.raises(NotImplementedError):
        src.fetch(Period.parse("2026-05"), DayRange.full_month(Period.parse("2026-05")))
