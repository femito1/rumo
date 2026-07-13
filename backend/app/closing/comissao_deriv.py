# backend/app/closing/comissao_deriv.py
"""Derive per-area **Comissão** (Participação + Repasse) directly from SISJURI.

Comissão is ~zero most months, with occasional Participação entries. It has two
DB sources, both verified against the workbook ``Base_Resultado`` to the centavo
(``docs/SISJURI_QUERIES.md`` §12a):

* **``020.110.0010`` "Participação Externa (comissões)"** — booked at the AREA
  level (``ID_GRUPOJURIDICO``). The extract emits these as ``kind='area'`` rows
  carrying the grupo name; we fold them onto the three DRE areas via
  :func:`workbook_layouts.match_area` (e.g. Feb 1.500 → Econômico).
* **``030.010.0120`` "Participação Interna (comissões)"** — booked per lawyer.
  The sigla is read from ``CONTASPAGAR.COD_ADVG`` (the ``LANCAMENTO.LANCPROFDEST``
  is NULL on these rows — the sigla lives only in the histórico "Comissão EHF" —
  which is why the old LANCPROFDEST arm dropped it and ``comissao_deriv`` came
  back null; see the 2026-07-13 probe). The extract emits these as
  ``kind='lawyer'`` rows; we fold them to each lawyer's area using the SAME split
  machinery as Custo equipe (home grupo + ``CAD_RATEIO_GRUPO`` %), so a multi-area
  lawyer's comissão splits the same way (e.g. Mai EHF 2.128,06 → Econômico).

``030.010.0080`` "Participação E" is always empty and is not read.

Pure module: it takes the already-extracted rows plus the per-lawyer area splits
(built by :func:`custo_equipe_deriv.build_area_splits`), so it is unit-testable
without a database.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.closing.custo_equipe_deriv import LawyerAreaSplit, _grupo_to_area
from app.closing.workbook_layouts import AREAS


def derive_area_comissao(
    rows: Sequence[Mapping[str, object]],
    splits: Mapping[str, LawyerAreaSplit],
) -> dict[str, float]:
    """Fold Comissão rows into per-area totals.

    ``rows`` come from the snapshot ``comissao_deriv`` block. Each row is either
    ``{kind: 'area', area, valor}`` (Participação Externa, area-level) or
    ``{kind: 'lawyer', sigla, valor}`` (Participação Interna, per lawyer).
    ``splits`` maps each lawyer to their area fractions (see
    :func:`custo_equipe_deriv.build_area_splits`).
    """
    area_total: dict[str, float] = {a: 0.0 for a in AREAS}
    for row in rows:
        kind = str(row.get("kind") or "").strip()
        valor = float(row.get("valor") or 0.0)  # type: ignore[arg-type]
        if not valor:
            continue
        if kind == "area":
            line_area = _grupo_to_area(str(row.get("area") or ""))
            if line_area is not None:
                area_total[line_area] = round(area_total.get(line_area, 0.0) + valor, 2)
        elif kind == "lawyer":
            sigla = str(row.get("sigla") or "").strip()
            split = splits.get(sigla)
            if split is None:
                continue
            for area, frac in split.normalized().items():
                area_total[area] = round(area_total.get(area, 0.0) + valor * frac, 2)
    return {a: round(v, 2) for a, v in area_total.items()}
