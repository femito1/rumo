# backend/tests/test_deps.py
import pytest
from fastapi import HTTPException
from app.api.deps import require_user, require_admin, require_client_access
from app.auth.tokens import create_access_token
from app.config import Settings
from app.tenancy.models import User, Role
from tests.fakes import FakeRepository

SECRET = "t"

def _user(repo, email):
    return repo.get_user_by_email(email)

def _settings():
    return Settings(jwt_secret=SECRET, jwt_ttl_minutes=60, cors_origins=["*"], supabase_url="", supabase_service_key="")

def test_require_user_rejects_missing_token():
    repo = FakeRepository.seeded()
    with pytest.raises(HTTPException) as e:
        require_user(authorization=None, repo=repo, settings=_settings())
    assert e.value.status_code == 401

def test_require_user_returns_user_for_valid_token():
    repo = FakeRepository.seeded()
    u = _user(repo, "admin@rumo.com.br")
    tok = create_access_token(sub=u.id, role=u.role.value, client_id=u.client_id, secret=SECRET, ttl_minutes=60)
    got = require_user(authorization=f"Bearer {tok}", repo=repo, settings=_settings())
    assert got.id == u.id

def test_require_admin_rejects_client():
    repo = FakeRepository.seeded()
    client_user = _user(repo, "financeiro@mbclaw.com.br")
    with pytest.raises(HTTPException) as e:
        require_admin(client_user)
    assert e.value.status_code == 403

def test_require_client_access_blocks_other_client():
    repo = FakeRepository.seeded()
    client_user = _user(repo, "financeiro@mbclaw.com.br")  # client_id = mbc
    with pytest.raises(HTTPException) as e:
        require_client_access(client_user, "demo")
    assert e.value.status_code == 403
    assert require_client_access(client_user, "mbc") is None
