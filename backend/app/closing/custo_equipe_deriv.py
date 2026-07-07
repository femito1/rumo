# backend/app/closing/custo_equipe_deriv.py
"""Derive per-area **Custo equipe** directly from SISJURI, with no monthly manual
ledger. This replaces both the noisy ``custo_area`` aggregation and the workbook
``ledger`` import for Custo equipe.

The recipe (proven against the client dashboard for 2026, see
``docs/SISJURI_QUERIES.md`` §11): per lawyer, sum the team-cost components and
place them into a DRE area:

* **Amount** — from the snapshot ``custo_equipe_deriv`` block, which the SISJURI
  extract emits per ``(sigla, id_conta, valor)``. Account ``030.010.0010``
  (Distribuição) is the CONTASPAGAR **gross base excluding "Bônus" histórico**
  (Fixa + Diferença); ``030.010.0130`` (Pró-Labore) is gross; ``030.010.0110``
  (Convênio) is net; ``030.010.0140`` (Bolsa) is gross. INSS ``030.010.0050`` is
  excluded.
* **Area** — the lawyer's **home grupo** (``CAD_PROFISSIONAL.ID_GRUPOJURIDICO``),
  overridden by the **percentage split** in ``CAD_RATEIO_GRUPO`` when a lawyer is
  multi-area (only Aurelio/AM today: 50% Contencioso / 50% Econômico). SIGLADEST
  (payment cost-center) is deliberately NOT used — it disagrees with the ledger
  for BBX.
* **Per-lawyer override** — a small ``overrides`` map (from the manual-actuals
  path) can cap/replace a lawyer's derived total for rare negotiated cases
  (e.g. JGS capped at a round figure some months). This is the entire manual
  surface; everything else is automatic.

Pure module: it takes already-extracted rows + the area map, so it is unit
testable without a database. The extract does the Oracle read.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from app.closing.workbook_layouts import AREAS, match_area

#: Account excluded from per-lawyer Custo equipe (booked outside the area blocks).
INSS_ACCOUNT = "030.010.0050"


@dataclass
class LawyerAreaSplit:
    """A lawyer's area allocation: ``{DRE area -> fraction}`` summing to 1.0.

    Single-area lawyers have one entry at 1.0 (their home grupo). Multi-area
    lawyers (Aurelio) carry the ``CAD_RATEIO_GRUPO`` percentages.
    """

    fractions: dict[str, float] = field(default_factory=dict)

    def normalized(self) -> dict[str, float]:
        total = sum(self.fractions.values())
        if total <= 0:
            return {}
        return {a: v / total for a, v in self.fractions.items()}


def build_area_splits(
    rateio_grupo: Sequence[Mapping[str, object]],
    home_area: Mapping[str, str],
) -> dict[str, LawyerAreaSplit]:
    """Build per-lawyer area splits from the ``rateio_grupo`` snapshot rows and a
    ``sigla -> home grupo name`` map.

    ``rateio_grupo`` rows are ``{sigla, grupo, percentual}`` (from
    ``CAD_RATEIO_GRUPO`` joined to grupo name, active window only). A lawyer with
    rateio rows uses them; otherwise falls back to a single 100% home area.
    """
    splits: dict[str, LawyerAreaSplit] = {}
    for row in rateio_grupo:
        sigla = str(row.get("sigla") or "").strip()
        grupo = str(row.get("grupo") or "")
        pct = float(row.get("percentual") or 0.0)  # type: ignore[arg-type]
        if not sigla or pct <= 0:
            continue
        area = _grupo_to_area(grupo)
        if area is None:
            continue
        split = splits.setdefault(sigla, LawyerAreaSplit())
        split.fractions[area] = split.fractions.get(area, 0.0) + pct
    # Home-area fallback for lawyers without a rateio entry.
    for sigla, grupo in home_area.items():
        if sigla in splits:
            continue
        area = _grupo_to_area(str(grupo))
        if area is not None:
            splits[sigla] = LawyerAreaSplit({area: 1.0})
    return splits


def _grupo_to_area(grupo_name: str) -> str | None:
    for area in AREAS:
        if match_area(grupo_name, area):
            return area
    return None


def derive_area_custo_equipe(
    rows: Sequence[Mapping[str, object]],
    splits: Mapping[str, LawyerAreaSplit],
    *,
    overrides: Mapping[str, float] | None = None,
    exclude_accounts: frozenset[str] = frozenset({INSS_ACCOUNT}),
) -> dict[str, float]:
    """Fold per-``(sigla, id_conta, valor)`` rows into per-area Custo equipe.

    ``rows`` come from the snapshot ``custo_equipe_deriv`` block. ``splits`` maps
    each lawyer to their area fractions (see :func:`build_area_splits`).
    ``overrides`` optionally replaces a lawyer's *total* (all accounts) with a
    fixed figure, still allocated by that lawyer's area split (for rare
    negotiated caps). Amounts for a lawyer with no split are dropped (logged by
    the caller if needed) — every real lawyer has a home grupo.
    """
    overrides = overrides or {}
    per_lawyer: dict[str, float] = {}
    for row in rows:
        sigla = str(row.get("sigla") or "").strip()
        id_conta = str(row.get("id_conta") or "")
        if not sigla or id_conta in exclude_accounts:
            continue
        per_lawyer[sigla] = round(
            per_lawyer.get(sigla, 0.0) + float(row.get("valor") or 0.0), 2  # type: ignore[arg-type]
        )
    for sigla, capped in overrides.items():
        per_lawyer[sigla] = round(float(capped), 2)

    area_total: dict[str, float] = {a: 0.0 for a in AREAS}
    for sigla, total in per_lawyer.items():
        split = splits.get(sigla)
        if split is None:
            continue
        for area, frac in split.normalized().items():
            area_total[area] = area_total.get(area, 0.0) + total * frac
    return {a: round(v, 2) for a, v in area_total.items()}
