# backend/app/closing/presentation.py
"""Assemble the client-facing presentation deck — an in-app mirror of Rumo's
monthly PPTX (reference/workbook/MBC Resultado Jan a Mai 2026.pdf).

This is a PURE PROJECTION of already-assembled data:
  * ``month_sections``  — {month_index: assemble_dre_sections(...)} for every
    CLOSED month Jan→competence (same objects the monthly tabs use);
  * ``ytd_sections``    — accumulate_ytd(...) over those months (the acumulado
    tab's data), carrying Orçado YTD / Realizado YTD / Variação per line;
  * ``meta``            — assemble_meta(...) for per-month recebimento vs goal.

It re-shapes them into the deck the client presents, slide by slide:

  1  Capa                       — título + período + subtítulo
  2  Índice
  3  Institucional — mês        — 4 KPI headline + monthly detail table (per month
                                  + YTD column), mirroring PDF p.3
  4  Institucional — YTD × Meta — receita/RB/RL/margem YTD KPIs + per-month
                                  attainment bars + reserva-bônus column (PDF p.4)
  5  Análise YTD                — Orçado×Realizado per line, Variação R$/%, status
                                  dot (PDF p.5)
  6+ Por área (Contencioso / Econômico / Arbitragem) — mês + YTD KPIs, attainment
                                  bars, custo detail, DRE YTD (PDF p.6-11)
  N  Reserva de bônus           — per-área × per-month matrix + YTD (PDF p.12)

The frontend renders these as printable slides; nothing here computes a NEW
financial number — every value traces to a monthly/YTD section cell.
"""
from __future__ import annotations

from typing import Any

# Deck-wide line order for the per-área DRE table (PDF p.7/9/11).
_AREA_DRE_LINES: tuple[tuple[str, str], ...] = (
    ("recebimento", "Receita"),
    ("custo_equipe", "Custo Equipe"),
    ("comissao", "Participação/Comissão"),
    ("despesas_equipe", "Despesas Equipe"),
    ("despesa_institucional", "Despesas Institucionais"),
    ("resultado_bruto", "Resultado Bruto"),
    ("imposto", "Impostos"),
    ("amortizacao", "Invest./Amortização"),
    ("resultado_liquido", "Resultado Líquido"),
    ("reserva_bonus", "Reserva de Bônus"),
)

_MESES_ABBR = (
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
)
_MESES = (
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
)

_AREAS: tuple[tuple[str, str], ...] = (
    ("contencioso", "Contencioso"),
    ("economico", "Econômico"),
    ("arbitragem", "Arbitragem & Compliance"),
)


def _num(v: Any) -> float | None:
    """Unwrap a sourced cell / bare number to a float, else None."""
    if isinstance(v, dict):
        v = v.get("value")
    return float(v) if isinstance(v, (int, float)) else None


def _cell(rows: list[dict[str, Any]] | None, key: str, col: str = "Realizado") -> float | None:
    if not rows:
        return None
    row = next((r for r in rows if r.get("key") == key), None)
    return _num(row.get(col)) if row else None


def _rows(section: dict[str, Any] | None) -> list[dict[str, Any]] | None:
    if not isinstance(section, dict):
        return None
    rows = section.get("rows")
    return rows if isinstance(rows, list) else None


def _pct(num: float | None, den: float | None) -> float | None:
    if num is None or not den:
        return None
    return round(num / den, 4)


#: Lines where a HIGHER realizado is favourable (revenue/result). Everything else
#: (costs, expenses, taxes) is favourable when LOWER. Drives the status dot color.
_HIGHER_IS_BETTER = frozenset({
    "recebimento", "resultado_bruto", "resultado_liquido", "reserva_bonus",
    "margem_bruta", "margem_liquida",
})


def _variation(orcado: float | None, realizado: float | None, key: str = "") -> dict[str, Any]:
    """Variação block: R$ delta, %, and a traffic-light status like the PDF dots.

    Status mirrors the deck legend — verde = economia/acima da meta, amarelo =
    atenção, vermelho = desvio crítico — oriented by whether the line is
    higher-is-better (revenue/result) or lower-is-better (cost). Thresholds on the
    favourable-signed % gap: within 5% → ok, 5–15% adverse → atenção, >15% adverse
    → crítico; any favourable gap → ok.
    """
    if orcado is None or realizado is None:
        return {"delta": None, "pct": None, "status": None}
    delta = round(realizado - orcado, 2)
    pct = round(delta / orcado, 4) if orcado else None
    status: str | None = None
    if pct is not None:
        higher_better = key in _HIGHER_IS_BETTER
        # Favourable direction: + for revenue/result, − for cost.
        favourable = pct if higher_better else -pct
        if favourable >= -0.05:
            status = "ok"
        elif favourable >= -0.15:
            status = "atencao"
        else:
            status = "critico"
    return {"delta": delta, "pct": pct, "status": status}


def build_presentation(
    *,
    client_name: str,
    period_label: str,
    period_month: int,
    period_year: int,
    kpis: dict[str, Any],
    month_sections: dict[int, dict[str, Any]],
    ytd_sections: dict[str, Any] | None,
    meta: dict[str, Any] | None,
    faturamento_by_month: dict[int, float] | None = None,
) -> dict[str, Any]:
    """Return the full presentation payload (see module docstring)."""
    present_months = sorted(m for m in month_sections if m <= period_month)
    comp = month_sections.get(period_month, {})

    # ── Slide 3: Institucional monthly detail (per-month columns + YTD) ──────
    inst_lines = (
        ("faturamento", "Faturamento"),
        ("recebimento", "Receita"),
        ("resultado_bruto", "Res. Bruto"),
        ("margem_bruta", "Mg. Bruta"),
        ("resultado_liquido", "Res. Líquido"),
        ("margem_liquida", "Mg. Líquida"),
        ("reserva_bonus", "Reserva Bônus"),
    )
    inst_ytd = _rows((ytd_sections or {}).get("institucional"))

    # Faturamento is not a DRE row, so it cannot come from the sections or the YTD
    # accumulator. ``faturamento_by_month`` carries it per month, read straight off
    # each snapshot's ``revenue.faturamento_bruto`` by the provider (all six 2026
    # months tie Fechamento MBC 06.2026 exactly). Client, 2026-07-28 19:49: *"ele não
    # está puxando janeiro, fevereiro, março, abril no faturamento embaixo."*
    fat_months = dict(faturamento_by_month or {})

    def inst_month_value(m: int, key: str) -> float | None:
        if key == "faturamento":
            return fat_months.get(m)
        return _cell(_rows(month_sections.get(m, {}).get("institucional")), key)

    detail_rows: list[dict[str, Any]] = []
    for key, label in inst_lines:
        by_month = {m: inst_month_value(m, key) for m in present_months}
        if key == "faturamento":
            # The competence month's KPI is the authoritative faturamento (it is the
            # sacred LegalDesk figure); keep it winning over the snapshot copy.
            by_month[period_month] = (
                _num(kpis.get("faturamento_realizado")) or by_month.get(period_month)
            )
            # No DRE row to accumulate ⇒ sum what we show.
            present = [v for v in by_month.values() if v is not None]
            ytd_val = round(sum(present), 2) if present else None
        else:
            ytd_val = _cell(inst_ytd, key, "Realizado YTD")
        detail_rows.append({"key": key, "label": label, "months": by_month, "ytd": ytd_val})

    # ── Slide 4: YTD vs Meta + per-month attainment + reserva column ─────────
    meta = meta or {}
    meta_rows = meta.get("rows") or []
    attainment = []
    for idx, mes in enumerate(_MESES, start=1):
        if idx not in present_months:
            continue
        mrow = next((r for r in meta_rows if r.get("Mês") == mes), None)
        receb = _num(mrow.get("Recebimento")) if mrow else None
        meta_mensal = _num(mrow.get("Meta")) if mrow else None
        attainment.append({
            "mes": mes,
            "abbr": _MESES_ABBR[idx - 1],
            "recebimento": receb,
            "meta": meta_mensal,
            "pct": _pct(receb, meta_mensal),
            "gap": (round(receb - meta_mensal, 2) if (receb is not None and meta_mensal is not None) else None),
        })
    meta_anual = _num(meta.get("meta_anual"))
    receita_ytd = _cell(inst_ytd, "recebimento", "Realizado YTD")
    rb_ytd = _cell(inst_ytd, "resultado_bruto", "Realizado YTD")
    rl_ytd = _cell(inst_ytd, "resultado_liquido", "Realizado YTD")

    # ── Slide 5: Análise YTD (Orçado × Realizado per line, Variação) ─────────
    analysis_lines = (
        ("recebimento", "Receita Líquida"),
        ("custo_equipe", "Custos Diretos"),
        ("despesas", "Despesas Indiretas"),
        ("resultado_bruto", "Resultado Bruto"),
        ("imposto", "Impostos"),
        ("amortizacao", "Invest./Amortização"),
        ("resultado_liquido", "Resultado Líquido"),
    )
    analysis = []
    for key, label in analysis_lines:
        orc = _cell(inst_ytd, key, "Orçado YTD")
        real = _cell(inst_ytd, key, "Realizado YTD")
        analysis.append({"key": key, "label": label, "orcado": orc,
                         "realizado": real, **_variation(orc, real, key)})

    # ── Slides 6+: per-área (mês + YTD + DRE) ────────────────────────────────
    areas = []
    for akey, alabel in _AREAS:
        acomp = _rows(comp.get(akey))
        aytd = _rows((ytd_sections or {}).get(akey))
        # per-month attainment for this área (receita vs its recebimento Orçado)
        area_att = []
        for m in present_months:
            arows = _rows(month_sections.get(m, {}).get(akey))
            receb = _cell(arows, "recebimento")
            orc = _cell(arows, "recebimento", "Orçado")
            area_att.append({
                "abbr": _MESES_ABBR[m - 1],
                "recebimento": receb,
                "meta": orc,
                "pct": _pct(receb, orc),
                "gap": (round(receb - orc, 2) if (receb is not None and orc is not None) else None),
            })
        dre = []
        for key, label in _AREA_DRE_LINES:
            orc = _cell(aytd, key, "Orçado YTD")
            real = _cell(aytd, key, "Realizado YTD")
            dre.append({"key": key, "label": label, "orcado": orc,
                        "realizado": real, **_variation(orc, real, key)})
        areas.append({
            "key": akey,
            "label": alabel,
            "mes": {
                "receita": _cell(acomp, "recebimento"),
                "resultado_bruto": _cell(acomp, "resultado_bruto"),
                "resultado_liquido": _cell(acomp, "resultado_liquido"),
                "meta_receita": _cell(acomp, "recebimento", "Orçado"),
            },
            "ytd": {
                "receita": _cell(aytd, "recebimento", "Realizado YTD"),
                "resultado_liquido": _cell(aytd, "resultado_liquido", "Realizado YTD"),
                "meta_receita": _cell(aytd, "recebimento", "Orçado YTD"),
            },
            "atingimento": area_att,
            "dre": dre,
        })

    # ── Reserva de bônus matrix (institucional + áreas × months + YTD) ───────
    reserva_areas = [("institucional", "Institucional"), *_AREAS]
    reserva = []
    for akey, alabel in reserva_areas:
        by_month = {
            m: _cell(_rows(month_sections.get(m, {}).get(akey)), "reserva_bonus")
            for m in present_months
        }
        ytd_val = _cell(_rows((ytd_sections or {}).get(akey)), "reserva_bonus", "Realizado YTD")
        reserva.append({"key": akey, "label": alabel, "months": by_month, "ytd": ytd_val})

    return {
        "titulo": client_name,
        "periodo": period_label,
        "periodo_mes": _MESES[period_month - 1] if 1 <= period_month <= 12 else period_label,
        "ano": period_year,
        "meses_presentes": [_MESES_ABBR[m - 1] for m in present_months],
        # Slide 3 headline (competence month)
        "headline": {
            "faturamento": _num(kpis.get("faturamento_realizado")),
            "recebimento": _num(kpis.get("receita_honorarios")),
            "resultado_bruto": _num(kpis.get("resultado_bruto")),
            "margem_bruta": _num(kpis.get("margem_bruta")),
            "resultado_liquido": _num(kpis.get("resultado_liquido")),
            "margem_liquida": _num(kpis.get("margem_liquida")),
            "reserva_bonus": _num(kpis.get("reserva_bonus")),
        },
        "institucional_detalhe": {
            "meses": [_MESES_ABBR[m - 1] for m in present_months],
            "month_indices": present_months,
            "linhas": detail_rows,
        },
        "meta": {
            "anual": meta_anual,
            "receita_ytd": receita_ytd,
            "resultado_bruto_ytd": rb_ytd,
            "resultado_liquido_ytd": rl_ytd,
            "margem_liquida_ytd": _pct(rl_ytd, receita_ytd),
            "atingimento": attainment,
        },
        "analise_ytd": analysis,
        "areas": areas,
        "reserva": {
            "meses": [_MESES_ABBR[m - 1] for m in present_months],
            "linhas": reserva,
        },
    }


__all__ = ["build_presentation"]
