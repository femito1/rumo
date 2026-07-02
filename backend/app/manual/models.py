# backend/app/manual/models.py
"""Manual Realizado inputs SISJURI cannot derive (per-area Recebimento, etc.).

Grain: per client + competence month (ano_mes) + area + line_key. The prime use
is per-area Recebimento, which the workbook assigns via manual case-by-area
classification + cross-area transfers ('Resumo_Recebidas'). No DB equivalent, so
it is entered by hand; if finance later gives a fixed rule, an automatic source
can supersede these rows.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.closing.dre import COMISSAO, DESPESA_INSTITUCIONAL, DESPESAS_EQUIPE, RECEBIMENTO
from app.closing.workbook_layouts import AREAS

#: Areas that accept manual per-area actuals (the three cost centers).
MANUAL_AREAS = tuple(AREAS)

#: Manually-entered Realizado lines per area, in workbook order.
MANUAL_LINES: tuple[tuple[str, str], ...] = (
    (RECEBIMENTO, "Recebimento"),
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
