# RUMO — Plataforma de Fechamento Mensal Multi-Cliente

Production-grade, multi-tenant SaaS that turns the original single-tenant MBC
monthly-closing script into a web product sold to **RUMO**.

- **RUMO (ADMIN)** logs in and sees **every client**, drilling into any client's
  monthly closing.
- Each **client (CLIENT)** logs in and sees **only their own** closing.
- The competence month is chosen **in the UI**, with an optional **day-range
  refinement** for the date-driven tabs.

Stack: **FastAPI** (Python) backend + **React + TypeScript (Vite)** SPA. Upstream
credentials (LegalDesk) stay server-side; the browser only talks to our
authenticated backend.

> **Working on this repo?** Read **`PROJECT_STATUS.md`** first (living status,
> what's built vs stubbed, known limitations) and **`CLAUDE.md`** (conventions
> and gotchas).

## Architecture

```
backend/    FastAPI service — auth (JWT/argon2), tenancy, data Sources,
            ClosingProvider, /api routers, pytest suite, Dockerfile
frontend/   React + TS + Vite SPA — login, admin clients list, client
            workspace (month picker + day-range, KPIs, 15 tabs), Dockerfile
docs/       LEGALDESK.md (API reference + sacred numbers), DESIGN.md (architecture)
reference/  workbook + Postman artifacts (not runtime)
docker-compose.yml   local dev parity (backend :8000, frontend :5173)
```

The data layer is built for **Juritis-readiness**: each upstream system is a
`Source` emitting canonical `SectionKey`s; a `ClosingProvider` composes ordered
Sources into a provider-agnostic `ClosingPayload`. Adding the future Juritis /
TOTVS Backoffice API is a localized change, never a frontend or contract
rewrite. See `PROJECT_STATUS.md` §5.

## Prerequisites

- Python 3.11+
- Node 22+ (CI pins Node 22; the frontend test runner needs it)
- A Supabase project (Postgres) for the `clients` + `users` tables
- Docker + Docker Compose (for the containerized workflow)

## Local development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env        # fill in real values (never commit .env)
uvicorn app.main:app --reload   # http://localhost:8000
```

**Try it with zero external setup** (no Supabase): set `USE_FAKE_REPO=1` to serve
an in-memory repo seeded with the demo accounts below. The demo client renders
real-looking data via `FixtureSource`; MBC's actual numbers still need LegalDesk
credentials. Never enable this in production.

```bash
USE_FAKE_REPO=1 JWT_SECRET=dev-secret-at-least-32-chars-long uvicorn app.main:app --reload
```

Demo logins (passwords overridable via `SEED_*_PASSWORD`):

| Email | Role | Default password |
| --- | --- | --- |
| `admin@rumo.com.br` | ADMIN (all clients) | `admin123` |
| `demo@cliente.com.br` | CLIENT → demo | `demo123` |
| `financeiro@mbclaw.com.br` | CLIENT → mbc | `mbc123` |

### Frontend

```bash
cd frontend
npm ci
cp .env.example .env        # VITE_API_URL=http://localhost:8000
npm run dev                 # http://localhost:5173
```

### Full stack via Docker

```bash
cp backend/.env.example backend/.env   # required: compose reads it
docker compose up --build              # backend :8000, frontend :5173
```

### Seed users (dev/demo)

Requires Supabase env vars + `SEED_*_PASSWORD` env vars (see `scripts/seed.py`):

```bash
cd backend && python -m scripts.seed
```

Seeds `admin@rumo.com.br` (ADMIN), `financeiro@mbclaw.com.br` (CLIENT → mbc),
`demo@cliente.com.br` (CLIENT → demo). Passwords come from env — never real
secrets in the repo.

## Environment variables (backend)

| Var | Purpose |
| --- | --- |
| `JWT_SECRET` | signing secret for access tokens (use ≥ 32 bytes in prod) |
| `JWT_TTL_MINUTES` | token lifetime |
| `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` | Supabase Postgres access |
| `LEGALDESK_BASE` / `LEGALDESK_USER` / `LEGALDESK_PASSWORD` | LegalDesk OData API |
| `CORS_ORIGINS` | allowed SPA origin(s) |

Frontend: `VITE_API_URL` → backend base URL. See the `.env.example` files.

## Tests & quality gates

```bash
# Backend
cd backend && ruff check . && mypy app && pytest

# Frontend
cd frontend && npm run lint && npm run typecheck && npm run test
```

CI (`.github/workflows/ci.yml`) runs all of the above on push/PR.

## Deployment (EasyPanel + Supabase)

- **Backend:** Dockerized FastAPI (uvicorn) deployed as an EasyPanel app. Set the
  env vars above (secrets via EasyPanel/Supabase, never committed). `/api/health`
  serves liveness.
- **Frontend:** built static assets served by nginx (`frontend/Dockerfile` +
  `nginx.conf`) as its own EasyPanel app; point `VITE_API_URL` at the backend.
- HTTPS + routing via the EasyPanel proxy.
- Apply `backend/app/db/schema.sql` to Supabase once.

## Project conventions (short version)

- **TDD**: a failing test precedes every new function/endpoint.
- **Secrets** never committed or shipped — always from env.
- The verified LegalDesk numbers are **sacred** (see `PROJECT_STATUS.md` §4).
- UI is **Brazilian Portuguese**; money is `R$ 415.927,84`.
- The **ADMIN/CLIENT boundary is enforced server-side** on every request.

Full detail in `CLAUDE.md` and `PROJECT_STATUS.md`.
