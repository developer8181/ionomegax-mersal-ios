#!/usr/bin/env bash
# Provision Mersal for bank / government enterprise profile (v7).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

ENV_FILE="${1:-mersal-guard.enterprise.env}"
if [[ ! -f "$ENV_FILE" ]]; then
  cp mersal-guard.enterprise.example.env "$ENV_FILE"
  echo "Created $ENV_FILE — edit secrets before production use."
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

mkdir -p "$(dirname "${MERSAL_DB:-data/mersal-enterprise.sqlite3}")"
./scripts/generate-tls.sh "${MERSAL_TLS_DIR:-data/tls}"

if [[ -z "${MERSAL_SIGNING_SECRET:-}" ]] && [[ -z "${MERSAL_API_TOKEN:-}" ]]; then
  echo "Generate MERSAL_SIGNING_SECRET (openssl rand -hex 32)" >&2
  exit 1
fi

python3 -c "
from xig.storage import Database
import os
db = Database(os.environ.get('MERSAL_DB', 'data/mersal-enterprise.sqlite3'))
db.init_schema()
db.ensure_rbac_seed()
print('Schema ready:', db.path)
"

echo "Enterprise profile ready. Start with:"
echo "  set -a && source $ENV_FILE && set +a && python3 -m xig"
