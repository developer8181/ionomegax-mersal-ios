#!/usr/bin/env bash
# Mersal v8.7 — complete integrated platform install (enterprise / large org)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${1:-mersal-guard.organization.example.env}"
echo "=== Mersal Complete Platform Install ==="

if [[ ! -f "$ENV_FILE" ]]; then
  cp mersal-guard.organization.example.env "$ENV_FILE" 2>/dev/null || cp mersal-guard.enterprise.example.env "$ENV_FILE"
  echo "Created $ENV_FILE — configure secrets before production."
fi
# shellcheck disable=SC1090
set -a && source "$ENV_FILE" && set +a

export MERSAL_ENTERPRISE="${MERSAL_ENTERPRISE:-1}"
export MERSAL_PRODUCTION="${MERSAL_PRODUCTION:-1}"
export MERSAL_AUTONOMOUS="${MERSAL_AUTONOMOUS:-1}"

if [[ -x ./scripts/provision-enterprise.sh ]]; then
  ./scripts/provision-enterprise.sh "$ENV_FILE"
else
  ./scripts/provision-organization.sh "$ENV_FILE" 2>/dev/null || true
fi

if [[ -n "${MERSAL_POSTGRES_DSN:-}" ]] && command -v python3 >/dev/null; then
  python3 scripts/init-postgres-schema.py || python3 scripts/init-postgres-schema.py --verify || true
fi

python3 <<'PY'
import os
from xig.platform_ops.unified_platform import UnifiedPlatformController
from xig.storage import Database

db = Database(os.environ.get("MERSAL_DB", "data/mersal-guard.sqlite3"))
db.init_schema()
ctrl = UnifiedPlatformController(db, fabric=None)
result = ctrl.bootstrap_enterprise(tenant_id=os.environ.get("MERSAL_DEFAULT_TENANT", "default"))
print("Bootstrap:", result.get("ok"), "tier:", (result.get("steps") or {}).get("adoption", {}).get("tier"))
PY

echo ""
echo "Start platform:"
echo "  set -a && source $ENV_FILE && set +a && python3 -m xig"
echo "Command Center: http://127.0.0.1:${MERSAL_PORT:-8090}/console/"
echo "Unified API:    GET /api/platform/unified"
