# backend/app/api/budget_router.py
"""Admin+client budget (Orcado) API. Both ADMIN and CLIENT may edit, but a
CLIENT is confined to its own client via ``require_client_access``."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import require_client_access, require_user
from app.api.providers import get_budget_repo, get_repo
from app.budget.models import (
    BUDGET_AREAS,
    BUDGET_LINES,
    BudgetEntry,
    is_valid_area,
    is_valid_line,
)
from app.tenancy.models import User
from app.tenancy.repository import Repository

router = APIRouter(prefix="/api/clients", tags=["budget"])


def _serialize(entries: list[BudgetEntry]) -> list[dict[str, Any]]:
    return [
        {
            "area": e.area,
            "line_key": e.line_key,
            "annual_amount": e.annual_amount,
        }
        for e in entries
    ]


@router.get("/{client_id}/budget")
def get_budget(
    client_id: str,
    ano: int = Query(..., ge=2000, le=2100),
    user: User = Depends(require_user),
    repo: Repository = Depends(get_repo),
    budget_repo=Depends(get_budget_repo),
) -> dict[str, Any]:
    require_client_access(user, client_id)
    if repo.get_client(client_id) is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    entries = budget_repo.get_budget(client_id, ano)
    return {
        "client_id": client_id,
        "ano": ano,
        "areas": list(BUDGET_AREAS),
        "lines": [{"key": k, "label": label} for k, label in BUDGET_LINES],
        "entries": _serialize(entries),
    }


@router.put("/{client_id}/budget")
def put_budget(
    client_id: str,
    payload: dict[str, Any],
    ano: int = Query(..., ge=2000, le=2100),
    user: User = Depends(require_user),
    repo: Repository = Depends(get_repo),
    budget_repo=Depends(get_budget_repo),
) -> dict[str, Any]:
    require_client_access(user, client_id)
    if repo.get_client(client_id) is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    raw = payload.get("entries")
    if not isinstance(raw, list):
        raise HTTPException(status_code=422, detail="Corpo inválido: 'entries' ausente")

    entries: list[BudgetEntry] = []
    for item in raw:
        area = str(item.get("area", "institucional"))
        line_key = str(item.get("line_key", ""))
        if not is_valid_area(area):
            raise HTTPException(status_code=422, detail=f"Área inválida: {area}")
        if not is_valid_line(line_key):
            raise HTTPException(status_code=422, detail=f"Linha inválida: {line_key}")
        try:
            amount = float(item.get("annual_amount", 0.0) or 0.0)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="Valor anual inválido") from exc
        entries.append(BudgetEntry(client_id, ano, area, line_key, round(amount, 2)))

    budget_repo.set_budget(client_id, ano, entries)
    return {"client_id": client_id, "ano": ano, "entries": _serialize(entries)}
