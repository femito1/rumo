"""Assemble the structured dashboard payload (``data.json``) for one month.

The output mirrors the MBC closing workbook tab-by-tab. Every value is tagged
with a ``source`` so the frontend can render the API / MANUAL / FORMULA badges:

- ``"api"``     – value came live from the Legal Manager OData API.
- ``"manual"``  – not available in this API (TOTVS Backoffice); left blank.
- ``"formula"`` – derived from other cells.

This is intentionally a pure transformation over the API client so it can be
unit-tested and re-run deterministically for any closed month.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from .api_client import LegalDeskClient, to_float
from .base_resultado_layout import BASE_RESULTADO_LINES
from .period import Period
from .tab_layouts import TAB_LAYOUTS, TAB_ORDER

API = "api"
MANUAL = "manual"
FORMULA = "formula"

# The four tabs whose live values we compute for the target month get a "rich"
# bespoke renderer. Every other tab is rendered as a generic reference grid so
# the dashboard still mirrors all 15 workbook tabs 1:1.
RICH_TABS = {"meta", "base_resultado", "resumo_recebidas", "faturas_centro_custo"}

# Human-readable note shown atop each grid tab explaining its automation status.
GRID_NOTES = {
    "areas_sintetico": ("api", "Receita e Faturamento Realizado do mês vêm da API; a quebra por área/advogado é detalhamento/fórmula. Valores numéricos exibidos são a referência do workbook."),
    "dre_2026": ("formula", "DRE orçado/planejado. Depende da aba Orçamento 2026 (sem API) e de fórmulas. Valores são referência do workbook."),
    "orcamento_2026": ("manual", "Orçamento detalhado por advogado. A API só expõe orçado de 2025 (estrutura diferente). Montado à mão — sem API hoje."),
    "institucional": ("formula", "Consolidado Orçado × Realizado. Recalcula a partir das áreas e despesas (Fase 2)."),
    "institucional_ano": ("formula", "Consolidado anual. Fórmula sobre as fontes."),
    "contencioso": ("formula", "Área Contencioso: Orçado × Realizado. Recebimento vem do rateio (API); custos/despesas são Fase 2."),
    "economico": ("formula", "Área Econômico: Orçado × Realizado. Idem Contencioso."),
    "arbitragem": ("formula", "Área Arbitragem e Compliance: Orçado × Realizado. Idem Contencioso."),
    "rateio_mensal": ("formula", "Rateio de custo de equipe + despesas por área. 100% fórmula; depende da folha/despesa (Fase 2)."),
    "fluxo_consolidado": ("formula", "Fluxo consolidado por área/mês. Fórmula sobre Areas Sintetico."),
    "amortizacao": ("manual", "Cronograma de amortização (parcelas 1/60...). Tabela fixa histórica — sem API."),
}


def _cell(value: float | None, source: str) -> dict[str, Any]:
    return {"value": value, "source": source}


def build_payload(period: Period, client: LegalDeskClient | None = None) -> dict[str, Any]:
    client = client or LegalDeskClient()

    rec_rows = client.recebimento_rows(period.ano_mes)
    fat_rows = client.faturamento_rows(period.ano_mes)
    rateio_rows = client.rateio_profissional_rows(period.date_start, period.date_end)
    fatura_rows = client.fatura_rows(period.date_start, period.date_end)
    caso_rows = client.rateio_caso_rows(period.date_start, period.date_end)

    recebimento_bruto = round(sum(to_float(r.get("Valor1")) for r in rec_rows), 2)
    faturamento_bruto = round(sum(to_float(r.get("Valor1")) for r in fat_rows), 2)

    tax_rates = client.tributo_percentuais(period.ano_mes)
    derived = _build_derived(recebimento_bruto, faturamento_bruto, tax_rates)

    rich = {
        "base_resultado": _build_base_resultado(recebimento_bruto),
        "meta": _build_meta(period, recebimento_bruto, faturamento_bruto),
        "resumo_recebidas": _build_resumo_recebidas(rateio_rows),
        "faturas_centro_custo": _build_faturas_centro_custo(fatura_rows, caso_rows),
    }

    tabs: dict[str, Any] = {}
    for tab_id in TAB_ORDER:
        layout = TAB_LAYOUTS[tab_id]
        if tab_id in RICH_TABS:
            tabs[tab_id] = {"kind": "rich", "name": layout["name"], **rich[tab_id]}
        else:
            tabs[tab_id] = _build_grid_tab(tab_id, layout)

    payload: dict[str, Any] = {
        "meta": {
            "period": period.ano_mes,
            "period_label": period.label,
            "column_letter": period.column_letter,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "kpis": {
            "receita_honorarios": recebimento_bruto,
            "faturamento_realizado": faturamento_bruto,
            "faturas_emitidas": len({f.get("Numero") for f in fatura_rows}),
            "recebimento_rows": len(rec_rows),
            "faturamento_rows": len(fat_rows),
        },
        "tab_order": list(TAB_ORDER),
        "tabs": tabs,
        "derived": derived,
    }
    payload["coverage"] = _compute_coverage(payload)
    return payload


def _build_derived(recebimento: float, faturamento: float, rates: dict[str, float]) -> dict[str, Any]:
    """Live-computed values that the workbook gets via formulas.

    These need no institutional-expense data — they derive purely from the
    revenue we already pull exactly, plus the published tax rates. Tax figures
    are *estimates* (base × rate), matching the DRE's own formula approach, not
    the actual amounts paid (which live in TOTVS Backoffice).
    """
    impostos = {
        name: round(faturamento * rate, 2)
        for name, rate in rates.items()
    }
    impostos_total = round(sum(impostos.values()), 2)
    return {
        "recebimento_bruto": recebimento,
        "faturamento_bruto": faturamento,
        "tax_rates": rates,
        "impostos_estimados": impostos,
        "impostos_estimados_total": impostos_total,
        "resultado_bruto_sobre_faturamento": round(faturamento - impostos_total, 2),
        "note": "Impostos = Faturamento × alíquota (TributoViews). Estimativa por fórmula, não o valor pago.",
    }


def _build_grid_tab(tab_id: str, layout: dict) -> dict[str, Any]:
    """Generic reference grid for a non-bespoke tab (1:1 layout mirror)."""
    note_source, note = GRID_NOTES.get(tab_id, ("formula", ""))
    return {
        "kind": "grid",
        "id": tab_id,
        "name": layout["name"],
        "note": note,
        "note_source": note_source,
        "rows": layout["rows"],
        "cols": layout["cols"],
        "grid": layout["grid"],
    }


def _build_base_resultado(recebimento_bruto: float) -> dict[str, Any]:
    """The 1:1 line layout. Only 'Receita de honorários' is API-fed in v0."""
    rows = []
    for line in BASE_RESULTADO_LINES:
        if line["source"] == API:
            cell = _cell(recebimento_bruto, API)
        else:
            cell = _cell(None, line["source"])
        rows.append({
            "row": line["row"],
            "label": line["label"],
            "indent": line.get("indent", 0),
            "is_total": line.get("is_total", False),
            **cell,
        })
    return {
        "name": "Base_Resultado Mensal_V2",
        "description": "DRE mensal. Linha 4 (Receita de honorários) = Recebimento Bruto da API. Demais linhas são despesa institucional (TOTVS Backoffice, sem API) ou totais por fórmula.",
        "columns": ["#", "Linha", "Valor (Maio 2026)"],
        "rows": rows,
    }


def _build_meta(period: Period, recebimento: float, faturamento: float) -> dict[str, Any]:
    """Meta__2 monthly Recebimento + Faturamento for the target month."""
    return {
        "name": "Meta (2)",
        "description": "Recebimento e Faturamento do mês (Σ Valor1). Meta mensal e despesas seguem manuais.",
        "columns": ["Mês", "Recebimento", "Faturamento", "Meta", "Despesas"],
        "rows": [
            {
                "label": period.month_name_pt,
                "recebimento": _cell(recebimento, API),
                "faturamento": _cell(faturamento, API),
                "meta": _cell(None, MANUAL),
                "despesas": _cell(None, MANUAL),
            }
        ],
    }


def _build_resumo_recebidas(rateio_rows: list[dict]) -> dict[str, Any]:
    """One block per invoice; per-lawyer rows de-duplicated.

    RateioFaturaProfissionalViews returns each (FaturaNumero, ProfissionalSigla)
    pair **twice** (one per timesheet entry). We take the per-pair value once.
    """
    by_invoice: dict[Any, dict[str, Any]] = {}
    seen_pairs: dict[tuple, float] = {}

    for r in rateio_rows:
        fatura = r.get("FaturaNumero")
        sigla = r.get("ProfissionalSigla")
        pair = (fatura, sigla)
        if pair in seen_pairs:
            continue
        seen_pairs[pair] = to_float(r.get("ValorTrabalhado"))

        inv = by_invoice.setdefault(fatura, {
            "fatura": fatura,
            "cliente": r.get("ClientePessoaNome"),
            "caso": r.get("CasoAssunto"),
            "data_emissao": (r.get("FaturaDataEmissao") or "")[:10],
            "valor_faturado": to_float(r.get("ValorFaturado")),
            "lawyers": [],
        })
        inv["lawyers"].append({
            "sigla": sigla,
            "nome": r.get("ProfissionalPessoaNome"),
            "valor_trabalhado": round(seen_pairs[pair], 2),
        })

    invoices = sorted(by_invoice.values(), key=lambda x: str(x["fatura"]))
    return {
        "name": "Resumo_Recebidas 2025_2026",
        "description": "Cada fatura quebrada por advogado (valores agrupados por advogado).",
        "columns": ["Fatura", "Cliente", "Caso", "Advogado", "Valor", "DT Emissão", "Total Fatura"],
        "source": API,
        "invoices": invoices,
        "invoice_count": len(invoices),
    }


def _build_faturas_centro_custo(fatura_rows: list[dict], caso_rows: list[dict]) -> dict[str, Any]:
    """Invoice header + per-case breakdown joined on FaturaNumero."""
    casos_by_fatura: dict[Any, list[dict]] = defaultdict(list)
    for c in caso_rows:
        casos_by_fatura[c.get("FaturaNumero")].append({
            "caso_codigo": c.get("CasoCodigo"),
            "caso_assunto": c.get("CasoAssunto"),
            "total_faturado": round(to_float(c.get("TotalFaturado")), 2),
            "total_rateado": round(to_float(c.get("TotalRateado")), 2),
        })

    rows = []
    for f in sorted(fatura_rows, key=lambda x: str(x.get("Numero"))):
        numero = f.get("Numero")
        rows.append({
            "numero": numero,
            "razao_social": f.get("RazaoSocial") or f.get("ClientePessoaNome"),
            "data_emissao": (f.get("DataEmissao") or "")[:10],
            "valor_honorarios": round(to_float(f.get("ValorHonorarios")), 2),
            "valor_desconto": round(to_float(f.get("ValorDesconto")), 2),
            "situacao": f.get("Situacao"),
            "responsavel": f.get("ProfissionalResponsavelSigla"),
            "casos": casos_by_fatura.get(numero, []),
        })
    return {
        "name": "FATURAS Analitico CENTRO CUSTO",
        "description": "Cabeçalho da fatura + quebra por caso/centro de custo.",
        "columns": ["Núm. Fat.", "Razão Social", "Data Emissão", "Valor Honorários", "Situação", "Sócio Responsável"],
        "source": API,
        "rows": rows,
        "fatura_count": len(rows),
    }


def _compute_coverage(payload: dict[str, Any]) -> dict[str, int]:
    """Count Base_Resultado line items by source, for the coverage meter."""
    counts = {API: 0, MANUAL: 0, FORMULA: 0}
    for row in payload["tabs"]["base_resultado"]["rows"]:
        counts[row["source"]] = counts.get(row["source"], 0) + 1
    total = sum(counts.values())
    return {
        "automated": counts[API],
        "manual": counts[MANUAL],
        "formula": counts[FORMULA],
        "total": total,
    }
