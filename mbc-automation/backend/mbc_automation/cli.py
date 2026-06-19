"""Build the dashboard data file for a given competence month.

Usage:
    python -m mbc_automation.cli --month 2026-05 --out ../data/data.json
    python -m mbc_automation.cli --month 2026-05 --check   # assert sanity totals

The Basic-auth credentials stay server-side (see config.py). The frontend only
ever consumes the generated data.json — the API password is never shipped to
the browser.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .api_client import LegalDeskClient
from .builder import build_payload
from .period import Period

# Verified expectations from docs/AUTOMATION_BUILD_GUIDE.md §5.4.
SANITY_CHECKS = {
    "2026-05": {"receita": 415927.84, "faturamento": 719988.05, "faturas": 53},
    "2026-01": {"receita": 279821.07, "faturamento": 444545.69},
    "2026-02": {"receita": 319233.58, "faturamento": 534752.84},
}

DEFAULT_OUT = Path(__file__).resolve().parents[2] / "data" / "data.json"


def _assert_close(name: str, got: float, expected: float, tol: float = 0.05) -> bool:
    ok = abs(got - expected) <= tol
    flag = "OK " if ok else "FAIL"
    print(f"  [{flag}] {name}: got {got:,.2f}, expected {expected:,.2f} (Δ {got - expected:+,.2f})")
    return ok


def run_checks(payload: dict, month: str) -> bool:
    expected = SANITY_CHECKS.get(month)
    if not expected:
        print(f"  (no recorded expectations for {month}; skipping)")
        return True
    kpis = payload["kpis"]
    ok = True
    ok &= _assert_close("receita_honorarios", kpis["receita_honorarios"], expected["receita"])
    ok &= _assert_close("faturamento_realizado", kpis["faturamento_realizado"], expected["faturamento"])
    if "faturas" in expected:
        got = kpis["faturas_emitidas"]
        flag = "OK " if got == expected["faturas"] else "FAIL"
        print(f"  [{flag}] faturas_emitidas: got {got}, expected {expected['faturas']}")
        ok &= got == expected["faturas"]
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build MBC closing dashboard data.")
    parser.add_argument("--month", default="2026-05", help="competence month YYYY-MM (default 2026-05)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output data.json path")
    parser.add_argument("--check", action="store_true", help="assert sanity totals; non-zero exit on mismatch")
    args = parser.parse_args(argv)

    period = Period.parse(args.month)
    print(f"Building MBC closing data for {period.label} ({period.ano_mes})...")
    client = LegalDeskClient()
    payload = build_payload(period, client)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    kpis = payload["kpis"]
    cov = payload["coverage"]
    print(f"  Receita de honorários : {kpis['receita_honorarios']:,.2f}")
    print(f"  Faturamento Realizado : {kpis['faturamento_realizado']:,.2f}")
    print(f"  Faturas emitidas      : {kpis['faturas_emitidas']}")
    print(f"  Coverage (Base_Resultado): {cov['automated']} API / {cov['formula']} formula / {cov['manual']} manual of {cov['total']}")
    print(f"  Wrote {args.out}")

    if args.check:
        print("Running sanity checks:")
        if not run_checks(payload, args.month):
            print("Sanity checks FAILED.", file=sys.stderr)
            return 1
        print("All sanity checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
