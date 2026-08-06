# backend/app/api/clients_router.py
from __future__ import annotations
from fastapi import APIRouter, Depends
from app.api.deps import active_client_or_404, require_user, require_admin, require_client_access
from app.api.providers import get_repo
from app.closing.available import available_months, available_months_detail
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
    c = active_client_or_404(repo, client_id)
    # ``available_months`` stays CLOSED-only for back-compat (callers read it as
    # "months that are done"); ``available_months_detail`` adds the open month with
    # an explicit is_partial flag so the picker can offer and label it.
    return {
        **_client_public(c),
        "available_months": available_months(),
        "available_months_detail": available_months_detail(),
    }
