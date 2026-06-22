# RUMO — Plataforma de Fechamento Mensal Multi-Cliente — Design (v1)

> **Date:** 2026-06-21
> **Status:** Approved design, ready for implementation planning.
> **Audience:** Engineers/agents implementing v1. Read top to bottom.

## 1. Summary

Turn the existing single-tenant **MBC monthly-closing dashboard** (a Python script
that builds a static `data.json`, rendered by a static page) into a **production-grade,
multi-tenant SaaS product** sold to **RUMO**.

- **RUMO** logs in with a master/admin account and sees **all clients**, drilling into
  any client's monthly closing.
- Each **client** (e.g. MBC) logs in and sees **only their own** closing.
- The competence month is selected **in the UI** (replacing the CLI `--month`), with an
  optional **day-range refinement within the month** for the date-driven tabs.
- Everything is **production grade**: real auth, multi-tenancy, tested data layer,
  built design system, CI, Docker, deploy to existing infra.

### 1.1 Existing infrastructure (decided around it)

- **Supabase** — managed Postgres. Used as the database only (this app owns `users` +
  `clients`); our own JWT auth on top. Accessed via `supabase-py` (no ORM/migrations).
- **EasyPanel VPS** — deployment target. Backend + frontend ship as Docker images; HTTPS
  and routing via EasyPanel's proxy.
- **Evolution API (WhatsApp)** — available notification channel; **out of scope for v1**,
  noted for a future phase.

## 2. Architecture

Python **FastAPI** backend (promoting the verified `mbc_automation` package) + a
**React + TypeScript (Vite)** SPA. Credentials and the LegalDesk password stay
server-side; the browser only talks to our authenticated backend.

```
rumo/
├── backend/                   # FastAPI service (Python)
│   ├── app/
│   │   ├── main.py                # FastAPI app, CORS, router wiring, /health
│   │   ├── config.py              # env-driven settings (secrets never hard-coded)
│   │   ├── auth/                  # password hashing (argon2/bcrypt), JWT, deps
│   │   ├── tenancy/               # User, Client models + access rules
│   │   ├── db/                    # supabase-py client + schema.sql
│   │   ├── sources/               # Source layer (one upstream system each)
│   │   │   ├── base.py               # Source protocol + SectionKey enum
│   │   │   ├── legaldesk.py           # MBC — wraps the verified API client
│   │   │   ├── fixture.py             # demo client — minimal placeholder
│   │   │   └── juritis.py             # PLACEHOLDER, not wired (see §4)
│   │   ├── closing/               # ClosingProvider (composes Sources), period, payload
│   │   └── api/                   # routers: /auth, /clients, /closing
│   ├── tests/                     # pytest (unit + API + recorded-fixture integration)
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                  # React + TS + Vite SPA
│   ├── src/
│   │   ├── app/                   # router, providers, layout shell, route guards
│   │   ├── features/auth/         # login, session restore
│   │   ├── features/clients/      # admin clients list (cards)
│   │   ├── features/closing/      # workspace: month picker, day filter, KPIs, 15 tabs
│   │   ├── lib/                   # api client, formatBRL, types, auth store
│   │   └── components/            # design-system primitives
│   ├── tests/                     # vitest + React Testing Library
│   ├── Dockerfile
│   └── package.json
├── docs/                      # existing docs (validated) + this spec
├── docker-compose.yml         # local dev parity
├── PROJECT_STATUS.md          # living status doc (read-first for agents)
├── CLAUDE.md                  # agent operating guide (defers to PROJECT_STATUS)
└── README.md                  # product overview, dev, deploy
```

**Migration:** the proven `api_client.py`, `period.py`, `builder.py`, and layout
generators move into `backend/app/` behind the new Source/Provider seams — behavior
preserved, exposed via HTTP instead of CLI. The old static `frontend/` is replaced by
the React SPA.

## 3. Authentication & tenancy

### 3.1 Data model (two roles, one user table)

```
clients
  id            text primary key         -- "mbc", "demo"
  name          text                     -- "MBC", "Cliente Demonstração"
  provider      text                     -- composition key (see §4)
  provider_config jsonb                  -- opaque, server-side only (sources + creds refs)
  active        boolean default true
  created_at    timestamptz default now()

users
  id            uuid primary key default gen_random_uuid()
  email         text unique not null
  password_hash text not null            -- argon2/bcrypt, never plaintext
  role          text not null            -- "ADMIN" | "CLIENT"
  client_id     text references clients(id)  -- null for ADMIN; required for CLIENT
  active        boolean default true
  created_at    timestamptz default now()
```

Schema lives in `backend/app/db/schema.sql`, applied via Supabase. No ORM, no Alembic.

The `provider` + `provider_config` columns together resolve to an ordered list of
**Sources** (and a `merge_policy`) for that client — see §4. For v1: `mbc` → `[LegalDeskSource]`,
`demo` → `[FixtureSource]`.

### 3.2 Access rules (enforced server-side on every request)

- **ADMIN (RUMO):** may list all clients and read any client's closing.
- **CLIENT:** may only read closings for their own `client_id`; any other id → **403**.
  Never sees the clients list.
- Enforced in a FastAPI dependency on `/clients/{id}/...`. The frontend hiding a button is
  **never** the security boundary.

### 3.3 Auth mechanism

- Email + password, hashed with **argon2** (preferred) or bcrypt.
- Login issues a short-lived **JWT** carrying `sub`, `role`, `client_id`. Frontend sends
  `Authorization: Bearer`. JWT secret + lifetime from env.
- `GET /auth/me` for silent session restore on refresh.

### 3.4 Seeding (dev + demo)

A seed script creates: `admin@rumo.com.br` (ADMIN), `financeiro@mbclaw.com.br`
(CLIENT→mbc), `demo@cliente.com.br` (CLIENT→demo). Passwords from env, documented dev
defaults, never real secrets in the repo.

## 4. Data layer — Sources, Providers, and Juritis-readiness

The product's defining constraint: the **Juritis / TOTVS Backoffice** API is coming but
its shape is **unknown**. It could be **additive** (fill the ~170 manual institutional
lines, LegalDesk stays), **partial override**, or a **full replacement**. The data layer
is built so any of these is a localized change — never a frontend or contract rewrite.

### 4.1 Two layers

```python
# Layer 1: a Source = one upstream system; emits canonical SectionKeys it can supply.
class Source(Protocol):
    name: str                                    # "legaldesk" | "juritis" | "fixture"
    def supports(self) -> set[SectionKey]: ...
    def fetch(self, period: Period, day_range: DayRange | None) \
        -> dict[SectionKey, SectionData]: ...

# Layer 2: a ClosingProvider composes ordered Sources into the full payload.
class ClosingProvider:
    sources: list[Source]                        # ordered; later may fill/override earlier
    merge_policy: MergePolicy                     # per-section precedence
    def build_closing(self, period, day_range) -> ClosingPayload: ...
```

- **`SectionKey`** — a canonical enum of every closing section (the 15 tabs / KPI groups),
  decoupled from any source's field names. Each Source maps *its* raw fields → SectionKeys.
- **Per-cell origin tag** — generalizes today's API/FORMULA/MANUAL badges. Every value cell
  carries `origin` ∈ {`legaldesk`, `juritis`, `manual`, `formula`, `fixture`}. A line that
  is MANUAL today simply becomes `juritis` later — no structural change.

### 4.2 Sources in v1

- **`LegalDeskSource`** — wraps the **verified** `LegalDeskClient` + `build_payload` logic
  (MBC). Honors `day_range` via the existing `date_start`/`date_end` queries. Credentials
  from env / `provider_config`.
- **`FixtureSource`** — **minimal placeholder** for the demo client: a couple of populated
  tabs + token KPIs, deterministic, no external calls. Exists only to demonstrate the
  admin multi-client view.
- **`JuritisSource`** — **documented placeholder, NOT wired.** When access arrives, the
  three migration paths are:
  1. **Additive:** add `JuritisSource` supplying institutional-expense SectionKeys; merge
     fills previously-MANUAL lines. LegalDesk untouched.
  2. **Partial override:** Juritis supplies some sections LegalDesk also did; `merge_policy`
     sets per-section precedence.
  3. **Full replacement:** a client's provider lists `[JuritisSource]` instead of
     `[LegalDeskSource]`. LegalDesk source stays for clients still on it.

### 4.3 Verified facts preserved (sacred)

The validated LegalDesk totals (see `docs/AUTOMATION_BUILD_GUIDE.md`) become backend tests
against recorded fixtures and must never silently regress:

- `recebimento_bruto('2026-05')` ≈ **415.927,84** (98 rows)
- `faturamento_bruto('2026-05')` ≈ **719.988,05** (97 rows)
- 53 distinct invoices in May 2026
- Historicals: jan/2026 = 279.821,07 · fev/2026 = 319.233,58
- `RateioFaturaProfissionalViews` rows are **duplicated** — de-dup by `(FaturaNumero, ProfissionalSigla)`.
- The workbook year is **2026** (not 2025). OData **v3** syntax.

## 5. API surface & closing payload

All JSON. All except `/auth/login` and `/health` require a valid JWT.

| Method & path | Role | Purpose |
| --- | --- | --- |
| `POST /api/auth/login` | public | email+senha → `{ access_token, user }` |
| `GET /api/auth/me` | any | current user (session restore) |
| `GET /api/clients` | ADMIN | list clients + headline summary each |
| `GET /api/clients/{id}` | ADMIN or owning CLIENT | client metadata + `available_months` |
| `GET /api/clients/{id}/closing?month=YYYY-MM&from=DD&to=DD` | ADMIN or owning CLIENT | full `ClosingPayload`; `from`/`to` optional |
| `GET /api/health` | public | liveness for EasyPanel |

- CLIENT requesting any `{id}` ≠ their own → **403**.
- `month` must be a closed month; open/future → **422** with a clear PT-BR message.

**`ClosingPayload`** (provider-agnostic; the SPA renders this regardless of source):

```jsonc
{
  "client": { "id": "mbc", "name": "MBC" },
  "period": { "ano_mes": "2026-05", "label": "Maio 2026", "column_letter": "G" },
  "day_range": { "from": "2026-05-01", "to": "2026-05-31", "is_full_month": true },
  "kpis": {
    "receita_honorarios": 415927.84,
    "faturamento_realizado": 719988.05,
    "faturas_emitidas": 53
  },
  "coverage": { "by_origin": { "legaldesk": 1, "manual": 160, "formula": 80 }, "total": 241 },
  "tab_order": ["meta", "base_resultado", "..."],
  "tabs": { "meta": { "kind": "rich", "name": "...", "sections": ["..."] } },
  "generated_at": "2026-..."
}
```

Each value cell: `{ "value": number|null, "origin": "legaldesk|juritis|manual|formula|fixture" }`.
**KPIs stay monthly** even with a day-range applied; only dated tabs (invoices, fee-splits)
react to `from`/`to`. When narrowed, `day_range.is_full_month=false` so the UI shows a
"filtrado por dia" indicator.

## 6. Frontend UI/UX (React + TS, dark fintech, PT-BR)

The entire UI is **Brazilian Portuguese**; money is `R$ 415.927,84` (BRL).

### 6.1 Routes & flow

- `/login` — email + senha. ADMIN → `/clientes`; CLIENT → `/clientes/{seuId}`.
- `/clientes` (ADMIN only, guarded) — **client cards**: name, latest closed month,
  headline Receita, status dot, "Abrir →". A CLIENT hitting this route is redirected.
- `/clientes/{id}` — **workspace** (both roles): left rail of the 15 tabs; top bar with
  month picker (◀ ▶ + year/month grid) and optional day-range refiner; KPI cards; coverage
  meter; active tab table.

### 6.2 Design system (built, not improvised)

- Tokens: dark palette, spacing scale, radii, **tabular-nums** for money, semantic origin
  colors (legaldesk=green, juritis=violet reserved, formula=blue, manual=grey).
- Components: `Button`, `Card`, `KpiCard`, `Badge`, `Table`/`DataGrid`, `MonthPicker`,
  `DayRangeFilter`, `Sidebar`, `Topbar`, `Toast`, `EmptyState`, `Skeleton`, `ErrorState`.
- One `formatBRL` util for all currency.

### 6.3 Polish (production-grade feel)

- Skeleton loaders while a closing fetches (no layout jump).
- Typed API errors → friendly PT-BR toasts/inline states ("Mês ainda em aberto",
  "Sem acesso a este cliente").
- Open/future months disabled in the picker with a tooltip.
- Day-range active → "filtrado: 01–15 Mai" chip on dated tabs; KPIs labeled "mês completo".
- Token persisted; silent session-restore via `/auth/me`; clean logout; route guards.
- Responsive to laptop; tables scroll within container; sidebar collapses on narrow widths.
- Accessibility: focus states, keyboard-navigable tabs/picker, aria labels, contrast.

### 6.4 The 15 tabs

Keep the validated rendering logic — **rich** rendering for the 4 API-fed tabs (Meta,
Base_Resultado, Resumo Recebidas, Faturas Centro Custo), **reference grid** for the other
11 — ported to React with the new origin-badge system.

## 7. Testing & quality (TDD — test-first)

Per the test-driven-development discipline: a failing test precedes every new
function/endpoint.

### 7.1 Backend (pytest)

- **Auth:** hash round-trip, JWT issue/verify, login success/failure, expired/invalid token.
- **Authorization (security boundary):** CLIENT cannot read another client (403); ADMIN
  reads any; unauthenticated → 401. First-class tests.
- **Providers:** `FixtureSource` deterministic; `LegalDeskSource` against **recorded API
  fixtures** (offline/fast), asserting the verified totals (§4.3). De-dup + day-range tested.
- **Source/merge layer:** SectionKey mapping + merge_policy (additive/override) — proves
  Juritis-readiness by test.
- **API contract:** payload shape, period validation (open month → 422), day-range narrows
  dated tabs while KPIs stay monthly.

### 7.2 Frontend (vitest + React Testing Library)

- `formatBRL` and formatting utils.
- Route guards (CLIENT redirected from `/clientes`; unauthenticated → `/login`).
- MonthPicker disables open/future months; DayRangeFilter emits correct range; skeleton/
  error states render.
- One render test per tab type (rich vs grid) against a payload fixture.

### 7.3 Quality gates / CI

- Backend: **ruff** (lint+format) + **mypy** + pytest.
- Frontend: **ESLint + Prettier** + **tsc** + vitest.
- **GitHub Actions** runs all of the above on push/PR.
- `.env.example` (backend + frontend); no secrets committed; secrets via EasyPanel/Supabase.
- Dockerfiles for both, `docker-compose.yml` for local dev, health checks.

## 8. Deployment (EasyPanel + Supabase)

- **Backend:** Dockerized FastAPI (uvicorn/gunicorn) → EasyPanel app; env: `DATABASE_URL`/
  `SUPABASE_URL`/`SUPABASE_SERVICE_KEY`, `JWT_SECRET`, `LEGALDESK_USER/PASSWORD/BASE`,
  token lifetime. `/api/health` for liveness.
- **Frontend:** built static assets served by nginx (own EasyPanel app or same domain);
  `VITE_API_URL` → backend.
- HTTPS + routing via EasyPanel proxy. README documents the deploy steps.

## 9. Repo hygiene & living docs

- **`README.md`** — product overview, architecture, local dev, deploy-to-EasyPanel, env vars.
- **`PROJECT_STATUS.md`** — living, read-first status doc for agents: what this is, current
  status (built vs stubbed), architecture at a glance, known limitations, future plans/phases,
  verified facts, how to run/test/deploy (pointers). Updated each milestone.
- **`CLAUDE.md`** — agent operating guide: opens with "read `PROJECT_STATUS.md` first";
  conventions (TDD mandatory; secrets never committed/shipped; verified LegalDesk numbers
  are sacred; UI in PT-BR; new sources implement `Source` + emit `SectionKey`s; enforce the
  ADMIN/CLIENT boundary server-side); a growing "gotchas" list (OData v3, row duplication,
  query year 2026); where things live. Defers to `PROJECT_STATUS.md` for current state to
  avoid drift.
- Existing `docs/` preserved; `AUTOMATION_BUILD_GUIDE.md` remains the source of truth for
  the LegalDesk numbers.
- Conventional, focused commits.

## 10. Scope boundaries (YAGNI)

**In v1:** auth + roles, multi-tenant clients (MBC live + demo placeholder), in-UI month
picker + day-range refinement, the 15 tabs, design system, tests, CI, Docker, deploy.

**Out of v1 (noted, not precluded):** Juritis source implementation; Evolution/WhatsApp
notifications; password-reset emails; self-serve client onboarding UI; .xlsx export.

## 11. Decisions log (this brainstorm)

1. Architecture: **A** — FastAPI (reuse verified Python) + React/TS SPA.
2. Tenancy: two roles (ADMIN/CLIENT), one user table.
3. Auth: email+password (hashed) + JWT.
4. DB: **Supabase Postgres** via `supabase-py`; **no SQLAlchemy/Alembic** (2 small tables).
5. Data model: per-client **provider composing Sources**; **abstraction now, Juritis stubbed**.
6. Navigation: **A** — clients list → shared client workspace.
7. Visual: **A** — dark fintech; UI in **PT-BR**.
8. Period filter: **A** — month picker + **optional day-range within the month**; default
   full month; monthly KPIs stay monthly.
9. Deploy: EasyPanel (Docker) + Supabase; Evolution deferred.
10. Add `PROJECT_STATUS.md` (living) + `CLAUDE.md` (agent guide).
