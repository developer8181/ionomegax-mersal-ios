#!/usr/bin/env bash
# Generate production credentials for Ionomegax Mersal Guard
set -euo pipefail

ENV_FILE="${1:-mersal-guard.env}"
API_TOKEN="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
ADMIN_PASS="$(python3 -c 'import secrets; print(secrets.token_urlsafe(18))')"

cat >"${ENV_FILE}" <<EOF
# Ionomegax Mersal Guard — generated $(date -u +%Y-%m-%dT%H:%MZ)
export MERSAL_HOST=0.0.0.0
export MERSAL_PORT=8090
export MERSAL_DB=/var/lib/mersal-guard/mersal-guard.sqlite3
export MERSAL_API_TOKEN=${API_TOKEN}
export MERSAL_ADMIN_USER=admin
export MERSAL_ADMIN_PASSWORD=${ADMIN_PASS}
# Production trial (integrated build):
# export MERSAL_PRODUCTION=1
# export MERSAL_BOOTSTRAP=1
# export MERSAL_KEV_FEED_URL=https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
# Optional TLS:
# export MERSAL_TLS_CERT=/etc/mersal-guard/tls/server.crt
# export MERSAL_TLS_KEY=/etc/mersal-guard/tls/server.key
# Optional agent mTLS:
# export MERSAL_AGENT_CA=/etc/mersal-guard/tls/ca.crt
# export MERSAL_AGENT_MTLS=1
EOF

chmod 600 "${ENV_FILE}"
echo "Wrote ${ENV_FILE}"
echo "Command Center: http://127.0.0.1:8090/console/"
echo "Admin user: admin"
echo "Set agent api_token in config/agent.json to the API token above."
