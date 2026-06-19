"""Convenience: build data.json (into both data/ and frontend/) and serve the UI.

    python mbc-automation/backend/scripts/build_and_serve.py --month 2026-05

Stops at build if --no-serve is passed (useful for CI / scheduled refresh).
"""
from __future__ import annotations

import argparse
import functools
import http.server
import shutil
import socketserver
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from mbc_automation.api_client import LegalDeskClient  # noqa: E402
from mbc_automation.builder import build_payload  # noqa: E402
from mbc_automation.cli import run_checks  # noqa: E402
from mbc_automation.period import Period  # noqa: E402

import json  # noqa: E402

PROJECT = BACKEND.parent
DATA_JSON = PROJECT / "data" / "data.json"
FRONTEND = PROJECT / "frontend"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", default="2026-05")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-serve", action="store_true")
    args = ap.parse_args()

    period = Period.parse(args.month)
    print(f"Building {period.label}...")
    payload = build_payload(period, LegalDeskClient())
    DATA_JSON.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    DATA_JSON.write_text(text)
    shutil.copyfile(DATA_JSON, FRONTEND / "data.json")
    run_checks(payload, args.month)
    print(f"Wrote {DATA_JSON} and {FRONTEND / 'data.json'}")

    if args.no_serve:
        return 0

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(FRONTEND))
    with socketserver.TCPServer(("", args.port), handler) as httpd:
        print(f"Serving dashboard at http://localhost:{args.port}/  (Ctrl+C to stop)")
        httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
