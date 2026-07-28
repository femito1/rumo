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

### Verifying what is actually deployed

**Backend — `/openapi.json` is public and definitive.** It reflects the *deployed*
FastAPI route signatures, so any route/param change is provable:

```bash
curl -s https://rumo-backend.xem1qi.easypanel.host/openapi.json \
  | python3 -c "import sys,json; s=json.load(sys.stdin); \
print([p['name'] for p in s['paths']['/api/clients/{client_id}/closing']['get']['parameters']])"
```

**Frontend — compare the bundle hash** (there is no version endpoint):

```bash
curl -s https://rumo-frontend.xem1qi.easypanel.host/ | grep -oE 'assets/[^"]+\.js'
```

An unchanged hash after a deploy means the new image never replaced the old one.

### A deploy can be accepted and still fail

`deployService` returns `ok: {}` when the *trigger* is accepted; the build then runs
asynchronously and can fail afterwards, in which case the helper prints
`FAILED: {…"Command failed with exit code 1: docker buildx build…"}` and the service
keeps serving its previous image. **Always read the output** — and note the panel
exposes **no build logs**: every log/inspect tRPC proc (`getServiceLogs`,
`inspectService`, …) returns `Bad Request` on both GET and POST, so a failing build
has to be diagnosed by reproducing it locally:

```bash
git archive <sha> frontend | tar -x -C /tmp/x
cd /tmp/x/frontend && docker build --network host -f Dockerfile -t t \
  --build-arg VITE_API_URL=https://rumo-backend.xem1qi.easypanel.host .
```

If that passes but the server's fails, the cause is a **host** condition (Docker disk /
build-cache pressure, or a base-image registry pull) and needs operator action on the box.

## SISJURI extraction agent

See `sisjuri-agent/README.md` — the on-box (MBC-LDESK01) extract/probe workflow,
the RDP command recipes, and the ingest credentials.
