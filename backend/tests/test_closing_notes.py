# backend/tests/test_closing_notes.py
"""The PT-BR discrepancy notes registry.

These are HUMAN-WRITTEN explanations of known, diagnosed differences between our
numbers and the client's workbook, surfaced next to the number they concern so the
client stops re-discovering them in meetings (2026-07-30 request).

Deliberately NOT runtime detection: the user rejected an intrinsic
validation/guard layer as useless ("derive numbers correctly from the DB, don't
police them after the fact" — see the no-sanity-guard decision). Nothing here
inspects a value or decides anything is wrong. A note is a committed fact we
diagnosed and chose to explain.
"""
import pytest

from app.closing.notes import (
    NOTES,
    Note,
    notes_for,
    notes_for_row,
)


def test_every_seeded_note_is_well_formed():
    assert NOTES, "the registry should ship with the notes diagnosed on 2026-07-30"
    for n in NOTES:
        assert n.id and n.id == n.id.lower(), f"{n.id}: id must be lowercase kebab"
        assert n.titulo and n.detalhe, f"{n.id}: needs a PT-BR title and body"
        # PT-BR UI convention: no English leaking into client-facing copy.
        assert "workbook" not in n.titulo.lower(), f"{n.id}: use 'planilha' in PT-BR copy"
        # A note must point AT something, or it can never be rendered in place.
        assert n.months, f"{n.id}: must name the months it applies to"
        for m in n.months:
            assert m.startswith("2026-") or m == "*", f"{n.id}: odd month {m!r}"


def test_notes_for_month_filters_by_competence():
    # The March Vale note applies to March only; asking for June must not return it.
    mar = {n.id for n in notes_for("2026-03")}
    jun = {n.id for n in notes_for("2026-06")}
    assert "vale-adm-meses-nao-ajustados" in mar
    assert "vale-adm-meses-nao-ajustados" not in jun


def test_notes_for_row_matches_section_and_line():
    # Row-level lookup is what lets the UI badge the exact cell.
    hits = notes_for_row("2026-03", section="institucional", line="despesas")
    assert any(n.id == "vale-adm-meses-nao-ajustados" for n in hits)
    # A different line in the same section must NOT inherit the note.
    assert not notes_for_row("2026-03", section="institucional", line="recebimento")


def test_a_wildcard_month_note_applies_to_every_month():
    # "*" is for structural facts that aren't month-specific (e.g. the 4,80 bank
    # tariff, which finance zeroes in Excel every month).
    n = Note(id="teste-wildcard", titulo="T", detalhe="D", months=("*",),
             section="institucional", lines=("despesas",))
    assert n.applies_to("2026-01") and n.applies_to("2026-12")


def test_notes_are_ordered_deterministically():
    # The UI lists them; a set-iteration order would make the panel jump around.
    twice = [tuple(n.id for n in notes_for("2026-03")) for _ in range(2)]
    assert twice[0] == twice[1]


def test_seeded_notes_cover_the_three_diagnosed_discrepancies():
    ids = {n.id for n in NOTES}
    assert {
        "vale-adm-meses-nao-ajustados",   # mar/abr/mai: her own un-adjusted entries
        "vale-adm-janeiro-ajuste-manual",  # Jan: hand-typed 35,52 with no lançamento
        "despesas-area-formula-deslocada",  # Jan–May: Base_Resultado r204/205/206
    } <= ids


def test_note_payload_is_json_safe_and_pt_br():
    # The payload goes straight to the SPA; it must be plain data, and the
    # client-facing copy must be Portuguese.
    for n in NOTES:
        d = n.to_payload()
        assert set(d) >= {"id", "titulo", "detalhe", "severidade"}
        assert isinstance(d["titulo"], str) and isinstance(d["detalhe"], str)
        assert d["severidade"] in ("info", "atencao")


def test_contact_hint_is_present_so_the_client_knows_what_to_do():
    # The client asked to be told whom to contact, not just what differs.
    for n in NOTES:
        assert n.to_payload().get("contato") is not None


@pytest.mark.parametrize("month", ["2026-03", "2026-04", "2026-05"])
def test_vale_note_covers_all_three_unadjusted_months(month):
    assert any(
        n.id == "vale-adm-meses-nao-ajustados" for n in notes_for(month)
    ), f"{month} is one of Renata's un-adjusted months and must carry the note"
