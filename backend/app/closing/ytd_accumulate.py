# backend/app/closing/ytd_accumulate.py
"""Accumulate per-month DRE sections into a year-to-date (acumulado) view.

The 2026-07 client checkpoint asked for a cumulative view of the closed months
Jan→competence ("é só pegar de janeiro ao mês que a gente está falando"). In the
workbook this is NOT a separate sheet or render mode: it is the column group at the
far right of 'Areas Sintetico atualizado' (06.2026 cols Z..AE) over the SAME stacked
rows. So we ACCUMULATE the already-assembled monthly sections and surface them as
one extra tab — which inherits every per-month rule (per-área reserva, imposto, the
expense breakdown) for free, instead of re-deriving them:

- numeric ``amount``/``subtotal``/``section_total`` rows: sum Realizado and Orçado
  across the closed months Jan→competence, per (block, line);
- ``margin`` rows: recomputed from the accumulated base *of their own block*
  (a ratio can't be summed);
- ``header`` rows: label preserved, value cells empty.

Columns mirror the workbook's cumulative block VALUES with corrected NAMES — the
sheet's own headers are misleading (its "Orçado YTG" holds the annual budget and its
"Variação Mensal" holds a ratio), and shipping them verbatim would mean two
similarly-named columns plus a "%"-detection trap in the frontend:

    Linha | Orçado YTD | Realizado YTD | Variação | Desvio % | Orçado Anual | Falta p/ meta
      A         AA            AB            AC         AD           Z              AE

Every row keeps display-value keys BEFORE metadata keys (``key``/``indent``/
``is_total``/``kind``) — including header rows — because the frontend binds columns
positionally via ``Object.keys(rows[0]).slice(0, columns.length)`` and row 0 of
``areas_sintetico`` is a header.
"""
from __future__ import annotations

from typing import Any

#: Display columns, in positional-binding order. Public: tests and the provider
#: assert against this rather than re-spelling the header strings.
YTD_COLUMNS = [
    "Linha", "Orçado YTD", "Realizado YTD", "Variação", "Desvio %",
    "Orçado Anual", "Falta p/ meta",
]

#: Sections that carry the DRE Orçado/Realizado shape and therefore accumulate.
#: Everything else has its own columns and no YTD meaning (``rateio_mensal`` is a
#: within-month share, ``amortizacao`` a static schedule, ``dre_2026`` already the
#: annual budget across 12 month columns, ``meta_dashboard`` already cumulative,
#: ``base_resultado``/``nacional``/``moedas``/``faturas_analitico`` single-month
#: ledgers) — force-fitting them to the YTD columns emptied them.
_YTD_SECTIONS = frozenset({
    "institucional", "contencioso", "economico", "arbitragem", "areas_sintetico",
})

#: Line keys whose YTD is a ratio recomputed from the accumulated base (numerator
#: line ÷ recebimento), never a sum. Mirrors the monthly ``kind == "margin"`` rows.
_MARGIN_NUMERATOR = {
    "margem_bruta": "resultado_bruto",
    "margem_liquida": "resultado_liquido",
}

#: Accumulator key: (block index within the section, line key, nth occurrence in
#: that block). ``areas_sintetico`` stacks institucional + the three áreas, all
#: repeating the same line keys, so a flat ``{key: total}`` map would show every
#: block the sum of all four.
_AccKey = tuple[int, str, int]


def annual_by_block(
    annual_budget: dict[str, dict[str, float]] | None,
) -> dict[str, list[dict[str, float]]]:
    """Reshape the área-keyed annual budget into per-section, per-block maps.

    ``budget.models.annual_budget`` returns ``{área: {line: annual}}`` — only
    ``institucional`` is typed in practice. The accumulator needs one map per BLOCK
    of each section, so:

    - single-block sections (``institucional``, ``contencioso``, ``economico``,
      ``arbitragem``) get a one-element list;
    - ``areas_sintetico`` gets ``[institucional, Contencioso, Econômico, Arbitragem]``.

    Per-área annuals are DERIVED, mirroring the workbook (06.2026 'Areas Sintetico'
    ``Z36 = ($Z$3-($Z$3/4))/2``, ``Z54`` same, ``Z72 = $Z$3/4``): the institucional
    annual split 37,5 / 37,5 / 25 — the same fixed plan split ``dre._per_area_orcado``
    already uses for the monthly Orçado. Lines the workbook doesn't split per área
    are left out (→ the cell renders "—", which is correct: no per-área annual plan).
    """
    from app.closing.dre import RECEBIMENTO, RECEBIMENTO_ORCADO_SHARE

    ann = annual_budget or {}
    inst = ann.get("institucional", {})

    def area_map(area: str) -> dict[str, float]:
        out: dict[str, float] = {}
        recb = inst.get(RECEBIMENTO)
        if recb is not None:
            out[RECEBIMENTO] = round(recb * RECEBIMENTO_ORCADO_SHARE[area], 2)
        # The área's own typed annual lines (e.g. custo_equipe) pass through.
        for line, v in (ann.get(area) or {}).items():
            out[line] = v
        return out

    areas = [area_map(a) for a in ("Contencioso", "Econômico", "Arbitragem")]
    return {
        "institucional": [inst],
        "contencioso": [areas[0]],
        "economico": [areas[1]],
        "arbitragem": [areas[2]],
        "areas_sintetico": [inst, *areas],
    }


def _cell_value(row: dict[str, Any], col: str) -> float | None:
    v = row.get(col)
    if isinstance(v, dict):
        v = v.get("value")
    return v if isinstance(v, (int, float)) else None


def _cell(v: float | None, source: str) -> dict[str, Any]:
    return {"value": v, "source": source}


def _walk(rows: list[dict[str, Any]]) -> list[tuple[dict[str, Any], _AccKey | None]]:
    """Pair each row with its accumulator key, partitioning at ``header`` rows.

    Header rows open a new block and accumulate nothing (key ``None``). Occurrence
    counting is per (block, line key), so it tolerates a month whose row list
    differs in length — ``_institucional_rows`` emits one ``acct::`` row per account
    actually present in that month's snapshot.
    """
    out: list[tuple[dict[str, Any], _AccKey | None]] = []
    block = 0
    seen: dict[tuple[int, str], int] = {}
    for row in rows:
        key = row.get("key")
        if row.get("kind") == "header":
            block += 1
            out.append((row, None))
            continue
        if key is None:
            out.append((row, None))
            continue
        n = seen.get((block, str(key)), 0)
        seen[(block, str(key))] = n + 1
        out.append((row, (block, str(key), n)))
    return out


def accumulate_ytd(
    months: dict[int, dict[str, dict[str, Any]]],
    *,
    annual_budget: dict[str, list[dict[str, float]]] | None,
    up_to_month: int,
) -> dict[str, dict[str, Any]]:
    """Return accumulated DRE sections (Jan→``up_to_month``) with YTD columns.

    ``months`` is ``{month_index: assembled_sections}`` (as ``assemble_dre_sections``
    returns). Only months ``<= up_to_month`` that are present contribute. Section /
    row structure is taken from the latest present month so labels/order are current.

    ``annual_budget`` is ``{section_id: [annual line map PER BLOCK]}`` — one map per
    block, in block order (for ``areas_sintetico``: institucional, Contencioso,
    Econômico, Arbitragem). It is NOT the raw ``budget.models.annual_budget`` output:
    that is keyed by *área*, so indexing it by *section id* missed on every section
    and left ``Orçado Anual`` / ``Falta p/ meta`` blank everywhere. Build it with
    ``annual_by_block``.
    """
    annual_budget = annual_budget or {}
    present = sorted(m for m in months if m <= up_to_month)
    if not present:
        return {}
    template_month = present[-1]

    out: dict[str, dict[str, Any]] = {}
    for section_key, section in months[template_month].items():
        if section_key not in _YTD_SECTIONS:
            continue
        if not isinstance(section, dict) or section.get("kind") != "rich":
            continue

        # Accumulate Realizado/Orçado per (block, line, occurrence) across months.
        acc_real: dict[_AccKey, float] = {}
        acc_orc: dict[_AccKey, float] = {}
        for m in present:
            sec_m = months[m].get(section_key)
            if not isinstance(sec_m, dict):
                continue
            for row, acc_key in _walk(sec_m.get("rows", [])):
                if acc_key is None:
                    continue
                rv = _cell_value(row, "Realizado")
                if rv is not None:
                    acc_real[acc_key] = round(acc_real.get(acc_key, 0.0) + rv, 2)
                ov = _cell_value(row, "Orçado")
                if ov is not None:
                    acc_orc[acc_key] = round(acc_orc.get(acc_key, 0.0) + ov, 2)

        ann_blocks = annual_budget.get(section_key) or []
        walked = _walk(section.get("rows", []))
        # Map each raw block id to a dense 0-based ordinal, so `ann_blocks` is
        # simply "one map per block, in order" regardless of whether the section
        # opens with a header (areas_sintetico) or not (institucional, áreas).
        ordinals = {
            b: i
            for i, b in enumerate(
                sorted({k[0] for _, k in walked if k is not None})
            )
        }
        rows_out: list[dict[str, Any]] = []
        for tmpl, acc_key in walked:
            idx = ordinals.get(acc_key[0], -1) if acc_key else -1
            ann_sec = ann_blocks[idx] if 0 <= idx < len(ann_blocks) else {}
            rows_out.append(
                _ytd_row(tmpl, acc_key, acc_real, acc_orc, ann_sec)
            )

        out[section_key] = {
            "kind": "rich",
            "name": section.get("name"),
            "columns": list(YTD_COLUMNS),
            "rows": rows_out,
            "snapshot_missing": section.get("snapshot_missing", False),
        }
    return out


def _ytd_row(
    tmpl: dict[str, Any],
    acc_key: _AccKey | None,
    acc_real: dict[_AccKey, float],
    acc_orc: dict[_AccKey, float],
    ann_sec: dict[str, float],
) -> dict[str, Any]:
    """Build one output row. Header/structural rows keep their label with empty
    value cells — but still expose the YTD keys first, so the frontend's positional
    column binding (which samples ``rows[0]``) stays correct."""
    kind = tmpl.get("kind")
    meta = {
        "key": tmpl.get("key"),
        "indent": tmpl.get("indent", 0),
        "is_total": tmpl.get("is_total", False),
        "kind": kind,
    }
    if acc_key is None:
        return {
            "Linha": tmpl.get("Linha"),
            "Orçado YTD": None,
            "Realizado YTD": None,
            "Variação": None,
            "Desvio %": None,
            "Orçado Anual": None,
            "Falta p/ meta": None,
            **meta,
        }

    block, key, occurrence = acc_key
    if kind == "margin":
        # A ratio is recomputed from its OWN block's accumulated base.
        num_key = _MARGIN_NUMERATOR.get(key)
        real_ytd = _ratio(acc_real, block, num_key, occurrence)
        orc_ytd = _ratio(acc_orc, block, num_key, occurrence)
        var = desvio = annual = falta = None
    else:
        real_ytd = acc_real.get(acc_key)
        orc_ytd = acc_orc.get(acc_key)
        var = (
            round(real_ytd - orc_ytd, 2)
            if (real_ytd is not None and orc_ytd is not None)
            else None
        )
        desvio = (
            round(real_ytd / orc_ytd, 4)
            if (real_ytd is not None and orc_ytd)
            else None
        )
        annual = ann_sec.get(key)
        # Workbook AE = annual − Realizado YTD: what is still missing to hit the plan.
        falta = (
            round(annual - real_ytd, 2)
            if (annual is not None and real_ytd is not None)
            else None
        )

    return {
        "Linha": tmpl.get("Linha"),
        "Orçado YTD": _cell(orc_ytd, "orcado"),
        "Realizado YTD": _cell(real_ytd, "realizado"),
        "Variação": _cell(var, "realizado"),
        "Desvio %": desvio,
        "Orçado Anual": _cell(annual, "orcado"),
        "Falta p/ meta": _cell(falta, "realizado"),
        **meta,
    }


def _ratio(
    acc: dict[_AccKey, float], block: int, num_key: str | None, occurrence: int
) -> float | None:
    """Margem = numerator line ÷ recebimento, both from ``block``'s accumulation."""
    if num_key is None:
        return None
    num = acc.get((block, num_key, occurrence))
    den = acc.get((block, "recebimento", 0))
    if num is None or not den:
        return None
    return round(num / den, 4)
