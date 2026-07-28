# backend/app/closing/provider.py
from __future__ import annotations
from datetime import datetime, timezone
from app.closing.available import is_closeable
from app.closing.period import Period
from app.closing.tab_layouts import TAB_ORDER
from app.sources.assembler_source import AssemblerSource
from app.sources.base import SectionKey, DayRange, Source, SectionData
from app.sources.budget_source import BudgetSource
from app.sources.fixture import FixtureSource
from app.sources.legaldesk import LegalDeskSource
from app.sources.sisjuri_db import SisjuriDbSource
from app.tenancy.models import Client

#: Competence months where the workbook hard rule is applied (Realizado blanked if
#: it diverges from the authoritative workbook target). Only the reconciliation
#: month 2026-05: earlier months render DB-derived numbers directly ("segue com o
#: sistema", 2026-07 checkpoint), later months have no workbook target anyway.
_HARD_RULE_MONTHS = frozenset({"2026-05"})

#: Tabs kept in the product after the 2026-07 cleanup (the per-área/Meta/Nacional/
#: Moedas/Institucional detail tabs were removed). Everything else is still
#: assembled (KPIs lift from ``institucional``) but not shown as a tab.
_KEEP_TABS = frozenset({
    "base_resultado", "areas_sintetico", "dre_2026", "orcamento_2026",
    "rateio_mensal", "amortizacao",
})


def _visible_tabs(role: str | None) -> frozenset[str]:
    """Tabs a role may see. ADMIN (RUMO) sees the KEEP set; a CLIENT sees none of
    the detail tabs (it gets the presentation panel, built from KPIs + sections)."""
    if role == "CLIENT":
        return frozenset()
    return _KEEP_TABS


def _row_value(section: SectionData | None, key: str, col: str = "Realizado"):
    """Read a numeric cell from an assembled rich section's row, or None."""
    if not isinstance(section, dict):
        return None
    for row in section.get("rows", []):
        if row.get("key") == key:
            cell = row.get(col)
            v = cell.get("value") if isinstance(cell, dict) else cell
            return v if isinstance(v, (int, float)) else None
    return None


def _build_presentation(
    client: Client,
    period: Period,
    kpis: dict,
    sections: dict,
    tabs: dict,
) -> dict:
    """Assemble the client-facing presentation panel data (mirrors the monthly PPTX).

    Pure projection of the already-assembled sections: institucional headline,
    per-área cards (Receita / Resultado Bruto / Resultado Líquido / Reserva, with
    Orçado for meta attainment), and the monthly recebimento series. Both roles
    receive this; a CLIENT receives ONLY this (detail tabs withheld)."""
    inst = sections.get(SectionKey.INSTITUCIONAL)
    areas = []
    for area_key, label in (
        ("contencioso", "Contencioso"),
        ("economico", "Econômico"),
        ("arbitragem", "Arbitragem"),
    ):
        sec = tabs.get(area_key)
        receita = _row_value(sec, "recebimento")
        receita_orc = _row_value(sec, "recebimento", "Orçado")
        areas.append({
            "key": area_key,
            "label": label,
            "receita": receita,
            "receita_orcado": receita_orc,
            "resultado_bruto": _row_value(sec, "resultado_bruto"),
            "resultado_liquido": _row_value(sec, "resultado_liquido"),
            "reserva_bonus": _row_value(sec, "reserva_bonus"),
            "atingimento": (
                round(receita / receita_orc, 4)
                if (receita is not None and receita_orc)
                else None
            ),
        })

    md = tabs.get("meta_dashboard") or {}
    monthly = [
        {"mes": r.get("Mês"),
         "recebimento": (r.get("Recebimento") or {}).get("value")
         if isinstance(r.get("Recebimento"), dict) else r.get("Recebimento")}
        for r in md.get("rows", [])
        if r.get("kind") != "total"
    ]

    return {
        "titulo": client.name,
        "periodo": period.label,
        "headline": {
            "faturamento": kpis.get("faturamento_realizado"),
            "recebimento": kpis.get("receita_honorarios"),
            "resultado_bruto": kpis.get("resultado_bruto"),
            "margem_bruta": kpis.get("margem_bruta"),
            "resultado_liquido": kpis.get("resultado_liquido"),
            "margem_liquida": kpis.get("margem_liquida"),
            "reserva_bonus": kpis.get("reserva_bonus"),
        },
        "institucional": {
            "recebimento": _row_value(inst, "recebimento"),
            "despesas": _row_value(inst, "despesas"),
            "imposto": _row_value(inst, "imposto"),
            "amortizacao": _row_value(inst, "amortizacao"),
        },
        "areas": areas,
        "meta_anual": md.get("meta_anual"),
        "atingimento_mes": md.get("atingimento_mes"),
        "recebimento_mensal": monthly,
    }


def _accumulate_dre_ytd(client: Client, period: Period) -> dict[str, dict]:
    """Assemble every CLOSED month Jan→competence and accumulate into a YTD view.

    Reuses the per-month assembler (so per-área reserva/imposto/expense breakdown
    accumulate correctly), then folds them via ``accumulate_ytd``. Best-effort:
    returns {} on any error so the mensal payload still renders."""
    try:
        from app.budget.models import annual_budget, monthly_budget
        from app.closing.available import is_closeable
        from app.closing.dre import assemble_dre_sections
        from app.closing.ytd_accumulate import accumulate_ytd

        entries = _budget_repo().get_budget(client.id, period.year)
        ann = annual_budget(entries) if entries else {}
        snaps = _snapshot_store().snapshots_by_year(period.year, client_id=client.id)
        months: dict[int, dict] = {}
        for m, snap in snaps.items():
            if m > period.month or not is_closeable(f"{period.year:04d}-{m:02d}"):
                continue
            bud_m = monthly_budget(entries, month=m) if entries else None
            bud_a = ann or None
            months[m] = assemble_dre_sections(
                snapshot=snap,
                budget=bud_m,
                budget_annual=bud_a,
                period_label=f"{period.year:04d}-{m:02d}",
                period_month=m,
                targets=None,  # YTD shows DB-derived numbers, no per-cell blanking
            )
        return accumulate_ytd(months, annual_budget=ann, up_to_month=period.month)
    except Exception:  # pragma: no cover - acumulado is a best-effort overlay
        return {}


class ClosingProvider:
    def __init__(self, sources: list[Source]) -> None:
        self.sources = sources

    def _merge(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        merged: dict[SectionKey, SectionData] = {}
        for src in self.sources:                       # ordered; later overrides earlier
            for key, data in src.fetch(period, day_range).items():
                merged[key] = data
        return merged

    def build_closing(
        self,
        *,
        client: Client,
        period: Period,
        day_range: DayRange,
        mode: str = "mensal",
        role: str | None = None,
    ) -> dict:
        sections = self._merge(period, day_range)
        meta_kpis = dict(sections.get(SectionKey.META, {}).get("kpis", {}))
        meta_kpis.update(_headline_kpis_from_dre(sections.get(SectionKey.INSTITUCIONAL)))
        tabs = {k.value: v for k, v in sections.items()}

        # Acumulado (YTD) mode: overlay the DRE tabs with Jan→competence accumulated
        # values + YTD/YTG/Variação columns. KPIs stay monthly (headline is the
        # month; the YTD lives in the tables/presentation), matching the workbook.
        if mode == "acumulado":
            ytd = _accumulate_dre_ytd(client, period)
            for key, section in ytd.items():
                tabs[key] = section

        # Presentation panel data (mirrors the monthly PPTX): headline + per-área +
        # monthly series. Built server-side from the assembled sections so BOTH roles
        # get exactly the panel's data — a CLIENT sees ONLY this (detail tabs withheld).
        presentation = _build_presentation(client, period, meta_kpis, sections, tabs)

        # Tab visibility: only the KEEP set is shown, and a CLIENT sees none of the
        # detail tabs (they get the presentation panel only). Boundary is server-side.
        visible = _visible_tabs(role)
        order = [t for t in TAB_ORDER if t in tabs and t in visible]

        return {
            "client": {"id": client.id, "name": client.name},
            "period": {"ano_mes": period.ano_mes, "label": period.label, "column_letter": period.column_letter},
            "day_range": {"from": day_range.start, "to": day_range.end, "is_full_month": day_range.is_full_month},
            "kpis": meta_kpis,
            "mode": mode,
            "presentation": presentation,
            "tab_order": order,
            "tabs": {t: tabs[t] for t in order} if role == "CLIENT" else tabs,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

def _headline_kpis_from_dre(institucional: SectionData | None) -> dict[str, float | None]:
    """Extract headline KPIs from the assembled institucional DRE rows.

    Returns an empty dict when the section is not the assembled DRE (e.g. only
    LegalDesk ran). Keys mirror the canonical line-keys in ``app.closing.dre``.
    """
    if not institucional or not isinstance(institucional, dict):
        return {}
    rows = institucional.get("rows")
    if not isinstance(rows, list):
        return {}
    wanted = {
        "resultado_bruto",
        "margem_bruta",
        "resultado_liquido",
        "margem_liquida",
        "reserva_bonus",
    }
    out: dict[str, float | None] = {}
    for row in rows:
        key = row.get("key")
        if key not in wanted:
            continue
        cell = row.get("Realizado")
        out[key] = cell.get("value") if isinstance(cell, dict) else None
    return out


def _snapshot_store():
    """Indirection so tests can inject a store; imported lazily to avoid cycles."""
    from app.api.providers import get_snapshot_store

    return get_snapshot_store()


def _budget_repo():
    """Lazy budget repo lookup; imported lazily to avoid import cycles."""
    from app.api.providers import get_budget_repo

    return get_budget_repo()


def _transfers_repo():
    """Lazy area-transfers repo lookup; imported lazily to avoid import cycles."""
    from app.api.providers import get_transfers_repo

    return get_transfers_repo()


def build_provider_for(client: Client, *, period: Period | None = None) -> ClosingProvider:
    """Resolve a client's `provider` column to an ordered list of Sources (spec §4)."""
    if client.provider == "legaldesk":
        return ClosingProvider(sources=[LegalDeskSource()])
    if client.provider == "fixture":
        return ClosingProvider(sources=[FixtureSource()])
    if client.provider == "legaldesk+sisjuri":
        # Order matters: later overrides earlier.
        #   1. LegalDesk  -> revenue/rateio/invoices + KPI-bearing META.
        #   2. SisjuriDb  -> raw expense detail (INSTITUCIONAL_ANO) + RATEIO_MENSAL.
        #   3. Budget     -> ORCAMENTO_2026 reference table.
        #   4. Assembler  -> computed DRE (Orcado x Realizado) over institucional
        #      + area blocks + areas_sintetico + dre_2026 + amortizacao.
        sources: list[Source] = [LegalDeskSource()]

        snapshot = None
        if period is not None:
            snapshot = _snapshot_store().get(period.ano_mes, client_id=client.id)
        if snapshot is not None:
            sources.append(SisjuriDbSource.from_snapshot(snapshot, emit_meta=False))

        budget_monthly: dict[str, dict[str, float]] | None = None
        budget_annual: dict[str, dict[str, float]] | None = None
        entries = []
        if period is not None:
            try:
                from app.budget.models import annual_budget, monthly_budget

                entries = _budget_repo().get_budget(client.id, period.year)
                budget_monthly = (
                    monthly_budget(entries, month=period.month) if entries else None
                )
                # Annual totals: the per-área custo-equipe rateio share (Despesa
                # Institucional Orçado) is keyed off the ANNUAL plan, not one month.
                budget_annual = annual_budget(entries) if entries else None
            except Exception:  # pragma: no cover - budget is best-effort overlay
                budget_monthly = None
                budget_annual = None
        sources.append(BudgetSource(entries))

        transfers = None
        if period is not None:
            try:
                transfers = _transfers_repo().get_transfers(client.id, period.ano_mes)
            except Exception:  # pragma: no cover - transfers overlay is best-effort
                transfers = None

        # Workbook verification overlay (hard rule): blank any Realizado cell that
        # diverges from the authoritative workbook target by more than R$0,01.
        #
        # Applied ONLY for the authoritative reconciliation month (2026-05). Per the
        # client's 2026-07 checkpoint ("segue com o sistema"), Jan–Abr now render the
        # DB-derived numbers directly — the old hand-entered workbook cells omitted
        # real lines (e.g. Jan Associações AASP/Canal) and the DB is more complete.
        # Gating here (not in ``targets_for``) keeps the raw target lookup intact for
        # the offline comparison harness and tests. Jun+ already have no targets.
        targets = None
        if period is not None and period.ano_mes in _HARD_RULE_MONTHS:
            try:
                from app.closing.workbook_targets import targets_for

                targets = targets_for(period)
            except Exception:  # pragma: no cover - targets overlay is best-effort
                targets = None

        # Meta dashboard: per-month realized recebimento for the whole competence
        # year, so the 12-month table fills every CLOSED month (not just the
        # competence one). Future months are absent from the map -> blank.
        ytd_recebimento: dict[int, float] | None = None
        if period is not None:
            try:
                full = _snapshot_store().recebimento_by_year(
                    period.year, client_id=client.id
                )
                ytd_recebimento = {
                    m: v
                    for m, v in full.items()
                    if is_closeable(f"{period.year:04d}-{m:02d}")
                }
            except Exception:  # pragma: no cover - meta YTD is best-effort overlay
                ytd_recebimento = None

        sources.append(
            AssemblerSource(
                snapshot=snapshot,
                budget=budget_monthly,
                budget_annual=budget_annual,
                transfers=transfers,
                targets=targets,
                ytd_recebimento=ytd_recebimento,
            )
        )
        return ClosingProvider(sources=sources)
    raise ValueError(f"unknown provider: {client.provider}")
