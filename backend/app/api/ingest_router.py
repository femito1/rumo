# backend/app/api/ingest_router.py
"""Ingest endpoint for the on-server SISJURI agent (egress Option A).

The agent runs on MBC-LDESK01 (the only host with a route to the private-VCN
Oracle DB) and POSTs a per-competence-month JSON snapshot here over HTTPS, with a
shared bearer token. We never open an inbound path to the DB; the server reaches
out to us. Snapshots are persisted via ``SnapshotStore`` for ``SisjuriDbSource``.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.providers import get_settings
from app.api.providers import get_snapshot_store as _get_snapshot_store

router = APIRouter(prefix="/api", tags=["ingest"])

#: Default tenant for agents that don't (yet) send a client_id. The current
#: single-client agent extracts MBC; new tenants pass meta.client_id.
_DEFAULT_CLIENT = "mbc"


def get_snapshot_store():
    """Snapshot persistence (Supabase in prod, filesystem for local/USE_FAKE_REPO)."""
    return _get_snapshot_store()


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
    store=Depends(get_snapshot_store),
) -> dict[str, str]:
    _require_ingest_token(authorization, token)

    meta = snapshot.get("meta") or {}
    ano_mes = meta.get("ano_mes")
    if not ano_mes:
        raise HTTPException(status_code=422, detail="Snapshot sem meta.ano_mes")
    client_id = meta.get("client_id") or _DEFAULT_CLIENT

    try:
        store.put(ano_mes, snapshot, client_id=client_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {"status": "ok", "ano_mes": ano_mes, "client_id": client_id}


@router.post("/ingest/migrate-fs-to-supabase")
def migrate_fs_to_supabase(
    client_id: str = _DEFAULT_CLIENT,
    authorization: str | None = Header(default=None),
    token: str = Depends(get_ingest_token),
) -> dict[str, Any]:
    """One-time migration: copy filesystem snapshots on this host into Supabase.

    Runs where the legacy files live (the VPS), so the 29-month backfill moves to
    the durable store without re-running the agent. Idempotent (upsert). Reads
    both the new ``sisjuri_{client}_{mes}.json`` and legacy ``sisjuri_{mes}.json``
    layouts.
    """
    _require_ingest_token(authorization, token)

    import os
    import re
    from pathlib import Path

    from app.sources.snapshot_store import SnapshotStore
    from app.sources.supabase_snapshot_store import SupabaseSnapshotStore

    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        raise HTTPException(status_code=503, detail="Supabase não configurado")

    root = Path(os.environ.get("SNAPSHOT_DIR", "data/snapshots"))
    fs = SnapshotStore(root)

    from supabase import create_client

    dest = SupabaseSnapshotStore(
        create_client(settings.supabase_url, settings.supabase_service_key)
    )

    months: set[str] = set()
    pat = re.compile(rf"^sisjuri_(?:{re.escape(client_id)}_)?(\d{{4}}-\d{{2}})\.json$")
    for p in root.glob("sisjuri_*.json"):
        m = pat.match(p.name)
        if m:
            months.add(m.group(1))

    migrated: list[str] = []
    skipped: list[str] = []
    for ano_mes in sorted(months):
        snap = fs.get(ano_mes, client_id=client_id)
        if snap is None:
            skipped.append(ano_mes)
            continue
        dest.put(ano_mes, snap, client_id=client_id)
        migrated.append(ano_mes)

    return {
        "client_id": client_id,
        "migrated": migrated,
        "skipped": skipped,
        "count": len(migrated),
    }


@router.get("/ingest/{ano_mes}/summary")
def ingest_summary(
    ano_mes: str,
    client_id: str = _DEFAULT_CLIENT,
    authorization: str | None = Header(default=None),
    token: str = Depends(get_ingest_token),
    store=Depends(get_snapshot_store),
) -> dict[str, Any]:
    """Token-protected integrity check for a stored snapshot.

    Returns structure/counts/headline values (not the full financial payload) so
    an operator can verify what actually landed after an agent run.
    """
    _require_ingest_token(authorization, token)

    try:
        snapshot = store.get(ano_mes, client_id=client_id)
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
