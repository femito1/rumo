# backend/tests/test_dre_assembler.py
import json
from pathlib import Path

import pytest

from app.closing.dre import (
    FATURAMENTO,
    RESULTADO_BRUTO,
    RESERVA_BONUS,
    RealizadoInputs,
    assemble_dre_sections,
    bonus_reserve,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sisjuri_2026_02.json"


@pytest.fixture
def snapshot() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _row(rows, key):
    return next(r for r in rows if r.get("key") == key)


def test_realizado_inputs_from_snapshot(snapshot):
    r = RealizadoInputs.from_snapshot(snapshot)
    assert r.faturamento == pytest.approx(534752.84, abs=0.05)
    assert r.receita == pytest.approx(319233.58, abs=0.05)
    # custos diretos prefers the per-area breakdown when present
    expected = 70796.83 + 49941.93 + 94571.59
    assert r.custos_diretos == pytest.approx(expected, abs=0.05)


def test_bonus_reserve_is_ten_percent():
    assert bonus_reserve(100000.0) == pytest.approx(10000.0)


def test_institucional_block_computes_resultado_and_margin(snapshot):
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026"
    )
    inst = sections["institucional"]
    assert inst["kind"] == "rich"
    assert inst["snapshot_missing"] is False
    rows = inst["rows"]
    fat = _row(rows, FATURAMENTO)
    assert fat["Realizado"]["value"] == pytest.approx(534752.84, abs=0.05)
    rb = _row(rows, RESULTADO_BRUTO)
    # resultado bruto = faturamento - custos diretos - despesas indiretas
    assert rb["is_total"] is True
    assert rb["Realizado"]["value"] is not None


def test_variance_and_desvio_when_budget_present(snapshot):
    budget = {"institucional": {FATURAMENTO: 671666.67}}
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=budget, period_label="Fev 2026"
    )
    fat = _row(sections["institucional"]["rows"], FATURAMENTO)
    assert fat["Orcado"]["value"] == pytest.approx(671666.67, abs=0.05)
    # variacao = realizado - orcado
    assert fat["Variacao"]["value"] == pytest.approx(534752.84 - 671666.67, abs=0.1)
    # desvio = realizado / orcado
    assert fat["Desvio %"] == pytest.approx(534752.84 / 671666.67, abs=0.001)


def test_orcado_null_when_no_budget(snapshot):
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026"
    )
    fat = _row(sections["institucional"]["rows"], FATURAMENTO)
    assert fat["Orcado"]["value"] is None
    assert fat["Variacao"]["value"] is None


def test_snapshot_missing_yields_zero_realizado_and_flag():
    sections = assemble_dre_sections(
        snapshot=None, budget=None, period_label="Jan 2026"
    )
    inst = sections["institucional"]
    assert inst["snapshot_missing"] is True
    fat = _row(inst["rows"], FATURAMENTO)
    assert fat["Realizado"]["value"] == pytest.approx(0.0)


def test_all_four_dre_blocks_present(snapshot):
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026"
    )
    for key in ("institucional", "contencioso", "economico", "arbitragem", "areas_sintetico"):
        assert key in sections
        assert sections[key]["kind"] == "rich"


def test_reserva_bonus_row_present(snapshot):
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026"
    )
    reserva = _row(sections["institucional"]["rows"], RESERVA_BONUS)
    assert reserva["Realizado"]["value"] is not None
