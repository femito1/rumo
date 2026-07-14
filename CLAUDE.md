# CLAUDE.md — Agent Operating Guide

> **Read `PROJECT_STATUS.md` first.** It is the living source of truth for
> current state, what is built vs stubbed, known limitations, and plans.
> This file is the *durable* operating guide: conventions and hard-won
> gotchas that rarely change. When current-state details here and in
> `PROJECT_STATUS.md` ever disagree, `PROJECT_STATUS.md` wins.

## Start here

0. **Active work order: `docs/HANDOFF_2026-07-13-despesas.md`** — current state
   (~85% automated, DRE spine ties to the centavo), the one bottleneck (re-run the
   net extract), and the remaining items with their known paths. Read it first.
1. Read `PROJECT_STATUS.md`. **§0 has client-confirmed business rules that you
   must NOT re-ask the user about** (no Juritis API ever — DB only; authoritative
   book = 05.2026; two-area lawyers always split 50/50; the workbook is the number
   of record and finance never touches the DB).
2. Skim `docs/DESIGN.md` (architecture) and `docs/LEGALDESK.md` (API + sacred numbers).
3. **Before touching the SISJURI DB or writing a probe**, read the living account
   index in `docs/SISJURI_DB.md` §"Known account facts — CHECK THIS BEFORE
   PROBING". It records every discovered account→meaning→destination (e.g. ADM Vale
   lives in `500.010.<SIGLA>`, not `020.050.*`). **When a probe teaches you a new DB
   fact, add it to that index in the same commit.** This is how we avoid
   re-discovering things we already learned.

## What this product is (one paragraph)

Multi-tenant SaaS for RUMO: an ADMIN (RUMO) sees all clients and any client's
monthly closing; a CLIENT sees only their own. FastAPI backend + React/TS
(Vite) SPA. The competence month is chosen in the UI with an optional day-range
refinement. The browser only talks to our authenticated backend; upstream
credentials (LegalDesk) never reach the client.

## Non-negotiable conventions

- **TDD, test-first.** Write a failing test before the implementation. Backend:
  pytest. Frontend: vitest + React Testing Library.
- **Secrets never committed or shipped.** Everything sensitive comes from env;
  keep `.env.example` files current; real `.env` is gitignored.
- **Verified LegalDesk numbers are SACRED.** See `PROJECT_STATUS.md` §4. They
  are locked by `backend/tests/test_legaldesk_source.py` against
  `backend/tests/fixtures/legaldesk_2026_05.json`. A change that moves them is
  a bug until proven otherwise.
- **UI is Brazilian Portuguese.** All user-facing strings in PT-BR; money is
  `R$ 415.927,84` via the single `formatBRL`/format util.
- **New data sources implement the `Source` protocol** (`app/sources/base.py`)
  and emit canonical `SectionKey`s. They must never change the API contract or
  the SPA. Compose them via `ClosingProvider`; precedence is later-overrides-
  earlier through `merge_policy`.
- **The ADMIN/CLIENT boundary is enforced server-side**, on every request, in
  FastAPI dependencies (`require_user`, `require_admin`, `require_client_access`).
  Hiding a frontend button is never the security boundary.

## Gotchas (the kind that waste an afternoon)

- **OData v3 syntax.** The LegalDesk API uses OData **v3**, not v4. Query
  patterns differ; do not "modernize" them.
- **Row duplication.** `RateioFaturaProfissionalViews` returns duplicated rows.
  De-dup by `(FaturaNumero, ProfissionalSigla)` before summing.
- **Query year is 2026**, not 2025. The validated workbook is for 2026.
- **Open/future months are rejected.** A closing month must be fully past; the
  endpoint returns 422 with a PT-BR message. `available_months` and `is_closeable`
  in `app/closing/available.py` are the gate.
- **KPIs stay monthly under a day-range.** Only dated tabs react to `from`/`to`;
  KPIs always reflect the full month. The payload exposes
  `day_range.is_full_month` so the UI shows a "filtrado por dia" indicator.
- **`docker compose up` needs `backend/.env`.** Copy `backend/.env.example`
  first. Build alone works without it; `up` does not.
- **Vitest + Node webstorage.** `frontend/vitest.config.ts` sets `pool: "forks"`
  and `execArgv: ["--no-experimental-webstorage"]` to stop Node's experimental
  native `localStorage` from shadowing jsdom's. This requires Node 22+ (CI pins
  Node 22). Do not remove these without re-checking the auth-store tests.
- **No ORM, no Alembic.** Persistence is `supabase-py` against two small tables
  (`clients`, `users`); DDL lives in `app/db/schema.sql`. Do not introduce
  SQLAlchemy/migrations for this.
- **React lint rules are strict.** `react-hooks/set-state-in-effect` and
  `react-refresh/only-export-components` are enforced. Prefer lazy `useState`
  initializers and render-phase state adjustment over `setState` inside effects;
  keep hooks/contexts in their own modules (e.g. `features/auth/useAuth.ts`),
  not co-located with components.

## Where things live

- Backend app: `backend/app/` (see `PROJECT_STATUS.md` §3 for the map).
- Backend tests: `backend/tests/` (fixtures under `tests/fixtures/`).
- Frontend: `frontend/src/{app,features,lib,components,styles}`.
- CI: `.github/workflows/ci.yml`.
- Docker: `backend/Dockerfile`, `frontend/Dockerfile` + `nginx.conf`,
  `docker-compose.yml`.

## Quality gates before you call something done

- Backend: `cd backend && ruff check . && mypy app && pytest`
- Frontend: `cd frontend && npm run lint && npm run typecheck && npm run test`
- If you touched Docker: `docker compose build` (and, ideally, boot the backend
  and hit `/api/health`).
- Update `PROJECT_STATUS.md` (status, test counts, any new limitation).
