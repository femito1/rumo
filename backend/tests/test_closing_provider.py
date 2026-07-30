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


def test_presentation_deck_has_all_slide_sections(tmp_path, monkeypatch):
    # The deck mirrors the PPTX slide by slide: headline, institucional monthly
    # detail, meta + attainment, per-line analysis, 3 áreas (mês/YTD/DRE), reserva.
    body = _closing(tmp_path, monkeypatch)
    pres = body["presentation"]
    # Institucional monthly detail: Receita line has a realized value in ≥1 month
    # (headline.recebimento comes from the META/LegalDesk KPI, absent in this
    # assembler-only fixture — the detail table sources from the DRE sections).
    receita = next(r for r in pres["institucional_detalhe"]["linhas"] if r["key"] == "recebimento")
    assert any(v is not None for v in receita["months"].values())
    assert pres["analise_ytd"]  # Orçado×Realizado analysis rows
    assert len(pres["areas"]) == 3
    assert any(a["ytd"]["receita"] is not None for a in pres["areas"])
    # every área DRE carries the full line set
    assert all(len(a["dre"]) >= 8 for a in pres["areas"])
    assert pres["reserva"]["linhas"]  # institucional + 3 áreas


def test_closing_carries_pt_br_notes_for_the_month(tmp_path, monkeypatch):
    # The month's explained discrepancies ship with the payload so the UI can show
    # them without a second request. Feb has the Jan–May área formula note.
    body = _closing(tmp_path, monkeypatch)
    notas = body["notas"]
    assert notas, "February should carry at least the área-formula note"
    ids = {n["id"] for n in notas}
    assert "despesas-area-formula-deslocada" in ids
    # Every note is client-ready: PT-BR text plus who to contact.
    for n in notas:
        assert n["titulo"] and n["detalhe"] and n["contato"]
        assert "origem" not in n, "internal provenance must not reach the client"


def test_row_level_notes_do_not_shift_the_positional_columns(tmp_path, monkeypatch):
    """Rows tagged with ``notas`` must keep the display keys FIRST.

    ``TabView.rowKeys`` samples ``Object.keys(rows[0]).slice(0, columns.length)``, so
    a key inserted before the display keys silently shifts every column — the D5
    defect from the 2026-07-28 cumulative review. Guard it.
    """
    body = _closing(tmp_path, monkeypatch)
    for tab_id, tab in body["tabs"].items():
        rows = tab.get("rows") if isinstance(tab, dict) else None
        cols = tab.get("columns") if isinstance(tab, dict) else None
        if not rows or not cols:
            continue
        for row in rows:
            if "notas" not in row:
                continue
            leading = list(row.keys())[: len(cols)]
            assert "notas" not in leading, (
                f"{tab_id}: 'notas' landed inside the positional column window "
                f"{leading} — it must come after the display keys"
            )


def test_partial_month_is_included_in_its_own_ytd(tmp_path, monkeypatch):
    """The open month renders as a partial, so its month-to-date figures must be part
    of the YTD it is the endpoint of — otherwise "Acumulado Jan → Julho" would silently
    stop at June while the header says Julho.

    Guarded because the accumulator gates on ``is_closeable``, which (correctly) still
    excludes the open month: the partial path has to opt it in explicitly.
    """
    from datetime import date

    from app.closing.provider import _accumulate_dre_ytd

    today = date.today()
    provider = _acumulado_provider(  # noqa: F841 — wires the monkeypatched stores
        tmp_path, monkeypatch, months=(today.month - 1, today.month)
    )
    client = Client(id="mbc", name="MBC", provider="legaldesk+sisjuri", provider_config={})
    acc = _accumulate_dre_ytd(client, Period(year=today.year, month=today.month))
    assert acc is not None
    assert today.month in acc["months"], "open month missing from its own YTD"
    assert today.month in acc["faturamento"]


def test_presentation_headline_carries_despesas_for_the_fourth_card(tmp_path, monkeypatch):
    """2026-07-28, 29:39 — Adriana: *"deveria ter essa linha de despesa: faturamento,
    receita, despesa."* Adriana Mendes, 30:01: *"só diminuir o tamanho da caixinha que
    cabe mais outra: faturamento, receita, despesas e resultados"* — because *"o
    resultado acaba sendo a diferença entre receita e despesa"* and without it the
    result reads *"perdido"*.

    Only the INSTITUCIONAL slide gets it. The per-área monthly slides deliberately
    show no despesa line (28:14 — *"a gente só mostra receita e resultado"*); per área
    despesa appears only in the acumulado (30:23 — *"e no acumulado, não no mensal"*).
    """
    body = _closing(tmp_path, monkeypatch)
    headline = body["presentation"]["headline"]
    assert "despesas" in headline, "headline has no despesas for the 4th card"
    assert headline["despesas"] is not None
    # Per-área MONTHLY cards must stay receita/resultado only — no despesa.
    for area in body["presentation"]["areas"]:
        assert "despesas" not in area["mes"], f"{area['label']} mês slide gained a despesa"


def test_presentation_faturamento_fills_every_month_not_just_competence(tmp_path, monkeypatch):
    """2026-07-28, 19:49 — *"ele não está puxando janeiro, fevereiro, março, abril no
    faturamento embaixo."* Receita filled but Faturamento only ever showed the
    competence month: ``inst_month_value`` returned ``None`` for the faturamento key
    outright and a second pass filled ``months[period_month]`` from the KPI alone.

    It was never a data gap — every snapshot carries ``revenue.faturamento_bruto``
    (verified against Fechamento MBC 06.2026: all six 2026 months tie exactly). So
    the deck now sources per-month faturamento from the snapshots.
    """
    body = _closing(tmp_path, monkeypatch, months=(1, 2))
    fat = next(
        r for r in body["presentation"]["institucional_detalhe"]["linhas"]
        if r["key"] == "faturamento"
    )
    # Both closed months present in the store must carry a value, not just Feb
    # (the competence month, which the old KPI-only path already filled).
    assert fat["months"][1] is not None, "January faturamento still blank"
    assert fat["months"][2] is not None
    # And the YTD cell is the sum of the months shown, not a single month.
    assert fat["ytd"] == pytest.approx(fat["months"][1] + fat["months"][2], abs=0.02)


def test_presentation_meta_anual_is_a_number_not_a_sourced_cell(tmp_path, monkeypatch):
    # ``assemble_meta`` returns meta.anual as {"value": ..., "source": ...}; passing
    # the dict through made the frontend render "R$ NaN".
    body = _closing(tmp_path, monkeypatch)
    meta_anual = body["presentation"]["meta"]["anual"]
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
