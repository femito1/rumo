# backend/tests/test_budget_source.py
import pytest

from app.budget.models import BudgetEntry, monthly_budget
from app.closing.period import Period
from app.sources.base import DayRange, SectionKey
from app.sources.budget_source import BudgetSource


def test_monthly_budget_splits_annual_evenly():
    entries = [BudgetEntry("mbc", 2026, "institucional", "recebimento", 1200.0)]
    monthly = monthly_budget(entries)
    assert monthly["institucional"]["recebimento"] == 100.0


def test_monthly_budget_prefers_monthly_detail_on_legacy_collision():
    """A legacy-key entry (custos_diretos, annual only) and its canonical
    counterpart (custo_equipe, with monthly detail) both normalize to the same
    (area, line_key). The one carrying monthly_amounts must win regardless of
    order, so an imported granular budget is never shadowed by an old seed."""
    legacy = BudgetEntry("mbc", 2026, "institucional", "custos_diretos", 2_403_882.65)
    canonical = BudgetEntry(
        "mbc",
        2026,
        "institucional",
        "custo_equipe",
        2_403_882.65,
        monthly_amounts=(208_717.59,) * 12,
    )
    for order in ([legacy, canonical], [canonical, legacy]):
        monthly = monthly_budget(order, month=2)
        assert monthly["institucional"]["custo_equipe"] == 208_717.59


def test_budget_source_emits_orcamento_tab():
    entries = [BudgetEntry("mbc", 2026, "institucional", "recebimento", 8060000.0)]
    src = BudgetSource(entries)
    assert SectionKey.ORCAMENTO_2026 in src.supports()
    p = Period.parse("2026-02")
    out = src.fetch(p, DayRange.full_month(p))
    tab = out[SectionKey.ORCAMENTO_2026]
    assert tab["kind"] == "rich"
    fat = next(r for r in tab["rows"] if r["Linha"] == "Recebimento")
    assert fat["Anual (Orcado)"]["value"] == 8060000.0
    assert fat["Mensal (Orcado)"]["value"] == round(8060000.0 / 12, 2)


def test_budget_source_empty_when_no_entries():
    src = BudgetSource([])
    p = Period.parse("2026-02")
    out = src.fetch(p, DayRange.full_month(p))
    rows = out[SectionKey.ORCAMENTO_2026]["rows"]
    assert all(r["Anual (Orcado)"]["value"] is None for r in rows)


def test_legacy_line_keys_map_to_canonical():
    from app.budget.models import canonical_line_key, is_valid_line

    assert canonical_line_key("faturamento") == "recebimento"
    assert canonical_line_key("custos_diretos") == "custo_equipe"
    assert canonical_line_key("despesas_indiretas") == "despesas"
    assert canonical_line_key("impostos") == "imposto"
    # legacy keys still validate (no 422 for pre-rework clients)
    assert is_valid_line("faturamento")


def test_monthly_budget_normalizes_legacy_keys():
    entries = [BudgetEntry("mbc", 2026, "institucional", "faturamento", 8060000.0)]
    monthly = monthly_budget(entries)
    assert monthly["institucional"]["recebimento"] == round(8060000.0 / 12, 2)
    assert "faturamento" not in monthly["institucional"]


def test_monthly_budget_uses_per_month_amounts_when_present():
    # Workbook-granularity budgets carry 12 distinct monthly values that need not
    # be annual/12 (e.g. Custo equipe varies by month).
    months = tuple(float(m) for m in range(1, 13))  # 1..12
    entries = [
        BudgetEntry("mbc", 2026, "contencioso", "custo_equipe", 78.0,
                    monthly_amounts=months)
    ]
    jan = monthly_budget(entries, month=1)
    feb = monthly_budget(entries, month=2)
    assert jan["contencioso"]["custo_equipe"] == 1.0
    assert feb["contencioso"]["custo_equipe"] == 2.0


def test_monthly_budget_falls_back_to_annual_over_twelve():
    # No per-month detail: keep the even split (backward compatible).
    entries = [BudgetEntry("mbc", 2026, "institucional", "recebimento", 1200.0)]
    assert monthly_budget(entries, month=5)["institucional"]["recebimento"] == 100.0


def test_annual_amount_reconciles_with_monthly_sum():
    from app.budget.models import BudgetEntry as BE

    e = BE("mbc", 2026, "institucional", "recebimento", 0.0,
           monthly_amounts=tuple([100.0] * 12))
    assert e.effective_annual() == pytest.approx(1200.0)
