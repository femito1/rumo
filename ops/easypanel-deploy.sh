#!/usr/bin/env bash
# Redeploy an EasyPanel service (rebuild + deploy from the configured GitHub
# source). Use after pushing to `main` so the deployed code catches up.
#
# Usage:
#   ops/easypanel-deploy.sh backend           # redeploy the backend service
#   ops/easypanel-deploy.sh frontend          # redeploy the frontend service
#   ops/easypanel-deploy.sh backend restart   # restart (no rebuild)
#   ops/easypanel-deploy.sh frontend logs     # print the LAST build log and exit
#
# Credentials come from ops/easypanel.local.secrets (gitignored). Never hard-code
# the key here.
#
# API: the panel speaks **oRPC at `/api/rpc/<ns>/<proc>`** (slash-separated),
# POST-only, body wrapped as `{"json": <input>}`. It is NOT tRPC at /api/trpc —
# that path 400s on everything with a generic `{"error":"Bad Request"}`, which is
# what made an earlier debugging pass conclude "the API only supports POST
# mutations and exposes no logs". Both conclusions were wrong; see ops/README.md.
set -euo pipefail

SECRETS="$(dirname "$0")/easypanel.local.secrets"
if [[ ! -f "$SECRETS" ]]; then
  echo "missing $SECRETS (gitignored) — see ops/README for the template" >&2
  exit 1
fi
# `set -a` so the file's plain KEY=VALUE lines are exported, and comments in it
# can't leak into a variable (a naive `grep KEY= | cut` did exactly that).
set -a
# shellcheck disable=SC1090
source "$SECRETS"
set +a

SERVICE="${1:?usage: easypanel-deploy.sh <backend|frontend> [deploy|restart|stop|start|logs]}"
ACTION="${2:-deploy}"

# POST an oRPC proc. $1 = ns/proc path, $2 = JSON input (unwrapped).
rpc() {
  curl -s -m 420 -X POST "$EASYPANEL_URL/api/rpc/$1" \
    -H "Authorization: Bearer $EASYPANEL_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"json\":$2}"
}

SVC_INPUT="{\"projectName\":\"$EASYPANEL_PROJECT\",\"serviceName\":\"$SERVICE\"}"

# Print the most recent build/deploy log for the service. This is the ONLY way to
# see why a build failed — the deploy response truncates to the docker command,
# and logs/queryServiceLogs (runtime logs) returns "fetch failed" on this host.
build_log() {
  local id
  id=$(rpc "actions/listActions" '{}' | python3 -c "
import sys, json
for a in json.load(sys.stdin)['json']:
    if a.get('serviceName') == '$SERVICE':
        print(a['id']); break
")
  [[ -n "$id" ]] || { echo "[easypanel] no action found for $SERVICE" >&2; return 1; }
  rpc "actions/getAction" "{\"id\":\"$id\"}" | python3 -c "
import sys, json
a = json.load(sys.stdin)['json']
print(f\"### action {a['id']}  status={a.get('status')}  {a.get('updatedAt')}\")
# Skip the leading commit-message echo; the build output starts at the banner.
log = a.get('log') or ''
i = log.find('###')
print(log[i:] if i > 0 else log)
"
}

if [[ "$ACTION" == "logs" ]]; then
  build_log
  exit 0
fi

case "$ACTION" in
  deploy)  PROC="services/app/deployService" ;;
  restart) PROC="services/app/restartService" ;;
  stop)    PROC="services/app/stopService" ;;
  start)   PROC="services/app/startService" ;;
  *) echo "unknown action: $ACTION" >&2; exit 1 ;;
esac

echo "[easypanel] $ACTION $EASYPANEL_PROJECT/$SERVICE ..."
resp=$(rpc "$PROC" "$SVC_INPUT")

# Success is `{}` or `{"json":<data>}`; an error is `{"error":...}` or
# `{"json":{"code":...}}`. NOTE a deploy can fail AFTER the trigger is accepted
# (the build runs, then errors), so this must be checked — and the check must
# really exit non-zero. An earlier `echo | grep -q` version exited 0 on failure,
# so callers/CI could not trust `$?`.
if [[ "$resp" == *'"code"'* || "$resp" == *'"error"'* ]]; then
  echo "[easypanel] FAILED: $resp" >&2
  echo "[easypanel] NOTE: the service keeps serving its previous image." >&2
  echo "[easypanel] --- last build log ---" >&2
  build_log >&2 || true
  exit 1
fi
echo "[easypanel] ok${resp:+: $resp}"
