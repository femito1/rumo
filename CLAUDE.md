# CLAUDE.md — Agent Operating Guide

> **Read `PROJECT_STATUS.md` first.** It is the living source of truth for
> current state, what is built vs stubbed, known limitations, and plans.
> This file is the *durable* operating guide: conventions and hard-won
> gotchas that rarely change. When current-state details here and in
> `PROJECT_STATUS.md` ever disagree, `PROJECT_STATUS.md` wins.

## Start here

0. **Latest state: the top section of `PROJECT_STATUS.md`** (2026-07-28 checkpoint) — the
   July client checkpoint is implemented and deployed: YTD/acumulado toggle, presentation
   panel + PDF, per-área Orçado fix, Jan–Abr un-blanked (hard rule = May only), per-área
   reserva, tab cleanup + a **server-side CLIENT-only boundary**. June validated the DB
   derivation (untuned month). Read that section first for what changed and why.
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
- **Future months are rejected; the OPEN month renders as a labelled partial.**
  Changed 2026-07-29 at the client's explicit request (*"Por que ele não é online?
  ... Não é um fechamento mensal, mas para a gente aproveitar muito mais as
  informações"*) — the extract already runs daily at 06:00, so this is a display
  rule. `app/closing/available.py` now keeps two DISTINCT predicates and you must
  not conflate them:
  - `is_closeable` — the month has fully elapsed. **Unchanged semantics.** This is
    what a *fechamento*, the YTD accumulator and the workbook-comparison harness
    mean. `available_months` likewise stays CLOSED-only (callers read it that way).
  - `is_viewable` — may be displayed: any closed month **plus** the current one.
    Only future months 422. `is_partial` flags the difference, and the closing
    payload carries `period.is_partial` / `is_closing` / `status_label` (PT-BR).
  **A partial month must never render as a closing.** The UI swaps the "Fechamento
  mensal" eyebrow for "Mês em aberto · parcial", shows a banner for both roles, and
  marks the month in the picker; the landing month is still the latest *closed* one.
  Use `available_months_detail` (open month first, `is_partial` flagged) for pickers.
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

- **The agent's `.ps1` files must be PURE ASCII.** MBC-LDESK01's PowerShell 3/4 reads
  BOM-less UTF-8 as cp1252, so an em-dash's trailing byte becomes a closing quote and
  the parse fails with a misleading "Unexpected token" far from the real line.
  `ops/sisjuri-agent/lint_ps1.py` enforces it (CI job `ops-scripts`).

## Where things live

- Backend app: `backend/app/` (see `PROJECT_STATUS.md` §3 for the map).
- Backend tests: `backend/tests/` (fixtures under `tests/fixtures/`).
- Frontend: `frontend/src/{app,features,lib,components,styles}`.
- CI: `.github/workflows/ci.yml`.
- Docker: `backend/Dockerfile`, `frontend/Dockerfile` + `nginx.conf`,
  `docker-compose.yml`.

## Deploying

- **A push to `main` auto-deploys BOTH services** (measured 2026-07-30: build `Success`
  7s after the push, no manual step). So a push IS a release — don't push half-finished
  work to `main`. Older notes in `PROJECT_STATUS.md` claiming "EasyPanel doesn't
  auto-deploy" are wrong and annotated as such.
- `ops/easypanel-deploy.sh <svc>` forces a rebuild; `<svc> logs` prints the last build
  log. A deploy can return `ok` and still fail the build — read the log.
- Verify what is actually live: frontend by comparing `assets/index-<hash>.js` against a
  local `VITE_API_URL=<prod> npm run build`; backend via the public `/openapi.json` when
  the route signatures changed, otherwise the build log timestamp.

## Quality gates before you call something done

- Backend: `cd backend && ruff check . && mypy app && pytest`
- Frontend: `cd frontend && npm run lint && npm run typecheck && npm run test`
- If you touched Docker: `docker compose build` (and, ideally, boot the backend
  and hit `/api/health`).
- Update `PROJECT_STATUS.md` (status, test counts, any new limitation).
