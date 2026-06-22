# RUMO Multi-Client Closing Platform — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the single-tenant MBC closing dashboard into a production-grade multi-tenant product where RUMO (ADMIN) sees all clients and each client sees only its own monthly closing, with an in-UI month picker + optional day-range filter.

**Architecture:** FastAPI backend (reusing the verified `mbc_automation` data logic behind a Source/ClosingProvider layer) + React/TypeScript (Vite) SPA. Supabase Postgres for `users`/`clients` via `supabase-py`; our own argon2 + JWT auth. Dockerized, deployed on EasyPanel.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, httpx/requests, passlib[argon2], pyjwt, supabase-py, pytest, ruff, mypy. React 18, TypeScript, Vite, React Router, vitest + React Testing Library, ESLint, Prettier.

**Reference spec:** `docs/superpowers/specs/2026-06-21-rumo-multi-client-platform-design.md`

---

## Conventions for every task

- **TDD:** write the failing test, run it (confirm the expected failure), write minimal code, run it (confirm pass), commit.
- **Commits:** conventional messages (`feat:`, `test:`, `chore:`, `docs:`), one per completed task unless noted.
- **Secrets:** never commit real secrets. Use `.env` (gitignored) + committed `.env.example`.
- **Run backend tests from `backend/`:** `pytest -q`. Run frontend tests from `frontend/`: `npm test`.
- **PT-BR:** all user-facing strings in Brazilian Portuguese.

---

## Phase 0 — Repository restructure & backend scaffold

### Task 0.1: Create backend package skeleton

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/.env.example`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_health.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_returns_ok():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_health.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'`.

- [ ] **Step 3: Write minimal implementation**

```toml
# backend/pyproject.toml
[project]
name = "rumo-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.110",
  "uvicorn[standard]>=0.29",
  "requests>=2.31",
  "passlib[argon2]>=1.7.4",
  "pyjwt>=2.8",
  "supabase>=2.4",
  "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8", "httpx>=0.27", "ruff>=0.4", "mypy>=1.10"]

[tool.ruff]
line-length = 100

[tool.pytest.ini_options]
pythonpath = ["."]
```

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="RUMO Closing Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # narrowed via env in Task 8.x
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

```python
# backend/app/__init__.py
# (empty)
```

```python
# backend/tests/__init__.py
# (empty)
```

```bash
# backend/.env.example
JWT_SECRET=change-me-in-prod
JWT_TTL_MINUTES=720
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
LEGALDESK_BASE=https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV
LEGALDESK_USER=integracao
LEGALDESK_PASSWORD=
CORS_ORIGINS=http://localhost:5173
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pip install -e ".[dev]" && pytest tests/test_health.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat: scaffold FastAPI backend with health endpoint"
```

### Task 0.2: Move the verified data logic into the backend (behavior-preserving)

**Files:**
- Create: `backend/app/closing/__init__.py`
- Move: `mbc-automation/backend/mbc_automation/period.py` -> `backend/app/closing/period.py`
- Move: `mbc-automation/backend/mbc_automation/api_client.py` -> `backend/app/sources/legaldesk_client.py`
- Move: `mbc-automation/backend/mbc_automation/builder.py` -> `backend/app/closing/builder.py`
- Move: `mbc-automation/backend/mbc_automation/base_resultado_layout.py` -> `backend/app/closing/base_resultado_layout.py`
- Move: `mbc-automation/backend/mbc_automation/tab_layouts.py` -> `backend/app/closing/tab_layouts.py`
- Create: `backend/app/sources/__init__.py`
- Test: `backend/tests/test_period.py`

- [ ] **Step 1: Write the failing test** (lock the period behavior we depend on)

```python
# backend/tests/test_period.py
from app.closing.period import Period

def test_period_parse_and_labels():
    p = Period.parse("2026-05")
    assert p.ano_mes == "2026-05"
    assert p.label == "Maio 2026"
    assert p.column_letter == "G"
    assert p.date_start == "2026-05-01"
    assert p.date_end == "2026-06-01"

def test_period_december_rolls_year():
    p = Period.parse("2026-12")
    assert p.date_end == "2027-01-01"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_period.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.closing'`.

- [ ] **Step 3: Move the files**

Use `git mv` to preserve history. Update internal imports: in `builder.py`, change
`from .api_client import ...` to `from app.sources.legaldesk_client import LegalDeskClient, to_float`,
and `from .base_resultado_layout import ...` / `from .tab_layouts import ...` to `from app.closing....`.
In `legaldesk_client.py`, replace the import of `.config` with reading settings from a passed-in
object (see Task 1.1 config) — for now, keep a module-level default that reads env via `os.environ`
so the move stays behavior-preserving:

```python
# top of backend/app/sources/legaldesk_client.py (replace the old `from .config import ...`)
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class _LegalDeskSettings:
    api_base: str = os.environ.get("LEGALDESK_BASE", "https://legaldesk.mbclaw.com.br/API/v1/ODataGERALADV").rstrip("/")
    api_user: str = os.environ.get("LEGALDESK_USER", "integracao")
    api_password: str = os.environ.get("LEGALDESK_PASSWORD", "")
    request_timeout: int = int(os.environ.get("LEGALDESK_TIMEOUT", "120"))
    default_top: int = int(os.environ.get("LEGALDESK_TOP", "5000"))

SETTINGS = _LegalDeskSettings()
```

Create empty `backend/app/closing/__init__.py` and `backend/app/sources/__init__.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_period.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/ mbc-automation/
git commit -m "refactor: move verified closing logic into backend/app (behavior-preserving)"
```

## Phase 1 — Config, auth primitives (password + JWT)

### Task 1.1: Settings loaded from env

**Files:**
- Create: `backend/app/config.py`
- Test: `backend/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_config.py
import os
from app.config import Settings

def test_settings_read_from_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "s3cret")
    monkeypatch.setenv("JWT_TTL_MINUTES", "60")
    monkeypatch.setenv("CORS_ORIGINS", "http://a.com,http://b.com")
    s = Settings.from_env()
    assert s.jwt_secret == "s3cret"
    assert s.jwt_ttl_minutes == 60
    assert s.cors_origins == ["http://a.com", "http://b.com"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.config'`.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/config.py
from __future__ import annotations
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    jwt_secret: str
    jwt_ttl_minutes: int
    cors_origins: list[str]
    supabase_url: str
    supabase_service_key: str

    @classmethod
    def from_env(cls) -> "Settings":
        origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
        return cls(
            jwt_secret=os.environ.get("JWT_SECRET", "dev-insecure-secret"),
            jwt_ttl_minutes=int(os.environ.get("JWT_TTL_MINUTES", "720")),
            cors_origins=[o.strip() for o in origins.split(",") if o.strip()],
            supabase_url=os.environ.get("SUPABASE_URL", ""),
            supabase_service_key=os.environ.get("SUPABASE_SERVICE_KEY", ""),
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_config.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/tests/test_config.py
git commit -m "feat: env-driven Settings"
```

### Task 1.2: Password hashing

**Files:**
- Create: `backend/app/auth/__init__.py`
- Create: `backend/app/auth/passwords.py`
- Test: `backend/tests/test_passwords.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_passwords.py
from app.auth.passwords import hash_password, verify_password

def test_hash_and_verify_roundtrip():
    h = hash_password("correct horse")
    assert h != "correct horse"
    assert verify_password("correct horse", h) is True

def test_verify_rejects_wrong_password():
    h = hash_password("correct horse")
    assert verify_password("battery staple", h) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_passwords.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.auth.passwords'`.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/auth/passwords.py
from __future__ import annotations
from passlib.context import CryptContext

_ctx = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(plain: str) -> str:
    return _ctx.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ctx.verify(plain, hashed)
    except ValueError:
        return False
```

```python
# backend/app/auth/__init__.py
# (empty)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_passwords.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/auth/ backend/tests/test_passwords.py
git commit -m "feat: argon2 password hashing"
```

### Task 1.3: JWT issue/verify

**Files:**
- Create: `backend/app/auth/tokens.py`
- Test: `backend/tests/test_tokens.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_tokens.py
import time
import pytest
from app.auth.tokens import create_access_token, decode_token, TokenError

SECRET = "unit-secret"

def test_roundtrip_carries_claims():
    tok = create_access_token(sub="u1", role="ADMIN", client_id=None, secret=SECRET, ttl_minutes=60)
    claims = decode_token(tok, secret=SECRET)
    assert claims["sub"] == "u1"
    assert claims["role"] == "ADMIN"
    assert claims["client_id"] is None

def test_expired_token_rejected():
    tok = create_access_token(sub="u1", role="CLIENT", client_id="mbc", secret=SECRET, ttl_minutes=-1)
    with pytest.raises(TokenError):
        decode_token(tok, secret=SECRET)

def test_wrong_secret_rejected():
    tok = create_access_token(sub="u1", role="CLIENT", client_id="mbc", secret=SECRET, ttl_minutes=60)
    with pytest.raises(TokenError):
        decode_token(tok, secret="other")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_tokens.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.auth.tokens'`.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/auth/tokens.py
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import jwt

class TokenError(Exception):
    pass

def create_access_token(*, sub: str, role: str, client_id: str | None,
                         secret: str, ttl_minutes: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "client_id": client_id,
        "iat": now,
        "exp": now + timedelta(minutes=ttl_minutes),
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def decode_token(token: str, *, secret: str) -> dict:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_tokens.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/auth/tokens.py backend/tests/test_tokens.py
git commit -m "feat: JWT issue/verify"
```

## Phase 2 — Tenancy: models, repository, and a fake repo for tests

We keep DB access behind a small repository interface so tests use an in-memory fake and
production uses `supabase-py`. This isolates the security/auth logic from the network.

### Task 2.1: Domain models (User, Client) and the repository protocol

**Files:**
- Create: `backend/app/tenancy/__init__.py`
- Create: `backend/app/tenancy/models.py`
- Create: `backend/app/tenancy/repository.py`
- Test: `backend/tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_models.py
from app.tenancy.models import User, Client, Role

def test_admin_user_has_no_client():
    u = User(id="u1", email="admin@rumo.com.br", password_hash="x", role=Role.ADMIN, client_id=None, active=True)
    assert u.is_admin is True
    assert u.can_access_client("mbc") is True  # admin can access any

def test_client_user_scoped_to_own_client():
    u = User(id="u2", email="fin@mbc", password_hash="x", role=Role.CLIENT, client_id="mbc", active=True)
    assert u.is_admin is False
    assert u.can_access_client("mbc") is True
    assert u.can_access_client("demo") is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.tenancy.models'`.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/tenancy/models.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class Role(str, Enum):
    ADMIN = "ADMIN"
    CLIENT = "CLIENT"

@dataclass(frozen=True)
class Client:
    id: str
    name: str
    provider: str
    provider_config: dict
    active: bool = True

@dataclass(frozen=True)
class User:
    id: str
    email: str
    password_hash: str
    role: Role
    client_id: str | None
    active: bool = True

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    def can_access_client(self, client_id: str) -> bool:
        if self.is_admin:
            return True
        return self.client_id == client_id
```

```python
# backend/app/tenancy/repository.py
from __future__ import annotations
from typing import Protocol
from app.tenancy.models import User, Client

class Repository(Protocol):
    def get_user_by_email(self, email: str) -> User | None: ...
    def get_user_by_id(self, user_id: str) -> User | None: ...
    def list_clients(self) -> list[Client]: ...
    def get_client(self, client_id: str) -> Client | None: ...
```

```python
# backend/app/tenancy/__init__.py
# (empty)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/tenancy/ backend/tests/test_models.py
git commit -m "feat: tenancy models + repository protocol"
```

### Task 2.2: In-memory fake repository (test double used across the suite)

**Files:**
- Create: `backend/tests/fakes.py`
- Test: `backend/tests/test_fake_repo.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_fake_repo.py
from tests.fakes import FakeRepository
from app.tenancy.models import Role

def test_fake_repo_lookup():
    repo = FakeRepository.seeded()
    admin = repo.get_user_by_email("admin@rumo.com.br")
    assert admin is not None and admin.role == Role.ADMIN
    assert repo.get_client("mbc").name == "MBC"
    assert {c.id for c in repo.list_clients()} == {"mbc", "demo"}
    assert repo.get_user_by_email("nobody@x") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_fake_repo.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'tests.fakes'`.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/tests/fakes.py
from __future__ import annotations
from app.tenancy.models import User, Client, Role
from app.auth.passwords import hash_password

class FakeRepository:
    def __init__(self, users: list[User], clients: list[Client]) -> None:
        self._users = {u.email: u for u in users}
        self._users_by_id = {u.id: u for u in users}
        self._clients = {c.id: c for c in clients}

    @classmethod
    def seeded(cls) -> "FakeRepository":
        clients = [
            Client(id="mbc", name="MBC", provider="legaldesk", provider_config={}),
            Client(id="demo", name="Cliente Demonstração", provider="fixture", provider_config={}),
        ]
        users = [
            User(id="u-admin", email="admin@rumo.com.br", password_hash=hash_password("admin123"), role=Role.ADMIN, client_id=None),
            User(id="u-mbc", email="financeiro@mbclaw.com.br", password_hash=hash_password("mbc123"), role=Role.CLIENT, client_id="mbc"),
            User(id="u-demo", email="demo@cliente.com.br", password_hash=hash_password("demo123"), role=Role.CLIENT, client_id="demo"),
        ]
        return cls(users, clients)

    def get_user_by_email(self, email: str) -> User | None:
        return self._users.get(email)

    def get_user_by_id(self, user_id: str) -> User | None:
        return self._users_by_id.get(user_id)

    def list_clients(self) -> list[Client]:
        return [c for c in self._clients.values() if c.active]

    def get_client(self, client_id: str) -> Client | None:
        return self._clients.get(client_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_fake_repo.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/fakes.py backend/tests/test_fake_repo.py
git commit -m "test: in-memory fake repository"
```

### Task 2.3: Supabase-backed repository (production implementation)

**Files:**
- Create: `backend/app/tenancy/supabase_repository.py`
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/schema.sql`
- Test: `backend/tests/test_supabase_repo_mapping.py`

> Network calls are NOT made in tests. We test the row->model mapping with a stub client.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_supabase_repo_mapping.py
from app.tenancy.supabase_repository import row_to_user, row_to_client
from app.tenancy.models import Role

def test_row_to_user_maps_fields():
    row = {"id": "u1", "email": "a@b", "password_hash": "h", "role": "ADMIN", "client_id": None, "active": True}
    u = row_to_user(row)
    assert u.role == Role.ADMIN and u.client_id is None

def test_row_to_client_maps_fields():
    row = {"id": "mbc", "name": "MBC", "provider": "legaldesk", "provider_config": {}, "active": True}
    c = row_to_client(row)
    assert c.id == "mbc" and c.provider == "legaldesk"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_supabase_repo_mapping.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/tenancy/supabase_repository.py
from __future__ import annotations
from app.tenancy.models import User, Client, Role

def row_to_user(row: dict) -> User:
    return User(
        id=str(row["id"]), email=row["email"], password_hash=row["password_hash"],
        role=Role(row["role"]), client_id=row.get("client_id"), active=row.get("active", True),
    )

def row_to_client(row: dict) -> Client:
    return Client(
        id=row["id"], name=row["name"], provider=row["provider"],
        provider_config=row.get("provider_config") or {}, active=row.get("active", True),
    )

class SupabaseRepository:
    """Production repository backed by supabase-py. Constructed with a supabase client."""
    def __init__(self, client) -> None:
        self._c = client

    def get_user_by_email(self, email: str) -> User | None:
        res = self._c.table("users").select("*").eq("email", email).limit(1).execute()
        rows = res.data or []
        return row_to_user(rows[0]) if rows else None

    def get_user_by_id(self, user_id: str) -> User | None:
        res = self._c.table("users").select("*").eq("id", user_id).limit(1).execute()
        rows = res.data or []
        return row_to_user(rows[0]) if rows else None

    def list_clients(self) -> list[Client]:
        res = self._c.table("clients").select("*").eq("active", True).execute()
        return [row_to_client(r) for r in (res.data or [])]

    def get_client(self, client_id: str) -> Client | None:
        res = self._c.table("clients").select("*").eq("id", client_id).limit(1).execute()
        rows = res.data or []
        return row_to_client(rows[0]) if rows else None
```

```sql
-- backend/app/db/schema.sql
create table if not exists clients (
  id text primary key,
  name text not null,
  provider text not null,
  provider_config jsonb not null default '{}'::jsonb,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  password_hash text not null,
  role text not null check (role in ('ADMIN','CLIENT')),
  client_id text references clients(id),
  active boolean not null default true,
  created_at timestamptz not null default now()
);
```

```python
# backend/app/db/__init__.py
# (empty)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_supabase_repo_mapping.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/tenancy/supabase_repository.py backend/app/db/ backend/tests/test_supabase_repo_mapping.py
git commit -m "feat: supabase-backed repository + schema.sql"
```

## Phase 3 — Data layer: Sources, SectionKey, ClosingProvider

### Task 3.1: SectionKey enum + Source protocol + DayRange

**Files:**
- Create: `backend/app/sources/base.py`
- Test: `backend/tests/test_sources_base.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_sources_base.py
from app.sources.base import SectionKey, DayRange
from app.closing.period import Period

def test_sectionkey_has_the_fifteen_tabs():
    # one SectionKey per workbook tab
    assert SectionKey.META in SectionKey
    assert SectionKey.BASE_RESULTADO in SectionKey
    assert len(list(SectionKey)) == 15

def test_dayrange_full_month_from_period():
    p = Period.parse("2026-05")
    dr = DayRange.full_month(p)
    assert dr.start == "2026-05-01"
    assert dr.end == "2026-06-01"
    assert dr.is_full_month is True

def test_dayrange_partial_within_month():
    p = Period.parse("2026-05")
    dr = DayRange.within(p, from_day=1, to_day=15)
    assert dr.start == "2026-05-01"
    assert dr.end == "2026-05-16"   # end-exclusive
    assert dr.is_full_month is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_sources_base.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.sources.base'`.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/sources/base.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from app.closing.period import Period

class SectionKey(str, Enum):
    META = "meta"
    BASE_RESULTADO = "base_resultado"
    AREAS_SINTETICO = "areas_sintetico"
    RESUMO_RECEBIDAS = "resumo_recebidas"
    FATURAS_CENTRO_CUSTO = "faturas_centro_custo"
    DRE_2026 = "dre_2026"
    ORCAMENTO_2026 = "orcamento_2026"
    INSTITUCIONAL = "institucional"
    INSTITUCIONAL_ANO = "institucional_ano"
    CONTENCIOSO = "contencioso"
    ECONOMICO = "economico"
    ARBITRAGEM = "arbitragem"
    RATEIO_MENSAL = "rateio_mensal"
    FLUXO_CONSOLIDADO = "fluxo_consolidado"
    AMORTIZACAO = "amortizacao"

@dataclass(frozen=True)
class DayRange:
    start: str          # ISO date inclusive lower bound
    end: str            # ISO date exclusive upper bound
    is_full_month: bool

    @classmethod
    def full_month(cls, period: Period) -> "DayRange":
        return cls(start=period.date_start, end=period.date_end, is_full_month=True)

    @classmethod
    def within(cls, period: Period, *, from_day: int, to_day: int) -> "DayRange":
        start = f"{period.year:04d}-{period.month:02d}-{from_day:02d}"
        # end-exclusive: day after to_day
        end_day = to_day + 1
        end = f"{period.year:04d}-{period.month:02d}-{end_day:02d}"
        return cls(start=start, end=end, is_full_month=False)

# SectionData is the raw per-section structure a Source emits (shape defined per section).
SectionData = dict

class Source(Protocol):
    name: str
    def supports(self) -> set[SectionKey]: ...
    def fetch(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]: ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_sources_base.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/sources/base.py backend/tests/test_sources_base.py
git commit -m "feat: SectionKey, DayRange, Source protocol"
```

### Task 3.2: FixtureSource (minimal demo client)

**Files:**
- Create: `backend/app/sources/fixture.py`
- Test: `backend/tests/test_fixture_source.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_fixture_source.py
from app.sources.fixture import FixtureSource
from app.sources.base import SectionKey, DayRange
from app.closing.period import Period

def test_fixture_is_deterministic_and_minimal():
    src = FixtureSource()
    p = Period.parse("2026-05")
    dr = DayRange.full_month(p)
    a = src.fetch(p, dr)
    b = src.fetch(p, dr)
    assert a == b                                   # deterministic
    assert SectionKey.META in src.supports()
    assert SectionKey.META in a
    # minimal: meta carries the two headline KPIs as numbers
    assert a[SectionKey.META]["kpis"]["receita_honorarios"] >= 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_fixture_source.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/sources/fixture.py
from __future__ import annotations
from app.sources.base import SectionKey, DayRange, SectionData
from app.closing.period import Period

class FixtureSource:
    """Minimal, deterministic placeholder data for the demo client.

    Exists only to demonstrate the admin multi-client view. NOT real data.
    """
    name = "fixture"

    def supports(self) -> set[SectionKey]:
        return {SectionKey.META, SectionKey.BASE_RESULTADO}

    def fetch(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        # Stable token numbers derived from the month so it looks alive but is fake.
        seed = period.month * 1000
        receita = float(120000 + seed)
        faturamento = float(180000 + seed)
        return {
            SectionKey.META: {
                "kpis": {
                    "receita_honorarios": receita,
                    "faturamento_realizado": faturamento,
                    "faturas_emitidas": 5 + period.month,
                },
            },
            SectionKey.BASE_RESULTADO: {
                "lines": [
                    {"row": 4, "label": "Receita de honorários", "value": receita, "origin": "fixture", "indent": 0, "is_total": False},
                ],
            },
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_fixture_source.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/sources/fixture.py backend/tests/test_fixture_source.py
git commit -m "feat: FixtureSource (minimal demo data)"
```

### Task 3.3: JuritisSource placeholder (documented, not wired)

**Files:**
- Create: `backend/app/sources/juritis.py`
- Test: `backend/tests/test_juritis_placeholder.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_juritis_placeholder.py
import pytest
from app.sources.juritis import JuritisSource
from app.closing.period import Period
from app.sources.base import DayRange

def test_juritis_supports_nothing_yet():
    assert JuritisSource().supports() == set()

def test_juritis_fetch_not_implemented():
    src = JuritisSource()
    with pytest.raises(NotImplementedError):
        src.fetch(Period.parse("2026-05"), DayRange.full_month(Period.parse("2026-05")))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_juritis_placeholder.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/sources/juritis.py
from __future__ import annotations
from app.sources.base import SectionKey, DayRange, SectionData
from app.closing.period import Period

class JuritisSource:
    """PLACEHOLDER for the Juritis / TOTVS Backoffice API (not yet accessible).

    When credentials arrive, implement `supports()` to return the institutional-expense
    SectionKeys it can fill and `fetch()` to emit them. Three integration paths are
    documented in docs/superpowers/specs/2026-06-21-rumo-multi-client-platform-design.md §4:
    additive, partial override, or full replacement. Do NOT guess the API shape until we
    have access.
    """
    name = "juritis"

    def supports(self) -> set[SectionKey]:
        return set()

    def fetch(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        raise NotImplementedError("JuritisSource is not wired yet (no API access).")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_juritis_placeholder.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/sources/juritis.py backend/tests/test_juritis_placeholder.py
git commit -m "feat: JuritisSource placeholder (documented, not wired)"
```

### Task 3.4: LegalDeskSource wrapping the verified builder (offline fixture test)

**Files:**
- Create: `backend/app/sources/legaldesk.py`
- Create: `backend/tests/fixtures/README.md`
- Create: `backend/tests/fixtures/legaldesk_2026_05.json` (recorded — see Step 0)
- Test: `backend/tests/test_legaldesk_source.py`

> **Step 0 (one-time fixture capture, run by a human with creds):** with `LEGALDESK_PASSWORD`
> set, capture the verified month's payload so tests run offline:
> `cd backend && python -c "from app.closing.builder import build_payload; from app.closing.period import Period; from app.sources.legaldesk_client import LegalDeskClient; import json; print(json.dumps(build_payload(Period.parse('2026-05'), LegalDeskClient())))" > tests/fixtures/legaldesk_2026_05.json`
> If creds are unavailable at plan-execution time, reuse the existing prior build at
> `mbc-automation/data/data.json` (a real 2026-05 payload) by copying it to the fixture path.
> The fixture is committed so CI is offline and the verified totals are locked.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_legaldesk_source.py
import json
from pathlib import Path
import pytest
from app.sources.legaldesk import LegalDeskSource
from app.sources.base import SectionKey, DayRange
from app.closing.period import Period

FIXTURE = Path(__file__).parent / "fixtures" / "legaldesk_2026_05.json"

@pytest.fixture
def recorded_payload() -> dict:
    return json.loads(FIXTURE.read_text())

def test_legaldesk_emits_rich_sections_from_recorded_payload(recorded_payload):
    src = LegalDeskSource.from_recorded_payload(recorded_payload)
    p = Period.parse("2026-05")
    out = src.fetch(p, DayRange.full_month(p))
    assert SectionKey.META in out
    assert SectionKey.BASE_RESULTADO in out

def test_legaldesk_verified_totals_locked(recorded_payload):
    # The sacred numbers from the build guide must never silently regress.
    kpis = recorded_payload["kpis"]
    assert abs(kpis["receita_honorarios"] - 415927.84) <= 0.05
    assert abs(kpis["faturamento_realizado"] - 719988.05) <= 0.05
    assert kpis["faturas_emitidas"] == 53
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_legaldesk_source.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.sources.legaldesk'`.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/sources/legaldesk.py
from __future__ import annotations
from app.sources.base import SectionKey, DayRange, SectionData
from app.sources.legaldesk_client import LegalDeskClient
from app.closing.builder import build_payload
from app.closing.period import Period

# All 15 SectionKeys are produced by the existing builder payload.
_ALL = set(SectionKey)

class LegalDeskSource:
    """Wraps the verified LegalDeskClient + build_payload behind the Source interface.

    `build_payload` already returns the full tab structure; this source adapts that into
    the SectionKey-keyed dict the ClosingProvider consumes. Behavior of the underlying
    numbers is unchanged and locked by recorded-fixture tests.
    """
    name = "legaldesk"

    def __init__(self, client: LegalDeskClient | None = None, *, _recorded: dict | None = None) -> None:
        self._client = client
        self._recorded = _recorded

    @classmethod
    def from_recorded_payload(cls, payload: dict) -> "LegalDeskSource":
        return cls(_recorded=payload)

    def supports(self) -> set[SectionKey]:
        return set(_ALL)

    def fetch(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        payload = self._recorded if self._recorded is not None else build_payload(period, self._client)
        tabs = payload["tabs"]
        out: dict[SectionKey, SectionData] = {}
        for key in SectionKey:
            if key.value in tabs:
                out[key] = tabs[key.value]
        # Carry KPIs alongside META so the provider can assemble headline numbers.
        out[SectionKey.META] = {**out.get(SectionKey.META, {}), "kpis": payload.get("kpis", {})}
        return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_legaldesk_source.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/sources/legaldesk.py backend/tests/test_legaldesk_source.py backend/tests/fixtures/
git commit -m "feat: LegalDeskSource wrapping verified builder + locked-totals fixture test"
```

### Task 3.5: ClosingProvider composes sources into the ClosingPayload

**Files:**
- Create: `backend/app/closing/provider.py`
- Test: `backend/tests/test_closing_provider.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_closing_provider.py
from app.closing.provider import ClosingProvider, build_provider_for
from app.closing.period import Period
from app.sources.base import SectionKey, DayRange, Source, SectionData
from app.sources.fixture import FixtureSource
from app.tenancy.models import Client

def test_provider_builds_payload_shape():
    p = Period.parse("2026-05")
    provider = ClosingProvider(sources=[FixtureSource()])
    payload = provider.build_closing(client=Client(id="demo", name="Cliente Demonstração", provider="fixture", provider_config={}), period=p, day_range=DayRange.full_month(p))
    assert payload["client"] == {"id": "demo", "name": "Cliente Demonstração"}
    assert payload["period"]["ano_mes"] == "2026-05"
    assert payload["period"]["label"] == "Maio 2026"
    assert payload["day_range"]["is_full_month"] is True
    assert "kpis" in payload and "tabs" in payload and "tab_order" in payload

def test_merge_later_source_overrides_earlier_for_same_section():
    class A:
        name = "a"
        def supports(self): return {SectionKey.META}
        def fetch(self, period, day_range): return {SectionKey.META: {"kpis": {"x": 1}}}
    class B:
        name = "b"
        def supports(self): return {SectionKey.META}
        def fetch(self, period, day_range): return {SectionKey.META: {"kpis": {"x": 2}}}
    p = Period.parse("2026-05")
    provider = ClosingProvider(sources=[A(), B()])  # B later -> wins
    payload = provider.build_closing(client=Client(id="t", name="T", provider="x", provider_config={}), period=p, day_range=DayRange.full_month(p))
    assert payload["kpis"]["x"] == 2

def test_build_provider_for_maps_client_to_sources():
    mbc = Client(id="mbc", name="MBC", provider="legaldesk", provider_config={})
    demo = Client(id="demo", name="Cliente Demonstração", provider="fixture", provider_config={})
    assert build_provider_for(mbc).sources[0].name == "legaldesk"
    assert build_provider_for(demo).sources[0].name == "fixture"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_closing_provider.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.closing.provider'`.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/closing/provider.py
from __future__ import annotations
from datetime import datetime, timezone
from app.closing.period import Period
from app.closing.tab_layouts import TAB_ORDER
from app.sources.base import SectionKey, DayRange, Source, SectionData
from app.sources.fixture import FixtureSource
from app.sources.legaldesk import LegalDeskSource
from app.tenancy.models import Client

class ClosingProvider:
    def __init__(self, sources: list[Source]) -> None:
        self.sources = sources

    def _merge(self, period: Period, day_range: DayRange) -> dict[SectionKey, SectionData]:
        merged: dict[SectionKey, SectionData] = {}
        for src in self.sources:                       # ordered; later overrides earlier
            for key, data in src.fetch(period, day_range).items():
                merged[key] = data
        return merged

    def build_closing(self, *, client: Client, period: Period, day_range: DayRange) -> dict:
        sections = self._merge(period, day_range)
        meta_kpis = sections.get(SectionKey.META, {}).get("kpis", {})
        tabs = {k.value: v for k, v in sections.items()}
        return {
            "client": {"id": client.id, "name": client.name},
            "period": {"ano_mes": period.ano_mes, "label": period.label, "column_letter": period.column_letter},
            "day_range": {"from": day_range.start, "to": day_range.end, "is_full_month": day_range.is_full_month},
            "kpis": meta_kpis,
            "tab_order": [t for t in TAB_ORDER if t in tabs] or list(tabs.keys()),
            "tabs": tabs,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

def build_provider_for(client: Client) -> ClosingProvider:
    """Resolve a client's `provider` column to an ordered list of Sources (spec §4)."""
    if client.provider == "legaldesk":
        return ClosingProvider(sources=[LegalDeskSource()])
    if client.provider == "fixture":
        return ClosingProvider(sources=[FixtureSource()])
    raise ValueError(f"unknown provider: {client.provider}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_closing_provider.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/closing/provider.py backend/tests/test_closing_provider.py
git commit -m "feat: ClosingProvider composes sources into payload + per-client resolution"
```

## Phase 4 — API layer: dependencies, auth, clients, closing

### Task 4.1: Auth dependencies (current user + role/tenancy guards)

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/deps.py`
- Test: `backend/tests/test_deps.py`

- [ ] **Step 1: Write the failing test**

```python
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
    # own client is allowed
    assert require_client_access(client_user, "mbc") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_deps.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.api.deps'`.

- [ ] **Step 3: Write minimal implementation**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_deps.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/ backend/tests/test_deps.py
git commit -m "feat: auth dependencies (user/admin/client-access guards)"
```

### Task 4.2: Dependency wiring (repo + settings providers, overridable in tests)

**Files:**
- Create: `backend/app/api/providers.py`
- Test: `backend/tests/conftest.py` (wires the FastAPI app to the FakeRepository)

- [ ] **Step 1: Write the failing test** (a conftest that builds a TestClient with fakes)

```python
# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api import providers
from app.config import Settings
from tests.fakes import FakeRepository

TEST_SECRET = "test-secret"

@pytest.fixture
def repo():
    return FakeRepository.seeded()

@pytest.fixture
def client(repo):
    app.dependency_overrides[providers.get_repo] = lambda: repo
    app.dependency_overrides[providers.get_settings] = lambda: Settings(
        jwt_secret=TEST_SECRET, jwt_ttl_minutes=60, cors_origins=["*"],
        supabase_url="", supabase_service_key="",
    )
    yield TestClient(app)
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_deps.py -v`
Expected: FAIL — `ImportError: cannot import name 'get_repo' from 'app.api.providers'`.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/api/providers.py
from __future__ import annotations
from functools import lru_cache
from app.config import Settings
from app.tenancy.repository import Repository

@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()

@lru_cache
def _build_supabase_repo() -> Repository:
    from supabase import create_client
    from app.tenancy.supabase_repository import SupabaseRepository
    s = get_settings()
    return SupabaseRepository(create_client(s.supabase_url, s.supabase_service_key))

def get_repo() -> Repository:
    return _build_supabase_repo()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_deps.py -v`
Expected: PASS (deps tests import cleanly; network repo is never constructed in tests because of the override).

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/providers.py backend/tests/conftest.py
git commit -m "feat: dependency wiring (settings + repo) overridable in tests"
```

### Task 4.3: Login + /auth/me

**Files:**
- Create: `backend/app/api/auth_router.py`
- Modify: `backend/app/main.py` (include router)
- Test: `backend/tests/test_auth_api.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_auth_api.py
def test_login_success_returns_token_and_user(client):
    resp = client.post("/api/auth/login", json={"email": "admin@rumo.com.br", "password": "admin123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["user"]["role"] == "ADMIN"
    assert body["user"]["client_id"] is None

def test_login_wrong_password_401(client):
    resp = client.post("/api/auth/login", json={"email": "admin@rumo.com.br", "password": "nope"})
    assert resp.status_code == 401

def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401

def test_me_returns_current_user(client):
    tok = client.post("/api/auth/login", json={"email": "financeiro@mbclaw.com.br", "password": "mbc123"}).json()["access_token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200
    assert resp.json()["client_id"] == "mbc"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_auth_api.py -v`
Expected: FAIL — 404 on `/api/auth/login` (router not mounted).

- [ ] **Step 3: Write minimal implementation**

```python
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
```

```python
# add to backend/app/main.py (after app/middleware setup)
from app.api.auth_router import router as auth_router
app.include_router(auth_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_auth_api.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/auth_router.py backend/app/main.py backend/tests/test_auth_api.py
git commit -m "feat: login + /auth/me endpoints"
```

### Task 4.4: Clients list + client detail (admin / owning client)

**Files:**
- Create: `backend/app/api/clients_router.py`
- Modify: `backend/app/main.py` (include router)
- Test: `backend/tests/test_clients_api.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_clients_api.py
def _token(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password}).json()["access_token"]

def test_admin_lists_all_clients(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.get("/api/clients", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200
    ids = {c["id"] for c in resp.json()}
    assert ids == {"mbc", "demo"}

def test_client_user_cannot_list_clients(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    resp = client.get("/api/clients", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 403

def test_client_detail_allows_own(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    resp = client.get("/api/clients/mbc", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == "mbc"
    assert "available_months" in resp.json()

def test_client_detail_blocks_other(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")
    resp = client.get("/api/clients/demo", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_clients_api.py -v`
Expected: FAIL — 404 (router not mounted).

- [ ] **Step 3: Write minimal implementation**

```python
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
```

```python
# add to backend/app/main.py
from app.api.clients_router import router as clients_router
app.include_router(clients_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_clients_api.py -v`
Expected: FAIL — `ModuleNotFoundError: app.closing.available`. Create it (Task 4.5 below) then PASS. (Implement Task 4.5 first if executing strictly in order.)

- [ ] **Step 5: Commit** (after 4.5 green)

```bash
git add backend/app/api/clients_router.py backend/app/main.py backend/tests/test_clients_api.py
git commit -m "feat: clients list + detail with tenancy guards"
```

### Task 4.5: Available (closed) months helper

**Files:**
- Create: `backend/app/closing/available.py`
- Test: `backend/tests/test_available.py`

> A month is "closeable" only if it is fully in the past relative to today. The current
> partial month and future months are not closeable (spec §6.3, build guide: open months
> have too few rows).

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_available.py
from datetime import date
from app.closing.available import available_months, is_closeable

def test_past_month_is_closeable():
    assert is_closeable("2026-05", today=date(2026, 6, 21)) is True

def test_current_month_not_closeable():
    assert is_closeable("2026-06", today=date(2026, 6, 21)) is False

def test_future_month_not_closeable():
    assert is_closeable("2026-12", today=date(2026, 6, 21)) is False

def test_available_months_descending_and_bounded():
    months = available_months(today=date(2026, 6, 21), back=3)
    assert months == ["2026-05", "2026-04", "2026-03"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_available.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/closing/available.py
from __future__ import annotations
from datetime import date

def is_closeable(ano_mes: str, *, today: date | None = None) -> bool:
    today = today or date.today()
    year, month = (int(x) for x in ano_mes.split("-"))
    # closeable iff the month ended strictly before the first day of the current month
    return (year, month) < (today.year, today.month)

def available_months(*, today: date | None = None, back: int = 24) -> list[str]:
    today = today or date.today()
    y, m = today.year, today.month
    out: list[str] = []
    for _ in range(back):
        m -= 1
        if m == 0:
            m = 12
            y -= 1
        out.append(f"{y:04d}-{m:02d}")
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/test_available.py tests/test_clients_api.py -v`
Expected: PASS (both files).

- [ ] **Step 5: Commit**

```bash
git add backend/app/closing/available.py backend/tests/test_available.py
git commit -m "feat: closeable-month helper"
```

### Task 4.6: Closing endpoint (month + optional day-range; tenancy enforced)

**Files:**
- Create: `backend/app/api/closing_router.py`
- Modify: `backend/app/main.py` (include router)
- Test: `backend/tests/test_closing_api.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_closing_api.py
def _token(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password}).json()["access_token"]

def test_demo_closing_returns_payload(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.get("/api/clients/demo/closing?month=2026-05", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["client"]["id"] == "demo"
    assert body["period"]["ano_mes"] == "2026-05"
    assert body["day_range"]["is_full_month"] is True

def test_open_month_rejected_422(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.get("/api/clients/demo/closing?month=2999-01", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 422

def test_client_cannot_read_other_clients_closing(client):
    tok = _token(client, "financeiro@mbclaw.com.br", "mbc123")  # mbc client
    resp = client.get("/api/clients/demo/closing?month=2026-05", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 403

def test_day_range_marks_partial(client):
    tok = _token(client, "admin@rumo.com.br", "admin123")
    resp = client.get("/api/clients/demo/closing?month=2026-05&from=1&to=15", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200
    assert resp.json()["day_range"]["is_full_month"] is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_closing_api.py -v`
Expected: FAIL — 404 (router not mounted).

- [ ] **Step 3: Write minimal implementation**

```python
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
        if from_ > to:
            raise HTTPException(status_code=422, detail="Intervalo de dias inválido")
        day_range = DayRange.within(period, from_day=from_, to_day=to)
    else:
        day_range = DayRange.full_month(period)
    provider = build_provider_for(client)
    return provider.build_closing(client=client, period=period, day_range=day_range)
```

```python
# add to backend/app/main.py
from app.api.closing_router import router as closing_router
app.include_router(closing_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && pytest -q`
Expected: PASS (entire backend suite).

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/closing_router.py backend/app/main.py backend/tests/test_closing_api.py
git commit -m "feat: closing endpoint with month validation + day-range + tenancy"
```

### Task 4.7: Seed script (idempotent)

**Files:**
- Create: `backend/scripts/seed.py`

- [ ] **Step 1: Implement (no test; operational script, guarded by env)**

```python
# backend/scripts/seed.py
"""Idempotent seed: creates the demo clients + the three seed users in Supabase.
Run once after applying schema.sql:  python -m scripts.seed
Passwords come from env (SEED_ADMIN_PASSWORD, SEED_MBC_PASSWORD, SEED_DEMO_PASSWORD)
with dev defaults; override in production.
"""
from __future__ import annotations
import os
from supabase import create_client
from app.auth.passwords import hash_password
from app.config import Settings

def main() -> None:
    s = Settings.from_env()
    c = create_client(s.supabase_url, s.supabase_service_key)
    clients = [
        {"id": "mbc", "name": "MBC", "provider": "legaldesk", "provider_config": {}},
        {"id": "demo", "name": "Cliente Demonstração", "provider": "fixture", "provider_config": {}},
    ]
    for row in clients:
        c.table("clients").upsert(row).execute()
    users = [
        {"email": "admin@rumo.com.br", "role": "ADMIN", "client_id": None,
         "password_hash": hash_password(os.environ.get("SEED_ADMIN_PASSWORD", "admin123"))},
        {"email": "financeiro@mbclaw.com.br", "role": "CLIENT", "client_id": "mbc",
         "password_hash": hash_password(os.environ.get("SEED_MBC_PASSWORD", "mbc123"))},
        {"email": "demo@cliente.com.br", "role": "CLIENT", "client_id": "demo",
         "password_hash": hash_password(os.environ.get("SEED_DEMO_PASSWORD", "demo123"))},
    ]
    for row in users:
        c.table("users").upsert(row, on_conflict="email").execute()
    print("Seed complete.")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add backend/scripts/seed.py
git commit -m "feat: idempotent Supabase seed script"
```

## Phase 5 — Frontend SPA (React + TS + Vite, PT-BR, dark fintech)

> Run frontend commands from `frontend/`. Scaffold with Vite React-TS, then add React
> Router, vitest, and Testing Library. All user-facing copy is Brazilian Portuguese.

### Task 5.1: Scaffold the SPA + tooling

**Files:**
- Create: `frontend/` (Vite react-ts template)
- Create: `frontend/.env.example` (`VITE_API_URL=http://localhost:8000`)
- Modify: `frontend/package.json` (add deps + test script)
- Create: `frontend/vitest.config.ts`
- Create: `frontend/src/test/setup.ts`

- [ ] **Step 1: Scaffold**

```bash
cd frontend # if dir exists, else: npm create vite@latest frontend -- --template react-ts
npm create vite@latest . -- --template react-ts
npm install
npm install react-router-dom
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom eslint prettier
```

- [ ] **Step 2: Add test config**

```ts
// frontend/vitest.config.ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: { environment: "jsdom", globals: true, setupFiles: ["./src/test/setup.ts"] },
});
```

```ts
// frontend/src/test/setup.ts
import "@testing-library/jest-dom";
```

```jsonc
// frontend/package.json — ensure scripts include:
// "test": "vitest run", "test:watch": "vitest", "lint": "eslint src", "typecheck": "tsc --noEmit"
```

```bash
# frontend/.env.example
VITE_API_URL=http://localhost:8000
```

- [ ] **Step 3: Smoke test**

```bash
cd frontend && npm run typecheck && npm test
```
Expected: typecheck passes; vitest runs (0 tests is OK at this point).

- [ ] **Step 4: Commit**

```bash
git add frontend/ ':!frontend/node_modules'
git commit -m "chore: scaffold React+TS Vite SPA with vitest"
```

### Task 5.2: Currency + date formatting utils

**Files:**
- Create: `frontend/src/lib/format.ts`
- Test: `frontend/src/lib/format.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/lib/format.test.ts
import { describe, it, expect } from "vitest";
import { formatBRL, formatMonthLabel } from "./format";

describe("formatBRL", () => {
  it("formats with R$, thousands dot, decimal comma", () => {
    expect(formatBRL(415927.84)).toBe("R$ 415.927,84");
  });
  it("renders null as em dash", () => {
    expect(formatBRL(null)).toBe("—");
  });
});

describe("formatMonthLabel", () => {
  it("maps ano_mes to a PT-BR label", () => {
    expect(formatMonthLabel("2026-05")).toBe("Maio 2026");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/lib/format.test.ts`
Expected: FAIL — cannot find `./format`.

- [ ] **Step 3: Write minimal implementation**

```ts
// frontend/src/lib/format.ts
const BRL = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatBRL(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return BRL.format(value).replace("\u00a0", " ");
}

const MESES = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
];

export function formatMonthLabel(anoMes: string): string {
  const [y, m] = anoMes.split("-").map(Number);
  return `${MESES[m - 1]} ${y}`;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/lib/format.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/format.ts frontend/src/lib/format.test.ts
git commit -m "feat: BRL + month-label formatting"
```

### Task 5.3: API client + typed errors

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/types.ts`
- Test: `frontend/src/lib/api.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/lib/api.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ApiError, apiFetch } from "./api";

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});

describe("apiFetch", () => {
  it("attaches bearer token when present", async () => {
    localStorage.setItem("rumo_token", "abc");
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200 }),
    );
    await apiFetch("/api/clients");
    const headers = (spy.mock.calls[0][1] as RequestInit).headers as Record<string, string>;
    expect(headers["Authorization"]).toBe("Bearer abc");
  });

  it("throws ApiError with status + detail on non-2xx", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Sem acesso a este cliente" }), { status: 403 }),
    );
    await expect(apiFetch("/api/clients/demo")).rejects.toMatchObject({
      status: 403,
      detail: "Sem acesso a este cliente",
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/lib/api.test.ts`
Expected: FAIL — cannot find `./api`.

- [ ] **Step 3: Write minimal implementation**

```ts
// frontend/src/lib/api.ts
const BASE = import.meta.env.VITE_API_URL ?? "";
const TOKEN_KEY = "rumo_token";

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(t: string | null): void {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

export async function apiFetch<T = unknown>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!resp.ok) {
    let detail = "Erro inesperado";
    try {
      detail = (await resp.json()).detail ?? detail;
    } catch {
      /* keep default */
    }
    throw new ApiError(resp.status, detail);
  }
  return (await resp.json()) as T;
}
```

```ts
// frontend/src/lib/types.ts
export type Role = "ADMIN" | "CLIENT";
export type Origin = "legaldesk" | "juritis" | "manual" | "formula" | "fixture";

export interface AuthUser {
  id: string;
  email: string;
  role: Role;
  client_id: string | null;
}

export interface ClientSummary {
  id: string;
  name: string;
  provider: string;
}

export interface Cell {
  value: number | null;
  origin: Origin;
}

export interface ClosingPayload {
  client: { id: string; name: string };
  period: { ano_mes: string; label: string; column_letter: string };
  day_range: { from: string; to: string; is_full_month: boolean };
  kpis: Record<string, number>;
  tab_order: string[];
  tabs: Record<string, unknown>;
  generated_at: string;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/lib/api.test.ts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/lib/types.ts frontend/src/lib/api.test.ts
git commit -m "feat: typed API client with bearer + ApiError"
```

### Task 5.4: Auth store + session restore

**Files:**
- Create: `frontend/src/features/auth/authStore.tsx`
- Test: `frontend/src/features/auth/authStore.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/features/auth/authStore.test.tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth } from "./authStore";
import * as api from "../../lib/api";

function Probe() {
  const { user, status } = useAuth();
  return <div>{status}:{user?.role ?? "none"}</div>;
}

beforeEach(() => { localStorage.clear(); vi.restoreAllMocks(); });

describe("AuthProvider", () => {
  it("is unauthenticated when no token", async () => {
    render(<AuthProvider><Probe /></AuthProvider>);
    await waitFor(() => expect(screen.getByText("unauthenticated:none")).toBeInTheDocument());
  });

  it("restores session from token via /auth/me", async () => {
    localStorage.setItem("rumo_token", "abc");
    vi.spyOn(api, "apiFetch").mockResolvedValue({ id: "u", email: "a@b", role: "ADMIN", client_id: null });
    render(<AuthProvider><Probe /></AuthProvider>);
    await waitFor(() => expect(screen.getByText("authenticated:ADMIN")).toBeInTheDocument());
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/auth/authStore.test.tsx`
Expected: FAIL — cannot find `./authStore`.

- [ ] **Step 3: Write minimal implementation**

```tsx
// frontend/src/features/auth/authStore.tsx
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { apiFetch, getToken, setToken } from "../../lib/api";
import type { AuthUser } from "../../lib/types";

type Status = "loading" | "authenticated" | "unauthenticated";

interface AuthCtx {
  user: AuthUser | null;
  status: Status;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    if (!getToken()) { setStatus("unauthenticated"); return; }
    apiFetch<AuthUser>("/api/auth/me")
      .then((u) => { setUser(u); setStatus("authenticated"); })
      .catch(() => { setToken(null); setStatus("unauthenticated"); });
  }, []);

  async function login(email: string, password: string) {
    const res = await apiFetch<{ access_token: string; user: AuthUser }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(res.access_token);
    setUser(res.user);
    setStatus("authenticated");
  }

  function logout() {
    setToken(null);
    setUser(null);
    setStatus("unauthenticated");
  }

  return <Ctx.Provider value={{ user, status, login, logout }}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used within AuthProvider");
  return v;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/auth/authStore.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/auth/authStore.tsx frontend/src/features/auth/authStore.test.tsx
git commit -m "feat: auth store with session restore"
```

### Task 5.5: Route guards + router

**Files:**
- Create: `frontend/src/app/guards.tsx`
- Create: `frontend/src/app/router.tsx`
- Modify: `frontend/src/main.tsx` (wrap with AuthProvider + RouterProvider)
- Test: `frontend/src/app/guards.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/app/guards.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { RequireAuth, RequireAdmin } from "./guards";
import * as authStore from "../features/auth/authStore";

function mockAuth(status: string, role: string | null) {
  vi.spyOn(authStore, "useAuth").mockReturnValue({
    user: role ? ({ id: "u", email: "a@b", role, client_id: role === "CLIENT" ? "mbc" : null } as never) : null,
    status: status as never, login: vi.fn(), logout: vi.fn(),
  });
}

describe("guards", () => {
  it("RequireAuth redirects to /login when unauthenticated", () => {
    mockAuth("unauthenticated", null);
    render(
      <MemoryRouter initialEntries={["/clientes"]}>
        <Routes>
          <Route path="/login" element={<div>LOGIN</div>} />
          <Route element={<RequireAuth />}>
            <Route path="/clientes" element={<div>CLIENTES</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("LOGIN")).toBeInTheDocument();
  });

  it("RequireAdmin redirects a CLIENT to its own workspace", () => {
    mockAuth("authenticated", "CLIENT");
    render(
      <MemoryRouter initialEntries={["/clientes"]}>
        <Routes>
          <Route path="/clientes/:id" element={<div>WORKSPACE</div>} />
          <Route element={<RequireAdmin />}>
            <Route path="/clientes" element={<div>CLIENTES</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText("WORKSPACE")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/app/guards.test.tsx`
Expected: FAIL — cannot find `./guards`.

- [ ] **Step 3: Write minimal implementation**

```tsx
// frontend/src/app/guards.tsx
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../features/auth/authStore";

export function RequireAuth() {
  const { status } = useAuth();
  if (status === "loading") return <div className="page-loading">Carregando…</div>;
  if (status === "unauthenticated") return <Navigate to="/login" replace />;
  return <Outlet />;
}

export function RequireAdmin() {
  const { status, user } = useAuth();
  if (status === "loading") return <div className="page-loading">Carregando…</div>;
  if (status === "unauthenticated") return <Navigate to="/login" replace />;
  if (user?.role !== "ADMIN") return <Navigate to={`/clientes/${user?.client_id}`} replace />;
  return <Outlet />;
}
```

```tsx
// frontend/src/app/router.tsx
import { createBrowserRouter } from "react-router-dom";
import { RequireAuth, RequireAdmin } from "./guards";
import { LoginPage } from "../features/auth/LoginPage";
import { ClientsPage } from "../features/clients/ClientsPage";
import { WorkspacePage } from "../features/closing/WorkspacePage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <RequireAuth />,
    children: [
      { element: <RequireAdmin />, children: [{ path: "/clientes", element: <ClientsPage /> }] },
      { path: "/clientes/:id", element: <WorkspacePage /> },
      { path: "/", element: <ClientsPage /> },
    ],
  },
]);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/app/guards.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/guards.tsx frontend/src/app/router.tsx frontend/src/app/guards.test.tsx
git commit -m "feat: route guards + router"
```

### Task 5.6: Design tokens + primitives (Badge, KpiCard, Button, Skeleton)

**Files:**
- Create: `frontend/src/styles/tokens.css` (dark palette, spacing, origin colors, tabular-nums)
- Create: `frontend/src/components/Badge.tsx`
- Create: `frontend/src/components/KpiCard.tsx`
- Create: `frontend/src/components/Button.tsx`
- Create: `frontend/src/components/Skeleton.tsx`
- Test: `frontend/src/components/Badge.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/components/Badge.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { OriginBadge } from "./Badge";

describe("OriginBadge", () => {
  it("labels legaldesk as API", () => {
    render(<OriginBadge origin="legaldesk" />);
    expect(screen.getByText("API")).toBeInTheDocument();
  });
  it("labels manual as MANUAL", () => {
    render(<OriginBadge origin="manual" />);
    expect(screen.getByText("MANUAL")).toBeInTheDocument();
  });
  it("labels juritis as Juritis", () => {
    render(<OriginBadge origin="juritis" />);
    expect(screen.getByText("Juritis")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/components/Badge.test.tsx`
Expected: FAIL — cannot find `./Badge`.

- [ ] **Step 3: Write minimal implementation**

```tsx
// frontend/src/components/Badge.tsx
import type { Origin } from "../lib/types";

const LABELS: Record<Origin, string> = {
  legaldesk: "API",
  juritis: "Juritis",
  manual: "MANUAL",
  formula: "FÓRMULA",
  fixture: "DEMO",
};

export function OriginBadge({ origin }: { origin: Origin }) {
  return <span className={`badge badge-${origin}`}>{LABELS[origin]}</span>;
}
```

```tsx
// frontend/src/components/Button.tsx
import type { ButtonHTMLAttributes } from "react";
export function Button({ variant = "primary", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" }) {
  return <button className={`btn btn-${variant}`} {...props} />;
}
```

```tsx
// frontend/src/components/KpiCard.tsx
import { formatBRL } from "../lib/format";
export function KpiCard({ label, value, foot, highlight = false }: { label: string; value: number | null; foot?: string; highlight?: boolean }) {
  return (
    <div className={`kpi${highlight ? " kpi-highlight" : ""}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value num">{formatBRL(value)}</div>
      {foot ? <div className="kpi-foot">{foot}</div> : null}
    </div>
  );
}
```

```tsx
// frontend/src/components/Skeleton.tsx
export function Skeleton({ rows = 6 }: { rows?: number }) {
  return <div className="skeleton">{Array.from({ length: rows }).map((_, i) => <div key={i} className="skeleton-row" />)}</div>;
}
```

```css
/* frontend/src/styles/tokens.css */
:root {
  --bg: #0f1115; --surface: #161922; --border: #262b36; --text: #e6e8ee; --muted: #8b91a0;
  --api: #22c55e; --formula: #3b82f6; --manual: #6b7280; --juritis: #8b5cf6; --fixture: #a3a3a3;
  --radius: 8px; --space: 8px;
}
body { background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; margin: 0; }
.num { font-variant-numeric: tabular-nums; }
.badge { font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 4px; }
.badge-legaldesk { background: rgba(34,197,94,.15); color: var(--api); }
.badge-formula { background: rgba(59,130,246,.15); color: var(--formula); }
.badge-manual, .badge-fixture { background: rgba(107,114,128,.18); color: var(--muted); }
.badge-juritis { background: rgba(139,92,246,.15); color: var(--juritis); }
.kpi { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }
.kpi-highlight { border-color: var(--api); }
.btn { border-radius: var(--radius); padding: 8px 14px; border: 1px solid var(--border); cursor: pointer; }
.btn-primary { background: var(--api); color: #04210f; border-color: var(--api); }
.skeleton-row { height: 14px; background: var(--surface); border-radius: 4px; margin: 8px 0; animation: pulse 1.2s infinite; }
@keyframes pulse { 0%,100% { opacity: .5 } 50% { opacity: 1 } }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/components/Badge.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/ frontend/src/styles/
git commit -m "feat: design tokens + Badge/KpiCard/Button/Skeleton primitives"
```

### Task 5.7: MonthPicker (disables open/future months) + DayRangeFilter

**Files:**
- Create: `frontend/src/features/closing/MonthPicker.tsx`
- Create: `frontend/src/features/closing/DayRangeFilter.tsx`
- Test: `frontend/src/features/closing/MonthPicker.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/features/closing/MonthPicker.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MonthPicker } from "./MonthPicker";

describe("MonthPicker", () => {
  it("disables months not in availableMonths", () => {
    render(<MonthPicker value="2026-05" availableMonths={["2026-05", "2026-04"]} onChange={() => {}} />);
    // current/open month e.g. 2026-06 is not available -> rendered disabled
    const open = screen.getByRole("button", { name: /Jun/ });
    expect(open).toBeDisabled();
  });

  it("emits the selected ano_mes on click", async () => {
    const onChange = vi.fn();
    render(<MonthPicker value="2026-05" availableMonths={["2026-05", "2026-04"]} onChange={onChange} />);
    await userEvent.click(screen.getByRole("button", { name: /Abr/ }));
    expect(onChange).toHaveBeenCalledWith("2026-04");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/closing/MonthPicker.test.tsx`
Expected: FAIL — cannot find `./MonthPicker`.

- [ ] **Step 3: Write minimal implementation**

```tsx
// frontend/src/features/closing/MonthPicker.tsx
const MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

export function MonthPicker({ value, availableMonths, onChange }:
  { value: string; availableMonths: string[]; onChange: (anoMes: string) => void }) {
  const [year] = value.split("-").map(Number);
  const available = new Set(availableMonths);
  return (
    <div className="month-picker">
      <div className="month-picker-year">{year}</div>
      <div className="month-grid">
        {MESES.map((label, i) => {
          const anoMes = `${year}-${String(i + 1).padStart(2, "0")}`;
          const enabled = available.has(anoMes);
          const selected = anoMes === value;
          return (
            <button
              key={label}
              className={`month-cell${selected ? " selected" : ""}`}
              disabled={!enabled}
              title={enabled ? "" : "Mês ainda em aberto"}
              onClick={() => onChange(anoMes)}
            >
              {label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
```

```tsx
// frontend/src/features/closing/DayRangeFilter.tsx
export function DayRangeFilter({ from, to, onChange, onClear }:
  { from: number | null; to: number | null; onChange: (from: number, to: number) => void; onClear: () => void }) {
  return (
    <div className="day-range">
      <label>De
        <input type="number" min={1} max={31} value={from ?? ""} onChange={(e) => onChange(Number(e.target.value), to ?? Number(e.target.value))} />
      </label>
      <label>até
        <input type="number" min={1} max={31} value={to ?? ""} onChange={(e) => onChange(from ?? Number(e.target.value), Number(e.target.value))} />
      </label>
      {from || to ? <button className="btn btn-ghost" onClick={onClear}>Limpar</button> : null}
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/closing/MonthPicker.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/closing/MonthPicker.tsx frontend/src/features/closing/DayRangeFilter.tsx frontend/src/features/closing/MonthPicker.test.tsx
git commit -m "feat: MonthPicker (disables open months) + DayRangeFilter"
```

### Task 5.8: LoginPage

**Files:**
- Create: `frontend/src/features/auth/LoginPage.tsx`
- Test: `frontend/src/features/auth/LoginPage.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/features/auth/LoginPage.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { LoginPage } from "./LoginPage";
import * as authStore from "./authStore";

describe("LoginPage", () => {
  it("shows a PT-BR error when login fails", async () => {
    vi.spyOn(authStore, "useAuth").mockReturnValue({
      user: null, status: "unauthenticated",
      login: vi.fn().mockRejectedValue(Object.assign(new Error("x"), { detail: "E-mail ou senha inválidos" })),
      logout: vi.fn(),
    });
    render(<MemoryRouter><LoginPage /></MemoryRouter>);
    await userEvent.type(screen.getByLabelText(/E-mail/i), "a@b.com");
    await userEvent.type(screen.getByLabelText(/Senha/i), "x");
    await userEvent.click(screen.getByRole("button", { name: /Entrar/i }));
    expect(await screen.findByText("E-mail ou senha inválidos")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/auth/LoginPage.test.tsx`
Expected: FAIL — cannot find `./LoginPage`.

- [ ] **Step 3: Write minimal implementation**

```tsx
// frontend/src/features/auth/LoginPage.tsx
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./authStore";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError((err as { detail?: string }).detail ?? "Não foi possível entrar");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={onSubmit}>
        <h1>RUMO</h1>
        <p className="muted">Plataforma de Fechamento Mensal</p>
        <label htmlFor="email">E-mail</label>
        <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoFocus />
        <label htmlFor="senha">Senha</label>
        <input id="senha" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error ? <div className="form-error" role="alert">{error}</div> : null}
        <button className="btn btn-primary" disabled={busy} type="submit">{busy ? "Entrando…" : "Entrar"}</button>
      </form>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/auth/LoginPage.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/auth/LoginPage.tsx frontend/src/features/auth/LoginPage.test.tsx
git commit -m "feat: LoginPage with PT-BR errors"
```

### Task 5.9: ClientsPage (admin landing — client cards)

**Files:**
- Create: `frontend/src/features/clients/ClientsPage.tsx`
- Test: `frontend/src/features/clients/ClientsPage.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/features/clients/ClientsPage.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ClientsPage } from "./ClientsPage";
import * as api from "../../lib/api";

describe("ClientsPage", () => {
  it("renders a card per client", async () => {
    vi.spyOn(api, "apiFetch").mockResolvedValue([
      { id: "mbc", name: "MBC", provider: "legaldesk" },
      { id: "demo", name: "Cliente Demonstração", provider: "fixture" },
    ]);
    render(<MemoryRouter><ClientsPage /></MemoryRouter>);
    await waitFor(() => {
      expect(screen.getByText("MBC")).toBeInTheDocument();
      expect(screen.getByText("Cliente Demonstração")).toBeInTheDocument();
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/clients/ClientsPage.test.tsx`
Expected: FAIL — cannot find `./ClientsPage`.

- [ ] **Step 3: Write minimal implementation**

```tsx
// frontend/src/features/clients/ClientsPage.tsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../../lib/api";
import type { ClientSummary } from "../../lib/types";
import { Skeleton } from "../../components/Skeleton";

export function ClientsPage() {
  const [clients, setClients] = useState<ClientSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<ClientSummary[]>("/api/clients")
      .then(setClients)
      .catch((e) => setError((e as { detail?: string }).detail ?? "Erro ao carregar clientes"));
  }, []);

  if (error) return <div className="error-state" role="alert">{error}</div>;
  if (!clients) return <div className="clients-page"><Skeleton rows={4} /></div>;

  return (
    <div className="clients-page">
      <header className="page-head"><h1>Clientes</h1><span className="muted">{clients.length} ativos</span></header>
      <div className="client-cards">
        {clients.map((c) => (
          <Link key={c.id} to={`/clientes/${c.id}`} className="client-card">
            <div className="client-card-name">{c.name}</div>
            <div className="client-card-open">Abrir →</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/clients/ClientsPage.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/clients/
git commit -m "feat: admin ClientsPage (client cards)"
```

### Task 5.10: WorkspacePage (fetches closing, renders KPIs + active tab)

**Files:**
- Create: `frontend/src/features/closing/WorkspacePage.tsx`
- Create: `frontend/src/features/closing/useClosing.ts`
- Test: `frontend/src/features/closing/WorkspacePage.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/features/closing/WorkspacePage.test.tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { WorkspacePage } from "./WorkspacePage";
import * as api from "../../lib/api";

const payload = {
  client: { id: "mbc", name: "MBC" },
  period: { ano_mes: "2026-05", label: "Maio 2026", column_letter: "G" },
  day_range: { from: "2026-05-01", to: "2026-06-01", is_full_month: true },
  kpis: { receita_honorarios: 415927.84, faturamento_realizado: 719988.05, faturas_emitidas: 53 },
  tab_order: ["meta"],
  tabs: { meta: { kind: "rich", name: "Meta", kpis: {} } },
  generated_at: "2026-06-01T00:00:00Z",
};

describe("WorkspacePage", () => {
  it("renders client name + headline KPI from the closing", async () => {
    vi.spyOn(api, "apiFetch").mockImplementation((path: string) => {
      if (path.includes("/closing")) return Promise.resolve(payload as never);
      return Promise.resolve({ id: "mbc", name: "MBC", provider: "legaldesk", available_months: ["2026-05"] } as never);
    });
    render(
      <MemoryRouter initialEntries={["/clientes/mbc"]}>
        <Routes><Route path="/clientes/:id" element={<WorkspacePage />} /></Routes>
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByText("Fechamento — MBC")).toBeInTheDocument();
      expect(screen.getByText("R$ 415.927,84")).toBeInTheDocument();
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/closing/WorkspacePage.test.tsx`
Expected: FAIL — cannot find `./WorkspacePage`.

- [ ] **Step 3: Write minimal implementation**

```ts
// frontend/src/features/closing/useClosing.ts
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import type { ClosingPayload } from "../../lib/types";

export function useClosing(clientId: string, month: string, from: number | null, to: number | null) {
  const [data, setData] = useState<ClosingPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    setLoading(true);
    setError(null);
    const q = new URLSearchParams({ month });
    if (from && to) { q.set("from", String(from)); q.set("to", String(to)); }
    apiFetch<ClosingPayload>(`/api/clients/${clientId}/closing?${q.toString()}`)
      .then(setData)
      .catch((e) => setError((e as { detail?: string }).detail ?? "Erro ao carregar fechamento"))
      .finally(() => setLoading(false));
  }, [clientId, month, from, to]);
  return { data, error, loading };
}
```

```tsx
// frontend/src/features/closing/WorkspacePage.tsx
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiFetch } from "../../lib/api";
import { useClosing } from "./useClosing";
import { MonthPicker } from "./MonthPicker";
import { DayRangeFilter } from "./DayRangeFilter";
import { KpiCard } from "../../components/KpiCard";
import { Skeleton } from "../../components/Skeleton";
import { TabView } from "./TabView";

export function WorkspacePage() {
  const { id = "" } = useParams();
  const [months, setMonths] = useState<string[]>([]);
  const [month, setMonth] = useState<string>("");
  const [from, setFrom] = useState<number | null>(null);
  const [to, setTo] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<string>("");

  useEffect(() => {
    apiFetch<{ available_months: string[] }>(`/api/clients/${id}`).then((c) => {
      setMonths(c.available_months);
      setMonth(c.available_months[0] ?? "");
    });
  }, [id]);

  const { data, error, loading } = useClosing(id, month, from, to);
  useEffect(() => { if (data && !activeTab) setActiveTab(data.tab_order[0] ?? ""); }, [data, activeTab]);

  if (!month) return <div className="workspace"><Skeleton rows={6} /></div>;

  return (
    <div className="workspace">
      <header className="workspace-top">
        <h1>Fechamento — {data?.client.name ?? ""}</h1>
        <div className="filters">
          <MonthPicker value={month} availableMonths={months} onChange={(m) => { setMonth(m); setFrom(null); setTo(null); }} />
          <DayRangeFilter from={from} to={to} onChange={(f, t) => { setFrom(f); setTo(t); }} onClear={() => { setFrom(null); setTo(null); }} />
        </div>
      </header>

      {error ? <div className="error-state" role="alert">{error}</div> : null}
      {loading || !data ? <Skeleton rows={6} /> : (
        <>
          <section className="kpis">
            <KpiCard label="Receita de honorários" value={data.kpis.receita_honorarios ?? null} highlight />
            <KpiCard label="Faturamento Realizado" value={data.kpis.faturamento_realizado ?? null} highlight />
            <KpiCard label="Faturas emitidas" value={data.kpis.faturas_emitidas ?? null} />
          </section>
          {!data.day_range.is_full_month ? <div className="filter-chip">Filtrado por dia · KPIs referem-se ao mês completo</div> : null}
          <nav className="tab-rail">
            {data.tab_order.map((t) => (
              <button key={t} className={t === activeTab ? "active" : ""} onClick={() => setActiveTab(t)}>
                {(data.tabs[t] as { name?: string })?.name ?? t}
              </button>
            ))}
          </nav>
          <section className="tab-content"><TabView tab={data.tabs[activeTab]} /></section>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/closing/WorkspacePage.test.tsx`
Expected: FAIL — cannot find `./TabView`. Implement Task 5.11, then PASS.

- [ ] **Step 5: Commit** (after 5.11 green)

```bash
git add frontend/src/features/closing/WorkspacePage.tsx frontend/src/features/closing/useClosing.ts frontend/src/features/closing/WorkspacePage.test.tsx
git commit -m "feat: WorkspacePage (closing fetch, KPIs, tabs, day-range chip)"
```

### Task 5.11: TabView (rich vs grid rendering)

**Files:**
- Create: `frontend/src/features/closing/TabView.tsx`
- Test: `frontend/src/features/closing/TabView.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// frontend/src/features/closing/TabView.test.tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TabView } from "./TabView";

describe("TabView", () => {
  it("renders a rich tab name", () => {
    render(<TabView tab={{ kind: "rich", name: "Meta", kpis: {} }} />);
    expect(screen.getByText("Meta")).toBeInTheDocument();
  });

  it("renders a grid tab note", () => {
    render(<TabView tab={{ kind: "grid", name: "DRE 2026", note: "Fórmula", grid: [], rows: 0, cols: 0 }} />);
    expect(screen.getByText("DRE 2026")).toBeInTheDocument();
    expect(screen.getByText("Fórmula")).toBeInTheDocument();
  });

  it("renders empty-state when tab is missing", () => {
    render(<TabView tab={undefined} />);
    expect(screen.getByText(/Selecione uma aba/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/closing/TabView.test.tsx`
Expected: FAIL — cannot find `./TabView`.

- [ ] **Step 3: Write minimal implementation**

```tsx
// frontend/src/features/closing/TabView.tsx
interface GridCell { t: "label" | "number" | "formula" | "empty"; v?: string | null; n?: number | null }
interface RichTab { kind: "rich"; name: string; [k: string]: unknown }
interface GridTab { kind: "grid"; name: string; note?: string; grid: GridCell[][]; rows: number; cols: number }
type Tab = RichTab | GridTab | undefined | unknown;

export function TabView({ tab }: { tab: Tab }) {
  if (!tab || typeof tab !== "object") {
    return <div className="empty-state">Selecione uma aba para ver o fechamento.</div>;
  }
  const t = tab as RichTab | GridTab;
  if (t.kind === "grid") {
    const g = t as GridTab;
    return (
      <div className="tab grid-tab">
        <h2>{g.name}</h2>
        {g.note ? <p className="muted">{g.note}</p> : null}
        <div className="table-wrap">
          <table className="grid-table">
            <tbody>
              {g.grid.map((row, ri) => (
                <tr key={ri}>{row.map((c, ci) => <td key={ci} className={c.t === "number" || c.t === "formula" ? "num" : ""}>{cellText(c)}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }
  return (
    <div className="tab rich-tab">
      <h2>{(t as RichTab).name}</h2>
      <p className="muted">Renderização rica com valores ao vivo.</p>
    </div>
  );
}

function cellText(c: GridCell): string {
  if (c.t === "label") return c.v ?? "";
  if ((c.t === "number" || c.t === "formula") && c.n != null) {
    return new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(c.n);
  }
  return "";
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/features/closing/TabView.test.tsx src/features/closing/WorkspacePage.test.tsx`
Expected: PASS (both).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/closing/TabView.tsx frontend/src/features/closing/TabView.test.tsx
git commit -m "feat: TabView (rich + grid rendering)"
```

### Task 5.12: Wire main.tsx + app shell, full suite green

**Files:**
- Modify: `frontend/src/main.tsx`
- Create: `frontend/src/app/AppShell.tsx` (sidebar/logout chrome)
- Modify: `frontend/src/index.css` (import tokens.css)

- [ ] **Step 1: Wire it**

```tsx
// frontend/src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { AuthProvider } from "./features/auth/authStore";
import { router } from "./app/router";
import "./styles/tokens.css";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  </React.StrictMode>,
);
```

```tsx
// frontend/src/app/AppShell.tsx
import { useAuth } from "../features/auth/authStore";
export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">RUMO</div>
        <div className="sidebar-foot">
          <span className="muted">{user?.email}</span>
          <button className="btn btn-ghost" onClick={logout}>Sair</button>
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
```

- [ ] **Step 2: Run the full frontend suite + typecheck**

Run: `cd frontend && npm run typecheck && npm test`
Expected: PASS, no type errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/main.tsx frontend/src/app/AppShell.tsx frontend/src/index.css
git commit -m "feat: wire app shell + router + providers"
```

## Phase 6 — CI, Docker, docs, deploy

### Task 6.1: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Implement**

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  backend:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: backend } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: mypy app
      - run: pytest -q
  frontend:
    runs-on: ubuntu-latest
    defaults: { run: { working-directory: frontend } }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: backend (ruff/mypy/pytest) + frontend (eslint/tsc/vitest)"
```

### Task 6.2: Dockerfiles + compose

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Create: `docker-compose.yml`

- [ ] **Step 1: Implement**

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

```nginx
# frontend/nginx.conf
server {
  listen 80;
  location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;   # SPA fallback
  }
}
```

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    env_file: ./backend/.env
    ports: ["8000:8000"]
  frontend:
    build:
      context: ./frontend
    ports: ["5173:80"]
    depends_on: [backend]
```

- [ ] **Step 2: Smoke build**

Run: `docker compose build`
Expected: both images build successfully.

- [ ] **Step 3: Commit**

```bash
git add backend/Dockerfile frontend/Dockerfile frontend/nginx.conf docker-compose.yml
git commit -m "chore: Dockerfiles + compose for backend/frontend"
```

### Task 6.3: PROJECT_STATUS.md (living status doc)

**Files:**
- Create: `PROJECT_STATUS.md`

- [ ] **Step 1: Implement** (seed it; updated at each milestone thereafter)

```markdown
# PROJECT_STATUS

> Read this first. Single source of truth for the current state of the RUMO closing platform.

## What this is
Multi-tenant monthly-closing platform sold to RUMO. RUMO (ADMIN) sees all clients; each
client (e.g. MBC) sees only its own closing. Month + optional day-range chosen in the UI.

## Current status
- Backend (FastAPI): auth (argon2 + JWT), tenancy (ADMIN/CLIENT), Source/ClosingProvider
  data layer, clients + closing endpoints. Tests green.
- Frontend (React/TS): login, admin clients list, client workspace (month picker, day-range,
  KPIs, 15 tabs). PT-BR, dark theme. Tests green.
- Data sources: `legaldesk` (MBC, verified live) + `fixture` (demo, minimal placeholder).
  `juritis` is a PLACEHOLDER, not wired.

## Known limitations
- Institutional expenses (~170 lines) remain MANUAL until the Juritis/TOTVS API arrives.
- Demo client data is minimal/token, for showcasing the multi-client view only.
- Verified totals are pinned to May 2026 from recorded fixtures.

## Future phases
- Juritis source (3 paths: additive / partial override / full replacement — spec §4).
- Evolution (WhatsApp) "fechamento disponível" notifications.
- Password reset, self-serve client onboarding, .xlsx export.

## Verified facts (do not regress)
- recebimento 2026-05 ≈ 415.927,84 · faturamento ≈ 719.988,05 · 53 faturas.
- Source of truth: docs/AUTOMATION_BUILD_GUIDE.md.

## Run / test / deploy
- Backend: `cd backend && pip install -e ".[dev]" && pytest -q && uvicorn app.main:app`.
- Frontend: `cd frontend && npm ci && npm test && npm run dev`.
- Deploy: Docker images on EasyPanel; Supabase Postgres. See README.
```

- [ ] **Step 2: Commit**

```bash
git add PROJECT_STATUS.md
git commit -m "docs: add living PROJECT_STATUS"
```

### Task 6.4: CLAUDE.md (agent operating guide)

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Implement**

```markdown
# CLAUDE.md — Agent operating guide

**Read `PROJECT_STATUS.md` first** for current state. This file holds durable conventions.

## Conventions
- **TDD is mandatory.** Write the failing test, watch it fail, minimal code, watch it pass, commit.
- **Secrets** never committed and never shipped to the browser. Use env + `.env.example`.
- **Verified LegalDesk numbers are sacred** — never let the recorded-fixture totals regress.
- **UI is Brazilian Portuguese.** Money is `R$ 1.234,56`.
- **New data sources** implement the `Source` interface and emit `SectionKey`s — never
  couple the frontend/payload to a source's field names.
- **Security boundary is server-side.** Enforce ADMIN/CLIENT access in FastAPI deps; hiding
  a button is never the boundary.

## Gotchas (grow this list)
- OData **v3** (not v4); always send `$top` + `$filter`. Workbook year is **2026**.
- `RateioFaturaProfissionalViews` rows are duplicated — de-dup by `(FaturaNumero, ProfissionalSigla)`.
- A month is closeable only if fully past (current partial month is not).

## Where things live
- Backend: `backend/app/{auth,tenancy,sources,closing,api}`. Tests: `backend/tests`.
- Frontend: `frontend/src/{lib,components,features,app}`. Tests colocated `*.test.tsx`.
- Spec: `docs/superpowers/specs/`. Plan: `docs/superpowers/plans/`.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md agent guide"
```

### Task 6.5: Top-level README + retire the old tree

**Files:**
- Create: `README.md`
- Remove: `mbc-automation/` (logic already moved; keep `docs/` and ground-truth artifacts)

- [ ] **Step 1: Write README** (product overview, architecture diagram pointer, local dev for
  backend + frontend, env vars table, EasyPanel deploy steps, link to spec/PROJECT_STATUS/CLAUDE).

- [ ] **Step 2: Remove the migrated tree** (confirm every moved file now lives under `backend/`):

```bash
git rm -r mbc-automation
```

> Keep `docs/`, the workbook artifacts, and `work/analysis/*` (ground truth). Only remove the
> `mbc-automation/` app tree whose code was moved in Task 0.2.

- [ ] **Step 3: Run both suites once more**

Run: `cd backend && pytest -q` then `cd ../frontend && npm test`
Expected: all green.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: top-level README; retire migrated mbc-automation tree"
```

### Task 6.6: Update .gitignore for the new layout

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add** `frontend/node_modules/`, `frontend/dist/`, `backend/.env`, `frontend/.env`,
  `*.egg-info/`, and keep `.superpowers/`. Remove the now-obsolete `mbc-automation/...` ignores.

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: gitignore for backend/frontend layout"
```

## Final verification (run before declaring done)

- [ ] `cd backend && ruff check . && mypy app && pytest -q` → all green.
- [ ] `cd frontend && npm run lint && npm run typecheck && npm test` → all green.
- [ ] `docker compose build` → both images build.
- [ ] Manual smoke (optional, needs Supabase + seed): login as each of the three seed users;
      confirm ADMIN sees both clients, MBC client sees only MBC and is blocked from `demo`,
      month picker disables open months, day-range marks partial.
