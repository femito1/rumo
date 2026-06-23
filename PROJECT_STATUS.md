# PROJECT_STATUS.md

> **Living status document. Read this first.**
> Agents and engineers working on this repo should treat this file as the
> single source of truth for *current* state, limitations, and plans.
> Keep it updated at the end of every milestone. When it disagrees with
> older docs, this file wins (except for the sacred LegalDesk numbers, which
> live in `docs/AUTOMATION_BUILD_GUIDE.md`).

**Last updated:** 2026-06-22
**Product:** RUMO — Plataforma de Fechamento Mensal Multi-Cliente
**Design spec:** `docs/superpowers/specs/2026-06-21-rumo-multi-client-platform-design.md`

---

## 1. What this is

A production-grade, multi-tenant SaaS turning the old single-tenant MBC
monthly-closing script into a web product sold to **RUMO**:

- **RUMO** logs in as **ADMIN** and sees **all clients**, drilling into any
  client's monthly closing.
- Each **client** (e.g. MBC) logs in as **CLIENT** and sees **only their own**.
- Competence month is chosen **in the UI** (replacing the old CLI `--month`),
  with an optional **day-range refinement** for date-driven tabs.

Stack: **FastAPI** (Python) backend + **React + TypeScript (Vite)** SPA.
Credentials and the LegalDesk password stay server-side; the browser only
talks to our authenticated backend.

---

## 2. Current status (built vs stubbed)

### Built and tested
- Backend scaffold, `/api/health`, env-driven `Settings` (no hard-coded secrets).
- Verified MBC data logic ported into `backend/app/` (period, builder, layouts,
  LegalDesk client) behind the new Source/Provider seams — behavior preserved.
- Auth: argon2 password hashing, JWT issue/verify, `POST /api/auth/login`,
  `GET /api/auth/me`.
- Tenancy: `User`/`Client` models, `Role` enum, `can_access_client`; server-side
  guards (`require_user`, `require_admin`, `require_client_access`).
- Repository abstraction: `Repository` protocol, in-memory `FakeRepository`
  (tests), `SupabaseRepository` (prod) + `app/db/schema.sql`.
- Data layer: `SectionKey` (15 sections), `DayRange`, `Source` protocol,
  `ClosingProvider` (ordered sources, later-overrides-earlier merge).
- Sources: `LegalDeskSource` (wraps verified builder; locked by recorded
  fixture), `FixtureSource` (demo client), `JuritisSource` (placeholder).
- API: `/api/clients` (admin list), `/api/clients/{id}` (tenancy-guarded),
  `/api/clients/{id}/closing?month=&from=&to=` (month validation + day-range).
- Idempotent Supabase seed script (`backend/scripts/seed.py`).
- Frontend: typed API client + `ApiError`, auth store with silent session
  restore, route guards (`RequireAuth`/`RequireAdmin`), design tokens +
  primitives, `MonthPicker` + `DayRangeFilter`, `LoginPage`, `ClientsPage`,
  `WorkspacePage`, `TabView` (rich + grid), app shell. All PT-BR, dark fintech.
- CI: GitHub Actions running ruff + mypy + pytest (backend) and eslint + tsc +
  vitest (frontend) on push/PR.
- Docker: `backend/Dockerfile`, `frontend/Dockerfile` + `nginx.conf`,
  `docker-compose.yml`. **Smoke-tested:** `docker compose build` builds both
  images; backend container boots and serves `/api/health` → 200.

### Stubbed / placeholder (intentional)
- **`JuritisSource`** — documented placeholder, NOT wired. `supports()` returns
  empty; `fetch()` raises `NotImplementedError`. See §5 for the migration paths.
- **`FixtureSource`** — minimal deterministic demo data; exists only to showcase
  the admin multi-client view. Not real client data.

### Test counts (as of last update)
- Backend: **54 passing** (`cd backend && pytest`).
- Frontend: **29 passing** (`cd frontend && npm run test`).

### Production (EasyPanel + Supabase) — live 2026-06-22
- **Frontend:** https://rumo-frontend.xem1qi.easypanel.host
- **Backend API:** https://rumo-backend.xem1qi.easypanel.host (`/api/health` → 200)
- **Supabase:** project `skrwptamwbhwaiwwhrqj` — `schema.sql` applied, seed run (`mbc` + `demo` clients, three users).
- **EasyPanel:** project `rumo`, services `backend` + `frontend` (GitHub `femito1/rumo` @ `main`, Dockerfiles in `backend/` + `frontend/`).
- **Auth:** production uses Supabase (`USE_FAKE_REPO=0`). Dev zero-setup toggle still available locally.
- Env templates: `backend/.env.production.example`, `frontend/.env.production.example`.

---

## 3. Architecture at a glance

```
rumo/
├── backend/            FastAPI service (Python)
│   ├── app/
│   │   ├── main.py         app + CORS + router wiring + /api/health
│   │   ├── config.py       env-driven Settings.from_env()
│   │   ├── auth/           passwords (argon2), tokens (JWT)
│   │   ├── tenancy/        User/Client models, Repository, SupabaseRepository
│   │   ├── db/             schema.sql (clients + users)
│   │   ├── sources/        base (SectionKey/DayRange/Source), legaldesk,
│   │   │                   fixture, juritis (placeholder), legaldesk_client
│   │   ├── closing/        period, builder, layouts, available, provider
│   │   └── api/            deps, providers, auth_router, clients_router,
│   │                       closing_router
│   ├── tests/          pytest (unit + API + recorded-fixture integration)
│   ├── scripts/seed.py idempotent Supabase seeding
│   └── Dockerfile, pyproject.toml
├── frontend/           React + TS + Vite SPA
│   └── src/{app,features/{auth,clients,closing},lib,components,styles}
│       + Dockerfile, nginx.conf
├── .github/workflows/ci.yml
├── docker-compose.yml
├── PROJECT_STATUS.md   (this file)
├── CLAUDE.md           agent operating guide
└── docs/               existing validated docs + design spec
```

Data flow: `provider`/`provider_config` on a client → ordered `Source`s →
`ClosingProvider.build_closing(period, day_range)` → provider-agnostic
`ClosingPayload` → SPA renders it regardless of upstream source.

---

## 4. Verified facts preserved (SACRED — never silently regress)

Source of truth: `docs/AUTOMATION_BUILD_GUIDE.md`. Locked by backend tests
against the recorded fixture `backend/tests/fixtures/legaldesk_2026_05.json`:

- `recebimento_bruto('2026-05')` ≈ **415.927,84** (98 rows)
- `faturamento_bruto('2026-05')` ≈ **719.988,05** (97 rows)
- **53** distinct invoices in May 2026
- Historicals: jan/2026 = **279.821,07** · fev/2026 = **319.233,58**
- `RateioFaturaProfissionalViews` rows are **duplicated** — de-dup by
  `(FaturaNumero, ProfissionalSigla)`.
- Workbook year is **2026** (not 2025). OData **v3** syntax.

If a change moves any of these numbers, it is a bug until proven otherwise.

---

## 5. Juritis-readiness (the defining constraint)

The Juritis / TOTVS Backoffice API is coming but its shape is **unknown**. The
data layer is built so integrating it is a localized change, never a frontend or
contract rewrite. When access arrives, pick one path:

1. **Additive** — add `JuritisSource` supplying the institutional-expense
   SectionKeys; merge fills previously-MANUAL lines. LegalDesk untouched.
2. **Partial override** — Juritis supplies some sections LegalDesk also did;
   `merge_policy` sets per-section precedence (later source wins).
3. **Full replacement** — a client's provider lists `[JuritisSource]` instead
   of `[LegalDeskSource]`. LegalDesk stays for clients still on it.

In all three, the API contract and the SPA are unchanged: cells just carry a
different `origin` tag (`juritis` instead of `manual`).

---

## 6. Known limitations / tech debt

Non-blocking items found during review. Fix opportunistically; add new ones here.

- **Login timing oracle (low):** login compares password only when the user
  exists, so response timing can hint whether an email is registered. Acceptable
  for a small known user set; mitigate later with a constant-time dummy verify.
- **`DayRange` calendar validation gap (low):** `DayRange.within` trusts the
  caller's day bounds; it does not reject impossible days (e.g. day 31 in a
  30-day month) beyond basic ISO formatting. The closing endpoint clamps to the
  month, so impact is limited, but explicit validation would be cleaner.
- **`FixtureSource` is not representative:** demo numbers are arbitrary; do not
  use them to reason about real behavior or in screenshots shown to clients.
- **JWT secret length warning in tests:** test secrets are short and trigger a
  PyJWT `InsecureKeyLengthWarning`. Production secret comes from env and must be
  ≥ 32 bytes.
- **`docker compose up` needs `backend/.env`:** compose references
  `env_file: ./backend/.env`. Copy `backend/.env.example` → `backend/.env`
  before `up`. The `.env` is gitignored and must never be committed.

---

## 7. Future plans / phases (out of v1, noted not precluded)

- Implement `JuritisSource` once the API is available (see §5).
- Evolution API (WhatsApp) closing notifications.
- Password-reset emails; self-serve client onboarding UI.
- `.xlsx` export of a closing.
- Per-request audit logging for ADMIN cross-client access.

---

## 8. How to run / test / deploy (pointers)

See `README.md` for full instructions. Quick reference:

- **Backend tests:** `cd backend && pytest`
- **Frontend tests:** `cd frontend && npm run test`
- **Backend lint/type:** `cd backend && ruff check . && mypy app`
- **Frontend lint/type:** `cd frontend && npm run lint && npm run typecheck`
- **Local stack:** copy `backend/.env.example` → `backend/.env`, then
  `docker compose up --build`. Backend on :8000, frontend on :5173.
- **Zero-setup dev mode:** set `USE_FAKE_REPO=1` to serve an in-memory
  repo seeded with the three demo accounts (no Supabase needed). The demo
  client renders via `FixtureSource`; MBC's real numbers still require
  LegalDesk creds. Never enable in production. Implemented in
  `app/tenancy/fixture_repository.py`, selected in `app/api/providers.py`.
- **Seed:** `cd backend && python -m scripts.seed` (needs Supabase env vars
  + `SEED_*_PASSWORD` env vars).
- **Deploy:** EasyPanel (Docker images) + Supabase (Postgres). Secrets via
  EasyPanel/Supabase env, never committed.

---

## 9. Conventions (enforced)

- **TDD:** a failing test precedes every new function/endpoint.
- **Secrets:** never committed or shipped; always from env / `.env.example`.
- **Sacred numbers:** the verified LegalDesk totals (§4) must not regress.
- **UI is PT-BR**, money formatted as `R$ 415.927,84`.
- **New data sources** implement the `Source` protocol and emit `SectionKey`s;
  they never touch the API contract or the SPA.
- **Tenancy boundary is server-side.** Hiding a frontend button is never the
  security boundary; `require_client_access` is.
- Conventional, focused commits.
