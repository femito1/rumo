# backend/app/api/closing_router.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import require_user, require_client_access
from app.api.providers import get_repo
from app.closing.available import is_closeable
from app.closing.period import Period
from app.closing.provider import build_provider_for
from app.sources.base import DayRange
from app.tenancy.models import User
from app.tenancy.repository import Repository

router = APIRouter(prefix="/api/clients", tags=["closing"])

@router.get("/{client_id}/closing")
def get_closing(
    client_id: str,
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    from_: int | None = Query(default=None, alias="from", ge=1, le=31),
    to: int | None = Query(default=None, ge=1, le=31),
    user: User = Depends(require_user),
    repo: Repository = Depends(get_repo),
) -> dict:
    require_client_access(user, client_id)
    client = repo.get_client(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    if not is_closeable(month):
        raise HTTPException(status_code=422, detail="Mês ainda em aberto ou no futuro")
    period = Period.parse(month)
    if from_ is not None and to is not None:
        last = period.days_in_month
        if from_ > to:
            raise HTTPException(status_code=422, detail="Intervalo de dias inválido")
        if from_ > last or to > last:
            raise HTTPException(
                status_code=422,
                detail=f"{period.label} tem {last} dias; informe dias entre 1 e {last}.",
            )
        day_range = DayRange.within(period, from_day=from_, to_day=to)
    else:
        day_range = DayRange.full_month(period)
    provider = build_provider_for(client)
    return provider.build_closing(client=client, period=period, day_range=day_range)
