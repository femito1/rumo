# backend/tests/test_snapshot_text_integrity.py
"""Guards against the chunk-boundary space loss (extract < v5).

See `test_extract_chunk_transport.py` for the mechanism and the fix. These tests
catch the *symptom* in the actual snapshots — a value that arrives glued in one month
and spaced in another — from two angles:

1. cross-month consistency: master data (account names, home grupo) cannot legitimately
   change spelling between months, so a space-only difference is a transport defect;
2. no glued word reaches a workbook section label, which is where the defect would
   silently create a DUPLICATE expense family (`section_for` is an exact dict lookup).

The fixtures still carry the corruption until the operator runs the v5 re-extract
(batched by decision on 2026-08-04), so the cross-month test is ``xfail(strict=True)``
against a KNOWN list of glued values: it stays red while they are present and turns
GREEN the moment the re-extracted fixtures land — which is exactly the signal that the
fix worked end-to-end. If it flips to xpass, delete the known-corruption list and drop
the marker (the test then enforces the invariant going forward).
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import pytest

from app.closing.workbook_layouts import _PAI_TO_SECTION, section_for

FIXTURES = Path(__file__).parent / "fixtures"
CLOSED_MONTHS = tuple(range(1, 7))

#: A lowercase/accented letter immediately followed by an uppercase one — the
#: fingerprint of a word glued to the next by a lost space ("DespesasGerais").
_GLUE = re.compile(r"[a-zà-ÿ][A-ZÀ-Þ]")

#: The exact space-losses still present in the committed fixtures (extract v4). This
#: list is the test's memory of the bug: it must EMPTY OUT after the v5 re-extract.
#: Format: the corrupted spelling that appears in at least one month while another
#: month spells the same value correctly. NOT a normalisation table — nothing reads
#: it but this test.
KNOWN_GLUED_UNTIL_V5 = {
    "Materialde Copa/Higiene",
    "Custos comPessoal Técnico",
    "EquipeDireito Econômico",
    "Equipe DireitoEconômico",
}


def _load(month: int) -> dict:
    return json.loads((FIXTURES / f"sisjuri_2026_{month:02d}.json").read_text(encoding="utf-8"))


def _drop_one_space(s: str) -> set[str]:
    return {s[:i] + s[i + 1 :] for i, c in enumerate(s) if c == " "}


def _cross_month_space_losses() -> set[str]:
    """Values that appear glued in one month and correctly spaced in another.

    Keyed on a STABLE identifier (account code, sigla) so a genuine reclassification
    — e.g. a lawyer moving área between months — is not mistaken for a space loss.
    Only differences that are exactly "one string is the other minus a space" count.
    """
    keyed: dict[tuple[str, str], set[str]] = defaultdict(set)
    for m in CLOSED_MONTHS:
        snap = _load(m)
        for r in snap.get("despesas_conta") or []:
            keyed[("conta", r.get("id_conta"))].add(r.get("nome_conta"))
            keyed[("pai", r.get("id_conta"))].add(r.get("nome_conta_pai"))
        for sig, grupo in (snap.get("home_area") or {}).items():
            keyed[("home", sig)].add(grupo)

    glued: set[str] = set()
    for values in keyed.values():
        strs = {v for v in values if isinstance(v, str)}
        if len(strs) < 2:
            continue
        longest = max(strs, key=len)
        for v in strs:
            if v != longest and v in _drop_one_space(longest):
                glued.add(v)
    return glued


@pytest.mark.xfail(
    reason="fixtures carry extract-v4 space losses until the v5 re-extract (batched, "
    "2026-08-04); this turns GREEN once the re-extracted fixtures land",
    strict=True,
)
def test_snapshot_text_is_spelled_consistently_across_months():
    """No account name / home grupo may differ between months by only a space.

    Master data cannot legitimately change spelling month to month; a space-only
    difference is the chunk-boundary transport defect (extract < v5).
    """
    assert _cross_month_space_losses() == set()


def test_the_known_corruption_list_is_exactly_what_is_present():
    """Pins the CURRENT damage so the xfail above is meaningful, not just red for some
    unrelated reason. If a re-extract fixes some but not all, this fails and tells you
    the list is stale — update it, do not silence it.
    """
    assert _cross_month_space_losses() == KNOWN_GLUED_UNTIL_V5


def _glued_indirect_families() -> list[tuple[int, str, str, str]]:
    """Indirect (institutional) accounts whose glued ``nome_conta_pai`` resolves to an
    UNMAPPED family — i.e. ``section_for`` falls through to the glued name itself and
    opens a DUPLICATE expense family in the section tree (dre.py:318 only routes
    indirect accounts through ``section_for``; direct 030.* team costs never do, so a
    glue there cannot split a family).
    """
    from app.closing.workbook_layouts import (
        _CONTA3_TO_SECTION,
        _PREFIX_TO_SECTION,
        is_indirect,
    )

    offenders = []
    for m in CLOSED_MONTHS:
        for r in _load(m).get("despesas_conta") or []:
            pai = r.get("nome_conta_pai")
            idc = str(r.get("id_conta") or "")
            if not pai or not _GLUE.search(pai) or not is_indirect(idc):
                continue
            has_code_rule = idc in _CONTA3_TO_SECTION or any(
                idc.startswith(p) for p, _ in _PREFIX_TO_SECTION
            )
            if not has_code_rule and pai not in _PAI_TO_SECTION:
                offenders.append((m, idc, pai, section_for(pai, idc)))
    return offenders


@pytest.mark.xfail(
    reason="the v4 fixtures carry a glued 'DespesasGerais' on 020.030.0060 (May), an "
    "indirect account with no code rule -> a real duplicate family; fixed by the v5 "
    "re-extract (batched, 2026-08-04), at which point this turns GREEN",
    strict=True,
)
def test_no_glued_parent_name_reaches_an_unmapped_expense_family():
    """A glued ``nome_conta_pai`` on an INDIRECT account with no id_conta code rule
    silently splits an expense family in two. This is the concrete harm the transport
    bug does to a rendered number's LABEL (the money survives, under the wrong family).
    """
    offenders = _glued_indirect_families()
    assert not offenders, (
        "a glued nome_conta_pai resolves to an unmapped (duplicate) family: "
        + "; ".join(f"m{m} {idc} {pai!r}->{sec!r}" for m, idc, pai, sec in offenders)
    )
