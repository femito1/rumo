"""Generate tab_layouts.py: a generic grid for every workbook tab.

For full 1:1 fidelity we render all 15 tabs. Each tab becomes a 2D grid of
cells. Each cell is classified by how its value originates:

- ``"formula"``  – the workbook cell holds an Excel formula (=...).
- ``"label"``    – non-numeric text (headers, row labels).
- ``"number"``   – a numeric literal in the workbook. By default these are
  institutional/reference values (MANUAL in v0); the builder may *promote*
  specific cells to live ``"api"`` values for the target month.
- ``"empty"``    – blank.

Built at *build time* from the verified TSV dumps in work/analysis/. The TSVs
are the ground truth used to fix layout + which cells are formulas. Live values
are layered on at request time by the builder, never the workbook's own numbers
for the automated cells.

Run from repo root:
    .venv/bin/python mbc-automation/backend/scripts/gen_tab_layouts.py
"""
from __future__ import annotations

import pprint
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VALUES_DIR = REPO_ROOT / "work/analysis/fechamento_values"
FORMULAS_DIR = REPO_ROOT / "work/analysis/fechamento_formulas"
OUT = REPO_ROOT / "mbc-automation/backend/mbc_automation/tab_layouts.py"

# (tab_id, display name, values TSV stem). Order = nav order in the UI.
TABS = [
    ("meta", "Meta", "Meta__2"),
    ("base_resultado", "Base_Resultado Mensal_V2", "Base_Resultado_Mensal_V2"),
    ("areas_sintetico", "Areas Sintetico atualizado", "Areas_Sintetico_atualizado"),
    ("resumo_recebidas", "Resumo_Recebidas 2025_2026", "Resumo_Recebidas_2025_2026"),
    ("faturas_centro_custo", "FATURAS Analitico CENTRO CUSTO", "FATURAS_Analitico_CENTRO_CUSTO"),
    ("dre_2026", "DRE 2026", "DRE_2026"),
    ("orcamento_2026", "Orçamento 2026", "Orçamento_2026"),
    ("institucional", "Institucional", "Institucional"),
    ("institucional_ano", "Institucional ano", "Institucional_ano"),
    ("contencioso", "Contencioso", "Contencioso"),
    ("economico", "Econômico", "Econômico"),
    ("arbitragem", "Arbitragem", "Arbitragem"),
    ("rateio_mensal", "Rateio Mensal", "Rateio_Mensal"),
    ("fluxo_consolidado", "Fluxo consolidado", "Fluxo_consolidado"),
    ("amortizacao", "Amortização", "Amortização"),
]

# Which tabs carry live API data for the target month, and a short note.
API_TABS = {"meta", "base_resultado", "areas_sintetico", "resumo_recebidas", "faturas_centro_custo"}


def _is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


def read_grid(stem: str) -> list[list[str]]:
    path = VALUES_DIR / f"{stem}.tsv"
    rows = []
    with path.open() as f:
        for line in f:
            rows.append(line.rstrip("\n").split("\t"))
    return rows


def read_formulas(stem: str) -> list[list[str]]:
    path = FORMULAS_DIR / f"{stem}.tsv"
    if not path.exists():
        return []
    rows = []
    with path.open() as f:
        for line in f:
            rows.append(line.rstrip("\n").split("\t"))
    return rows


def trim(grid: list[list[str]]) -> list[list[str]]:
    """Drop fully-empty trailing rows and columns to keep the payload tight."""
    while grid and all(c.strip() == "" for c in grid[-1]):
        grid.pop()
    if not grid:
        return grid
    max_w = max((len(r) for r in grid), default=0)
    grid = [r + [""] * (max_w - len(r)) for r in grid]
    # drop trailing empty columns
    while max_w > 1 and all((len(r) <= max_w - 1 or r[max_w - 1].strip() == "") for r in grid):
        for r in grid:
            if len(r) >= max_w:
                r.pop()
        max_w -= 1
    return grid


def classify(value: str, formula: str) -> str:
    v = (value or "").strip()
    f = (formula or "").strip()
    if f.startswith("="):
        return "formula"
    if v == "":
        return "empty"
    if _is_number(v):
        return "number"
    return "label"


def build_tab(tab_id: str, name: str, stem: str) -> dict:
    values = trim(read_grid(stem))
    formulas = read_formulas(stem)
    grid = []
    for r, row in enumerate(values):
        out_row = []
        for c, val in enumerate(row):
            fcell = ""
            if r < len(formulas) and c < len(formulas[r]):
                fcell = formulas[r][c]
            kind = classify(val, fcell)
            # Keep the computed numeric value for both literals and formula cells
            # (the values TSV is the evaluated workbook), so the UI can show the
            # figure alongside the FÓRMULA badge.
            num = float(val) if (kind in ("number", "formula") and _is_number(val)) else None
            out_row.append({"t": kind, "v": val if kind == "label" else None, "n": num})
        grid.append(out_row)
    return {
        "id": tab_id,
        "name": name,
        "has_api": tab_id in API_TABS,
        "rows": len(grid),
        "cols": len(grid[0]) if grid else 0,
        "grid": grid,
    }


def main() -> None:
    tabs = [build_tab(tid, name, stem) for tid, name, stem in TABS]
    header = (
        '"""Generic grid layouts for all 15 workbook tabs (1:1 mirror).\n\n'
        "Auto-generated by scripts/gen_tab_layouts.py from the verified TSV dumps.\n"
        "Each cell: {'t': kind, 'v': label-text | None, 'n': number | None} where\n"
        "kind in {formula, number, label, empty}. The builder overlays live API\n"
        "values for the target month on the automated tabs.\n"
        '"""\n'
        "from __future__ import annotations\n\n"
        "TAB_ORDER = " + pprint.pformat([t[0] for t in TABS], width=120) + "\n\n"
        "TAB_LAYOUTS: dict = "
    )
    OUT.write_text(header + pprint.pformat({t["id"]: t for t in tabs}, sort_dicts=False, width=160) + "\n")
    total_cells = sum(t["rows"] * t["cols"] for t in tabs)
    print(f"wrote {OUT}: {len(tabs)} tabs, {total_cells} cells")
    for t in tabs:
        print(f"  {t['id']:22s} {t['rows']:>4}x{t['cols']:<3} api={t['has_api']}")


if __name__ == "__main__":
    main()
