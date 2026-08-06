# backend/app/api/deps.py
from __future__ import annotations
from fastapi import Depends, Header, HTTPException
from app.auth.tokens import decode_token, TokenError
from app.config import Settings
from app.tenancy.models import Client, User
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
    # A deactivated CLIENT must lose access immediately, not when its JWT expires
    # (TTL is 720 min by default). Checked HERE rather than per-route so it covers
    # every endpoint — including user provisioning, where a dead tenant's manager
    # could otherwise keep creating logins. An ADMIN has no client_id and is
    # deliberately exempt: deactivating a tenant must not lock out the only people
    # who can reverse it.
    if user.client_id is not None:
        client = repo.get_client(user.client_id)
        if client is None or not client.active:
            raise HTTPException(status_code=403, detail="Cliente inativo")
    return user

def require_admin(user: User = Depends(require_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")
    return user

def require_client_access(user: User, client_id: str) -> None:
    if not user.can_access_client(client_id):
        raise HTTPException(status_code=403, detail="Sem acesso a este cliente")
    return None


def active_client_or_404(repo: Repository, client_id: str) -> Client:
    """The client, or 404 if it is missing OR deactivated.

    An inactive client must read as ABSENT, not as forbidden: ``list_clients()``
    already filters it out, so a route that still served it by direct URL was
    leaking a client RUMO had chosen to hide. Every route that resolves a
    ``{client_id}`` path segment goes through here so the two cannot drift apart.
    """
    client = repo.get_client(client_id)
    if client is None or not client.active:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client
