# backend/tests/test_mbc_golden.py
"""MBC integrity net — a GOLDEN FINGERPRINT of the assembled numbers.

Why this file exists: the product is being generalised for a second client (per-client
áreas, per-client account map). Every existing test asserts a specific rule; none of
them would notice a *broad* drift — a refactor that quietly moved R$ 300 between two
áreas while every targeted assertion still passed.

So this hashes the numbers. It walks the assembled sections for the six closed 2026
months, collects EVERY number in a canonical order, and pins the totals plus a digest.
It is deliberately dumb and deliberately wide:

* If a generalisation is behaviour-preserving, this file does not move.
* If it changes ANY number for MBC, this fails and names the month.

⚠ Never "update the expected values" to make this pass. That is the one move it exists
to prevent. If it fails, either the change was not behaviour-preserving (fix the code)
or a number genuinely had to change (then say so explicitly in the commit, and record
WHY in PROJECT_STATUS.md — the workbook-validated cells are client-facing).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.closing.period import Period
from app.sources.assembler_source import AssemblerSource
from app.sources.base import DayRange
from app.closing.provider import ClosingProvider
from app.tenancy.models import Client

FIXTURES = Path(__file__).parent / "fixtures"
MONTHS = (1, 2, 3, 4, 5, 6)

MBC = Client(id="mbc", name="MBC", provider="legaldesk+sisjuri", provider_config={})


def _snapshot(month: int) -> dict:
    return json.loads((FIXTURES / f"sisjuri_2026_{month:02d}.json").read_text())


def _numbers(obj, out: list[float]) -> None:
    """Every number anywhere in the payload, in a stable traversal order."""
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        out.append(round(float(obj), 2))
    elif isinstance(obj, dict):
        for k in sorted(obj):
            _numbers(obj[k], out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _numbers(v, out)


def _fingerprint(month: int) -> tuple[int, float, str]:
    """(count, sum, sha256) of every number the assembler produces for one month."""
    snap = _snapshot(month)
    period = Period.parse(f"2026-{month:02d}")
    provider = ClosingProvider(sources=[AssemblerSource(snapshot=snap, budget=None)])
    payload = provider.build_closing(
        client=MBC, period=period, day_range=DayRange.full_month(period), role="ADMIN"
    )
    # `generated_at` is a timestamp; everything else is derived from the snapshot.
    payload.pop("generated_at", None)
    nums: list[float] = []
    _numbers(payload, nums)
    digest = hashlib.sha256(
        ";".join(f"{n:.2f}" for n in nums).encode()
    ).hexdigest()[:16]
    return len(nums), round(sum(nums), 2), digest


#: Recorded 2026-08-06 from the six committed fixtures, on code whose June cells the
#: client validated line by line. count + sum are printed on failure because they say
#: *how* it drifted (a changed value moves the sum; a changed shape moves the count).
GOLDEN: dict[int, tuple[int, float, str]] = {
    1: (923, 10803780.34, "31edd606f6dd63fc"),
    2: (911, 12967224.24, "203a2f3319ef2056"),
    3: (889, 21697874.57, "b5fd951b704627b3"),
    4: (949, 8398418.35, "406cba26b58561c2"),
    5: (947, 17405063.34, "67f1dcc8117d4540"),
    6: (983, 13397851.50, "0b76e9d9ff1996db"),
}


@pytest.mark.parametrize("month", MONTHS)
def test_mbc_numbers_are_unchanged(month: int) -> None:
    got = _fingerprint(month)
    want = GOLDEN[month]
    assert got == want, (
        f"2026-{month:02d} drifted.\n"
        f"  expected count/sum/digest: {want}\n"
        f"  actual                   : {got}\n"
        "A generalisation must not move MBC's numbers. Do NOT update GOLDEN to silence "
        "this — fix the code, or justify the change explicitly."
    )
