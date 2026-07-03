# backend/tests/test_meta_tab.py
"""Meta goal-tracking dashboard (workbook 'Meta' sheet).

Headline: annual recebimento goal (8.060.000), monthly goal, this-month
attainment, remaining. Plus the 12-month goal table with the realized month
filled in from the snapshot's recebimento.
"""
import json
from pathlib import Path

import pytest

from app.closing.dre import assemble_dre_sections

FIXTURE = Path(__file__).parent / "fixtures" / "sisjuri_2026_02.json"


@pytest.fixture
def snapshot() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_meta_tab_emitted_with_annual_goal(snapshot):
    budget = {"institucional": {"recebimento": 671666.67}}  # monthly (annual/12)
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=budget, period_label="Fevereiro 2026",
    )
    assert "meta_dashboard" in sections
    meta = sections["meta_dashboard"]
    assert meta["kind"] == "rich"
    assert meta["meta_anual"]["value"] == pytest.approx(8060000.0, abs=1.0)
    assert meta["meta_mensal"]["value"] == pytest.approx(671666.67, abs=0.5)


def test_meta_table_has_twelve_months_with_realized_month(snapshot):
    budget = {"institucional": {"recebimento": 671666.67}}
    sections = assemble_dre_sections(
        snapshot=snapshot, budget=budget, period_label="Fevereiro 2026",
    )
    meta = sections["meta_dashboard"]
    month_rows = [r for r in meta["rows"] if r.get("kind") != "total"]
    assert len(month_rows) == 12
    fev = next(r for r in meta["rows"] if r["Mês"] == "Fevereiro")
    # Realized recebimento for the competence month appears in the Recebimento col.
    assert fev["Recebimento"]["value"] == pytest.approx(319233.58, abs=0.05)
    # Other months have no realized recebimento (single-snapshot flow).
    jan = next(r for r in meta["rows"] if r["Mês"] == "Janeiro")
    assert jan["Recebimento"]["value"] is None


def test_meta_tab_missing_goal_is_blank():
    sections = assemble_dre_sections(
        snapshot=None, budget=None, period_label="Jan 2026",
    )
    meta = sections["meta_dashboard"]
    assert meta["meta_anual"]["value"] is None
