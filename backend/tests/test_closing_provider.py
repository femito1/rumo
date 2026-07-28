# backend/tests/test_closing_provider.py
import pytest

from app.closing.provider import ClosingProvider, build_provider_for
from app.closing.period import Period
from app.sources.base import SectionKey, DayRange
from app.sources.fixture import FixtureSource
from app.tenancy.models import Client

def test_provider_builds_payload_shape():
    p = Period.parse("2026-05")
    provider = ClosingProvider(sources=[FixtureSource()])
    payload = provider.build_closing(client=Client(id="demo", name="Cliente Demonstração", provider="fixture", provider_config={}), period=p, day_range=DayRange.full_month(p))
    assert payload["client"] == {"id": "demo", "name": "Cliente Demonstração"}
    assert payload["period"]["ano_mes"] == "2026-05"
    assert payload["period"]["label"] == "Maio 2026"
    assert payload["day_range"]["is_full_month"] is True
    assert "kpis" in payload and "tabs" in payload and "tab_order" in payload

def test_merge_later_source_overrides_earlier_for_same_section():
    class A:
        name = "a"
        def supports(self): return {SectionKey.META}
        def fetch(self, period, day_range): return {SectionKey.META: {"kpis": {"x": 1}}}
    class B:
        name = "b"
        def supports(self): return {SectionKey.META}
        def fetch(self, period, day_range): return {SectionKey.META: {"kpis": {"x": 2}}}
    p = Period.parse("2026-05")
    provider = ClosingProvider(sources=[A(), B()])  # B later -> wins
    payload = provider.build_closing(client=Client(id="t", name="T", provider="x", provider_config={}), period=p, day_range=DayRange.full_month(p))
    assert payload["kpis"]["x"] == 2

def test_build_provider_for_maps_client_to_sources():
    mbc = Client(id="mbc", name="MBC", provider="legaldesk", provider_config={})
    demo = Client(id="demo", name="Cliente Demonstração", provider="fixture", provider_config={})
    assert build_provider_for(mbc).sources[0].name == "legaldesk"
    assert build_provider_for(demo).sources[0].name == "fixture"


def test_legaldesk_plus_sisjuri_composes_both_when_snapshot_present(tmp_path, monkeypatch):
    # The DB source augments LegalDesk with institutional expenses when a snapshot
    # exists for the period; falls back to LegalDesk-only when it doesn't.
    import json

    from app.sources.snapshot_store import SnapshotStore

    fixture = (
        __import__("pathlib").Path(__file__).parent
        / "fixtures"
        / "sisjuri_2026_02.json"
    )
    store = SnapshotStore(tmp_path)
    store.put("2026-02", json.loads(fixture.read_text(encoding="utf-8")))
    monkeypatch.setattr("app.closing.provider._snapshot_store", lambda: store)

    from app.budget.repository import InMemoryBudgetRepository

    monkeypatch.setattr(
        "app.closing.provider._budget_repo", lambda: InMemoryBudgetRepository.seeded()
    )

    mbc = Client(id="mbc", name="MBC", provider="legaldesk+sisjuri", provider_config={})
    provider = build_provider_for(mbc, period=Period.parse("2026-02"))
    names = [s.name for s in provider.sources]
    # LegalDesk (revenue) -> SisjuriDb (expenses) -> Budget -> Assembler (DRE).
    assert names == ["legaldesk", "sisjuri_db", "budget", "assembler"]


def test_legaldesk_plus_sisjuri_falls_back_when_no_snapshot(tmp_path, monkeypatch):
    from app.sources.snapshot_store import SnapshotStore

    store = SnapshotStore(tmp_path)  # empty
    monkeypatch.setattr("app.closing.provider._snapshot_store", lambda: store)

    from app.budget.repository import InMemoryBudgetRepository

    monkeypatch.setattr(
        "app.closing.provider._budget_repo", lambda: InMemoryBudgetRepository.seeded()
    )

    mbc = Client(id="mbc", name="MBC", provider="legaldesk+sisjuri", provider_config={})
    provider = build_provider_for(mbc, period=Period.parse("2026-02"))
    names = [s.name for s in provider.sources]
    # No snapshot -> no sisjuri_db source, but budget+assembler still run so the
    # DRE tabs render (with snapshot_missing flagged and zeroed realizado).
    assert names == ["legaldesk", "budget", "assembler"]


def test_hard_rule_applies_only_to_may_not_jan_apr(tmp_path, monkeypatch):
    # "segue com o sistema" (2026-07 checkpoint): Jan–Abr render the DB-derived
    # numbers directly (no workbook target blanking). The hard rule applies ONLY to
    # the authoritative reconciliation month 2026-05. Assert on the targets the
    # AssemblerSource receives per month.
    from app.budget.repository import InMemoryBudgetRepository
    from app.sources.assembler_source import AssemblerSource
    from app.sources.snapshot_store import SnapshotStore

    store = SnapshotStore(tmp_path)  # empty is fine; targets are period-gated
    monkeypatch.setattr("app.closing.provider._snapshot_store", lambda: store)
    monkeypatch.setattr(
        "app.closing.provider._budget_repo", lambda: InMemoryBudgetRepository.seeded()
    )
    mbc = Client(id="mbc", name="MBC", provider="legaldesk+sisjuri", provider_config={})

    def assembler_targets(ano_mes: str):
        provider = build_provider_for(mbc, period=Period.parse(ano_mes))
        asm = next(s for s in provider.sources if isinstance(s, AssemblerSource))
        return asm._targets

    # May: hard rule ON (targets present).
    assert assembler_targets("2026-05") is not None
    # Jan–Abr: hard rule OFF (targets withheld → raw DB numbers render).
    for m in ("2026-01", "2026-02", "2026-03", "2026-04"):
        assert assembler_targets(m) is None


def test_provider_gathers_closeable_ytd_recebimento_map(tmp_path, monkeypatch):
    # The provider builds the {month: recebimento} map for the year from the
    # per-month snapshots, filtered to CLOSED months, and hands it to the
    # AssemblerSource. Assert the map the assembler receives, without invoking the
    # live LegalDesk source (which _merge would call).
    import json

    from app.budget.repository import InMemoryBudgetRepository
    from app.sources.assembler_source import AssemblerSource
    from app.sources.snapshot_store import SnapshotStore

    fixtures = __import__("pathlib").Path(__file__).parent / "fixtures"
    store = SnapshotStore(tmp_path)
    store.put(
        "2026-02",
        json.loads((fixtures / "sisjuri_2026_02.json").read_text(encoding="utf-8")),
    )
    store.put("2026-01", {"revenue": {"recebimento_bruto": 279821.07}})
    # A far-future month within the year must be excluded (not closeable).
    store.put("2026-12", {"revenue": {"recebimento_bruto": 999.0}})
    monkeypatch.setattr("app.closing.provider._snapshot_store", lambda: store)
    monkeypatch.setattr(
        "app.closing.provider._budget_repo", lambda: InMemoryBudgetRepository.seeded()
    )

    mbc = Client(id="mbc", name="MBC", provider="legaldesk+sisjuri", provider_config={})
    provider = build_provider_for(mbc, period=Period.parse("2026-02"))
    assembler = next(s for s in provider.sources if isinstance(s, AssemblerSource))
    ytd = assembler._ytd_recebimento
    assert ytd is not None
    assert ytd[1] == pytest.approx(279821.07, abs=0.01)
    assert ytd[2] == pytest.approx(319233.58, abs=0.05)
    assert 12 not in ytd  # December 2026 is in the future -> filtered out


def test_meta_dashboard_fills_ytd_via_assembler_source():
    # End of the chain: AssemblerSource forwards the YTD map into assemble_meta,
    # so the Meta dashboard fills every month present in the map.
    from app.sources.assembler_source import AssemblerSource

    p = Period.parse("2026-02")
    budget = {"institucional": {"recebimento": 671666.67}}
    provider = ClosingProvider(
        sources=[
            AssemblerSource(
                snapshot=None,
                budget=budget,
                ytd_recebimento={1: 279821.07, 2: 319233.58},
            )
        ]
    )
    sections = provider._merge(p, DayRange.full_month(p))
    meta = sections[SectionKey.META_DASHBOARD]
    rows = {r["Mês"]: r for r in meta["rows"]}
    assert rows["Janeiro"]["Recebimento"]["value"] == pytest.approx(279821.07, abs=0.01)
    assert rows["Fevereiro"]["Recebimento"]["value"] == pytest.approx(319233.58, abs=0.01)
    assert rows["Março"]["Recebimento"]["value"] is None


def _acumulado_provider(tmp_path, monkeypatch, *, months=(1, 2)):
    """A provider whose snapshot store holds ``months`` of 2026, wired so the
    acumulado tab can be built without touching the live LegalDesk API."""
    import json

    from app.budget.repository import InMemoryBudgetRepository
    from app.sources.assembler_source import AssemblerSource
    from app.sources.snapshot_store import SnapshotStore

    fixtures = __import__("pathlib").Path(__file__).parent / "fixtures"
    snap = json.loads((fixtures / "sisjuri_2026_02.json").read_text(encoding="utf-8"))
    store = SnapshotStore(tmp_path)
    for m in months:
        store.put(f"2026-{m:02d}", snap)
    monkeypatch.setattr("app.closing.provider._snapshot_store", lambda: store)
    monkeypatch.setattr(
        "app.closing.provider._budget_repo", lambda: InMemoryBudgetRepository.seeded()
    )
    budget = {"institucional": {"recebimento": 671666.67, "amortizacao": 8117.0}}
    return ClosingProvider(
        sources=[AssemblerSource(snapshot=snap, budget=budget, ytd_recebimento=None)]
    )


def _closing(tmp_path, monkeypatch, *, role="ADMIN", months=(1, 2)):
    provider = _acumulado_provider(tmp_path, monkeypatch, months=months)
    p = Period.parse("2026-02")
    return provider.build_closing(
        client=Client(id="mbc", name="MBC", provider="legaldesk+sisjuri",
                      provider_config={}),
        period=p,
        day_range=DayRange.full_month(p),
        role=role,
    )


def test_acumulado_tab_present_and_ordered_after_areas_sintetico(tmp_path, monkeypatch):
    # The cumulative view is a TAB (not a render mode): it sits next to the monthly
    # stacked tab it mirrors, and carries the YTD columns.
    from app.closing.ytd_accumulate import YTD_COLUMNS

    body = _closing(tmp_path, monkeypatch)
    order = body["tab_order"]
    assert "acumulado" in order
    assert order.index("acumulado") == order.index("areas_sintetico") + 1
    assert body["tabs"]["acumulado"]["columns"] == YTD_COLUMNS
    assert body["tabs"]["acumulado"]["rows"]


def test_monthly_tabs_are_not_overlaid_by_the_acumulado_tab(tmp_path, monkeypatch):
    # The monthly sections keep their own columns — the cumulative is additive.
    body = _closing(tmp_path, monkeypatch)
    assert body["tabs"]["areas_sintetico"]["columns"] == [
        "Linha", "Orçado", "Realizado", "Desvio %",
    ]


def test_presentation_survives_alongside_acumulado(tmp_path, monkeypatch):
    # The presentation reads the MONTHLY sections; adding the cumulative tab must
    # not blank its per-área cards or the monthly recebimento series.
    body = _closing(tmp_path, monkeypatch)
    pres = body["presentation"]
    assert len(pres["areas"]) == 3
    assert any(a["receita"] is not None for a in pres["areas"])
    assert any(m["recebimento"] is not None for m in pres["recebimento_mensal"])


def test_presentation_meta_anual_is_a_number_not_a_sourced_cell(tmp_path, monkeypatch):
    # ``assemble_meta`` returns meta_anual as {"value": ..., "source": ...}; passing
    # the dict through made the frontend render "Meta anual R$ NaN".
    body = _closing(tmp_path, monkeypatch)
    meta_anual = body["presentation"]["meta_anual"]
    assert isinstance(meta_anual, (int, float))
    assert meta_anual == pytest.approx(671666.67 * 12, abs=0.01)


def test_client_role_gets_no_acumulado_tab(tmp_path, monkeypatch):
    # A CLIENT receives only the presentation panel; the boundary is server-side.
    body = _closing(tmp_path, monkeypatch, role="CLIENT")
    assert body["tab_order"] == []
    assert body["tabs"] == {}
    assert body["presentation"]["titulo"] == "MBC"


def test_assembler_populates_dre_and_flags_missing_snapshot():
    # With no snapshot, the assembler still emits institucional (DRE) but with
    # snapshot_missing=True so the UI can show a banner. Test the assembler
    # source directly to avoid LegalDesk's live API.
    from app.sources.assembler_source import AssemblerSource

    p = Period.parse("2026-02")
    provider = ClosingProvider(sources=[AssemblerSource(snapshot=None, budget=None)])
    sections = provider._merge(p, DayRange.full_month(p))
    inst = sections[SectionKey.INSTITUCIONAL]
    assert inst["kind"] == "rich"
    assert inst["snapshot_missing"] is True
    # The four area blocks + reference tabs are present too.
    for key in (
        SectionKey.CONTENCIOSO,
        SectionKey.ECONOMICO,
        SectionKey.ARBITRAGEM,
        SectionKey.AREAS_SINTETICO,
        SectionKey.AMORTIZACAO,
    ):
        assert key in sections
