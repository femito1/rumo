"""Write a LIVE SISJURI snapshot to `tests/fixtures/sisjuri_<ano_mes>.json`.

Why this exists as a script rather than a hand-copied file: the committed fixtures had
drifted badly and nobody could tell, because there was no repeatable way to refresh
them. As of 2026-08-04 the three that existed were on three DIFFERENT extract
contracts — Feb pre-versioning (11 of 29 keys), May likewise, June v3 — while
production served v4. A fixture missing a key does not fail; it makes the tests that
read it pass VACUOUSLY. `test_every_vale_row_is_a_whole_number_of_days` documented
"all 41 rows across the eight months" and actually asserted **6**, because Feb and May
have no `vale_prof` at all.

So: refresh from one command, and keep every fixture on the same contract.

⚠ Fixtures are the regression guard for the client-facing numbers. After refreshing,
run the suite and EXPLAIN every expectation that moves before changing it — a fixture
refresh that quietly re-baselines an assertion converts a guard into a rubber stamp.
The June per-área cells validated by the client (Contencioso 75.424,21 · Econômico
80.536,85 · Arbitragem 54.383,94) must not move at all.

Run:
    cd backend
    python -m scripts.dump_fixture 2026-01 2026-02 2026-03 2026-04 2026-05 2026-06
    python -m scripts.dump_fixture --all-2026      # Jan..Jun (the CLOSED months)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "backend" / "tests" / "fixtures"

#: Fixtures cover the CLOSED months only. The open month changes under you, so a
#: fixture of it would make the suite's outcome depend on the day it is run.
CLOSED_2026 = tuple(f"2026-{m:02d}" for m in range(1, 7))

_ANO_MES = re.compile(r"^\d{4}-\d{2}$")


def dump(ano_mes: str, *, client_id: str = "mbc") -> Path:
    from app.api.providers import get_snapshot_store

    snap = get_snapshot_store().get(ano_mes, client_id=client_id)
    if snap is None:
        raise SystemExit(f"no stored snapshot for {ano_mes} (client {client_id})")

    out = FIXTURES / f"sisjuri_{ano_mes.replace('-', '_')}.json"
    # Pretty-printed and key-sorted: a fixture is read by humans during debugging, and
    # a stable key order keeps its git diff to the values that actually changed.
    out.write_text(
        json.dumps(snap, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    version = (snap.get("meta") or {}).get("extract_version") or 1
    keys = len(snap)
    print(f"{out.name}: extract v{version}, {keys} keys, {out.stat().st_size:,} bytes")
    return out


def main(argv: list[str]) -> None:
    from dotenv import load_dotenv

    load_dotenv(REPO / "backend" / ".env")

    args = argv[1:]
    months = list(CLOSED_2026) if "--all-2026" in args else [a for a in args if _ANO_MES.match(a)]
    if not months:
        raise SystemExit(__doc__)

    for ano_mes in months:
        dump(ano_mes)

    print(
        "\nNow run `pytest` and account for EVERY moved expectation before editing it."
    )


if __name__ == "__main__":
    main(sys.argv)
