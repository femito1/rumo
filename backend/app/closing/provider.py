# backend/app/closing/provider.py
from __future__ import annotations
from datetime import datetime, timezone
from app.closing.available import is_closeable
from app.closing.period import Period
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

#: Synthetic tab id for the cumulative (Jan→competence) view. Not a workbook sheet
#: and not emitted by any ``Source`` — the provider composes it from the per-month
#: assemblies (see ``_accumulate_dre_ytd``), so it deliberately has no ``SectionKey``.
ACUMULADO_TAB = "acumulado"

#: Tabs kept in the product after the 2026-07 cleanup (the per-área/Meta/Nacional/
#: Moedas/Institucional detail tabs were removed), in display order. Everything else
#: is still assembled (KPIs lift from ``institucional``) but not shown as a tab.
#: ``acumulado`` sits right after the monthly stacked tab it mirrors.
_KEEP_TAB_ORDER = (
    "base_resultado", "areas_sintetico", ACUMULADO_TAB, "dre_2026",
    "orcamento_2026", "rateio_mensal", "amortizacao",
)
_KEEP_TABS = frozenset(_KEEP_TAB_ORDER)


def _visible_tabs(role: str | None) -> frozenset[str]:
    """Tabs a role may see. ADMIN (RUMO) sees the KEEP set; a CLIENT sees none of
    the detail tabs (it gets the presentation panel, built from KPIs + sections)."""
    if role == "CLIENT":
        return frozenset()
    return _KEEP_TABS


def _num(v: object) -> float | None:
    """Unwrap a sourced cell (``{"value": …, "source": …}``) or a bare number.

    Several assemblers return sourced cells (``assemble_meta``'s ``meta_anual`` /
    ``meta_mensal`` / ``falta``); handing one straight to the frontend rendered
    "R$ NaN". Everything the presentation exposes goes through here.
    """
    if isinstance(v, dict):
        v = v.get("value")
    return v if isinstance(v, (int, float)) else None


def _row_value(section: SectionData | None, key: str, col: str = "Realizado"):
    """Read a numeric cell from an assembled rich section's row, or None."""
    if not isinstance(section, dict):
        return None
    for row in section.get("rows", []):
        if row.get("key") == key:
            return _num(row.get(col))
    return None


def _build_presentation(
    client: Client,
    period: Period,
    kpis: dict,
    sections: dict,
) -> dict:
    """Assemble the client-facing presentation panel data (mirrors the monthly PPTX).

    Pure projection of the already-assembled MONTHLY sections: institucional
    headline, per-área cards (Receita / Resultado Bruto / Resultado Líquido /
    Reserva, with Orçado for meta attainment), and the monthly recebimento series.
    Both roles receive this; a CLIENT receives ONLY this (detail tabs withheld).

    Takes ``sections`` (keyed by ``SectionKey``) rather than the display ``tabs``
    map on purpose: it must read the monthly ``Realizado``/``Orçado`` columns, so a
    view added to ``tabs`` later can never silently blank these cards."""
    inst = sections.get(SectionKey.INSTITUCIONAL)
    areas = []
    for area_key, label in (
        (SectionKey.CONTENCIOSO, "Contencioso"),
        (SectionKey.ECONOMICO, "Econômico"),
        (SectionKey.ARBITRAGEM, "Arbitragem"),
    ):
        sec = sections.get(area_key)
        receita = _row_value(sec, "recebimento")
        receita_orc = _row_value(sec, "recebimento", "Orçado")
        areas.append({
            "key": area_key.value,
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

    md = sections.get(SectionKey.META_DASHBOARD) or {}
    monthly = [
        {"mes": r.get("Mês"), "recebimento": _num(r.get("Recebimento"))}
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
        # ``meta_anual`` is a SOURCED CELL in assemble_meta — unwrap it, or the
        # frontend's formatBRL renders "R$ NaN". ``atingimento_mes`` is a bare float.
        "meta_anual": _num(md.get("meta_anual")),
        "atingimento_mes": _num(md.get("atingimento_mes")),
        "recebimento_mensal": monthly,
    }


def _accumulate_dre_ytd(client: Client, period: Period) -> dict[str, dict] | None:
    """Assemble every CLOSED month Jan→competence and accumulate into a YTD view.

    Reuses the per-month assembler (so per-área reserva/imposto/expense breakdown
    accumulate correctly), then folds them via ``accumulate_ytd``.

    ``targets=None`` on purpose: the cumulative shows the DB-derived sums. The
    2026-05 hard rule blanks individual diverging cells, which cannot be expressed
    in a sum without poisoning the whole line — and the client chose "segue com o
    sistema" for everything but that one reconciliation month.

    Returns None (not {}) when it can't be built, so the caller omits the tab
    entirely rather than showing a visibly empty one."""
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
            ano_mes = f"{period.year:04d}-{m:02d}"
            if m > period.month or not is_closeable(ano_mes):
                continue
            bud_m = monthly_budget(entries, month=m) if entries else None
            # Cross-área recebimento reclassifications are per month, same as the
            # monthly path — without them per-área YTD wouldn't equal the sum of
            # the monthly tabs (the institucional total ties either way).
            try:
                transfers = _transfers_repo().get_transfers(client.id, ano_mes)
            except Exception:  # pragma: no cover - transfers overlay is best-effort
                transfers = None
            months[m] = assemble_dre_sections(
                snapshot=snap,
                budget=bud_m,
                budget_annual=ann or None,
                transfers=transfers,
                period_label=ano_mes,
                period_month=m,
                targets=None,
            )
        ytd = accumulate_ytd(months, annual_budget=ann, up_to_month=period.month)
        return ytd or None
    except Exception:  # pragma: no cover - acumulado is a best-effort overlay
        return None


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
        role: str | None = None,
    ) -> dict:
        sections = self._merge(period, day_range)
        meta_kpis = dict(sections.get(SectionKey.META, {}).get("kpis", {}))
        meta_kpis.update(_headline_kpis_from_dre(sections.get(SectionKey.INSTITUCIONAL)))
        tabs: dict[str, SectionData] = {k.value: v for k, v in sections.items()}

        # Presentation panel data (mirrors the monthly PPTX): headline + per-área +
        # monthly series. Built server-side from the assembled sections so BOTH roles
        # get exactly the panel's data — a CLIENT sees ONLY this (detail tabs withheld).
        presentation = _build_presentation(client, period, meta_kpis, sections)

        # Cumulative (acumulado) TAB — the workbook's own cumulative view is the
        # right-hand column group of 'Areas Sintetico atualizado' over the same
        # stacked rows, so it is one additive tab, not a second render mode. Skipped
        # for a CLIENT (which gets no detail tabs) to avoid the ≤12 assemblies.
        if role != "CLIENT":
            ytd = _accumulate_dre_ytd(client, period)
            if ytd and (stacked := ytd.get("areas_sintetico")):
                tabs[ACUMULADO_TAB] = {
                    **stacked,
                    "name": f"Acumulado (Jan → {period.month_name_pt})",
                }

        # Tab visibility: only the KEEP set is shown, and a CLIENT sees none of the
        # detail tabs (they get the presentation panel only). Boundary is server-side.
        visible = _visible_tabs(role)
        order = [t for t in _KEEP_TAB_ORDER if t in tabs and t in visible]

        return {
            "client": {"id": client.id, "name": client.name},
            "period": {"ano_mes": period.ano_mes, "label": period.label, "column_letter": period.column_letter},
            "day_range": {"from": day_range.start, "to": day_range.end, "is_full_month": day_range.is_full_month},
            "kpis": meta_kpis,
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
