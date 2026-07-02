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


def _require_ingest_token(authorization: str | None, token: str) -> None:
    if not token:
        raise HTTPException(status_code=503, detail="Ingestão não configurada")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")
    if authorization.split(" ", 1)[1] != token:
        raise HTTPException(status_code=401, detail="Token de ingestão inválido")


@router.post("/ingest")
def ingest(
    snapshot: dict[str, Any],
    authorization: str | None = Header(default=None),
    token: str = Depends(get_ingest_token),
    store: SnapshotStore = Depends(get_snapshot_store),
) -> dict[str, str]:
    _require_ingest_token(authorization, token)

    ano_mes = (snapshot.get("meta") or {}).get("ano_mes")
    if not ano_mes:
        raise HTTPException(status_code=422, detail="Snapshot sem meta.ano_mes")

    try:
        store.put(ano_mes, snapshot)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {"status": "ok", "ano_mes": ano_mes}


@router.get("/ingest/{ano_mes}/summary")
def ingest_summary(
    ano_mes: str,
    authorization: str | None = Header(default=None),
    token: str = Depends(get_ingest_token),
    store: SnapshotStore = Depends(get_snapshot_store),
) -> dict[str, Any]:
    """Token-protected integrity check for a stored snapshot.

    Returns structure/counts/headline values (not the full financial payload) so
    an operator can verify what actually landed on the VPS after an agent run.
    """
    _require_ingest_token(authorization, token)

    try:
        snapshot = store.get(ano_mes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Sem snapshot para o mês")

    def _n(key: str) -> int:
        val = snapshot.get(key)
        return len(val) if isinstance(val, list) else 0

    revenue = snapshot.get("revenue") or {}
    return {
        "ano_mes": ano_mes,
        "meta": snapshot.get("meta"),
        "top_level_keys": sorted(snapshot.keys()),
        "counts": {
            "rateio_prof": _n("rateio_prof"),
            "despesas_conta": _n("despesas_conta"),
            "custo_area": _n("custo_area"),
            "prolabore": _n("prolabore"),
            "distribuicao_socio": _n("distribuicao_socio"),
        },
        "revenue": {
            "recebimento_bruto": revenue.get("recebimento_bruto"),
            "faturamento_bruto": revenue.get("faturamento_bruto"),
            "recebimento_rows": revenue.get("recebimento_rows"),
            "faturamento_rows": revenue.get("faturamento_rows"),
        },
        "faturas": snapshot.get("faturas"),
    }
