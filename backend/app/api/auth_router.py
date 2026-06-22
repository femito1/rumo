# backend/app/api/auth_router.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api.deps import require_user
from app.api.providers import get_repo, get_settings
from app.auth.passwords import verify_password
from app.auth.tokens import create_access_token
from app.config import Settings
from app.tenancy.models import User
from app.tenancy.repository import Repository

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginIn(BaseModel):
    email: str
    password: str

def _user_public(u: User) -> dict:
    return {"id": u.id, "email": u.email, "role": u.role.value, "client_id": u.client_id}

@router.post("/login")
def login(body: LoginIn, repo: Repository = Depends(get_repo), settings: Settings = Depends(get_settings)) -> dict:
    user = repo.get_user_by_email(body.email)
    if user is None or not user.active or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")
    token = create_access_token(sub=user.id, role=user.role.value, client_id=user.client_id,
                                secret=settings.jwt_secret, ttl_minutes=settings.jwt_ttl_minutes)
    return {"access_token": token, "token_type": "bearer", "user": _user_public(user)}

@router.get("/me")
def me(user: User = Depends(require_user)) -> dict:
    return _user_public(user)
