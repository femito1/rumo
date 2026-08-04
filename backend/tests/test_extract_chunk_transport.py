# backend/tests/test_extract_chunk_transport.py
"""The SISJURI agent's chunked transport must not lose a space.

`extract.sql` emits the JSON document in fixed-size chunks via
`DBMS_OUTPUT.PUT_LINE`, and `run-agent.ps1` reassembles it by deleting the physical
line breaks between them. sqlplus trims a blank at the edge of an emitted line
(`SET TRIMSPACE ON`), so before extract **v5** a chunk boundary landing on a space
silently GLUED the two neighbouring words together.

Found 2026-08-04, after it had been happening in every month of 2026 — ~6 losses per
month, 62 across the eight months. It moved no money, but it is a live tripwire:
`workbook_layouts.section_for` is an exact dict lookup on ``nome_conta_pai``, so a
corrupted ``'DespesasGerais'`` opens a DUPLICATE expense family instead of folding
into ``'Despesas Gerais'``.

Neither side of that pipeline is Python — one is PL/SQL, the other PowerShell running
on a box we cannot reach from CI. So these tests model the two stages exactly as the
real code performs them, and the model is pinned to the real files: the emit
expression and the reassembly loop are READ OUT of `extract.sql` / `run-agent.ps1`
and asserted, so editing either without updating this test fails here rather than
silently in a month's data.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
EXTRACT_SQL = REPO / "ops" / "sisjuri-agent" / "extract.sql"
RUN_AGENT = REPO / "ops" / "sisjuri-agent" / "run-agent.ps1"

#: Chunk size in extract.sql's emit loop.
CHUNK = 180

#: The character extract.sql wraps each emitted chunk in (v5+).
GUARD = "~"


def _emit(doc: str, *, guarded: bool, chunk: int = CHUNK) -> list[str]:
    """Model extract.sql's emit loop: fixed-size chunks, optionally guarded."""
    out = []
    for pos in range(0, len(doc), chunk):
        piece = doc[pos : pos + chunk]
        out.append(f"{GUARD}{piece}{GUARD}" if guarded else piece)
    return out


def _sqlplus_trim(lines: list[str]) -> list[str]:
    """Model sqlplus's blank-trimming at the edges of each emitted physical line.

    ``SET TRIMSPACE ON`` removes leading/trailing blanks from the printed line. This
    is the step that destroyed the data: it is applied per PHYSICAL line, so it can
    only ever see a chunk edge.
    """
    return [ln.strip(" ") for ln in lines]


def _reassemble(lines: list[str]) -> str:
    """Model run-agent.ps1: strip one guard from each end of each line, then join.

    Deliberately positional and per-line, exactly as the PowerShell does — never a
    global replace of the guard character, which would corrupt a guard that occurs
    inside the JSON as real data.
    """
    out = []
    for ln in lines:
        if len(ln) >= 2 and ln[0] == GUARD and ln[-1] == GUARD:
            ln = ln[1:-1]
        out.append(ln)
    return "".join(out)


def _roundtrip(doc: str, *, guarded: bool, chunk: int = CHUNK) -> str:
    return _reassemble(_sqlplus_trim(_emit(doc, guarded=guarded, chunk=chunk)))


# --- The bug, and the fix -----------------------------------------------------


def test_unguarded_chunking_loses_a_space_at_the_boundary():
    """The v4 behaviour, reproduced. This is the bug — it must stay demonstrable.

    Without it, a later reader has no way to tell that the guards in extract.sql are
    load-bearing rather than decoration, and removing them would look harmless.
    """
    # A space at exactly the chunk boundary: 'Despesas Gerais' split as
    # '...Despesas' | ' Gerais...'.
    doc = "x" * (CHUNK - len("Despesas")) + "Despesas Gerais"
    assert _roundtrip(doc, guarded=False) != doc
    assert "DespesasGerais" in _roundtrip(doc, guarded=False)


def test_guarded_chunking_preserves_the_space():
    doc = "x" * (CHUNK - len("Despesas")) + "Despesas Gerais"
    assert _roundtrip(doc, guarded=True) == doc
    assert "Despesas Gerais" in _roundtrip(doc, guarded=True)


@pytest.mark.parametrize("offset", range(-3, 4))
def test_guarded_chunking_survives_a_space_at_any_offset_near_the_boundary(offset: int):
    """The boundary can fall anywhere in a value; none of those may lose the space."""
    pad = CHUNK + offset - len("Despesas")
    doc = "x" * max(0, pad) + "Despesas Gerais" + "y" * 50
    assert _roundtrip(doc, guarded=True) == doc


def test_guarded_chunking_survives_a_space_at_every_position_in_a_long_document():
    """Exhaustive: one space walked across two full chunks, nothing else in the doc.

    A single hand-picked offset would not have caught the failure mode where the
    NEXT chunk starts on the space rather than the current one ending on it.
    """
    for i in range(1, 2 * CHUNK):
        doc = "a" * i + " " + "b" * (2 * CHUNK - i)
        assert _roundtrip(doc, guarded=True) == doc, f"lost the space at offset {i}"


def test_guarded_chunking_preserves_runs_of_spaces_and_leading_trailing_spaces():
    """Real data has multi-space runs (the convênio memos) and trailing spaces.

    ``strip(' ')`` on an unguarded line would eat as many as sit at the edge, so a
    run split by a boundary is the worst case.
    """
    for doc in (
        "a" * (CHUNK - 2) + "    " + "b" * 40,  # run straddling the boundary
        " " * 5 + "a" * (2 * CHUNK),  # leading spaces (doc starts with blanks)
        "a" * (2 * CHUNK) + " " * 5,  # trailing spaces
        " ",  # degenerate: the whole document is one space
    ):
        assert _roundtrip(doc, guarded=True) == doc


def test_a_guard_character_inside_the_json_is_never_eaten():
    """``~`` is legitimate data (case names carry punctuation), so the strip must be
    positional per line — a global replace would silently corrupt real text."""
    doc = "a" * (CHUNK - 5) + "~tilde~inside~" + "b" * 40
    assert _roundtrip(doc, guarded=True) == doc


def test_a_realistic_snapshot_survives_the_round_trip_byte_for_byte():
    """End-to-end on a real committed snapshot, not a synthetic string."""
    fixture = Path(__file__).parent / "fixtures" / "sisjuri_2026_06.json"
    doc = json.dumps(
        json.loads(fixture.read_text(encoding="utf-8")),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    assert _roundtrip(doc, guarded=True) == doc
    # And confirm the OLD behaviour really did damage this exact document, so the
    # test is measuring something.
    assert _roundtrip(doc, guarded=False) != doc


# --- Pin the model to the real files -----------------------------------------


def test_extract_sql_emits_guarded_chunks():
    """If the emit expression changes, this model is stale — fail here, loudly."""
    sql = EXTRACT_SQL.read_text(encoding="utf-8")
    assert "'~' || DBMS_LOB.SUBSTR(doc, chunk, pos) || '~'" in sql, (
        "extract.sql's emit loop no longer wraps each chunk in '~' guards; the "
        "chunk-boundary space loss is back. See the note at the top of extract.sql."
    )
    # The guards add 2 chars per line, which must stay inside LINESIZE.
    chunk = int(re.search(r"chunk PLS_INTEGER := (\d+)", sql).group(1))
    linesize = int(re.search(r"SET LINESIZE (\d+)", sql).group(1))
    assert chunk == CHUNK, "chunk size changed; update CHUNK in this test"
    assert chunk + 2 <= linesize, (
        f"chunk {chunk} + 2 guard chars exceeds LINESIZE {linesize}; sqlplus would "
        f"wrap the line and the reassembly would glue tokens together"
    )


def test_run_agent_strips_the_guards_positionally_and_not_globally():
    ps1 = RUN_AGENT.read_text(encoding="utf-8")
    assert "$t.Substring(1, $t.Length - 2)" in ps1, (
        "run-agent.ps1 no longer strips the chunk guards; the JSON would carry '~' "
        "at every 180-char boundary and fail to parse."
    )
    # A global replace would corrupt a '~' that is real data. Make that regression
    # visible here rather than in a month's case names. Comment lines are excluded --
    # the file's own explanation of why NOT to do this would otherwise match.
    code = "\n".join(
        ln for ln in ps1.splitlines() if not ln.lstrip().startswith("#")
    )
    assert "-replace '~'" not in code and '-replace "~"' not in code, (
        "run-agent.ps1 strips '~' globally; a tilde inside the JSON is legitimate "
        "data and must survive. Strip one guard from each END of each line instead."
    )
