# backend/app/closing/secondary_tabs.py
"""Workbook-faithful secondary tabs: Meta, Amortização, Rateio Mensal.

These are largely fixed/derived tables:
- Amortização: a fixed historical schedule of 8 investment originations (2022),
  each amortized over 60 months, summing to R$ 8.117,32/mês (matches workbook).
- Meta: annual target (from budget) split monthly, with realized recebimento.
- Rateio Mensal: per-area custo equipe with % share of the month total.
"""
from __future__ import annotations

from typing import Any

from app.closing.dre import RealizadoInputs
from app.closing.workbook_layouts import AMORTIZACAO_MENSAL, AREAS

#: The 8 investment originations (2022), each amortized over 60 months. Sum of
#: monthly installments = R$ 8.117,32/mês — the workbook's Amortização line.
#: Fixed historical finance data (no SISJURI source).
_AMORT_ORIGINATIONS: tuple[tuple[str, float, float, str], ...] = (
    ("2022-05", 78409.00, 1306.82, "parcela 1/60"),
    ("2022-06", 154730.96, 2578.85, "parcela 2/60"),
    ("2022-07", 116368.83, 1939.48, "parcela 3/60"),
    ("2022-08", 43795.59, 729.93, "parcela 4/60"),
    ("2022-09", 20140.00, 335.67, "parcela 5/60"),
    ("2022-10", 41551.00, 692.52, "parcela 6/60"),
    ("2022-11", 21722.00, 362.03, "parcela 7/60"),
    ("2022-12", 10321.00, 172.02, "parcela 8/60"),
)


def assemble_amortizacao() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for origem, total, mensal, parcela in _AMORT_ORIGINATIONS:
        rows.append(
            {
                "Origem": origem,
                "Total Investido": {"value": total, "source": "manual"},
                "Parcela Mensal": {"value": mensal, "source": "manual"},
                "Prazo": parcela,
            }
        )
    rows.append(
        {
            "Origem": "TOTAL / mês",
            "Total Investido": {"value": round(sum(o[1] for o in _AMORT_ORIGINATIONS), 2), "source": "manual"},
            "Parcela Mensal": {"value": AMORTIZACAO_MENSAL, "source": "manual"},
            "Prazo": "",
            "is_total": True,
        }
    )
    return {
        "kind": "rich",
        "name": "Amortização",
        "columns": ["Origem", "Total Investido", "Parcela Mensal", "Prazo"],
        "rows": rows,
    }


def assemble_rateio_mensal(
    snapshot: dict[str, Any] | None, period_label: str
) -> dict[str, Any]:
    r = (
        RealizadoInputs.from_snapshot(snapshot)
        if snapshot is not None
        else RealizadoInputs.empty()
    )
    total = round(sum(r.area_custo_equipe.values()), 2)
    rows: list[dict[str, Any]] = []
    for area in AREAS:
        val = r.area_custo_equipe.get(area, 0.0)
        share = round(val / total, 4) if total else None
        rows.append(
            {
                "Área": f"Custo equipe - {area}",
                "Custo Equipe": {"value": val, "source": "realizado"},
                "% do Total": share,
            }
        )
    rows.append(
        {
            "Área": "Total das Áreas",
            "Custo Equipe": {"value": total, "source": "realizado"},
            "% do Total": 1.0 if total else None,
            "is_total": True,
        }
    )
    return {
        "kind": "rich",
        "name": "Rateio Mensal",
        "columns": ["Área", "Custo Equipe", "% do Total"],
        "rows": rows,
        "snapshot_missing": snapshot is None,
    }


__all__ = [
    "assemble_amortizacao",
    "assemble_rateio_mensal",
    "assemble_dre_2026",
    "assemble_fluxo_consolidado",
    "assemble_institucional_ano",
]


_MESES = (
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
)


def assemble_dre_2026(
    budget: dict[str, dict[str, float]] | None,
) -> dict[str, Any]:
    """Annual budget projection with 12 monthly columns (all Orçado), mirroring
    the workbook 'DRE 2026'. Each line = annual budget split evenly per month."""
    from app.closing.dre import (
        AMORTIZACAO,
        CUSTO_EQUIPE,
        DESPESAS,
        IMPOSTO,
        RECEBIMENTO,
    )

    inst = (budget or {}).get("institucional", {})
    columns = ["Linha", "Anual", *_MESES]

    def line(label: str, key: str, *, is_total: bool = False,
             kind: str = "amount", default_monthly: float | None = None) -> dict[str, Any]:
        # ``default_monthly`` is a fixed worksheet value used when the client
        # budgeted nothing for this line (amortização = 8.117/mês); the budget
        # entry remains the manual override when present.
        monthly = inst.get(key)
        if monthly is None:
            monthly = default_monthly
        annual = round(monthly * 12, 2) if monthly is not None else None
        # Display columns first (Linha, Anual, 12 months), metadata last, so the
        # frontend's rowKeys slice (== column count) never grabs metadata.
        row: dict[str, Any] = {
            "Linha": label,
            "Anual": {"value": annual, "source": "orcado"},
        }
        for mes in _MESES:
            row[mes] = {"value": monthly, "source": "orcado"}
        row["is_total"] = is_total
        row["kind"] = kind
        row["key"] = key
        return row

    rows = [
        line("Faturamento", RECEBIMENTO),
        line("Custo equipe", CUSTO_EQUIPE),
        line("Despesas", DESPESAS),
        line("Imposto", IMPOSTO),
        line("Amortização", AMORTIZACAO, default_monthly=AMORTIZACAO_MENSAL),
    ]
    return {
        "kind": "rich",
        "name": "DRE 2026 (Orçado)",
        "columns": columns,
        "rows": rows,
    }


def assemble_faturas_analitico(
    snapshot: dict[str, Any] | None,
) -> dict[str, Any]:
    """Per-case faturamento detail ('FATURAS Analitico' grain). One row per case
    from the snapshot's faturas_analitico (POSFIN_RESULTFAT split by CASE), with
    código, assunto, área and the faturamento total; plus a Total row."""
    rows_in = (snapshot or {}).get("faturas_analitico", []) or []

    def cell(v: float | None) -> dict[str, Any]:
        return {"value": v, "source": "realizado"}

    rows: list[dict[str, Any]] = []
    running = 0.0
    for r in sorted(
        rows_in, key=lambda x: float(x.get("total", 0.0) or 0.0), reverse=True
    ):
        total = round(float(r.get("total", 0.0) or 0.0), 2)
        running += total
        rows.append(
            {
                "Código": str(r.get("codigo", "") or ""),
                "Caso": str(r.get("caso", "") or ""),
                "Área": str(r.get("area", "") or ""),
                "Faturamento": cell(total),
                "n": int(r.get("n", 0) or 0),
                "kind": "amount",
            }
        )
    rows.append(
        {
            "Código": "",
            "Caso": "Total",
            "Área": "",
            "Faturamento": cell(round(running, 2) if rows_in else None),
            "kind": "total",
            "is_total": True,
        }
    )
    return {
        "kind": "rich",
        "name": "FATURAS Analítico",
        "columns": ["Código", "Caso", "Área", "Faturamento"],
        "rows": rows,
    }


#: Columns for the per-invoice faturamento lists (Nacional / Moedas). Mirrors the
#: workbook layout: invoice + client + dates + currency + honorários (foreign & BRL)
#: + received.
_FATURAS_MOEDA_COLUMNS = [
    "Fatura", "Cliente", "Caso", "Emissão", "Vencimento", "Recebimento",
    "Moeda", "Honorários", "Honorários (R$)", "Recebido (R$)",
]


def _faturas_moeda_tab(
    name: str, rows_in: list[dict[str, Any]]
) -> dict[str, Any]:
    """Build one per-invoice faturamento tab (Nacional or Moedas) from already
    currency-filtered rows. One row per invoice; a Total row sums the BRL columns."""

    def cell(v: float | None) -> dict[str, Any]:
        return {"value": v, "source": "realizado"}

    rows: list[dict[str, Any]] = []
    hon_nac_sum = 0.0
    receb_nac_sum = 0.0
    for r in sorted(
        rows_in, key=lambda x: float(x.get("honorarios_nac", 0.0) or 0.0), reverse=True
    ):
        hon = round(float(r.get("honorarios", 0.0) or 0.0), 2)
        hon_nac = round(float(r.get("honorarios_nac", 0.0) or 0.0), 2)
        receb_nac = round(float(r.get("recebido_hon_nac", 0.0) or 0.0), 2)
        hon_nac_sum += hon_nac
        receb_nac_sum += receb_nac
        rows.append(
            {
                "Fatura": r.get("numero"),
                "Cliente": str(r.get("cliente", "") or ""),
                "Caso": str(r.get("caso", "") or ""),
                "Emissão": str(r.get("data_emissao", "") or ""),
                "Vencimento": str(r.get("vencimento", "") or ""),
                "Recebimento": str(r.get("recebimento", "") or ""),
                "Moeda": str(r.get("moeda", "") or ""),
                "Honorários": cell(hon),
                "Honorários (R$)": cell(hon_nac),
                "Recebido (R$)": cell(receb_nac),
                "kind": "amount",
            }
        )
    rows.append(
        {
            "Fatura": "",
            "Cliente": "",
            "Caso": "Total",
            "Emissão": "",
            "Vencimento": "",
            "Recebimento": "",
            "Moeda": "",
            "Honorários": cell(None),
            "Honorários (R$)": cell(round(hon_nac_sum, 2) if rows_in else None),
            "Recebido (R$)": cell(round(receb_nac_sum, 2) if rows_in else None),
            "kind": "total",
            "is_total": True,
        }
    )
    return {
        "kind": "rich",
        "name": name,
        "columns": _FATURAS_MOEDA_COLUMNS,
        "rows": rows,
    }


def assemble_faturas_moeda(
    snapshot: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return ``(nacional, moedas)`` per-invoice faturamento tabs.

    Source: the snapshot's ``faturas_moeda`` block (LDESK.DB_VW_FATURASEMI_REC,
    per-invoice, validated to the centavo vs the sacred faturamento). A row is
    "nacional" when its currency equals the office's nacional currency
    (``moeda`` == ``moeda_nac``, i.e. R$); everything else is foreign ("Moedas").
    """
    rows_in = (snapshot or {}).get("faturas_moeda", []) or []
    nacional_rows = [
        r for r in rows_in if str(r.get("moeda", "")) == str(r.get("moeda_nac", ""))
    ]
    moedas_rows = [
        r for r in rows_in if str(r.get("moeda", "")) != str(r.get("moeda_nac", ""))
    ]
    return (
        _faturas_moeda_tab("Nacional", nacional_rows),
        _faturas_moeda_tab("Moedas", moedas_rows),
    )


def assemble_meta(
    budget: dict[str, dict[str, float]] | None,
    *,
    month: int | None,
    recebimento_realizado: float | None,
    ytd_recebimento: dict[int, float] | None = None,
) -> dict[str, Any]:
    """Meta goal-tracking dashboard (workbook 'Meta' sheet).

    Headline: annual recebimento goal (budget monthly * 12), monthly goal, this
    month's realized recebimento + attainment %, and remaining vs goal. Plus a
    12-month table with per-month goal and each closed month's realized recebimento.

    ``ytd_recebimento`` is a ``{month_index: recebimento}`` map covering every closed
    month of the competence year (built by the provider from the per-month snapshots);
    each present month is filled and the Total row aggregates them. When it is None
    only the competence ``month`` is filled (single-snapshot fallback)."""
    from app.closing.dre import RECEBIMENTO

    inst = (budget or {}).get("institucional", {})
    meta_mensal = inst.get(RECEBIMENTO)
    meta_anual = round(meta_mensal * 12, 2) if meta_mensal is not None else None

    def cell(v: float | None, source: str = "orcado") -> dict[str, Any]:
        return {"value": v, "source": source}

    # Per-month realized: prefer the YTD map; else just the competence month.
    ytd = dict(ytd_recebimento) if ytd_recebimento is not None else None
    if ytd is None and month is not None and recebimento_realizado is not None:
        ytd = {month: recebimento_realizado}
    ytd = ytd or {}

    # Competence-month attainment (headline KPI) stays month-based.
    attainment_mes = None
    if meta_mensal and recebimento_realizado is not None:
        attainment_mes = round(recebimento_realizado / meta_mensal, 4)

    total_realizado = round(sum(ytd.values()), 2) if ytd else None
    remaining = None
    if meta_anual is not None and total_realizado is not None:
        remaining = round(meta_anual - total_realizado, 2)
    total_pct = (
        round(total_realizado / meta_anual, 4)
        if (total_realizado is not None and meta_anual)
        else None
    )

    rows: list[dict[str, Any]] = []
    for idx, mes in enumerate(_MESES, start=1):
        realized = ytd.get(idx)
        rows.append(
            {
                "Mês": mes,
                "Meta": cell(meta_mensal),
                "Recebimento": cell(realized, "realizado"),
                "% Meta": (
                    round(realized / meta_mensal, 4)
                    if (realized is not None and meta_mensal)
                    else None
                ),
                "kind": "amount",
            }
        )
    rows.append(
        {
            "Mês": "Total",
            "Meta": cell(meta_anual),
            "Recebimento": cell(total_realizado, "realizado"),
            "% Meta": total_pct,
            "kind": "total",
            "is_total": True,
        }
    )

    return {
        "kind": "rich",
        "name": "Meta 2026",
        "columns": ["Mês", "Meta", "Recebimento", "% Meta"],
        "rows": rows,
        "meta_anual": cell(meta_anual),
        "meta_mensal": cell(meta_mensal),
        "atingimento_mes": attainment_mes,
        "falta": cell(remaining, "realizado"),
    }


def assemble_fluxo_consolidado(
    snapshot: dict[str, Any] | None,
    period_label: str,
) -> dict[str, Any]:
    """Per-area cash flow (workbook 'Fluxo consolidado'): Recebimento, Equipe,
    Despesas, Impostos, Amortização, Margem líquida per area. All per-area figures
    are SISJURI-derived (the same basis as the area DRE tabs): Recebimento from
    ``area_recebimento``; Despesas = Comissão + Despesas Equipe + Despesa
    Institucional (ledger when present, else the DB-derived rateio/cost-center
    values); Equipe from ``area_custo_equipe``."""
    from app.closing.dre import RealizadoInputs

    r = (
        RealizadoInputs.from_snapshot(snapshot)
        if snapshot is not None
        else RealizadoInputs.empty()
    )
    amort_area = round(AMORTIZACAO_MENSAL / len(AREAS), 2)

    rows: list[dict[str, Any]] = []
    for area in AREAS:
        # Recebimento is SISJURI-derived (area tabs' basis).
        receb = r.area_recebimento.get(area)
        equipe = r.area_custo_equipe.get(area)
        # Despesas = Comissão + Despesas Equipe + Despesa Institucional, each
        # DB-derived (ledger/rateio/cost-center) — mirrors the precedence in
        # ``dre._area_rows`` so the two tabs never disagree.
        comissao = r.area_comissao.get(area)
        desp_equipe = r.area_despesas_equipe.get(area)
        desp_inst = r.area_despesa_institucional.get(area)
        despesas = None
        if any(v is not None for v in (comissao, desp_equipe, desp_inst)):
            despesas = round(
                (comissao or 0.0) + (desp_equipe or 0.0) + (desp_inst or 0.0), 2
            )
        margem = None
        if receb is not None:
            margem = round(
                receb - (equipe or 0.0) - (despesas or 0.0) - amort_area, 2
            )
        rows.append({"Linha": area, "Valor": None, "is_total": True, "kind": "header", "key": f"hdr::{area}"})
        rows.append({"Linha": "Recebimento", "Valor": {"value": receb, "source": "realizado"}, "indent": 1, "key": f"{area}::receb"})
        rows.append({"Linha": "Equipe", "Valor": {"value": equipe, "source": "realizado"}, "indent": 1, "key": f"{area}::equipe"})
        rows.append({"Linha": "Despesas", "Valor": {"value": despesas, "source": "realizado"}, "indent": 1, "key": f"{area}::despesas"})
        rows.append({"Linha": "Amortização", "Valor": {"value": amort_area, "source": "realizado"}, "indent": 1, "key": f"{area}::amort"})
        rows.append({"Linha": "Margem líquida", "Valor": {"value": margem, "source": "calc"}, "indent": 1, "is_total": True, "key": f"{area}::margem"})
    return {
        "kind": "rich",
        "name": "Fluxo consolidado",
        "columns": ["Linha", "Valor"],
        "rows": rows,
        "snapshot_missing": snapshot is None,
    }


def assemble_institucional_ano(
    snapshot: dict[str, Any] | None,
    budget: dict[str, dict[str, float]] | None,
    period_label: str,
) -> dict[str, Any]:
    """Annual consolidated Institucional (workbook 'Institucional ano'): Orçado
    anual vs Realizado acumulado for the headline DRE lines. With single-month
    snapshots, Realizado is the month; Orçado is the annual budget."""
    from app.closing.dre import (
        AMORTIZACAO,
        CUSTO_EQUIPE,
        DESPESAS,
        IMPOSTO,
        RECEBIMENTO,
        RealizadoInputs,
    )

    r = (
        RealizadoInputs.from_snapshot(snapshot)
        if snapshot is not None
        else RealizadoInputs.empty()
    )
    inst = (budget or {}).get("institucional", {})

    def orc_annual(key: str) -> float | None:
        m = inst.get(key)
        return round(m * 12, 2) if m is not None else None

    # Amortização is a fixed worksheet value (8.117/mês); default to it when the
    # client budgeted no amortização, so the Orçado never blanks. The budget entry
    # (BudgetEditor) remains the manual override when present.
    amort_annual = round((inst.get(AMORTIZACAO) or AMORTIZACAO_MENSAL) * 12, 2)

    rows = [
        {"Linha": "Recebimento", "Orçado (ano)": {"value": orc_annual(RECEBIMENTO), "source": "orcado"}, "Realizado": {"value": r.recebimento, "source": "realizado"}, "key": RECEBIMENTO},
        {"Linha": "Custo equipe", "Orçado (ano)": {"value": orc_annual(CUSTO_EQUIPE), "source": "orcado"}, "Realizado": {"value": r.custo_equipe, "source": "realizado"}, "key": CUSTO_EQUIPE},
        {"Linha": "Despesas", "Orçado (ano)": {"value": orc_annual(DESPESAS), "source": "orcado"}, "Realizado": {"value": r.despesas, "source": "realizado"}, "key": DESPESAS},
        {"Linha": "Resultado Bruto", "Orçado (ano)": None, "Realizado": {"value": r.resultado_bruto, "source": "realizado"}, "is_total": True, "kind": "subtotal", "key": "resultado_bruto"},
        {"Linha": "Imposto", "Orçado (ano)": {"value": orc_annual(IMPOSTO), "source": "orcado"}, "Realizado": {"value": r.imposto, "source": "realizado"}, "key": IMPOSTO},
        {"Linha": "Amortização", "Orçado (ano)": {"value": amort_annual, "source": "orcado"}, "Realizado": {"value": r.amortizacao, "source": "manual"}, "key": "amortizacao"},
        {"Linha": "Resultado Liquido", "Orçado (ano)": None, "Realizado": {"value": r.resultado_liquido, "source": "realizado"}, "is_total": True, "kind": "subtotal", "key": "resultado_liquido"},
    ]
    return {
        "kind": "rich",
        "name": "Institucional ano",
        "columns": ["Linha", "Orçado (ano)", "Realizado"],
        "rows": rows,
        "snapshot_missing": snapshot is None,
    }
