# PROJECT_STATUS.md

> **Living status document. Read this first.**
> Agents and engineers working on this repo should treat this file as the
> single source of truth for *current* state, limitations, and plans.
> Keep it updated at the end of every milestone. When it disagrees with
> older docs, this file wins (except for the sacred LegalDesk numbers, which
> live in `docs/LEGALDESK.md`).

**Last updated:** 2026-07-03
**Product:** RUMO — Plataforma de Fechamento Mensal Multi-Cliente
**Architecture:** `docs/DESIGN.md` · **LegalDesk:** `docs/LEGALDESK.md`

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
  Tables have **sticky column headers** (`thead` pinned inside the scroll body);
  rich tabs (Meta, Base_Resultado, Resumo Recebidas, Faturas Centro Custo) render
  their real structure and fill not-yet-available cells with **"ainda não temos"**
  instead of a placeholder paragraph.
- **`.xlsx` export:** `lib/exportClosing.ts` turns a `ClosingPayload` into a
  multi-sheet workbook (one sheet per tab). WorkspacePage exposes "Exportar tudo"
  (all sheets) and "Exportar esta página" (current tab only). Uses SheetJS
  (patched CDN build `xlsx-0.20.3`, **0 npm audit vulns**), lazy-imported so it
  ships as a separate chunk and stays out of the initial bundle.
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

### Workbook-faithful DRE rework (2026-07-02)
The closing tabs now mirror `Copy of Fechamento MBC 02.2026.xlsx` in vocabulary
and structure (base = **Recebimento**, not Faturamento):
- `app/closing/workbook_layouts.py` — canonical section vocabulary + account-
  family rollups (`020./040.*` → institutional sections by `nome_conta_pai`,
  `030.*` → Custo equipe, Impostos → Impostos).
- `app/closing/dre.py` rebuilt: **Institucional** (DRE block + section-by-section
  expense breakdown with sub-accounts, % of Recebimento), **area tabs**
  (Recebimento/Custo equipe/Comissão/Despesas Equipe/Despesa Institucional/
  Resultado Bruto), **Base_Resultado Mensal** (hierarchical: per-lawyer custo
  equipe grouped by area + institutional sections/sub-accounts + Impostos).
- `app/closing/secondary_tabs.py` — **Amortização** real fixed schedule (8 × 2022
  originations, 60 parcelas each = R$ 8.117,32/mês) + **Rateio Mensal** per-area
  shares.
- `ops/sisjuri-agent/extract.sql` extended with `custo_equipe_prof` (per-lawyer ×
  account 030.*, area via professional→grupo). **Needs a re-backfill** to
  populate historical months (existing snapshots lack this key; Base_Resultado
  per-lawyer rows show only for months re-run with the new extract).

### Per-area Recebimento — RULE CONFIRMED, now auto-derived (2026-07-03)
Per-area **Recebimento** *is* derivable from SISJURI after all (the earlier
2026-07-02 note below is superseded). The receipt view splits by **case → área
jurídica**: `GERENC_VW_POSFIN_RESULTREC` (via `ID_CASO`) → `CAD_CASO.
ID_AREAJURIDICA` → `CAD_AREAJURIDICA.NOME`, summing `VALOR1`. Verified to the
centavo vs the workbook base numbers for Jan & Fev 2026. See
`docs/SISJURI_QUERIES.md` §9 (2026-07-03) for the query + table.

Built on top of that:
- **`extract.sql`** emits `recebimento_area` (this split), `faturamento_area`
  (same split on the faturamento view) and `faturas_analitico` (per-CASE
  faturamento detail from `GERENC_VW_POSFIN_RESULTFAT`). All 29 months
  (2024-01 → last closed) backfilled to Supabase (2026-07-03). The agent emits
  the JSON in DBMS_OUTPUT chunks so it never hits sqlplus's 32767 LINESIZE
  ceiling (see `run-agent.ps1`/`extract.sql`).
- **`dre.py`** `RealizadoInputs.area_recebimento` parses `recebimento_area` and
  folds names onto the three areas; area tabs' Recebimento is SISJURI-derived
  and **no longer hand-fillable** (with `Resumo_Recebidas` transfers applied
  upstream). Manual per-area recebimento is rejected by the API and ignored by
  the assembler.
- **`Resumo_Recebidas` transfers** modeled as `area_transfers` (origem→destino
  deltas, net 0) overlaid on the base — new `app/manual/transfers.py` +
  `area_transfers` table. These small cross-area reclassifications are still
  finance-entered (no DB rule), but the *base* is now automatic.
- **Distribuição de Lucros extras** block surfaced in `base_resultado` (Bônus
  equipe, DL Extraordinária, DL excedente sócios/MV, Repasse Cacione), values
  from optional snapshot `distribuicao_extras`, blank otherwise.
- **Budget granularity:** `BudgetEntry.monthly_amounts` (optional 12-value array)
  → workbook per-month Orçado; `monthly_budget(entries, month=...)` selects it;
  `budgets.monthly_amounts` jsonb column + API accepts/returns it. On a
  legacy/canonical key collision the entry with monthly detail wins (so an
  imported granular budget is never shadowed by an old annual seed).
- **Budget import from workbook:** `app/budget/workbook_import.py` +
  `scripts/import_budget.py` parse the `DRE 2026` sheet (per-area Custo equipe,
  institucional Recebimento/Despesas/Imposto/Amortização/Reserva) into
  `BudgetEntry`s with 12-month detail, upserted on (client,ano,area,line) so the
  **manual budget API still works** (imported lines refresh in place, manual
  lines under other keys are preserved). MBC 2026 imported (2026-07-03); the 4
  legacy annual-only seed rows were removed.
- **Meta dashboard:** new `meta_dashboard` tab (annual goal 8.060.000, monthly
  goal, this-month attainment, 12-month table) via `assemble_meta`.

Still manual (no verified DB rule): per-area Comissão / Despesas Equipe /
Despesa Institucional, the `area_transfers`, and `distribuicao_extras`.

**Blocked on more workbook samples:** automating the hand-built per-lawyer
ledger (`Base_Resultado Mensal_V2`: Custo equipe / Comissão / Despesas Equipe,
and the `Despesa Institucional` rateio allocation that depends on it). Those
cells contain per-lawyer manual splits (`=12500-C8`, `=3182.83/2`); we need
several months to confirm the structure is stable before automating.

### Operator steps to finish the deploy
1. Apply the new DDL in Supabase (`area_transfers` table + `budgets.
   monthly_amounts` column + earlier `manual_actuals` — see `app/db/schema.sql`).
2. Update the on-server `extract.sql` and **re-run the backfill** so snapshots
   carry `recebimento_area`, `faturamento_area`, `faturas_analitico`
   (see "When to re-run the backfill" below).
3. Optionally verify `FAT_FATURA` columns with `probe_faturas_analitico.sql`
   before trusting `faturas_analitico`.

### Test counts (as of last update)
- Backend: **135 passing** (`cd backend && pytest`).
- Frontend: **49 passing** (`cd frontend && npm run test`).

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
├── docs/               LEGALDESK.md, DESIGN.md
└── reference/workbook/ ground-truth xlsx + Postman (not runtime)
```

Data flow: `provider`/`provider_config` on a client → ordered `Source`s →
`ClosingProvider.build_closing(period, day_range)` → provider-agnostic
`ClosingPayload` → SPA renders it regardless of upstream source.

---

## 4. Verified facts preserved (SACRED — never silently regress)

Source of truth: `docs/LEGALDESK.md`. Locked by backend tests
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

> **UPDATE 2026-07-01 — may be partly obsolete.** The institutional expenses this
> section assumes live only in TOTVS Backoffice were found in the **SISJURI Oracle
> DB** (`FINANCE` schema), readable today via the bridge server. See
> `docs/SISJURI_DB.md` §"Full-closing coverage". A `FinanceDbSource` could supply
> the expense side without waiting for the Juritis API. Revisit the paths below
> in light of that. Reconciliation of exact per-line DRE definitions is still open.

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

## 6b. SISJURI direct DB access (discovered 2026-07-01)

An **Oracle 19c** database behind SISJURI is reachable **read-only** through the
authorized Windows bridge server `MBC-LDESK01` (the Power BI gateway host). It
contains the **`LDESK`** schema (601 tables) — the same LegalDesk data RUMO pulls
via OData — and **`SSJR`** (704 tables) of SISJURI core data. Confirmed: real
`SELECT` on `LDESK` billing tables, 98 months of history (2018-05 → 2026-06),
53 May-2026 invoices matching the sacred `faturas_emitidas`. This opens an
**audit / fallback / alternative-`Source`** path to the API. Details, schema map,
and the (hard-won) `sqlplus`-over-RDP invocation recipe live in
`docs/SISJURI_DB.md`; the implementation-ready SQL per DRE line and the egress
options live in `docs/SISJURI_QUERIES.md`. The DB and RDP credentials used during
discovery were shared out-of-band and **must be rotated**; never commit them.

**Now partially wired (2026-07-02).** Full closing proven sourceable from the DB
via three objects + one fixed formula: revenue (`GERENC_VW_POSFIN_RESULT*`),
expenses gross/competence (`GERENC_LANCAMENTORESUMO`), pró-labore gross
(`CONTASPAGAR.CPGNVALORBASE`), and reserva de bônus = 10% da margem líquida
(finance-confirmed). Built so far:

- **On-server agent** `ops/sisjuri-agent/{extract.sql, run-agent.ps1}` — pure
  PowerShell + the existing `sqlplus` (no Python on the box), emits one JSON
  snapshot per competence month, TLS-1.2 outbound POST. Verified on the server:
  `closing_2026-02.json` (recebimento 319.233,58; 30 expense accounts).
- **Egress = Option A** (server pushes to VPS): `POST /api/ingest` (bearer-token,
  `INGEST_TOKEN`) stores snapshots via the snapshot store.
- **Snapshots persist in Supabase (2026-07-03).** `sisjuri_snapshots`
  (`client_id, ano_mes, payload jsonb`, PK `(client_id, ano_mes)`) is now the
  durable, multi-tenant source of truth — the whole financial dataset lives in
  Postgres alongside `budgets`/`manual_actuals`, not on the VPS disk.
  `SupabaseSnapshotStore` is selected in prod; the filesystem `SnapshotStore`
  (`SNAPSHOT_DIR`) remains the `USE_FAKE_REPO`/local-dev fallback and gained
  client scoping (with a legacy clientless-filename read fallback). `client_id`
  flows through `/api/ingest` (`meta.client_id`, default `"mbc"`) and the closing
  read path (`client.id`). The agent stamps `meta.client_id`. A one-time
  token-protected `POST /api/ingest/migrate-fs-to-supabase` copied the existing
  30 months (2024-01 → 2026-06) into Supabase; verified the closing endpoint now
  reads from Supabase with the sacred numbers intact.
- **`app/sources/sisjuri_db.py`** (`SisjuriDbSource`) consumes a snapshot and
  emits `SectionKey`s, encoding the pró-labore-gross and bonus-reserve rules.
  Tested against a recorded fixture (`tests/fixtures/sisjuri_2026_02.json`).
- **`ClosingProvider`** now has a `legaldesk+sisjuri` mode: composes
  `LegalDeskSource` (KPIs) with `SisjuriDbSource` in augment mode (institucional),
  preserving the sacred numbers.
- **LIVE on EasyPanel (2026-07-02):** `POST /api/ingest` is deployed and verified
  end-to-end — 401 without/with-wrong token, 422 on missing `meta.ano_mes`, 200 on
  the real Feb-2026 snapshot, persisted to a named volume `sisjuri-snapshots` →
  `/data/snapshots` (survives redeploys). **Root-cause fix:** the `backend` service
  was building via **Nixpacks** (wrong start cmd `python -m rumo-backend` → boot
  crash / 502); switched `build.type` to **`dockerfile`** so it uses the tested
  `backend/Dockerfile` (`uvicorn app.main:app`). `INGEST_TOKEN` is set in the
  EasyPanel backend env (not committed).
- **SCHEDULED & LIVE (2026-07-02):** `RUMO-SISJURI-Agent` runs daily at 06:00 on
  MBC-LDESK01 for the previous full month, extracts, and pushes to the VPS.
  Verified `LastTaskResult=0` (2026-06 snapshot uploaded). Constraints found on
  that box: `bia4u` is **not** a local admin, so env vars are **User-scope** and
  the task **runs as `bia4u`** (not SYSTEM). "Run whether logged on or not"
  needed the *Log on as a batch job* right, which an admin granted to `bia4u`
  (error `2147943785` until then). `register-task.ps1` now has `-StorePassword`
  (run-as-user) and `-AsSystem` modes.
- **Agent upload:** must send the body as **UTF-8 bytes** with an explicit
  charset (fixed in `run-agent.ps1`); a plain string body 400s on FastAPI,
  especially with accented account names.
- **Still TODO:** rotate the DB/RDP credentials that were shared in chat.

---

## 6c. Workbook mirror + manual budget (2026-07-02)

The deployed closing page now mirrors the MBC workbook DRE structure and adds a
manually-entered Orçado (budget) for Orçado × Realizado variance. Built:

- **DRE engine `app/closing/dre.py`** — a canonical DRE line-key registry
  (`faturamento`, `custos_diretos`, `despesas_indiretas`, `resultado_bruto`,
  `margem_bruta`, `impostos`, `amortizacao`, `resultado_liquido`,
  `margem_liquida`, `reserva_bonus`) shared by the SISJURI source, the budget
  domain and the frontend. `assemble_dre_sections` computes the **Institucional**
  block plus three area blocks (Contencioso/Economico/Arbitragem) and
  `areas_sintetico`, each row carrying `orcado | realizado | variacao | desvio%`.
  It **recomputes** from clean sources (not the workbook cells, which have
  `#REF!`s). Reserva de bônus = 10% da margem líquida; amortização = fixed
  monthly institutional installment.
- **`SisjuriDbSource` expanded** — emits rich, grouped expense detail
  (`INSTITUCIONAL_ANO`, section subtotal + indented sub-accounts) plus
  `RATEIO_MENSAL` (per-area team cost + per-lawyer rateio), prolabore (gross/net)
  and distribuição tables. The assembled DRE owns `INSTITUCIONAL`.
- **Budget domain `app/budget/`** — `budgets` Supabase table
  (`client_id, ano, area, line_key, annual_amount`; DDL in `app/db/schema.sql`),
  `BudgetRepository` (supabase + in-memory seeded), annual granularity split
  evenly to monthly. `BudgetSource` emits the `ORCAMENTO_2026` reference tab.
- **Budget API** — `GET/PUT /api/clients/{id}/budget?ano=YYYY`, guarded by
  `require_client_access` (ADMIN + that client's CLIENT may edit). Validates
  area/line keys. Seeded placeholder budget (Meta 8.060.000/ano) for MBC 2026.
- **Provider composition** — `legaldesk+sisjuri` now composes
  LegalDesk → SisjuriDb → Budget → **Assembler** (last, overrides). Headline KPIs
  (`resultado_bruto`, `margem_bruta`, `resultado_liquido`, `margem_liquida`,
  `reserva_bonus`) are lifted from the assembled DRE into the `kpis` map. When no
  snapshot exists the DRE still renders with `snapshot_missing: true`.
- **Frontend** — new KPI cards (with `formatPercent`/`formatNumber` and a
  `KpiCard format` prop); `RichTabView` renders DRE percent columns, section/total
  rows and indented sub-accounts; a PT-BR **missing-data banner**
  ("Dados institucionais ainda não importados para este mês") on institucional/DRE
  tabs; a **budget editor** panel (`BudgetEditor` + `useBudget` hook in its own
  module) for ADMIN and CLIENT. Spinner already existed. New rich tabs export via
  the existing `exportClosing.ts` automatically.
- **Backfill** — `ops/sisjuri-agent/backfill.ps1` loops 2024-01 → last closed
  month calling `run-agent.ps1` per month (one-shot catch-up; the daily task
  keeps recent months fresh). Documented in the agent README.
- **MBC provider** — the fixture/demo MBC client is now `legaldesk+sisjuri`. The
  **prod `clients.provider` for MBC must be set to `legaldesk+sisjuri`** for this
  to show live.

**Tests:** backend 95 passing (new: DRE assembler math/variance/margins,
BudgetSource, budget repo/API auth boundary, provider composition with all four
sources, snapshot_missing flag; sacred-number lock still green). Frontend 44
passing (new: `formatPercent`/`formatNumber`, DRE percent + grouped/indent
rendering + banner, BudgetEditor). Backend `ruff`+`mypy` clean; frontend
`lint`+`typecheck` clean.

**Operator TODO before this is fully live:**
1. Apply the `budgets` DDL (`backend/app/db/schema.sql`) to Supabase.
2. Set MBC's `clients.provider = 'legaldesk+sisjuri'` in Supabase.
3. Deploy backend+frontend (GitHub → EasyPanel, Dockerfile build).
4. Run `backfill.ps1` once on MBC-LDESK01, then verify a few months via
   `GET /api/ingest/{ano_mes}/summary`.

---

## 7. Future plans / phases (out of v1, noted not precluded)

- Implement `JuritisSource` once the API is available (see §5).
- Evolution API (WhatsApp) closing notifications.
- Password-reset emails; self-serve client onboarding UI.
- Per-request audit logging for ADMIN cross-client access.

---

## 8. Run / test / deploy

See `README.md`. Quality gates: backend `ruff` + `mypy` + `pytest`; frontend `lint` +
`typecheck` + `vitest`. Update this file when status changes.

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
