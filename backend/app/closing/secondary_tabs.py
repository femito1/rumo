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
]
