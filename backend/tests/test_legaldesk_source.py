# backend/tests/test_legaldesk_source.py
import json
from pathlib import Path
import pytest
from app.sources.legaldesk import LegalDeskSource
from app.sources.base import SectionKey, DayRange
from app.closing.period import Period

FIXTURE = Path(__file__).parent / "fixtures" / "legaldesk_2026_05.json"

@pytest.fixture
def recorded_payload() -> dict:
    return json.loads(FIXTURE.read_text())

def test_legaldesk_emits_rich_sections_from_recorded_payload(recorded_payload):
    src = LegalDeskSource.from_recorded_payload(recorded_payload)
    p = Period.parse("2026-05")
    out = src.fetch(p, DayRange.full_month(p))
    assert SectionKey.META in out
    assert SectionKey.BASE_RESULTADO in out

def test_legaldesk_verified_totals_locked(recorded_payload):
    kpis = recorded_payload["kpis"]
    assert abs(kpis["receita_honorarios"] - 415927.84) <= 0.05
    assert abs(kpis["faturamento_realizado"] - 719988.05) <= 0.05
    assert kpis["faturas_emitidas"] == 53
