# backend/app/api/deps.py
from __future__ import annotations
from fastapi import Depends, Header, HTTPException
from app.auth.tokens import decode_token, TokenError
from app.config import Settings
from app.tenancy.models import User
from app.tenancy.repository import Repository
from app.api.providers import get_repo, get_settings   # wiring defined in Task 4.2

def require_user(authorization: str | None = Header(default=None),
                 repo: Repository = Depends(get_repo),
                 settings: Settings = Depends(get_settings)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")
    token = authorization.split(" ", 1)[1]
    try:
        claims = decode_token(token, secret=settings.jwt_secret)
    except TokenError:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada")
    user = repo.get_user_by_id(claims["sub"])
    if user is None or not user.active:
        raise HTTPException(status_code=401, detail="Usuário inválido")
    return user

def require_admin(user: User = Depends(require_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")
    return user

def require_client_access(user: User, client_id: str) -> None:
    if not user.can_access_client(client_id):
        raise HTTPException(status_code=403, detail="Sem acesso a este cliente")
    return None
