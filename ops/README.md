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
error message / this file's git history note.

Print the last build log for a service (the only way to see *why* a build failed):

```bash
ops/easypanel-deploy.sh frontend logs
```

### The API is oRPC at `/api/rpc`, POST-only, `{"json": …}`-wrapped

```
POST http://<panel>/api/rpc/<namespace>/<proc>      # slash-separated, NOT dotted
Authorization: Bearer $EASYPANEL_API_KEY
{"json": { …input… }}
```

**It is not tRPC at `/api/trpc`.** That path answers every request — valid proc,
invalid proc, GET or POST — with a generic `{"error":"Bad Request","statusCode":400}`,
which is indistinguishable from an auth or input error. A debugging pass against it
concluded "only POST mutations work and the panel exposes no logs"; both were wrong.
If a call 400s, check the path shape and the `{"json":…}` envelope before believing
the proc doesn't exist. Real input errors come back as
`{"json":{"code":"BAD_REQUEST","message":"Input validation failed","data":{"zodErrors":{…}}}}`
— the `zodErrors` map names the missing fields.

Useful procs (all POST, all `{"json":…}`):

| proc | input | use |
|---|---|---|
| `projects/listProjectsAndServices` | `{}` | every service's `source`, **`build`**, `deploy`, `env` |
| `actions/listActions` | `{}` | recent deploys with `status` (`done`/`error`/`killed`) + `id` |
| `actions/getAction` | `{"id":…}` | **the full build log** (`.log`) |
| `services/app/deployService` | `{projectName,serviceName}` | rebuild + deploy |
| `services/app/updateBuild` | `…,{"build":{"type":"dockerfile","file":"Dockerfile"}}` | fix a missing build config |
| `services/app/updateSourceGithub` | `…,{owner,repo,ref,path,autoDeploy}` | re-register source → forces a fresh archive download |
| `dockerBuilders/listDockerBuilders` | `{}` | builder health |

Note `logs/queryServiceLogs` (runtime container logs) returns `"fetch failed"` on
this host — use `actions/getAction` for build output.

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

`deployService` returns `ok` when the *trigger* is accepted; the build then runs and
can fail afterwards, in which case the helper prints
`FAILED: {…"Command failed with exit code 1: docker buildx build…"}`, dumps the build
log, and the service keeps serving its previous image. The response message is
truncated — **read the build log**, not the response.

### Two failure modes seen in prod (2026-07-28)

**1. Stale checkout — the build uses an old Dockerfile.** EasyPanel keeps the GitHub
archive at `/etc/easypanel/projects/<proj>/<svc>/code`; it can go stale even though
`main` has moved. The tell is in the log: `transferring dockerfile: 336B` when the
committed file is 968B, and the quoted `Dockerfile:8` context showing old lines.
Fix by re-registering the source, then deploying:

```bash
# services/app/updateSourceGithub with {owner,repo,ref,path,autoDeploy}
ops/easypanel-deploy.sh frontend        # after the re-register
```

**2. Poisoned buildkit cache.** Symptom:

```
failed to commit <id> to <id> during finalize:
  failed to stat active key during commit: snapshot <id> does not exist: not found
```

with every earlier step reporting `CACHED`. The host's buildkit references a snapshot
whose parent is gone. `dockerBuilders/stopDockerBuilder` does **not** clear it (the
docker driver's cache survives). Route around it by changing a build-arg the
Dockerfile consumes: `frontend/Dockerfile` declares `ARG GIT_SHA` above
`RUN npm run build`, and EasyPanel passes `--build-arg GIT_SHA=<commit>` on every
deploy, so the layer's cache key changes per commit. Keep that ARG where it is.

A local reproduction is still the fastest way to prove the code is fine:

```bash
git archive <sha> frontend | tar -x -C /tmp/x
cd /tmp/x/frontend && docker build --network host -f Dockerfile -t t \
  --build-arg VITE_API_URL=https://rumo-backend.xem1qi.easypanel.host .
```

If that passes and the server's fails, it is one of the two host conditions above.

### Check the service's `build` config exists

A service with `build: null` has no build configuration (the frontend was in this
state). Compare services with `projects/listProjectsAndServices`; both `rumo`
services should read `{"type":"dockerfile","file":"Dockerfile"}`.

## SISJURI extraction agent

See `sisjuri-agent/README.md` — the on-box (MBC-LDESK01) extract/probe workflow,
the RDP command recipes, and the ingest credentials.
