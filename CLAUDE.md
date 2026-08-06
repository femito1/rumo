# CLAUDE.md — Agent Operating Guide

> **Read `PROJECT_STATUS.md` first.** It is the living source of truth for
> current state, what is built vs stubbed, known limitations, and plans.
> This file is the *durable* operating guide: conventions and hard-won
> gotchas that rarely change. When current-state details here and in
> `PROJECT_STATUS.md` ever disagree, `PROJECT_STATUS.md` wins.

## Start here

0. **Read the top section of `PROJECT_STATUS.md` (2026-08-06) first** — provisioning +
   branding + the per-client config layer, all **live and verified in production**. Two
   things to carry forward: `schema.sql` edits are **no-ops on an existing database and no
   test catches it** (pair every schema change with a hand-run `alter table`), and
   **`tests/test_mbc_golden.py` must never be "updated" to pass** — it is the fingerprint
   that proves a generalisation did not move MBC's client-facing numbers. Then
   `docs/HANDOFF_2026-08-05.md` for the accounting state. The contract is **v4**. What
   that handoff carries, in short:
   - **The client list is EMPTY** — nothing waits on finance. The R$35,52 was closed by the
     client; the convênio ruling was withdrawn when the Parte MBC became **derived**
     (`dre.convenio_mbc_shares`), which closed the YTD Resultado Bruto gap from −7.640,50 to
     −5.003,04. ⚠ RB **January** inside that is an extrapolation we own.
   - **The vale-ADM rule is client-confirmed correct** (*"o sistema está certo"*) — do NOT
     converge the workbook's Jan–May, which lumps three people into one line by its own
     account.
   - **One open item where the obvious fix is measurably wrong:** the Seguro
     (`020.060.0040`) belongs in Administrativas per the client and per the DB, but our
     account bundles two seguros and no value/count split survives 2025-10/11. Flipping the
     mapping takes Ocupação from 2 exact ties to 0. Read the handoff before touching it.
   - A v5 chunk-guard fix was attempted and **REVERTED the same day** (it corrupted the live
     store; the box is Oracle 11g, which rejects `SET TRIMSPACE`, so the root-cause theory
     was wrong — see `docs/HANDOFF_v5_reverted_2026-08-04.md`). The whitespace glue it chased
     is a known, money-neutral cosmetic defect; do not re-attempt without validating against
     the box first.
   - ⚠ **We are still ~R$5,0k apart from the workbook on Resultado Bruto YTD** — every
     component has a named cause, but "explained" is NOT "matching"; do not tell the client
     the numbers agree. ⚠ And **repairing the workbook's r204/205/206 would NOT close that
     gap** — measured: it halves the per-área despesa error but `r198` does not reference
     those rows, so the headline does not move at all.
   - Workbook-vs-system differences live in `docs/DIFERENCAS_ACUMULADO_2026.md`, not in the
     product; the deck labels a partial month + blanks a withheld card.

   `docs/HANDOFF_2026-08-04.md` is the *opinion* layer for the convênio session: hypotheses,
   a shipped judgement call that could have gone another way, and what has no test guarding it.
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
- **The role boundary is enforced server-side**, on every request, in FastAPI
  dependencies (`require_user`, `require_admin`, `require_user_manager`,
  `require_client_access`, `assert_may_grant`/`assert_may_manage`,
  `active_client_or_404`). Hiding a frontend button is never the security boundary.
  Three roles: `ADMIN` (RUMO, everything), `CLIENT_ADMIN` ("Gestor" — its own client's
  deck **plus** provisioning that client's ordinary users), `CLIENT` (its own deck).
  `is_admin` means RUMO only — a Gestor must never satisfy it. Full table and the three
  load-bearing rules: `docs/DESIGN.md` § API surface → Roles.

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

- **Role gates are ALLOW-lists. Never `!= "CLIENT"`.** `_visible_tabs`
  (`app/closing/provider.py`) and `WorkspacePage.tsx` both once denied on
  `role == "CLIENT"` and fell through to RUMO's full detail-tab set for every other
  role — so adding `CLIENT_ADMIN` silently handed a client's own manager the internal
  tabs. Gate on `role == "ADMIN"`. Guarded by a test parametrized over several role
  strings precisely so a future role cannot reintroduce it.

- **Any mutation of an existing user must resolve the STORED target and check ITS
  role/client** (`assert_may_manage` in `app/api/deps.py`), never the request body. A
  reset-password body carries no role and no `client_id`, so a body-only check passes
  vacuously — a Gestor could mint a credential for a RUMO admin. And
  `require_client_access` validates the `{client_id}` **path segment**, not the target.
  Cross-tenant misses answer **404, never 403**: a caller must not be able to confirm an
  id exists under another tenant. A Gestor may not create another Gestor (the role would
  be self-propagating), which also means it cannot deactivate itself.

- **`schema.sql` is `create table if not exists`, so editing a column or CHECK is a
  NO-OP on an existing database — and no test catches it** (the fakes have no
  constraints). Pair every schema edit with an idempotent `alter table …` block in the
  same file *and* run it by hand before deploying. This is how a `role` CHECK would
  have rejected the first Gestor in production while all tests passed green.

- **`clients.provider_config` holds upstream credentials.** Per-client LegalDesk
  settings live there (`_LegalDeskSettings.from_provider_config`), falling back to env
  per key so MBC's empty config is unchanged. It must never be serialized into a
  response — `_client_public` omits it and a test asserts no client endpoint leaks it.
  Related trap: config read as *dataclass field defaults* is evaluated at **import**,
  which is what pinned the whole process to one LegalDesk tenant; use a `from_env`
  classmethod so the environment is read at call time.

- **`<html lang>` must be `pt-BR`.** With `lang="en"` on a PT-BR app, Chrome translated
  the month picker's own abbreviations back into English — `Set`→"definir",
  `Out`→"fora", `Ago`→"atrás" — live on a client's screen during the 2026-08-05
  meeting, while the numbers looked fine, so it read as our bug. The month grid also
  carries `translate="no"`.

- **The agent's `.ps1` files must be PURE ASCII.** MBC-LDESK01's PowerShell 3/4 reads
  BOM-less UTF-8 as cp1252, so an em-dash's trailing byte becomes a closing quote and
  the parse fails with a misleading "Unexpected token" far from the real line.
  `ops/sisjuri-agent/lint_ps1.py` enforces it (CI job `ops-scripts`).

- **Known discrepancies live in a DOCUMENT, not in the product.** Client decision
  (2026-08-03): workbook-vs-system differences are explained in
  `docs/DIFERENCAS_ACUMULADO_2026.md`, regenerated by
  `backend/scripts/build_diferencas_doc.py` from live snapshots + the June workbook.
  - **The document is DESCRIPTIVE, never prescriptive.** Client instruction (2026-08-05):
    *"they will not change anything, this is just for understanding purposes."* No "copiar as
    fórmulas", no "O que fazer" section, no asking finance to confirm or update anything.
    Explain what each side does and why the numbers differ; stop there. A *measured*
    consequence is still fine as an observation ("if June's formulas applied to Jan–May the
    per-área error would halve but the Resultado Bruto would not move") — that one is worth
    keeping precisely because it is counter-intuitive. The `precisamos` field in `CAUSAS` was
    deleted for this reason (it was also never rendered).
  The former in-app "Diferenças conhecidas" panel (`app/closing/notes.py` +
  `NotesPanel.tsx`) was **removed** — do not reintroduce an in-app notes surface
  without asking. Materiality is R$ 1.000 on the YTD **or on any single month** ("R$ 4,80
  does not matter, R$ 1.900 does"); smaller ones are summed as a named remainder, never
  dropped. The or-any-month half is load-bearing, not decoration: YTD-only hid
  *Econômico · Despesas Equipe* (−31,45 YTD, but −1.166,75 in Feb and +1.504,72 in May)
  under "menores" in a document whose own second paragraph warns that a total which nets
  to zero is not validated. Each entry keeps one format: *planilha value + its cell
  reference · our value · signed delta · cause · where to verify · what we need from
  finance*. The causes are HAND-WRITTEN in the generator — nothing inspects a value or
  decides a number is wrong (that guard layer was explicitly rejected). **Fix a cause ⇒
  delete its entry in the same commit.**
  - **Every printed total must be reachable by adding the printed parts.** Use the single
    `_delta` helper (`round(ours) − round(theirs)`), never `round(ours − theirs)`: the
    latter makes Σ(months) ≠ Acumulado, and *Contencioso · Custo equipe* really did print
    **+3.140,19 in the summary and +3.140,20 in its own detail table**. The workbook
    carries a trailing half-centavo on many cells, so this is not hypothetical.
  - **Cite the sheet, not just the row.** The prose's *Conferir* lines name
    `Base_Resultado Mensal_V2` rows while every table is keyed to
    `Areas Sintetico atualizado`. Naming only "linha 204" sends a finance reader to the
    wrong tab, where that row is blank or means something else entirely.
  - **A line-level delta is not an answer.** "Despesa Institucional differs by R$ 1.400"
    says something moved, not *what* — the client's own request (2026-08-05). The two
    biggest despesa lines are therefore decomposed to the account: `_detalhe_despesas`
    (ten families × six months, then the individual accounts per differing family+month,
    agreeing ones netted out, subtotals printed) and `_detalhe_rateio` (the pool and the
    Custo-equipe share, which reproduce each per-área number to the centavo on both sides).
    Before presenting any such grid as complete, verify BOTH sides reconcile — the families
    sum to `r198` and to our `despesas`, and each family's leaves sum to its own header, in
    every month. They do; that is what makes it safe to say "sem resto".
  - **Match leaves by VALUE, never by label.** The two sides genuinely name accounts
    differently (our one *Serviços de Informática* = the book's *Suporte de Informática* +
    *Suporte Totvs*; the book splits *Associações* three ways by área, we keep one account).
    A label join would emit confident rows that are simply wrong. `_conciliar` pairs equal
    values and reports everything else as unmatched — and the unmatched remainder must
    reconstruct the family delta, which is the claim the document makes in prose.
  - `tests/test_diferencas_doc.py` guards the rules above (14 tests). It tests the pure
    helpers only — the generator itself needs live Supabase, which is why it went untested
    for so long.

- **A partial month must be labelled INSIDE `#presentation-root`.** The print CSS
  (`index.css`) hides everything outside that element, so the workspace `.partial-banner`
  never reached the exported PDF — an open month exported as a finished closing. The deck
  payload carries `is_partial`/`status_label` (from the same `_period_payload` helper as
  the `period` block, so they cannot disagree), the cover swaps its band, and every slide
  footer carries the marker because every slide is one printed page.

- **A WITHHELD cell is not zero.** On the hard-rule month (2026-05) the R$0,01
  workbook-tie rule blanks a diverging cell, so a card that sums components must use
  `_sum_all_or_none` (blank if any part is missing), not `_sum_or_none` (sum what is
  present). The Despesas card silently understated May by ~R$108k this way.

- **The `historico` free text carries the ARITHMETIC — never truncate it.** Finance writes
  the calculation into the lançamento text (*"Vale transporte / Calculo: 14 dias x
  R$ 18,76"*), so it is the fastest way to validate a figure: every vale is a whole number
  of days at a per-person rate. The extract capped three of these at 60/80 chars, cutting
  the text off exactly where the calculation began — widened to **300** in contract **v4**
  (2026-08-03). ⚠ Widening can MOVE MONEY: `despesas_liquido.net_by_account` reclassifies
  on markers found inside that string, so a longer histórico may match where a truncated
  one did not. Check `020.030.0020` and `040.040.0030` after any re-extract; the guard is
  `test_widening_the_historico_must_not_move_copa_to_informatica`.

- **A version bump is a CONTRACT marker, not a correctness claim** (v2 certified a rule
  that never fired). Pair every bump with a test that ties a real month, and remember the
  `stale` flag on `/api/ingest/summary/<mes>` is what tells an operator which months still
  need re-extracting.

- **`formatBRLShort` is NOT additive, and precision does not fix it.** Rounded parts
  never sum to a rounded total: measured over 200k random 6-month rows, ~49% diverge
  visibly at one decimal *and* at two. Adding decimals made a real live row worse. The
  deck therefore DISCLOSES the rounding (`.slide-note`) instead of chasing exactness in a
  K format. Use `formatBRL` where an exact figure matters.

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
