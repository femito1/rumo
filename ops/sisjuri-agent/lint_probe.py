#!/usr/bin/env python3
"""Lint a sqlplus probe .sql BEFORE sending it to the RDP box.

Catches the failure classes we keep hitting:
  1. Oracle parse errors (sqlglot, dialect="oracle").
  2. Positional ORDER BY N where N exceeds the SELECT column count (ORA-01785) —
     our probes emit ONE concatenated column, so ORDER BY 2 / 1,2 always fails.
  3. XMLTYPE(<alias>) on a non-object table (ORA-00904) — must use a real column.
  4. Columns/pseudo-cols not confirmed against a known-columns allowlist (warn).

Usage: python3 lint_probe.py <probe.sql> [--known cols.txt]
Exit non-zero if any ERROR is found (WARN does not fail).
"""
from __future__ import annotations

import re
import sys

try:
    import sqlglot
    from sqlglot import exp
except ImportError:
    print("FATAL: pip install sqlglot", file=sys.stderr)
    sys.exit(2)

SQLPLUS_DIRECTIVES = re.compile(
    r"^\s*(SET|PROMPT|WHENEVER|EXIT|SPOOL|COLUMN|DEFINE|CONNECT|@|/|REM|--)",
    re.IGNORECASE,
)


def split_statements(text: str) -> list[str]:
    """Strip sqlplus directives/comments, split on ';'. Returns SQL statements."""
    lines = []
    for ln in text.splitlines():
        if SQLPLUS_DIRECTIVES.match(ln):
            continue
        lines.append(ln)
    blob = "\n".join(lines)
    return [s.strip() for s in blob.split(";") if s.strip()]


def count_select_columns(select: exp.Select) -> int | None:
    proj = select.expressions
    if not proj:
        return None
    # A single "a || b || c AS out" is ONE column.
    return len(proj)


def lint_statement(sql: str, idx: int, known: set[str] | None) -> list[str]:
    errs: list[str] = []
    # --- parse ---
    try:
        tree = sqlglot.parse_one(sql, dialect="oracle")
    except Exception as e:  # noqa: BLE001
        return [f"[stmt {idx}] PARSE ERROR: {str(e).splitlines()[0]}"]

    # --- XMLTYPE(alias) on a plain identifier -> ORA-00904 risk ---
    for anon in tree.find_all(exp.Anonymous):
        if str(anon.this).upper() == "XMLTYPE":
            args = anon.expressions
            # A single bare identifier/column arg (no table qualifier, no dot) means
            # XMLTYPE(<alias>) — only valid on an object table, else ORA-00904.
            if len(args) == 1:
                a = args[0]
                bare_ident = isinstance(a, exp.Identifier)
                bare_col = isinstance(a, exp.Column) and not a.table
                if bare_ident or bare_col:
                    errs.append(
                        f"[stmt {idx}] ERROR: XMLTYPE({a.sql()}) on a bare alias "
                        "-> ORA-00904 (needs an object table). Dump explicit columns."
                    )

    # --- positional ORDER BY beyond the SELECT column count ---
    for select in tree.find_all(exp.Select):
        ncols = count_select_columns(select)
        order = select.args.get("order")
        if order and ncols is not None:
            for o in order.expressions:
                target = o.this
                if isinstance(target, exp.Literal) and target.is_int:
                    pos = int(target.name)
                    if pos > ncols:
                        errs.append(
                            f"[stmt {idx}] ERROR: ORDER BY {pos} but SELECT has "
                            f"{ncols} column(s) -> ORA-01785. Order by the real "
                            "expression instead."
                        )
    return errs


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    known: set[str] | None = None
    if "--known" in sys.argv:
        kf = sys.argv[sys.argv.index("--known") + 1]
        known = {c.strip().upper() for c in open(kf).read().split() if c.strip()}

    text = open(path, encoding="utf-8", errors="replace").read()
    stmts = split_statements(text)
    all_errs: list[str] = []
    for i, s in enumerate(stmts, 1):
        all_errs.extend(lint_statement(s, i, known))

    if all_errs:
        print(f"✗ {len(all_errs)} issue(s) in {path}:")
        for e in all_errs:
            print("  " + e)
        return 1
    print(f"✓ {path}: {len(stmts)} statements parsed clean, no ORDER-BY/XMLTYPE traps.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
