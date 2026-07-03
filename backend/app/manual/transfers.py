# backend/app/manual/transfers.py
"""Cross-area recebimento transfers ('Resumo_Recebidas' overlay).

The per-area recebimento *base* is auto-derived from SISJURI (CASO -> área
jurídica; see ``dre.RealizadoInputs``). On top of it, finance records manual
reclassifications that move received cash between areas — a commission credited
to the originating lawyer's area, a case worked by one area but billed to
another, etc. In the workbook these live in the 'Resumo_Recebidas' consolidation
blocks and net onto each area's Receita row (e.g. Fev 2026: Arbitragem gives
4362.58 + 2069.11 to Contencioso/Econômico).

Grain: per client + competence month + (origem area -> destino area) + valor.
A transfer subtracts ``valor`` from origem and adds it to destino, so the total
over all areas is conserved (matching the sacred SISJURI recebimento total).
These are genuinely manual decisions with no DB rule, but they are small and
structured — unlike the base, which is now fully derived.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.closing.workbook_layouts import AREAS


@dataclass(frozen=True)
class AreaTransfer:
    client_id: str
    ano_mes: str
    origem: str
    destino: str
    valor: float


def net_deltas(transfers: list[AreaTransfer]) -> dict[str, float]:
    """Fold transfers into per-area net deltas ({area: +/- valor}).

    Sums to ~0 across areas (value is moved, never created)."""
    deltas: dict[str, float] = {a: 0.0 for a in AREAS}
    for t in transfers:
        if t.origem in deltas:
            deltas[t.origem] = round(deltas[t.origem] - t.valor, 4)
        if t.destino in deltas:
            deltas[t.destino] = round(deltas[t.destino] + t.valor, 4)
    return deltas


def apply_to_base(
    base: dict[str, float], transfers: list[AreaTransfer]
) -> dict[str, float]:
    """Return a new per-area recebimento = base + net transfer deltas."""
    if not transfers:
        return dict(base)
    deltas = net_deltas(transfers)
    out = dict(base)
    for area, delta in deltas.items():
        if delta:
            out[area] = round(out.get(area, 0.0) + delta, 2)
    return out


# --- Persistence (mirrors the manual-actuals repository pattern) -------------


class AreaTransfersRepository(Protocol):
    def get_transfers(self, client_id: str, ano_mes: str) -> list[AreaTransfer]: ...
    def set_transfers(
        self, client_id: str, ano_mes: str, entries: list[AreaTransfer]
    ) -> None: ...


def _row_to_transfer(row: dict) -> AreaTransfer:
    return AreaTransfer(
        client_id=str(row["client_id"]),
        ano_mes=str(row["ano_mes"]),
        origem=str(row["origem"]),
        destino=str(row["destino"]),
        valor=float(row.get("valor", 0.0) or 0.0),
    )


class SupabaseAreaTransfersRepository:
    def __init__(self, client) -> None:
        self._c = client

    def get_transfers(self, client_id: str, ano_mes: str) -> list[AreaTransfer]:
        res = (
            self._c.table("area_transfers")
            .select("*")
            .eq("client_id", client_id)
            .eq("ano_mes", ano_mes)
            .execute()
        )
        return [_row_to_transfer(r) for r in (res.data or [])]

    def set_transfers(
        self, client_id: str, ano_mes: str, entries: list[AreaTransfer]
    ) -> None:
        payload = [
            {
                "client_id": e.client_id,
                "ano_mes": e.ano_mes,
                "origem": e.origem,
                "destino": e.destino,
                "valor": e.valor,
            }
            for e in entries
        ]
        # Append-only semantics: replace the month's set atomically.
        self._c.table("area_transfers").delete().eq("client_id", client_id).eq(
            "ano_mes", ano_mes
        ).execute()
        if payload:
            self._c.table("area_transfers").insert(payload).execute()


class InMemoryAreaTransfersRepository:
    def __init__(self) -> None:
        self._store: dict[tuple[str, str], list[AreaTransfer]] = {}

    def get_transfers(self, client_id: str, ano_mes: str) -> list[AreaTransfer]:
        return list(self._store.get((client_id, ano_mes), []))

    def set_transfers(
        self, client_id: str, ano_mes: str, entries: list[AreaTransfer]
    ) -> None:
        self._store[(client_id, ano_mes)] = list(entries)
