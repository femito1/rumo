# backend/tests/test_sisjuri_db_source.py
import json
from pathlib import Path

import pytest

from app.sources.base import DayRange, SectionKey
from app.sources.sisjuri_db import BONUS_RESERVE_RATE, SisjuriDbSource
from app.closing.period import Period

FIXTURE = Path(__file__).parent / "fixtures" / "sisjuri_2026_02.json"


@pytest.fixture
def snapshot() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def source(snapshot) -> SisjuriDbSource:
    return SisjuriDbSource.from_snapshot(snapshot)


def test_supports_the_sections_it_produces(source):
    supported = source.supports()
    assert SectionKey.META in supported
    assert SectionKey.INSTITUCIONAL in supported


def test_augment_mode_emits_only_institucional(snapshot):
    # When composed after another source, avoid clobbering META wholesale.
    src = SisjuriDbSource.from_snapshot(snapshot, emit_meta=False)
    assert SectionKey.META not in src.supports()
    p = Period.parse("2026-02")
    out = src.fetch(p, DayRange.full_month(p))
    assert SectionKey.META not in out
    assert SectionKey.INSTITUCIONAL in out


def test_meta_carries_revenue_kpis(source):
    p = Period.parse("2026-02")
    out = source.fetch(p, DayRange.full_month(p))
    kpis = out[SectionKey.META]["kpis"]
    assert abs(kpis["receita_honorarios"] - 319233.58) <= 0.05
    assert abs(kpis["faturamento_realizado"] - 534752.84) <= 0.05
    assert kpis["faturas_emitidas"] == 48


def test_expense_accounts_are_grouped_by_family(source):
    p = Period.parse("2026-02")
    out = source.fetch(p, DayRange.full_month(p))
    inst = out[SectionKey.INSTITUCIONAL]
    totals = inst["totais_por_tipo"]
    # D = institucional, C = pessoal, I = investimentos (verified figures)
    assert abs(totals["D"] - 68771.58) <= 0.05
    assert abs(totals["C"] - 215310.35) <= 0.05
    assert abs(totals["I"] - 30913.70) <= 0.05


def test_prolabore_uses_gross_valor_base(source):
    p = Period.parse("2026-02")
    out = source.fetch(p, DayRange.full_month(p))
    pro = out[SectionKey.INSTITUCIONAL]["prolabore_bruto_total"]
    # 12 x 1621 gross (workbook), NOT 12 x 1442.69 net
    assert abs(pro - 12 * 1621) <= 0.05


def test_bonus_reserve_is_ten_percent_of_net_margin(source):
    # Fixed formula confirmed by finance: reserva de bônus = 10% da margem líquida.
    assert BONUS_RESERVE_RATE == pytest.approx(0.10)
    net_margin = 100000.0
    assert source.bonus_reserve(net_margin) == pytest.approx(10000.0)
