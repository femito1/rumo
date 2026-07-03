# backend/tests/test_faturas_analitico.py
"""Per-case faturamento detail tab ('FATURAS Analitico' grain).

Built from the SISJURI snapshot's faturas_analitico (POSFIN_RESULTFAT split by
CASE, joined to área). One row per case: código, assunto, área, total, n.
"""
import json
from pathlib import Path

import pytest

from app.closing.dre import assemble_dre_sections

FIXTURE = Path(__file__).parent / "fixtures" / "sisjuri_2026_02.json"


@pytest.fixture
def snapshot() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_faturas_analitico_tab_emitted(snapshot):
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fevereiro 2026",
    )
    assert "faturas_analitico" in sections
    tab = sections["faturas_analitico"]
    assert tab["kind"] == "rich"
    assert tab["columns"] == ["Código", "Caso", "Área", "Faturamento"]
    rows = [r for r in tab["rows"] if r.get("kind") != "total"]
    assert len(rows) == 2
    econ = next(r for r in tab["rows"] if r["Caso"] == "Ream - Trabalhos Adicionais")
    assert econ["Faturamento"]["value"] == pytest.approx(42730.54, abs=0.05)
    assert econ["Área"] == "Direito Econômico"


def test_faturas_analitico_total_row(snapshot):
    tab = assemble_dre_sections(
        snapshot=snapshot, budget=None, period_label="Fev 2026",
    )["faturas_analitico"]
    total = next(r for r in tab["rows"] if r.get("kind") == "total")
    assert total["Faturamento"]["value"] == pytest.approx(42730.54 + 350.0, abs=0.05)


def test_faturas_analitico_empty_when_absent():
    tab = assemble_dre_sections(
        snapshot={}, budget=None, period_label="Fev 2026",
    )["faturas_analitico"]
    assert [r for r in tab["rows"] if r.get("kind") != "total"] == []
