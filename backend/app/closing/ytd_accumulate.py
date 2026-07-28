# backend/app/closing/ytd_accumulate.py
"""Accumulate per-month DRE sections into a year-to-date (acumulado) view.

The 2026-07 client checkpoint asked for a mensal↔acumulado toggle. Rather than a
second assembly path (fragile: the frontend binds columns positionally, and the
per-month assembler already encodes every rule — per-área reserva, imposto, the
expense breakdown), we ACCUMULATE the already-assembled monthly sections:

- numeric ``amount``/``subtotal``/``section_total`` rows: sum Realizado and Orçado
  across the closed months Jan→competence, per (section, line);
- ``margin`` rows: recomputed from the accumulated base (a ratio can't be summed);
- ``header``/non-numeric rows: passed through unchanged (first month's version).

Columns become ``[Linha, Orçado YTD, Realizado YTD, Variação, Orçado YTG]`` where
Variação = Realizado YTD − Orçado YTD and Orçado YTG (year-to-go) = annual budget
− Orçado YTD. The row shape keeps display-value keys BEFORE metadata keys
(``key``/``indent``/``is_total``/``kind``) so the frontend's positional
``Object.keys(row).slice(0, columns.length)`` binding stays correct.
"""
from __future__ import annotations

from typing import Any

_YTD_COLUMNS = ["Linha", "Orçado YTD", "Realizado YTD", "Variação", "Orçado YTG"]

#: Line keys whose YTD is a ratio recomputed from the accumulated base (numerator
#: line ÷ recebimento), never a sum. Mirrors the monthly ``kind == "margin"`` rows.
_MARGIN_NUMERATOR = {
    "margem_bruta": "resultado_bruto",
    "margem_liquida": "resultado_liquido",
}


def _cell_value(row: dict[str, Any], col: str) -> float | None:
    v = row.get(col)
    if isinstance(v, dict):
        v = v.get("value")
    return v if isinstance(v, (int, float)) else None


def accumulate_ytd(
    months: dict[int, dict[str, dict[str, Any]]],
    *,
    annual_budget: dict[str, dict[str, float]] | None,
    up_to_month: int,
) -> dict[str, dict[str, Any]]:
    """Return accumulated sections (Jan→``up_to_month``) with YTD/YTG columns.

    ``months`` is ``{month_index: assembled_sections}`` (as ``assemble_dre_sections``
    returns). Only months ``<= up_to_month`` that are present contribute. Section /
    row structure is taken from the latest present month so labels/order are current.
    """
    annual_budget = annual_budget or {}
    present = sorted(m for m in months if m <= up_to_month)
    if not present:
        return {}
    template_month = present[-1]

    out: dict[str, dict[str, Any]] = {}
    for section_key, section in months[template_month].items():
        if not isinstance(section, dict) or section.get("kind") != "rich":
            continue
        rows_out: list[dict[str, Any]] = []
        # Accumulate Realizado/Orçado per line across the present months.
        acc_real: dict[str, float] = {}
        acc_orc: dict[str, float] = {}
        for m in present:
            sec_m = months[m].get(section_key)
            if not isinstance(sec_m, dict):
                continue
            for row in sec_m.get("rows", []):
                key = row.get("key")
                if key is None:
                    continue
                rv = _cell_value(row, "Realizado")
                if rv is not None:
                    acc_real[key] = round(acc_real.get(key, 0.0) + rv, 2)
                ov = _cell_value(row, "Orçado")
                if ov is not None:
                    acc_orc[key] = round(acc_orc.get(key, 0.0) + ov, 2)

        ann_sec = annual_budget.get(section_key, {})
        acc_recebimento = acc_real.get("recebimento")

        for tmpl in section.get("rows", []):
            key = tmpl.get("key")
            kind = tmpl.get("kind")
            # Pass through structural (non-numeric) rows unchanged.
            if key is None or kind in ("header",):
                rows_out.append(dict(tmpl))
                continue

            if kind == "margin":
                num_key = _MARGIN_NUMERATOR.get(str(key))
                num = acc_real.get(num_key) if num_key else None
                real_ytd = (
                    round(num / acc_recebimento, 4)
                    if (num is not None and acc_recebimento)
                    else None
                )
                orc_ytd = None
                var = None
                ytg = None
            else:
                real_ytd = acc_real.get(key)
                orc_ytd = acc_orc.get(key)
                var = (
                    round(real_ytd - orc_ytd, 2)
                    if (real_ytd is not None and orc_ytd is not None)
                    else None
                )
                annual = ann_sec.get(str(key))
                ytg = (
                    round(annual - orc_ytd, 2)
                    if (annual is not None and orc_ytd is not None)
                    else None
                )

            rows_out.append({
                "Linha": tmpl.get("Linha"),
                "Orçado YTD": {"value": orc_ytd, "source": "orcado"},
                "Realizado YTD": {"value": real_ytd, "source": "realizado"},
                "Variação": {"value": var, "source": "realizado"},
                "Orçado YTG": {"value": ytg, "source": "orcado"},
                "key": key,
                "indent": tmpl.get("indent", 0),
                "is_total": tmpl.get("is_total", False),
                "kind": kind,
            })

        out[section_key] = {
            "kind": "rich",
            "name": section.get("name"),
            "columns": list(_YTD_COLUMNS),
            "rows": rows_out,
            "snapshot_missing": section.get("snapshot_missing", False),
        }
    return out
