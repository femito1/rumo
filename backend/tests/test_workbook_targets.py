# backend/tests/test_workbook_targets.py
"""The workbook targets feed the hard rule (never show a number that doesn't match).

These lock the verified Realizado targets extracted from the AUTHORITATIVE
Fechamento MBC 05.2026.xlsx (Areas Sintetico atualizado). Regenerate the JSON with
``python backend/scripts/build_workbook_targets.py`` if the workbook changes.
"""
import pytest

from app.closing.workbook_targets import targets_for


def test_targets_for_known_month_may():
    t = targets_for("2026-05")
    assert t is not None
    inst = t["institucional"]
    # The exact meeting numbers, reconciled to the centavo (MEETING_2026-07-10).
    assert inst["recebimento"] == pytest.approx(415928.0, abs=0.01)
    assert inst["imposto"] == pytest.approx(62389.20, abs=0.01)
    assert inst["resultado_bruto"] == pytest.approx(100327.11, abs=0.01)
    assert inst["resultado_liquido"] == pytest.approx(29820.91, abs=0.01)
    assert inst["reserva_bonus"] == pytest.approx(2982.09, abs=0.01)
    # Custo equipe Econômico maio = 79.436,24 (client-confirmed target).
    assert t["economico"]["custo_equipe"] == pytest.approx(79436.24, abs=0.01)
    assert t["contencioso"]["custo_equipe"] == pytest.approx(74141.21, abs=0.01)


def test_targets_for_unknown_month_is_none():
    assert targets_for("2026-12") is None
    assert targets_for("2099-01") is None


def test_targets_accepts_period_label_or_ano_mes():
    # Accept both "2026-05" and a period object exposing ``ano_mes``.
    class P:
        ano_mes = "2026-02"

    assert targets_for(P()) == targets_for("2026-02")
    assert targets_for("2026-02")["institucional"]["imposto"] == pytest.approx(
        47885.04, abs=0.01
    )
