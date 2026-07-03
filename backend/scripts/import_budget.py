# backend/scripts/import_budget.py
"""Import the granular monthly budget (Orçado) from a closing workbook's
``DRE 2026`` sheet into the ``budgets`` table.

Idempotent: upserts on (client_id, ano, area, line_key), so re-running refreshes
the imported lines without clobbering any budget rows entered manually via the
API (those live under different area/line_key combinations, or are re-imported
verbatim). The manual budget-entry path stays fully functional.

Usage:
    python -m scripts.import_budget --workbook "reference/workbook/Copy of Fechamento MBC 02.2026.xlsx" \
        --client mbc --ano 2026 [--dry-run]
"""
from __future__ import annotations

import argparse

from app.budget.workbook_import import parse_dre_budget


def _load_cell_reader(workbook_path: str, sheet: str = "DRE 2026"):
    import openpyxl

    wb = openpyxl.load_workbook(workbook_path, data_only=True, read_only=True)
    ws = wb[sheet]

    def cell(row: int, col: int):
        return ws.cell(row=row, column=col).value

    return cell


def main() -> None:
    ap = argparse.ArgumentParser(description="Import DRE 2026 budget into budgets table.")
    ap.add_argument("--workbook", required=True, help="Path to the closing .xlsx")
    ap.add_argument("--client", default="mbc", help="client_id (default: mbc)")
    ap.add_argument("--ano", type=int, default=2026, help="budget year (default: 2026)")
    ap.add_argument("--sheet", default="DRE 2026", help="sheet name (default: 'DRE 2026')")
    ap.add_argument("--dry-run", action="store_true", help="print, do not persist")
    args = ap.parse_args()

    cell = _load_cell_reader(args.workbook, args.sheet)
    entries = parse_dre_budget(cell, client_id=args.client, ano=args.ano)

    print(f"Parsed {len(entries)} budget line(s) from '{args.sheet}':")
    for e in entries:
        m = e.monthly_amounts or ()
        preview = ", ".join(f"{x:,.2f}" for x in m[:3])
        print(f"  {e.area:14} {e.line_key:16} annual={e.effective_annual():>14,.2f}  jan..mar=[{preview}]")

    if args.dry_run:
        print("\n[dry-run] nothing persisted.")
        return

    from app.api.providers import get_budget_repo

    repo = get_budget_repo()
    # Merge with any existing entries so a manual line under a different
    # (area, line_key) is preserved; imported keys overwrite themselves.
    existing = {(x.area, x.line_key): x for x in repo.get_budget(args.client, args.ano)}
    for e in entries:
        existing[(e.area, e.line_key)] = e
    repo.set_budget(args.client, args.ano, list(existing.values()))
    print(f"\nPersisted {len(entries)} imported line(s) (merged with {len(existing) - len(entries)} kept).")


if __name__ == "__main__":
    main()
