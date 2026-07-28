#!/usr/bin/env bash
# Redeploy an EasyPanel service (rebuild + deploy from the configured GitHub
# source). Use after pushing to `main` so the deployed code catches up.
#
# Usage:
#   ops/easypanel-deploy.sh backend        # redeploy the backend service
#   ops/easypanel-deploy.sh frontend       # redeploy the frontend service
#   ops/easypanel-deploy.sh backend restart   # restart (no rebuild)
#
# Credentials come from ops/easypanel.local.secrets (gitignored). The tRPC API
# shape is documented there. Never hard-code the key here.
set -euo pipefail

SECRETS="$(dirname "$0")/easypanel.local.secrets"
if [[ ! -f "$SECRETS" ]]; then
  echo "missing $SECRETS (gitignored) — see ops/README for the template" >&2
  exit 1
fi
# shellcheck disable=SC1090
source "$SECRETS"

SERVICE="${1:?usage: easypanel-deploy.sh <backend|frontend> [deploy|restart|stop|start]}"
ACTION="${2:-deploy}"

case "$ACTION" in
  deploy)  PROC="services.app.deployService" ;;
  restart) PROC="services.app.restartService" ;;
  stop)    PROC="services.app.stopService" ;;
  start)   PROC="services.app.startService" ;;
  *) echo "unknown action: $ACTION" >&2; exit 1 ;;
esac

echo "[easypanel] $ACTION $EASYPANEL_PROJECT/$SERVICE ..."
resp=$(curl -s -m 300 -X POST "$EASYPANEL_URL/api/trpc/$PROC" \
  -H "Authorization: Bearer $EASYPANEL_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"json\":{\"projectName\":\"$EASYPANEL_PROJECT\",\"serviceName\":\"$SERVICE\"}}")

# A successful mutation returns {"result":{"data":{"json":...}}} or {"json":...};
# an error returns {"error"...} or {"json":{"code":...}}. NOTE `deploy` can return
# an error AFTER the build starts (e.g. "Command failed ... docker buildx build") —
# an accepted trigger is not a successful build.
#
# `set -o pipefail` + `grep -q` used to make this exit 0 on the FAILED path (grep's
# status was consumed by the `if`, and the earlier `echo | grep` short-circuit lost
# the intended non-zero). Compare against the string directly so `exit 1` is real —
# CI/callers must be able to trust `$?`.
if [[ "$resp" == *'"code"'* || "$resp" == *'"error"'* ]]; then
  echo "[easypanel] FAILED: $resp" >&2
  echo "[easypanel] NOTE: the service keeps serving its previous image." >&2
  exit 1
fi
echo "[easypanel] ok: $resp"
