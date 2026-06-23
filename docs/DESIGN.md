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
| `GET /api/auth/me` | auth | session restore |
| `GET /api/clients` | ADMIN | client list |
| `GET /api/clients/{id}` | ADMIN or owner | metadata + `available_months` |
| `GET /api/clients/{id}/closing` | ADMIN or owner | `?month=YYYY-MM&from=&to=` |
| `GET /api/health` | public | liveness |

- Wrong client for CLIENT role → **403**.
- Open/future `month` → **422** (PT-BR message).
- KPIs always reflect the **full month**; only dated tabs react to `from`/`to`.

## Persistence

Supabase Postgres via `supabase-py` — tables `clients`, `users` (`app/db/schema.sql`).
No ORM. Auth is our own argon2 + JWT on top.

## Deploy

Docker images on EasyPanel; frontend nginx serves static build with `VITE_API_URL` pointing
at backend. See `README.md` and `PROJECT_STATUS.md` § production.
