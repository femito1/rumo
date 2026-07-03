# backend/tests/test_manual_actuals.py
import pytest

from app.closing.dre import DESPESA_INSTITUCIONAL, RECEBIMENTO, assemble_dre_sections
from app.manual.models import ManualActual, by_area


def _row(rows, key):
    return next(r for r in rows if r.get("key") == key)


def test_by_area_folds_entries():
    entries = [
        ManualActual("mbc", "2026-02", "Contencioso", DESPESA_INSTITUCIONAL, 35425.45),
        ManualActual("mbc", "2026-02", "Arbitragem", DESPESA_INSTITUCIONAL, 29858.04),
    ]
    folded = by_area(entries)
    assert folded["Contencioso"][DESPESA_INSTITUCIONAL] == pytest.approx(35425.45)
    assert folded["Arbitragem"][DESPESA_INSTITUCIONAL] == pytest.approx(29858.04)


def test_recebimento_is_sisjuri_derived_and_ignores_manual_override():
    """Recebimento is SISJURI-derived; a stray manual recebimento must NOT win."""
    import json
    from pathlib import Path

    snap = json.loads(
        (Path(__file__).parent / "fixtures" / "sisjuri_2026_02.json").read_text(
            encoding="utf-8"
        )
    )
    # Even if a legacy manual recebimento is present, the SISJURI value wins.
    manual = {"Contencioso": {RECEBIMENTO: 999999.99}}
    sections = assemble_dre_sections(
        snapshot=snap, budget=None, period_label="Fev 2026", manual=manual
    )
    rows = sections["contencioso"]["rows"]
    receb = _row(rows, RECEBIMENTO)
    assert receb["Realizado"]["value"] == pytest.approx(133202.74, abs=0.05)
    resultado = _row(rows, "resultado_bruto")
    assert resultado["Realizado"]["value"] is not None
