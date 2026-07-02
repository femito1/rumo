# backend/app/api/ingest_router.py
"""Ingest endpoint for the on-server SISJURI agent (egress Option A).

The agent runs on MBC-LDESK01 (the only host with a route to the private-VCN
Oracle DB) and POSTs a per-competence-month JSON snapshot here over HTTPS, with a
shared bearer token. We never open an inbound path to the DB; the server reaches
out to us. Snapshots are persisted via ``SnapshotStore`` for ``SisjuriDbSource``.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.providers import get_settings
from app.sources.snapshot_store import SnapshotStore

router = APIRouter(prefix="/api", tags=["ingest"])


@lru_cache
def get_snapshot_store() -> SnapshotStore:
    root = os.environ.get("SNAPSHOT_DIR", "data/snapshots")
    return SnapshotStore(root)


def get_ingest_token() -> str:
    return get_settings().ingest_token


@router.post("/ingest")
def ingest(
    snapshot: dict[str, Any],
    authorization: str | None = Header(default=None),
    token: str = Depends(get_ingest_token),
    store: SnapshotStore = Depends(get_snapshot_store),
) -> dict[str, str]:
    if not token:
        raise HTTPException(status_code=503, detail="Ingestão não configurada")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")
    presented = authorization.split(" ", 1)[1]
    if presented != token:
        raise HTTPException(status_code=401, detail="Token de ingestão inválido")

    ano_mes = (snapshot.get("meta") or {}).get("ano_mes")
    if not ano_mes:
        raise HTTPException(status_code=422, detail="Snapshot sem meta.ano_mes")

    try:
        store.put(ano_mes, snapshot)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {"status": "ok", "ano_mes": ano_mes}
