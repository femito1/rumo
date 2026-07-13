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
resp=$(curl -s -m 60 -X POST "$EASYPANEL_URL/api/trpc/$PROC" \
  -H "Authorization: Bearer $EASYPANEL_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"json\":{\"projectName\":\"$EASYPANEL_PROJECT\",\"serviceName\":\"$SERVICE\"}}")

# A successful mutation returns {"result":{"data":{"json":...}}} or {"json":...};
# an error returns {"error"...} or {"json":{"code":...}}.
if echo "$resp" | grep -q '"code"\|"error"'; then
  echo "[easypanel] FAILED: $resp" >&2
  exit 1
fi
echo "[easypanel] ok: $resp"
