# RUMO platform — architecture reference

> Implementation-complete as of 2026-06. For **current** status, limitations, and deploy
> URLs see `PROJECT_STATUS.md`. For LegalDesk API details see `docs/LEGALDESK.md`.

## Product

Multi-tenant SaaS: **ADMIN** (RUMO) sees all clients; **CLIENT** sees only their own
monthly closing. Competence month in the UI + optional day-range for dated tabs.

Stack: **FastAPI** backend + **React/TypeScript (Vite)** SPA. Upstream credentials stay
server-side; the browser talks only to our JWT-protected API.

## Repo layout

```
rumo/
├── backend/app/     auth, tenancy, sources, closing, api routers
├── frontend/src/    SPA (login, clients, workspace, 15 tabs)
├── docs/            LEGALDESK.md, DESIGN.md (this file)
├── reference/       workbook + Postman (not runtime)
├── PROJECT_STATUS.md
├── CLAUDE.md
└── README.md
```

## Data layer (Juritis-ready)

Each upstream system is a **`Source`** emitting canonical **`SectionKey`**s.
**`ClosingProvider`** composes ordered sources; later sources override earlier per
`merge_policy`.

| Source | Status |
| --- | --- |
| `LegalDeskSource` | Live for MBC — wraps verified builder |
| `FixtureSource` | Demo client only — deterministic placeholder |
| `JuritisSource` | Placeholder — not wired |

When Juritis/TOTVS Backoffice access arrives, pick one path (no SPA/API contract change):

1. **Additive** — Juritis fills previously-MANUAL institutional lines.
2. **Partial override** — per-section precedence in `merge_policy`.
3. **Full replacement** — client provider lists `[JuritisSource]` only.

Cells carry `origin`: `legaldesk | juritis | manual | formula | fixture`.

## API surface

| Method & path | Role | Notes |
| --- | --- | --- |
| `POST /api/auth/login` | public | email + senha → JWT |
| `GET /api/auth/me` | auth | session restore; carries `must_change_password` |
| `POST /api/auth/change-password` | auth | self-service; clears `must_change_password` |
| `GET /api/clients` | ADMIN | client list (active only) |
| `POST /api/clients` | ADMIN | new tenant |
| `GET /api/clients/{id}` | ADMIN or owner | metadata + `available_months` |
| `GET /api/clients/{id}/closing` | ADMIN or owner | `?month=YYYY-MM&from=&to=` |
| `GET`/`PUT` `/api/clients/{id}/budget` | ADMIN or owner | annual Orçado, `?ano=` |
| `GET`/`POST` `/api/clients/{id}/users` | ADMIN or Gestor | list / create; POST returns `temp_password` **once** |
| `PATCH /api/clients/{id}/users/{uid}` | ADMIN or Gestor | `{active}` |
| `POST /api/clients/{id}/users/{uid}/reset-password` | ADMIN or Gestor | new `temp_password` |
| `POST /api/ingest` | agent token | SISJURI snapshot push |
| `GET /api/ingest/{ano_mes}/summary` | ADMIN | per-month extract state + `stale` |
| `GET /api/health` | public | liveness |

- Wrong client for CLIENT role → **403**.
- Open/future `month` → **422** (PT-BR message).
- KPIs always reflect the **full month**; only dated tabs react to `from`/`to`.

### Roles

| Role | Sees | May provision |
| --- | --- | --- |
| `ADMIN` (RUMO) | every client, detail tabs + deck | anything |
| `CLIENT_ADMIN` ("Gestor") | its own client, **deck only** | ordinary `CLIENT` users of its own client |
| `CLIENT` | its own client, deck only | — |

Three rules the code depends on, each with a named test:

- **Gate RUMO-only surfaces on `role == "ADMIN"`, never on `!= "CLIENT"`.** The tab
  boundary was once a deny-list, so any new role fell through to RUMO's internal tabs.
- **A Gestor may not create another Gestor** — the role would be self-propagating
  inside a tenant. RUMO mints Gestores; a Gestor mints team members. It also cannot
  manage itself, so it cannot lock its own firm out.
- **Mutations resolve the STORED target and check *its* role/client**, never the
  request body. A reset-password body carries no role, so body-only gating would have
  let a Gestor mint a credential for a RUMO admin. Cross-tenant misses answer **404**,
  not 403, so a caller cannot confirm an id exists elsewhere.

Roles are re-read from the DB on **every** request (`require_user`), so a change takes
effect immediately rather than at token expiry — and a deactivated client's users lose
access at once (`403 Cliente inativo`).

## Persistence

Supabase Postgres via `supabase-py` — tables `clients`, `users` (`app/db/schema.sql`).
No ORM. Auth is our own argon2 + JWT on top.

## Selling this to a second client — what works and what is bespoke

The client expects to resell the product (2026-08-05). Measured, not estimated, so
nobody promises the wrong thing:

**Already multi-tenant.** Every table is keyed by `client_id`
(`clients`, `users`, `budgets`, `area_transfers`, `sisjuri_snapshots`).
`build_provider_for` dispatches on `client.provider`, and each source composes per
client. Upstream credentials live in `clients.provider_config` (see below), so one
process now serves several LegalDesk installations. Only ~10 hardcoded `"mbc"` strings
remain in the backend, all seed data or documented back-compat defaults.

**Per-client credentials.** `provider_config` shape, every key optional and falling
back to the environment individually:

```json
{"legaldesk": {"base": "...", "user": "...", "password": "...", "timeout": 120, "top": 5000}}
```

⚠ It holds secrets: never serialize it into a response (`_client_public` omits it, and
a test asserts no client endpoint leaks it) and never send it to the browser.

**Per-client accounting shape** (`app/tenancy/tenant_config.py`). Áreas, the account
map and the two rates are now configuration, not constants. MBC's values are the
DEFAULTS, so its empty config reproduces today's numbers exactly:

```json
{
  "areas": [
    {"label": "Tributário",  "match": ["tribut", "fiscal"]},
    {"label": "Trabalhista", "match": ["trabalh"]}
  ],
  "accounts": {"020.060.0040": "Administrativas"},
  "amortizacao_mensal": 8117.0,
  "bonus_reserve_rate": 0.10
}
```

* `areas` — any number of practice areas, not three. `match` lists the substrings that
  identify the área in a SISJURI grupo name (SISJURI drops spaces, so matching is
  substring-based); omit it and the label itself is used. ⚠ Each grupo must resolve to
  **exactly one** área: three loops in `dre.py` ADD over every match, so an ambiguous
  matcher books the same money twice. This is why MBC's Econômico is anchored on
  `econô`/`econo` and not a bare `econ` (which `equipecontencioso` contains).
* `accounts` — an **overlay** on the built-in CONTA3 map, not a replacement. A firm on
  the same SISJURI install shares most of the tree and only names its exceptions.
* A malformed config degrades to MBC's defaults rather than taking the closing down.

### Onboarding a second client

1. `POST /api/clients` `{id, name, provider}` (ADMIN). Use `legaldesk+sisjuri` for a
   firm on the same stack.
2. Set its `provider_config` **directly in Supabase** (never through the API — it holds
   the LegalDesk password): the `legaldesk` block plus the `areas`/`accounts` above.
3. `POST /api/clients/{id}/users` to create its Gestor; hand over the one-time password.
4. Point the SISJURI agent at the new tenant (`meta.client_id` in the extract payload)
   so its snapshots land under the right `client_id`.
5. Enter its budget via `PUT /api/clients/{id}/budget`.

**Still MBC-specific:**

| Coupling | Where | Note |
| --- | --- | --- |
| SIGLA→área (`ECT`/`EDE`/`ESP`) | `ops/sisjuri-agent/extract.sql` | cost-centre codes are per install; the extract is per-tenant anyway |
| 15 workbook tab layouts (20.9k lines) | `app/closing/tab_layouts.py` | mirrors MBC's workbook 1:1; **its generator (`gen_tab_layouts.py`) no longer exists**, so it cannot be regenerated for a different workbook shape. A second client gets the deck + DRE (which are config-driven) but not a 1:1 mirror of ITS workbook. |

So: **a second firm on the same stack is now mostly configuration** — credentials,
áreas, account exceptions, a budget. A client on a different ERP needs a new `Source`
implementation, which is what the protocol is for. The detail tabs remain MBC-shaped.

### The two tests that make this safe to change

* `tests/test_mbc_golden.py` — a fingerprint (count + sum + sha256) of **every number**
  the assembler produces for the six closed 2026 months. A generalisation that moves any
  MBC number fails it. Its own sensitivity was verified by perturbing one value by
  R$ 0,01 and confirming it is caught. ⚠ Never "update the expected values" to make it
  pass; that is the one move it exists to prevent.
* `tests/test_second_client.py` — drives the real provider with a non-MBC config and
  asserts the payload reshapes (its áreas, not MBC's; a different área count) while the
  institutional headline off the same snapshot is unchanged, since relabelling áreas
  must not create or destroy money.

## Deploy

Docker images on EasyPanel; frontend nginx serves static build with `VITE_API_URL` pointing
at backend. See `README.md` and `PROJECT_STATUS.md` § production.
