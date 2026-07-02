# backend/tests/test_budget_source.py
from app.budget.models import BudgetEntry, monthly_budget
from app.closing.period import Period
from app.sources.base import DayRange, SectionKey
from app.sources.budget_source import BudgetSource


def test_monthly_budget_splits_annual_evenly():
    entries = [BudgetEntry("mbc", 2026, "institucional", "recebimento", 1200.0)]
    monthly = monthly_budget(entries)
    assert monthly["institucional"]["recebimento"] == 100.0


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
