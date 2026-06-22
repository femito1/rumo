# backend/app/api/clients_router.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import require_user, require_admin, require_client_access
from app.api.providers import get_repo
from app.closing.available import available_months
from app.tenancy.models import User
from app.tenancy.repository import Repository

router = APIRouter(prefix="/api/clients", tags=["clients"])

def _client_public(c) -> dict:
    return {"id": c.id, "name": c.name, "provider": c.provider}

@router.get("")
def list_clients(_: User = Depends(require_admin), repo: Repository = Depends(get_repo)) -> list[dict]:
    return [_client_public(c) for c in repo.list_clients()]

@router.get("/{client_id}")
def get_client(client_id: str, user: User = Depends(require_user), repo: Repository = Depends(get_repo)) -> dict:
    require_client_access(user, client_id)
    c = repo.get_client(client_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return {**_client_public(c), "available_months": available_months()}
