# backend/app/api/manual_router.py
"""Admin+client Manual Realizado inputs API (per-area Recebimento etc.).

Both ADMIN and CLIENT may edit; a CLIENT is confined to its own client via
``require_client_access``. Grain is per competence month (ano_mes)."""
from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import require_client_access, require_user
from app.api.providers import get_manual_repo, get_repo
from app.manual.models import (
    MANUAL_AREAS,
    MANUAL_LINES,
    ManualActual,
    is_valid_area,
    is_valid_line,
)
from app.tenancy.models import User
from app.tenancy.repository import Repository

router = APIRouter(prefix="/api/clients", tags=["manual"])

_ANO_MES = re.compile(r"^\d{4}-\d{2}$")


def _serialize(entries: list[ManualActual]) -> list[dict[str, Any]]:
    return [
        {"area": e.area, "line_key": e.line_key, "valor": e.valor} for e in entries
    ]


@router.get("/{client_id}/manual")
def get_manual(
    client_id: str,
    ano_mes: str = Query(...),
    user: User = Depends(require_user),
    repo: Repository = Depends(get_repo),
    manual_repo=Depends(get_manual_repo),
) -> dict[str, Any]:
    require_client_access(user, client_id)
    if not _ANO_MES.match(ano_mes):
        raise HTTPException(status_code=422, detail="ano_mes inválido (use YYYY-MM)")
    if repo.get_client(client_id) is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    entries = manual_repo.get_actuals(client_id, ano_mes)
    return {
        "client_id": client_id,
        "ano_mes": ano_mes,
        "areas": list(MANUAL_AREAS),
        "lines": [{"key": k, "label": label} for k, label in MANUAL_LINES],
        "entries": _serialize(entries),
    }


@router.put("/{client_id}/manual")
def put_manual(
    client_id: str,
    payload: dict[str, Any],
    ano_mes: str = Query(...),
    user: User = Depends(require_user),
    repo: Repository = Depends(get_repo),
    manual_repo=Depends(get_manual_repo),
) -> dict[str, Any]:
    require_client_access(user, client_id)
    if not _ANO_MES.match(ano_mes):
        raise HTTPException(status_code=422, detail="ano_mes inválido (use YYYY-MM)")
    if repo.get_client(client_id) is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    raw = payload.get("entries")
    if not isinstance(raw, list):
        raise HTTPException(status_code=422, detail="Corpo inválido: 'entries' ausente")

    entries: list[ManualActual] = []
    for item in raw:
        area = str(item.get("area", ""))
        line_key = str(item.get("line_key", ""))
        if not is_valid_area(area):
            raise HTTPException(status_code=422, detail=f"Área inválida: {area}")
        if not is_valid_line(line_key):
            raise HTTPException(status_code=422, detail=f"Linha inválida: {line_key}")
        try:
            valor = float(item.get("valor", 0.0) or 0.0)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="Valor inválido") from exc
        entries.append(ManualActual(client_id, ano_mes, area, line_key, round(valor, 2)))

    manual_repo.set_actuals(client_id, ano_mes, entries)
    return {"client_id": client_id, "ano_mes": ano_mes, "entries": _serialize(entries)}
