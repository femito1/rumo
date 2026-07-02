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
    assert SectionKey.INSTITUCIONAL_ANO in supported
    assert SectionKey.RATEIO_MENSAL in supported


def test_augment_mode_emits_only_institucional(snapshot):
    # When composed after another source, avoid clobbering META wholesale.
    src = SisjuriDbSource.from_snapshot(snapshot, emit_meta=False)
    assert SectionKey.META not in src.supports()
    p = Period.parse("2026-02")
    out = src.fetch(p, DayRange.full_month(p))
    assert SectionKey.META not in out
    assert SectionKey.INSTITUCIONAL_ANO in out


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
    inst = out[SectionKey.INSTITUCIONAL_ANO]
    totals = inst["totais_por_tipo"]
    # D = institucional, C = pessoal, I = investimentos (verified figures)
    assert abs(totals["D"] - 68771.58) <= 0.05
    assert abs(totals["C"] - 215310.35) <= 0.05
    assert abs(totals["I"] - 30913.70) <= 0.05


def test_prolabore_uses_gross_valor_base(source):
    p = Period.parse("2026-02")
    out = source.fetch(p, DayRange.full_month(p))
    pro = out[SectionKey.INSTITUCIONAL_ANO]["prolabore_bruto_total"]
    # 12 x 1621 gross (workbook), NOT 12 x 1442.69 net
    assert abs(pro - 12 * 1621) <= 0.05


def test_bonus_reserve_is_ten_percent_of_net_margin(source):
    # Fixed formula confirmed by finance: reserva de bônus = 10% da margem líquida.
    assert BONUS_RESERVE_RATE == pytest.approx(0.10)
    net_margin = 100000.0
    assert source.bonus_reserve(net_margin) == pytest.approx(10000.0)


def test_institucional_is_a_rich_grouped_tree(source):
    p = Period.parse("2026-02")
    out = source.fetch(p, DayRange.full_month(p))
    inst = out[SectionKey.INSTITUCIONAL_ANO]
    assert inst["kind"] == "rich"
    assert inst["columns"] == ["Conta", "Valor", "Lancamentos"]
    # A section subtotal row (is_total) precedes its indented sub-accounts.
    section_rows = [r for r in inst["rows"] if r["is_total"]]
    sub_rows = [r for r in inst["rows"] if not r["is_total"]]
    assert section_rows and sub_rows
    # "Ocupação" is a known parent section in the fixture.
    assert any(r["Conta"] == "Ocupação" for r in section_rows)


def test_prolabore_rows_expose_per_socio(source):
    p = Period.parse("2026-02")
    out = source.fetch(p, DayRange.full_month(p))
    pro = out[SectionKey.INSTITUCIONAL_ANO]["prolabore"]
    assert len(pro) == 12
    assert pro[0]["Bruto"]["value"] == pytest.approx(1621.0)


def test_rateio_mensal_has_area_and_lawyer_detail(source):
    p = Period.parse("2026-02")
    out = source.fetch(p, DayRange.full_month(p))
    rateio = out[SectionKey.RATEIO_MENSAL]
    assert rateio["kind"] == "rich"
    assert len(rateio["rows"]) == 3  # three cost-center areas in the fixture
    assert len(rateio["rateio_profissional"]) == 13  # per-lawyer rows


def test_distribuicao_socio_tolerates_null(source):
    # The fixture has distribuicao_socio: null; must not crash and yields [].
    p = Period.parse("2026-02")
    out = source.fetch(p, DayRange.full_month(p))
    assert out[SectionKey.INSTITUCIONAL_ANO]["distribuicao_socio"] == []
