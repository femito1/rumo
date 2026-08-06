# backend/app/api/users_router.py
"""User + client provisioning.

Client commitment (2026-08-05): RUMO creates clients and users and hands out
logins; a client's own Gestor (``CLIENT_ADMIN``) provisions its team.

There is no mail delivery here, so a created account gets a generated temporary
password which is returned **once**, in the creation response, and never again. The
account carries ``must_change_password`` until the user replaces it.

Nested under ``/api/clients/{client_id}`` like the budget and closing routers — a
literal path such as ``/api/clients/users`` would be swallowed by the
``GET /api/clients/{client_id}`` catch-all.
"""
from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import (
    active_client_or_404,
    assert_may_grant,
    assert_may_manage,
    require_admin,
    require_client_access,
    require_user,
    require_user_manager,
)
from app.api.providers import get_repo
from app.auth.passwords import hash_password, verify_password
from app.auth.provisioning import generate_temp_password
from app.tenancy.models import Role, User
from app.tenancy.repository import Repository

router = APIRouter(prefix="/api", tags=["users"])

#: Deliberately loose — enough to catch a typo, not to adjudicate RFC 5322.
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MIN_PASSWORD_LEN = 8


class CreateUserIn(BaseModel):
    email: str
    role: str


class UpdateUserIn(BaseModel):
    active: bool | None = None


class CreateClientIn(BaseModel):
    id: str
    name: str
    provider: str


class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str


def _user_public(u: User) -> dict:
    """⚠ Never add ``password_hash`` here."""
    return {
        "id": u.id,
        "email": u.email,
        "role": u.role.value,
        "client_id": u.client_id,
        "active": u.active,
        "must_change_password": u.must_change_password,
    }


def _client_public(c) -> dict:
    """⚠ Never add ``provider_config`` — it holds upstream credentials."""
    return {"id": c.id, "name": c.name, "provider": c.provider, "active": c.active}


def _parse_role(raw: str) -> Role:
    try:
        return Role(raw)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Papel inválido: {raw}") from None


def _written(call, detail: str):
    """Run a repository write, turning a storage failure into a PT-BR 422.

    The repo raises ValueError for any failed write (see ``SupabaseRepository._write``).
    Every mutating route goes through here so a database problem can never reach the
    operator as a bare 500 — which is exactly what production did when `/usuarios` was
    used before the role-CHECK migration had been applied.
    """
    try:
        return call()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=detail) from exc


@router.get("/clients/{client_id}/users")
def list_users(
    client_id: str,
    user: User = Depends(require_user_manager),
    repo: Repository = Depends(get_repo),
) -> list[dict]:
    require_client_access(user, client_id)
    active_client_or_404(repo, client_id)
    return [_user_public(u) for u in repo.list_users_for_client(client_id)]


@router.post("/clients/{client_id}/users")
def create_user(
    client_id: str,
    body: CreateUserIn,
    user: User = Depends(require_user_manager),
    repo: Repository = Depends(get_repo),
) -> dict:
    require_client_access(user, client_id)
    active_client_or_404(repo, client_id)
    if not _EMAIL.match(body.email.strip()):
        raise HTTPException(status_code=422, detail="E-mail inválido")
    role = _parse_role(body.role)
    assert_may_grant(user, role)

    email = body.email.strip().lower()
    # Checked here, not inferred from a write failure: reporting every storage error as
    # "E-mail já cadastrado" is what would hide a real problem (e.g. a missing
    # migration) behind a plausible-looking validation message.
    if repo.get_user_by_email(email) is not None:
        raise HTTPException(status_code=422, detail="E-mail já cadastrado")

    temp_password = generate_temp_password()
    created = _written(
        lambda: repo.create_user(
            email=email,
            password_hash=hash_password(temp_password),
            role=role,
            client_id=client_id,
            must_change_password=True,
        ),
        "Não foi possível criar o usuário",
    )
    # The ONLY time the password leaves this process. Not stored, not logged.
    return {**_user_public(created), "temp_password": temp_password}


@router.patch("/clients/{client_id}/users/{user_id}")
def update_user(
    client_id: str,
    user_id: str,
    body: UpdateUserIn,
    user: User = Depends(require_user_manager),
    repo: Repository = Depends(get_repo),
) -> dict:
    require_client_access(user, client_id)
    active_client_or_404(repo, client_id)
    # Resolve the STORED target before deciding anything — see assert_may_manage.
    assert_may_manage(user, repo.get_user_by_id(user_id), client_id)
    if body.active is None:
        raise HTTPException(status_code=422, detail="Nada a alterar")
    updated = _written(
        lambda: repo.set_user_active(user_id, body.active),
        "Não foi possível alterar o usuário",
    )
    if updated is None:  # pragma: no cover - assert_may_manage already resolved it
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return _user_public(updated)


@router.post("/clients/{client_id}/users/{user_id}/reset-password")
def reset_password(
    client_id: str,
    user_id: str,
    user: User = Depends(require_user_manager),
    repo: Repository = Depends(get_repo),
) -> dict:
    """Issue a fresh temporary password (the user forgot theirs before first login).

    ⚠ This body carries no role and no client_id, which is exactly why the guard
    must resolve the stored target: gating on the body would let a Gestor mint a
    working credential for a RUMO admin.
    """
    require_client_access(user, client_id)
    active_client_or_404(repo, client_id)
    target = assert_may_manage(user, repo.get_user_by_id(user_id), client_id)

    temp_password = generate_temp_password()
    # ``must_change_password=True``: a password someone else chose must not stay.
    updated = _written(
        lambda: repo.set_password(
            target.id, hash_password(temp_password), must_change_password=True
        ),
        "Não foi possível gerar uma nova senha",
    )
    if updated is None:  # pragma: no cover - target already resolved
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {**_user_public(updated), "temp_password": temp_password}


@router.post("/clients")
def create_client(
    body: CreateClientIn,
    _: User = Depends(require_admin),
    repo: Repository = Depends(get_repo),
) -> dict:
    """RUMO only: a new tenant. Upstream credentials are NOT set here — they go into
    ``provider_config`` out of band so they never travel through the SPA."""
    slug = body.id.strip().lower()
    if not re.match(r"^[a-z0-9][a-z0-9-]{1,31}$", slug):
        raise HTTPException(
            status_code=422,
            detail="Identificador inválido: use letras minúsculas, números e hífen",
        )
    if not body.name.strip():
        raise HTTPException(status_code=422, detail="Nome obrigatório")
    try:
        created = repo.create_client(
            id=slug, name=body.name.strip(), provider=body.provider.strip()
        )
    except ValueError:
        raise HTTPException(status_code=422, detail="Cliente já existe") from None
    return _client_public(created)


@router.post("/auth/change-password")
def change_password(
    body: ChangePasswordIn,
    user: User = Depends(require_user),
    repo: Repository = Depends(get_repo),
) -> dict:
    """Self-service. Also what clears ``must_change_password`` after a temp password."""
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Senha atual incorreta")
    if len(body.new_password) < MIN_PASSWORD_LEN:
        raise HTTPException(
            status_code=422,
            detail=f"A nova senha precisa de ao menos {MIN_PASSWORD_LEN} caracteres",
        )
    updated = _written(
        lambda: repo.set_password(user.id, hash_password(body.new_password)),
        "Não foi possível alterar a senha",
    )
    if updated is None:  # pragma: no cover - the session already resolved this user
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return _user_public(updated)
