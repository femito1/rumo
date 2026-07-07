# backend/app/closing/ledger_import.py
"""Parse the hand-built per-lawyer ledger (``Base_Resultado Mensal_V2``) into
per-area monthly figures, and derive the Despesa Institucional rateio.

The ledger is the source of truth the finance team hand-maintains: per-lawyer
Custo equipe rows (with manual splits like ``=12500-C8``), Participação/Repasse
(Comissão), and the institutional expense blocks. Its **structure** is stable
across months -- only the per-lawyer rows churn as staff change -- so we locate
the *section anchor* rows by label and read their **cached (computed) values**.
Reading cached values (never the formulas) sidesteps the manual per-lawyer
adjustments entirely: Excel has already resolved them into the subtotal.

Validated to the centavo against "Fechamento MBC 05.2026.xlsx" and the client
dashboard "MBC Resultado Jan a Mai 2026.pdf" (2026-07): the YTD Jan..Mai sums
reproduce the dashboard's per-area Custo equipe, Despesas Equipe and Despesa
Institucional exactly.

The rateio rule (workbook ``Rateio Mensal`` / ``Base_Resultado`` rows 207-214):

    despesa_para_ratear = DespesaInstitucionalTotal - Sum(DespesasArea)
    ratio[area]         = custo_equipe[area] / Sum(custo_equipe)
    despesa_inst[area]  = despesa_para_ratear * ratio[area]

Despesas Área (the area-suffixed institutional line items) are allocated
directly to the area as **Despesas Equipe**, not rateado -- matching the
workbook's area tabs (row 41 = Despesas Equipe, row 42 = rateio only).

This parser is pure (takes a label->value reader) so it is unit-testable
without a spreadsheet; the thin ``scripts.import_ledger`` does the openpyxl read.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from app.closing.workbook_layouts import AREAS

#: Ledger row labels that anchor each figure, keyed by area where per-area.
#: These match ``Base_Resultado Mensal_V2`` column A exactly (both the
#: 02.2026 and 05.2026 workbook editions carry these labels verbatim).
AREA_ROW_LABELS: dict[str, object] = {
    # ``Custo equipe - <area>`` subtotal rows (C5 / C30 / C60).
    "custo_equipe": {
        "Contencioso": "Custo equipe - Contencioso",
        "Econômico": "Custo equipe - Econômico",
        "Arbitragem": "Custo equipe - Arbitragem e Compliance",
    },
    # Comissão = Participação + Repasse per area (rows 28/29, 58/59, 80/81).
    # First label is the Participação row, second the Repasse row.
    "comissao": {
        "Contencioso": (
            "Participação/Comissão - Contencioso",
            "Repasse - Contencioso",
        ),
        "Econômico": (
            "Participação/comissão - Economico",
            "Repasse - Economico",
        ),
        "Arbitragem": (
            "Participação/comissão - Arbitragem",
            "Repasse - Arbitragem",
        ),
    },
    # Despesas Área: the per-area subtotal rows just under "Despesas Área:".
    "despesas_area": {
        "Contencioso": "Contencioso",
        "Econômico": "Econômico",
        "Arbitragem": "Arbitragem e Compliance",
    },
    # Total institutional despesa (row "Despesas Institucional").
    "despesa_institucional_total": "Despesas Institucional",
}


@dataclass
class LedgerMonth:
    """One competence month parsed from the ledger (workbook vocabulary)."""

    month: int
    custo_equipe: dict[str, float] = field(default_factory=dict)
    comissao: dict[str, float] = field(default_factory=dict)
    despesas_equipe: dict[str, float] = field(default_factory=dict)
    despesa_institucional_total: float = 0.0

    def total_custo_equipe(self) -> float:
        return round(sum(self.custo_equipe.values()), 2)

    def total_despesas_area(self) -> float:
        return round(sum(self.despesas_equipe.values()), 2)


class LabelReader:  # pragma: no cover - typing protocol only
    """Callable protocol: ``(label: str) -> float | int | None`` for one month.

    Returns the cached value of the ledger row whose column-A label equals
    ``label`` for the reader's competence month, or ``None`` when absent/blank.
    """

    def __call__(self, label: str) -> float | int | None: ...


def _num(value: float | int | None) -> float:
    return round(float(value), 2) if isinstance(value, (int, float)) else 0.0


def parse_ledger_month(read: LabelReader, *, month: int) -> LedgerMonth:
    """Build a :class:`LedgerMonth` from a per-month label reader."""
    ce_labels: dict[str, str] = AREA_ROW_LABELS["custo_equipe"]  # type: ignore[assignment]
    com_labels: dict[str, tuple[str, str]] = AREA_ROW_LABELS["comissao"]  # type: ignore[assignment]
    da_labels: dict[str, str] = AREA_ROW_LABELS["despesas_area"]  # type: ignore[assignment]
    inst_label: str = AREA_ROW_LABELS["despesa_institucional_total"]  # type: ignore[assignment]

    custo: dict[str, float] = {}
    comissao: dict[str, float] = {}
    desp_area: dict[str, float] = {}
    for area in AREAS:
        custo[area] = _num(read(ce_labels[area]))
        part, repasse = com_labels[area]
        comissao[area] = round(_num(read(part)) + _num(read(repasse)), 2)
        desp_area[area] = _num(read(da_labels[area]))

    return LedgerMonth(
        month=month,
        custo_equipe=custo,
        comissao=comissao,
        despesas_equipe=desp_area,
        despesa_institucional_total=_num(read(inst_label)),
    )


#: First month column in ``Base_Resultado Mensal_V2`` is C (index 3); the twelve
#: competence months run C..N (Janeiro..Dezembro).
FIRST_MONTH_COL = 3
N_MONTHS = 12

#: Column A label -> its first occurrence 1-based row, built from the sheet. The
#: "Despesas Área" per-area subtotal rows share generic labels ("Contencioso"
#: etc.) with other blocks, so the caller resolves those by position (the rows
#: directly under the "Despesas Área:" header) rather than by bare label.


def month_reader_from_matrix(
    label_rows: dict[str, int],
    value_at: "MatrixReader",
    *,
    month_index: int,
    despesas_area_rows: dict[str, int],
) -> Callable[[str], float | int | None]:
    """Build a per-month :class:`LabelReader` from a label->row map.

    ``value_at(row, col)`` returns the cached cell value; ``month_index`` is
    0-based (Jan=0). ``despesas_area_rows`` maps area -> the concrete row of the
    per-area "Despesas Área" subtotal (resolved positionally by the caller).
    """
    col = FIRST_MONTH_COL + month_index
    da_labels: dict[str, str] = AREA_ROW_LABELS["despesas_area"]  # type: ignore[assignment]
    inst_label: str = AREA_ROW_LABELS["despesa_institucional_total"]  # type: ignore[assignment]
    da_row_by_label = {da_labels[a]: despesas_area_rows[a] for a in da_labels}

    def read(label: str) -> float | int | None:
        # "Despesas Área" per-area rows are resolved by their concrete row.
        if label in da_row_by_label:
            v = value_at(da_row_by_label[label], col)
        else:
            row = label_rows.get(label)
            v = value_at(row, col) if row is not None else None
        return v if isinstance(v, (int, float)) else None

    _ = inst_label  # documents intent; resolved through label_rows like the rest
    return read


class MatrixReader:  # pragma: no cover - typing protocol only
    """Callable protocol: ``(row: int, col: int) -> float | int | str | None``."""

    def __call__(self, row: int, col: int) -> float | int | str | None: ...


def despesa_institucional_rateio(m: LedgerMonth) -> dict[str, float]:
    """Per-area Despesa Institucional via the workbook's rateio rule.

    ``despesa_para_ratear = despesa_institucional_total - Sum(despesas_area)``
    is apportioned by each area's share of total Custo equipe.
    """
    total_ce = m.total_custo_equipe()
    ratear = round(m.despesa_institucional_total - m.total_despesas_area(), 2)
    out: dict[str, float] = {}
    for area in AREAS:
        ratio = (m.custo_equipe.get(area, 0.0) / total_ce) if total_ce else 0.0
        out[area] = round(ratear * ratio, 2)
    return out
