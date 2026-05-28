#!/usr/bin/env bash
# Provision Mersal for companies, NGOs, and government agencies.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
ENV_FILE="${1:-mersal-guard.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  cp mersal-guard.organization.example.env "$ENV_FILE"
  echo "Edit $ENV_FILE with strong secrets, then re-run." >&2
  exit 1
fi
# shellcheck disable=SC1090
source "$ENV_FILE"

./scripts/generate-tls.sh "${MERSAL_TLS_DIR:-data/tls}" 2>/dev/null || true

python3 <<'PY'
import os
import secrets
from pathlib import Path
from xig.storage import Database
from xig.security.agent_auth import generate_agent_key, hash_agent_key

db_path = os.environ.get("MERSAL_DB", "data/mersal-organization.sqlite3")
db = Database(db_path)
db.init_schema()
db.ensure_rbac_seed()
agent_id = "agent-org-bootstrap-001"
key = generate_agent_key()
db.set_agent_key_hash(agent_id, hash_agent_key(key))
out = Path("config/agent.organization.json")
out.parent.mkdir(parents=True, exist_ok=True)
import json
out.write_text(
    json.dumps(
        {
            "server": "https://127.0.0.1:8090",
            "agent_id": agent_id,
            "endpoint_id": "endpoint-org-001",
            "agent_api_key": key,
            "interval_seconds": 30,
        },
        indent=2,
    ),
    encoding="utf-8",
)
print("Database ready:", db_path)
print("Sample agent config:", out, "(protect agent_api_key)")
PY

echo "Start: source $ENV_FILE && python3 -m xig"
