# backend/app/sources/snapshot_store.py
"""Persistence for SISJURI agent snapshots (one JSON per competence month).

The on-server agent POSTs a snapshot to ``/api/ingest``; the store keeps the
latest per ``ano_mes`` so ``SisjuriDbSource`` can read it later. Filesystem-backed
by default (a directory of ``sisjuri_YYYY-MM.json`` files); trivially swappable
for object storage / Supabase later.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

_ANO_MES_RE = re.compile(r"^\d{4}-\d{2}$")


class SnapshotStore:
    def __init__(self, root: str | os.PathLike[str]) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, ano_mes: str) -> Path:
        if not _ANO_MES_RE.match(ano_mes):
            raise ValueError(f"invalid ano_mes: {ano_mes!r}")
        return self._root / f"sisjuri_{ano_mes}.json"

    def put(self, ano_mes: str, snapshot: dict[str, Any]) -> None:
        self._path(ano_mes).write_text(
            json.dumps(snapshot, ensure_ascii=False), encoding="utf-8"
        )

    def get(self, ano_mes: str) -> dict[str, Any] | None:
        path = self._path(ano_mes)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def has(self, ano_mes: str) -> bool:
        return self._path(ano_mes).exists()
