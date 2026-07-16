# backend/app/sources/supabase_snapshot_store.py
"""Supabase-backed SISJURI snapshot persistence (production).

One row per ``(client_id, ano_mes)`` in ``sisjuri_snapshots`` with the full
extraction payload in a ``jsonb`` column. Durable + backed up + multi-tenant,
replacing the earlier per-VPS filesystem store. Mirrors the repository pattern
used by budgets.
"""
from __future__ import annotations

import re
from typing import Any

_ANO_MES_RE = re.compile(r"^\d{4}-\d{2}$")
_TABLE = "sisjuri_snapshots"


class SupabaseSnapshotStore:
    def __init__(self, client) -> None:
        self._c = client

    @staticmethod
    def _check(ano_mes: str) -> None:
        if not _ANO_MES_RE.match(ano_mes):
            raise ValueError(f"invalid ano_mes: {ano_mes!r}")

    def put(self, ano_mes: str, snapshot: dict[str, Any], *, client_id: str) -> None:
        self._check(ano_mes)
        self._c.table(_TABLE).upsert(
            [{"client_id": client_id, "ano_mes": ano_mes, "payload": snapshot}],
            on_conflict="client_id,ano_mes",
        ).execute()

    def get(self, ano_mes: str, *, client_id: str) -> dict[str, Any] | None:
        self._check(ano_mes)
        res = (
            self._c.table(_TABLE)
            .select("payload")
            .eq("client_id", client_id)
            .eq("ano_mes", ano_mes)
            .execute()
        )
        rows = res.data or []
        if not rows:
            return None
        return rows[0].get("payload")

    def has(self, ano_mes: str, *, client_id: str) -> bool:
        return self.get(ano_mes, client_id=client_id) is not None

    def recebimento_by_year(self, year: int, *, client_id: str) -> dict[int, float]:
        """Return ``{month_index: recebimento_bruto}`` for every snapshot of ``year``.

        Used to fill the Meta dashboard's 12-month table without loading each
        month's full ~100KB payload: a single PostgREST call projects just the
        ``revenue.recebimento_bruto`` jsonb path (``->>`` yields text, so parse
        with ``float``). Months without a snapshot are simply absent from the map.
        """
        res = (
            self._c.table(_TABLE)
            .select("ano_mes, recebimento:payload->revenue->>recebimento_bruto")
            .eq("client_id", client_id)
            .gte("ano_mes", f"{year:04d}-01")
            .lte("ano_mes", f"{year:04d}-12")
            .execute()
        )
        out: dict[int, float] = {}
        for row in res.data or []:
            ano_mes = row.get("ano_mes")
            raw = row.get("recebimento")
            if not ano_mes or raw is None:
                continue
            try:
                out[int(str(ano_mes)[-2:])] = float(raw)
            except (TypeError, ValueError):
                continue
        return out
