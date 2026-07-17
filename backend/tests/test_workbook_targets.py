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
    # The exact meeting numbers, reconciled to the centavo (MEETING_2026-07-10),
    # WITH the client-authorized aluguel–Belline override (Renata, 2026-07-14):
    # the DB is authoritative for aluguel, so despesas rises by the +129,17 delta
    # and the dependent tail drops by it (reserva recomputed as 10% of líquido).
    # See build_workbook_targets.py::_apply_aluguel_override.
    assert inst["recebimento"] == pytest.approx(415928.0, abs=0.01)
    assert inst["imposto"] == pytest.approx(62389.20, abs=0.01)
    assert inst["despesas"] == pytest.approx(105640.60, abs=0.01)
    assert inst["resultado_bruto"] == pytest.approx(100197.94, abs=0.01)
    assert inst["resultado_liquido"] == pytest.approx(29691.74, abs=0.01)
    assert inst["reserva_bonus"] == pytest.approx(2969.17, abs=0.01)
    # Custo equipe Econômico maio = 79.436,24 (client-confirmed target).
    assert t["economico"]["custo_equipe"] == pytest.approx(79436.24, abs=0.01)
    assert t["contencioso"]["custo_equipe"] == pytest.approx(74141.21, abs=0.01)


def test_may_per_area_resultado_bruto_uses_renata_despesas_area_ruling():
    # Renata (2026-07-16) confirmed Despesas Área is allocated by label/cost-center
    # (Viagens-Econômico -> Econômico, assento -> Arbitragem); the workbook's
    # off-by-one Viagens subtotal formula was a spreadsheet mistake. The DB already
    # allocates this way, so the per-área Resultado Bruto targets are corrected to
    # the DB-derived values (build_workbook_targets._apply_despesas_area_override).
    t = targets_for("2026-05")
    assert t["contencioso"]["resultado_bruto"] == pytest.approx(129860.86, abs=0.01)
    assert t["economico"]["resultado_bruto"] == pytest.approx(43444.15, abs=0.01)
    assert t["arbitragem"]["resultado_bruto"] == pytest.approx(-39855.42, abs=0.01)


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
