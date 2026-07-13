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

**Rounding (client-confirmed 2026-07-13):** the workbook rounds many cells to whole
reais while our DB derivation carries centavos. E.g. May recebimento is typed as
``415928`` in the workbook but the sacred LegalDesk value is ``415927,84`` (a R$0,16
gap that used to cascade-blank the whole institucional tail: imposto, resultado
bruto/líquido, reserva). The client confirmed this rounding "is fine". So the match
tolerance is **R$1,00**, not R$0,01: large enough to absorb whole-real rounding on a
single input plus the small compounding down the DRE chain, yet far below any real
derivation bug (historically hundreds to thousands off), which still blanks. The
purpose is unchanged — never show a number that materially disagrees with the book.
"""
from __future__ import annotations

#: Tolerance for "matches the workbook". R$1,00 absorbs the workbook's whole-real
#: rounding (the DB carries centavos); a real bug is orders of magnitude larger.
MATCH_TOLERANCE = 1.00

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
