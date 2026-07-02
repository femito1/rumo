# backend/tests/test_manual_actuals.py
import pytest

from app.closing.dre import RECEBIMENTO, assemble_dre_sections
from app.manual.models import ManualActual, by_area


def _row(rows, key):
    return next(r for r in rows if r.get("key") == key)


def test_by_area_folds_entries():
    entries = [
        ManualActual("mbc", "2026-02", "Contencioso", RECEBIMENTO, 138600.13),
        ManualActual("mbc", "2026-02", "Arbitragem", RECEBIMENTO, 86846.33),
    ]
    folded = by_area(entries)
    assert folded["Contencioso"][RECEBIMENTO] == pytest.approx(138600.13)
    assert folded["Arbitragem"][RECEBIMENTO] == pytest.approx(86846.33)


def test_manual_recebimento_fills_area_tab_and_computes_resultado():
    import json
    from pathlib import Path

    snap = json.loads(
        (Path(__file__).parent / "fixtures" / "sisjuri_2026_02.json").read_text(
            encoding="utf-8"
        )
    )
    manual = {"Contencioso": {RECEBIMENTO: 138600.13}}
    sections = assemble_dre_sections(
        snapshot=snap, budget=None, period_label="Fev 2026", manual=manual
    )
    rows = sections["contencioso"]["rows"]
    receb = _row(rows, RECEBIMENTO)
    assert receb["Realizado"]["value"] == pytest.approx(138600.13, abs=0.05)
    # Resultado Bruto = recebimento - custo equipe (- comissao/despesas if any)
    resultado = _row(rows, "resultado_bruto")
    assert resultado["Realizado"]["value"] is not None
