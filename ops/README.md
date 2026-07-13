# ops/ — operational tooling

## EasyPanel deploy (redeploy prod from `main`)

Prod runs on EasyPanel (project **`rumo`**, services **`backend`** + **`frontend`**,
built from the GitHub repo via each service's Dockerfile). After pushing code to
`main`, the deployed containers only update when a **redeploy** is triggered.

Do it yourself with the helper (no dashboard needed):

```bash
ops/easypanel-deploy.sh backend      # rebuild + redeploy backend from main
ops/easypanel-deploy.sh frontend     # rebuild + redeploy frontend from main
ops/easypanel-deploy.sh backend restart   # restart only (no rebuild)
```

Credentials live in **`ops/easypanel.local.secrets`** (gitignored — the URL and
API key are there, never committed). If that file is missing, ask the operator for
the EasyPanel URL + API key and recreate it from the template inside the helper's
error message / this file's git history note. The tRPC API shape is documented in
that secrets file.

- Panel/API host: the EasyPanel dashboard IP (in the secrets file), **not** the app.
- The backend **app** API is `https://rumo-backend.xem1qi.easypanel.host`.
- Verify a deploy landed: hit `/api/health` (→ 200) and, for data, the
  token-protected `/api/ingest/<ano_mes>/summary`.

## SISJURI extraction agent

See `sisjuri-agent/README.md` — the on-box (MBC-LDESK01) extract/probe workflow,
the RDP command recipes, and the ingest credentials.
