# backend/app/closing/dre.py
"""Assemble the workbook's DRE views from clean sources (Orcado x Realizado).

The MBC workbook computes a consolidated (Institucional) P&L plus three
cost-center P&Ls (Contencioso, Economico, Arbitragem). We recompute those blocks
here from canonical inputs rather than copying workbook cells verbatim (the
workbook carries #REF! errors and blends hardcoded constants with references).

Vocabulary
----------
A DRE is a list of ``DreLine``. Each line has a stable ``key`` (used to align
Realizado, Orcado and the UI), a PT-BR ``label``, an ``indent`` for the tree,
and flags (``is_total``, ``is_section``). The ``kind`` marks how the value is
formed: a fetched amount, a subtotal, or a margin (%).

This module is a pure transformation: given realizado inputs and an optional
budget, it returns section payloads keyed by ``SectionKey``. No IO here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# --- canonical line keys -----------------------------------------------------
# These strings are the contract shared by SisjuriDbSource, BudgetSource and the
# frontend. Do not rename without a migration of stored budgets.

FATURAMENTO = "faturamento"
RECEITA = "receita"
CUSTOS_DIRETOS = "custos_diretos"
DESPESAS_INDIRETAS = "despesas_indiretas"
RESULTADO_BRUTO = "resultado_bruto"
MARGEM_BRUTA = "margem_bruta"
IMPOSTOS = "impostos"
AMORTIZACAO = "amortizacao"
RESULTADO_LIQUIDO = "resultado_liquido"
MARGEM_LIQUIDA = "margem_liquida"
RESERVA_BONUS = "reserva_bonus"

#: Reserva de bonus = fixed rate x margem liquida (finance-confirmed, all months).
BONUS_RESERVE_RATE = 0.10

#: Monthly amortization installment (Institucional), workbook 'Amortizacao' tab.
AMORTIZACAO_MENSAL = 8117.31

#: The three cost centers, workbook labels.
AREAS = ("Contencioso", "Economico", "Arbitragem")


@dataclass
class DreLine:
    key: str
    label: str
    indent: int = 0
    is_total: bool = False
    is_section: bool = False
    kind: str = "amount"  # amount | subtotal | margin
    children: list["DreLine"] = field(default_factory=list)


def _pct(numer: float, denom: float) -> float | None:
    if not denom:
        return None
    return round(numer / denom, 4)


def bonus_reserve(net_margin_value: float) -> float:
    """Reserva de bonus = fixed rate x margem liquida (finance-confirmed)."""
    return round(net_margin_value * BONUS_RESERVE_RATE, 2)


# --- expense grouping --------------------------------------------------------
# SISJURI chart-of-accounts families -> workbook expense buckets.
#   020.* -> institucional/indirect (D)
#   030.* -> custos com pessoal tecnico (C) -> Custos Diretos
#   040.* -> investimentos (I) -> indirect (investimento)
def _sum_despesas_indiretas(despesas: list[dict]) -> float:
    """Sum institutional indirect expenses (families 020.* and 040.*)."""
    total = 0.0
    for row in despesas:
        conta = str(row.get("id_conta", ""))
        if conta.startswith("020.") or conta.startswith("040."):
            total += float(row.get("total", 0.0))
    return round(total, 2)


def _sum_custos_diretos(despesas: list[dict], custo_area: list[dict]) -> float:
    """Direct team cost. Prefer the per-area breakdown when present."""
    if custo_area:
        return round(sum(float(a.get("total", 0.0)) for a in custo_area), 2)
    total = 0.0
    for row in despesas:
        if str(row.get("id_conta", "")).startswith("030."):
            total += float(row.get("total", 0.0))
    return round(total, 2)


@dataclass
class RealizadoInputs:
    """Clean realizado inputs for one competence month."""

    faturamento: float
    receita: float
    custos_diretos: float
    despesas_indiretas: float
    impostos: float
    amortizacao: float = AMORTIZACAO_MENSAL

    @classmethod
    def from_snapshot(cls, snap: dict[str, Any]) -> "RealizadoInputs":
        revenue = snap.get("revenue", {}) or {}
        despesas = snap.get("despesas_conta", []) or []
        custo_area = snap.get("custo_area", []) or []
        faturamento = float(revenue.get("faturamento_bruto", 0.0) or 0.0)
        receita = float(revenue.get("recebimento_bruto", 0.0) or 0.0)
        indiretas = _sum_despesas_indiretas(despesas)
        diretos = _sum_custos_diretos(despesas, custo_area)
        # Impostos: taxes captured under any 'Impostos' account family; the
        # snapshot lists them among despesas. Fall back to 0 when absent.
        impostos = 0.0
        for row in despesas:
            pai = str(row.get("nome_conta_pai", "")).lower()
            if "imposto" in pai:
                impostos += float(row.get("total", 0.0))
        return cls(
            faturamento=faturamento,
            receita=receita,
            custos_diretos=diretos,
            despesas_indiretas=indiretas,
            impostos=round(impostos, 2),
        )


def _dre_block_rows(
    realizado: RealizadoInputs, orcado: dict[str, float] | None
) -> list[dict[str, Any]]:
    """Build the canonical DRE line rows with orcado/realizado/variacao/desvio.

    ``orcado`` maps line-key -> budgeted (monthly) amount. When ``None`` the
    orcado column is left null (renders as 'ainda nao temos').
    """
    orc = orcado or {}

    resultado_bruto = round(
        realizado.faturamento - realizado.custos_diretos - realizado.despesas_indiretas,
        2,
    )
    resultado_liquido = round(
        resultado_bruto - realizado.impostos - realizado.amortizacao, 2
    )
    reserva = bonus_reserve(resultado_liquido)

    realizado_by_key: dict[str, float | None] = {
        FATURAMENTO: realizado.faturamento,
        RECEITA: realizado.receita,
        CUSTOS_DIRETOS: realizado.custos_diretos,
        DESPESAS_INDIRETAS: realizado.despesas_indiretas,
        RESULTADO_BRUTO: resultado_bruto,
        MARGEM_BRUTA: _pct(resultado_bruto, realizado.faturamento),
        IMPOSTOS: realizado.impostos,
        AMORTIZACAO: realizado.amortizacao,
        RESULTADO_LIQUIDO: resultado_liquido,
        MARGEM_LIQUIDA: _pct(resultado_liquido, realizado.faturamento),
        RESERVA_BONUS: reserva,
    }

    spec = [
        (FATURAMENTO, "Faturamento", 0, False, "amount"),
        (RECEITA, "Receita (recebimento)", 0, False, "amount"),
        (CUSTOS_DIRETOS, "Custos Diretos", 0, False, "amount"),
        (DESPESAS_INDIRETAS, "Despesas Indiretas", 0, False, "amount"),
        (RESULTADO_BRUTO, "Resultado Bruto", 0, True, "subtotal"),
        (MARGEM_BRUTA, "Margem Bruta", 1, False, "margin"),
        (IMPOSTOS, "Impostos", 0, False, "amount"),
        (AMORTIZACAO, "Amortizacao", 0, False, "amount"),
        (RESULTADO_LIQUIDO, "Resultado Liquido", 0, True, "subtotal"),
        (MARGEM_LIQUIDA, "Margem Liquida", 1, False, "margin"),
        (RESERVA_BONUS, "Reserva de Bonus", 0, False, "amount"),
    ]

    rows: list[dict[str, Any]] = []
    for key, label, indent, is_total, kind in spec:
        realizado_val = realizado_by_key.get(key)
        orcado_val = orc.get(key)
        if kind == "margin":
            variacao = None
            desvio = None
        else:
            if orcado_val is not None and realizado_val is not None:
                variacao = round(realizado_val - orcado_val, 2)
                desvio = _pct(realizado_val, orcado_val)
            else:
                variacao = None
                desvio = None
        rows.append(
            {
                "label": label,
                "orcado": orcado_val,
                "realizado": realizado_val,
                "variacao": variacao,
                "desvio": desvio,
                "key": key,
                "indent": indent,
                "is_total": is_total,
                "kind": kind,
            }
        )
    return rows


_DRE_COLUMNS = ["Linha", "Orcado", "Realizado", "Variacao", "Desvio %"]


def _rich_dre_tab(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap DRE rows as a rich tab the frontend renders generically.

    Each row exposes keys in column order (Linha, Orcado, Realizado, Variacao,
    Desvio) followed by ignored metadata (key/indent/is_total/kind).
    """
    render_rows = []
    for r in rows:
        render_rows.append(
            {
                "Linha": r["label"],
                "Orcado": {"value": r["orcado"], "source": "orcado"},
                "Realizado": {"value": r["realizado"], "source": "realizado"},
                "Variacao": {"value": r["variacao"], "source": "formula"},
                "Desvio %": r["desvio"],
                "key": r["key"],
                "indent": r["indent"],
                "is_total": r["is_total"],
                "kind": r["kind"],
            }
        )
    return {
        "kind": "rich",
        "name": name,
        "columns": _DRE_COLUMNS,
        "rows": render_rows,
    }


def area_budget(orcado: dict[str, dict[str, float]] | None, area: str) -> dict[str, float] | None:
    if not orcado:
        return None
    return orcado.get(area)


def assemble_dre_sections(
    *,
    snapshot: dict[str, Any] | None,
    budget: dict[str, Any] | None,
    period_label: str,
) -> dict[str, dict[str, Any]]:
    """Return section payloads keyed by SectionKey.value.

    ``budget`` shape (all optional):
      {
        "institucional": {line_key: monthly_amount, ...},
        "Contencioso": {...}, "Economico": {...}, "Arbitragem": {...},
      }
    ``snapshot`` is the SISJURI agent snapshot (or None when not imported yet).
    """
    sections: dict[str, dict[str, Any]] = {}
    inst_budget = (budget or {}).get("institucional")

    if snapshot is not None:
        realizado = RealizadoInputs.from_snapshot(snapshot)
    else:
        realizado = RealizadoInputs(
            faturamento=0.0,
            receita=0.0,
            custos_diretos=0.0,
            despesas_indiretas=0.0,
            impostos=0.0,
        )

    inst_rows = _dre_block_rows(realizado, inst_budget)
    sections["institucional"] = {
        **_rich_dre_tab("Resultado Institucional", inst_rows),
        "snapshot_missing": snapshot is None,
    }

    # Per-area blocks: realizado receita comes from custo_area/rateio when
    # available; a full per-area P&L needs the receita split (rateio) which we
    # surface as receita only for now, expenses left to institucional.
    custo_area = (snapshot or {}).get("custo_area", []) or []
    area_cost = {a.get("area", ""): float(a.get("total", 0.0)) for a in custo_area}
    for area in AREAS:
        area_real = RealizadoInputs(
            faturamento=0.0,
            receita=0.0,
            custos_diretos=_match_area_cost(area_cost, area),
            despesas_indiretas=0.0,
            impostos=0.0,
        )
        rows = _dre_block_rows(area_real, area_budget(budget, area))
        sections[_AREA_SECTION[area]] = {
            **_rich_dre_tab(f"Resultado {area}", rows),
            "snapshot_missing": snapshot is None,
        }

    # areas_sintetico: consolidated + the three area blocks stacked.
    sintetico_rows: list[dict[str, Any]] = []
    sintetico_rows.append(_section_header_row("RESULTADO INSTITUCIONAL"))
    sintetico_rows.extend(_rich_dre_tab("", inst_rows)["rows"])
    for area in AREAS:
        sintetico_rows.append(_section_header_row(f"RESULTADO {area.upper()}"))
        rows = _dre_block_rows(
            RealizadoInputs(
                faturamento=0.0,
                receita=0.0,
                custos_diretos=_match_area_cost(area_cost, area),
                despesas_indiretas=0.0,
                impostos=0.0,
            ),
            area_budget(budget, area),
        )
        sintetico_rows.extend(_rich_dre_tab("", rows)["rows"])
    sections["areas_sintetico"] = {
        "kind": "rich",
        "name": "Areas Sintetico atualizado",
        "columns": _DRE_COLUMNS,
        "rows": sintetico_rows,
        "snapshot_missing": snapshot is None,
    }

    # Secondary workbook views. NB: we intentionally do NOT emit `meta` here so
    # we never clobber the KPI-bearing META section from LegalDesk during merge;
    # the meta display tab stays LegalDesk's. `assemble_meta_tab` is available
    # for standalone/full-mode use.
    sections["dre_2026"] = assemble_dre_2026_tab(inst_budget)
    sections["amortizacao"] = assemble_amortizacao_tab()

    return sections


_AREA_SECTION = {
    "Contencioso": "contencioso",
    "Economico": "economico",
    "Arbitragem": "arbitragem",
}


def _match_area_cost(area_cost: dict[str, float], area: str) -> float:
    """The snapshot area labels differ from the workbook (e.g. 'Equipe
    Contencioso', 'Equipe Direito Economico'); match loosely by keyword."""
    for name, total in area_cost.items():
        low = name.lower()
        if area == "Economico" and ("econ" in low):
            return round(total, 2)
        if area == "Contencioso" and ("conten" in low):
            return round(total, 2)
        if area == "Arbitragem" and ("arbitr" in low):
            return round(total, 2)
    return 0.0


def _section_header_row(title: str) -> dict[str, Any]:
    return {
        "Linha": title,
        "Orcado": None,
        "Realizado": None,
        "Variacao": None,
        "Desvio %": None,
        "indent": 0,
        "is_total": True,
        "kind": "header",
    }


# --- secondary workbook views ------------------------------------------------
_MESES_PT = [
    "Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]


def assemble_meta_tab(
    *, realizado: RealizadoInputs, orcado: dict[str, float] | None, month_name: str
) -> dict[str, Any]:
    """Meta (2): monthly Recebimento/Faturamento vs Meta."""
    meta_val = (orcado or {}).get(FATURAMENTO)
    return {
        "kind": "rich",
        "name": "Meta (2)",
        "columns": ["Mes", "Recebimento", "Faturamento", "Meta"],
        "rows": [
            {
                "Mes": month_name,
                "Recebimento": {"value": realizado.receita, "source": "realizado"},
                "Faturamento": {"value": realizado.faturamento, "source": "realizado"},
                "Meta": {"value": meta_val, "source": "orcado"},
            }
        ],
    }


def assemble_amortizacao_tab() -> dict[str, Any]:
    """Amortizacao: the fixed 60-month institutional installment schedule."""
    rows = [
        {
            "Mes": f"Parcela {i}/60",
            "Valor Institucional": {"value": AMORTIZACAO_MENSAL, "source": "manual"},
        }
        for i in range(1, 13)
    ]
    return {
        "kind": "rich",
        "name": "Amortizacao",
        "columns": ["Mes", "Valor Institucional"],
        "rows": rows,
    }


def assemble_dre_2026_tab(orcado: dict[str, float] | None) -> dict[str, Any]:
    """DRE 2026: full-year budgeted DRE (annual = monthly x 12)."""
    orc = orcado or {}
    spec = [
        (FATURAMENTO, "Faturamento", False),
        (CUSTOS_DIRETOS, "Custos Diretos", False),
        (DESPESAS_INDIRETAS, "Despesas Indiretas", False),
        (RESULTADO_BRUTO, "Resultado Bruto", True),
        (IMPOSTOS, "Impostos", False),
        (AMORTIZACAO, "Amortizacao", False),
        (RESULTADO_LIQUIDO, "Resultado Liquido", True),
        (RESERVA_BONUS, "Reserva de Bonus", False),
    ]
    rows = []
    for key, label, is_total in spec:
        monthly = orc.get(key)
        annual = round(monthly * 12, 2) if monthly is not None else None
        rows.append(
            {
                "Linha": label,
                "Anual (Orcado)": {"value": annual, "source": "orcado"},
                "key": key,
                "is_total": is_total,
            }
        )
    return {
        "kind": "rich",
        "name": "DRE 2026",
        "columns": ["Linha", "Anual (Orcado)"],
        "rows": rows,
    }
