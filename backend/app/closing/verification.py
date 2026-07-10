# backend/app/closing/verification.py
"""The hard rule: never show a Realizado number that disagrees with the workbook.

The client's directive (docs/MEETING_2026-07-10.md §V): the workbook is the source
of truth, and a value we derive from SISJURI/LegalDesk must NEVER be displayed if it
fails to match the workbook. If it diverges from a known target beyond a tiny
tolerance, we blank the cell (the frontend renders "ainda não temos") instead of
showing a wrong number. Where no target is known, the derived value is shown.

``targets`` is an optional per-section map ``{section_key: {line_key: value}}``,
sourced from the workbook when one is available for the competence month. It is a
verification overlay only — it never becomes the displayed value; it just gates
whether the derived value may be shown.
"""
from __future__ import annotations

#: Cents-level tolerance for "matches the workbook".
MATCH_TOLERANCE = 0.01

#: Nested targets: section key -> line key -> expected workbook value.
Targets = dict[str, dict[str, float]]


def matches_target(value: float | None, target: float | None) -> bool:
    """True when there is no target, or the value ties the target within R$0,01.

    A ``None`` value can never satisfy a non-None target.
    """
    if target is None:
        return True
    if value is None:
        return False
    return abs(value - target) <= MATCH_TOLERANCE


def verified_value(
    value: float | None,
    section_key: str,
    line_key: str,
    targets: Targets | None,
) -> float | None:
    """Return ``value`` if it matches the workbook target (or none exists), else
    ``None`` so the cell blanks rather than showing a number that does not match.
    """
    if not targets:
        return value
    target = targets.get(section_key, {}).get(line_key)
    return value if matches_target(value, target) else None
