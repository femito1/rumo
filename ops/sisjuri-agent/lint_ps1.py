#!/usr/bin/env python3
"""Guard the agent's PowerShell scripts against the encoding trap that breaks them.

Run: python ops/sisjuri-agent/lint_ps1.py        (CI-friendly: non-zero on failure)

WHY THIS EXISTS. MBC-LDESK01 runs Windows Server 2012 / PowerShell 3-4, whose
parser reads a UTF-8 file **without BOM** as cp1252. An em-dash (U+2014) is the
bytes ``E2 80 94``; in cp1252 that trailing ``94`` decodes to ``"`` — a smart
CLOSING DOUBLE QUOTE, which PowerShell happily accepts as a string terminator.

The failure is spectacularly misleading. On 2026-07-30 a single em-dash inside a
``throw "..."`` message produced:

    Unexpected token 'otherwise' in expression or statement.
    Missing closing '}' in statement block or type definition.

...pointing at a line 1 char 207 that looks fine, and cascading upward through
every enclosing block. Nothing about the message suggests an encoding problem.

An em-dash in a COMMENT is harmless (run-agent.ps1 carried one for weeks), so the
rule could in principle be "no non-ASCII inside string literals". We enforce plain
**pure ASCII** instead: distinguishing the two requires parsing PowerShell, the
scripts have no need for non-ASCII, and a comment gets copy-pasted into a string
sooner or later. Accented Portuguese belongs in the product's UI, not in ops glue.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def check(path: Path) -> list[str]:
    raw = path.read_bytes()
    problems: list[str] = []
    # Byte offset -> (line, col), so the report points at something actionable.
    line = 1
    col = 1
    for byte in raw:
        if byte > 127:
            problems.append(
                f"{path.name}:{line}:{col}: non-ASCII byte 0x{byte:02X} "
                f"(cp1252 would read it as {bytes([byte]).decode('cp1252', 'replace')!r})"
            )
        if byte == 0x0A:
            line += 1
            col = 1
        else:
            col += 1
    return problems


def main() -> int:
    scripts = sorted(HERE.glob("*.ps1"))
    if not scripts:
        print("no .ps1 files found next to lint_ps1.py", file=sys.stderr)
        return 1
    failures: list[str] = []
    for s in scripts:
        found = check(s)
        status = "ok" if not found else f"{len(found)} non-ASCII byte(s)"
        print(f"  {s.name:24s} {status}")
        failures.extend(found)
    if failures:
        print(
            "\nFAIL: PowerShell 3/4 on MBC-LDESK01 reads these files as cp1252, where "
            "an em-dash's trailing byte becomes a closing quote and breaks the parse.\n"
            "Replace with ASCII ('--' for an em-dash, unaccented letters).\n",
            file=sys.stderr,
        )
        for f in failures[:40]:
            print("  " + f, file=sys.stderr)
        return 1
    print("\nAll agent PowerShell scripts are pure ASCII.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
