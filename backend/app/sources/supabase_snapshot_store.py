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
