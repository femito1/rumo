# backend/app/manual/models.py
"""Manual Realizado inputs SISJURI cannot derive.

Grain: per client + competence month (ano_mes) + area + line_key.

Per-area **Recebimento is no longer manual**: it is derived from SISJURI
(``GERENC_VW_POSFIN_RESULTREC`` via CASO → área jurídica, verified to the
centavo against the workbook) with the ``Resumo_Recebidas`` cross-area transfers
applied as deltas. Hand-filling it is therefore rejected. The remaining manual
lines are the ones still lacking a verified derivation rule (Comissão, Despesas
Equipe, Despesa Institucional); if finance confirms a rule for these, an
automatic source can supersede them too.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.closing.dre import COMISSAO, DESPESA_INSTITUCIONAL, DESPESAS_EQUIPE
from app.closing.workbook_layouts import AREAS

#: Areas that accept manual per-area actuals (the three cost centers).
MANUAL_AREAS = tuple(AREAS)

#: Manually-entered Realizado lines per area, in workbook order. Recebimento is
#: intentionally absent — it is SISJURI-derived (see module docstring).
MANUAL_LINES: tuple[tuple[str, str], ...] = (
    (COMISSAO, "Comissão"),
    (DESPESAS_EQUIPE, "Despesas Equipe"),
    (DESPESA_INSTITUCIONAL, "Despesa Institucional"),
)

_MANUAL_LINE_KEYS = {k for k, _ in MANUAL_LINES}


@dataclass(frozen=True)
class ManualActual:
    client_id: str
    ano_mes: str
    area: str
    line_key: str
    valor: float


def is_valid_line(line_key: str) -> bool:
    return line_key in _MANUAL_LINE_KEYS


def is_valid_area(area: str) -> bool:
    return area in MANUAL_AREAS


def by_area(entries: list[ManualActual]) -> dict[str, dict[str, float]]:
    """Fold into {area: {line_key: valor}}."""
    out: dict[str, dict[str, float]] = {}
    for e in entries:
        out.setdefault(e.area, {})[e.line_key] = round(e.valor, 2)
    return out
