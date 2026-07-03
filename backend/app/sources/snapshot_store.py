# backend/app/sources/snapshot_store.py
"""Filesystem persistence for SISJURI agent snapshots.

Kept as the local-dev / USE_FAKE_REPO fallback. Production persists snapshots in
Supabase (see ``supabase_snapshot_store.SupabaseSnapshotStore``) so the whole
financial dataset is durable, backed up, and multi-tenant.

Files are named ``sisjuri_{client_id}_{ano_mes}.json`` so multiple clients can
coexist. ``client_id`` defaults to ``"mbc"`` for backward compatibility with the
original single-client layout.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

_ANO_MES_RE = re.compile(r"^\d{4}-\d{2}$")
_CLIENT_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_DEFAULT_CLIENT = "mbc"


class SnapshotStore:
    def __init__(self, root: str | os.PathLike[str]) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, ano_mes: str, client_id: str) -> Path:
        if not _ANO_MES_RE.match(ano_mes):
            raise ValueError(f"invalid ano_mes: {ano_mes!r}")
        if not _CLIENT_RE.match(client_id):
            raise ValueError(f"invalid client_id: {client_id!r}")
        return self._root / f"sisjuri_{client_id}_{ano_mes}.json"

    def put(
        self, ano_mes: str, snapshot: dict[str, Any], *, client_id: str = _DEFAULT_CLIENT
    ) -> None:
        self._path(ano_mes, client_id).write_text(
            json.dumps(snapshot, ensure_ascii=False), encoding="utf-8"
        )

    def get(
        self, ano_mes: str, *, client_id: str = _DEFAULT_CLIENT
    ) -> dict[str, Any] | None:
        path = self._path(ano_mes, client_id)
        if not path.exists():
            # Fall back to the legacy (client-less) filename so pre-existing
            # snapshots keep resolving after the rename.
            legacy = self._root / f"sisjuri_{ano_mes}.json"
            if client_id == _DEFAULT_CLIENT and legacy.exists():
                return json.loads(legacy.read_text(encoding="utf-8"))
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def has(self, ano_mes: str, *, client_id: str = _DEFAULT_CLIENT) -> bool:
        return self.get(ano_mes, client_id=client_id) is not None
