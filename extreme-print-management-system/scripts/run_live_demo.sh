#!/usr/bin/env bash
# Start EPMS with mandatory admin login and published demo credentials.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export EPMS_LIVE_DEMO=1
export EPMS_REQUIRE_AUTH=1
export EPMS_SEED_DEMO=1
export EPMS_HOST="${EPMS_HOST:-127.0.0.1}"
export EPMS_PORT="${EPMS_PORT:-8765}"
export EPMS_DB="${EPMS_DB:-/tmp/epms-live-demo.db}"
export EPMS_SESSION_SECRET="${EPMS_SESSION_SECRET:-live-demo-session-secret-32chars-min}"
export EPMS_BOOTSTRAP_ADMIN_PASSWORD="${EPMS_BOOTSTRAP_ADMIN_PASSWORD:-Extreme@Demo2026}"

rm -f "$EPMS_DB"
echo "Starting live demo on http://${EPMS_HOST}:${EPMS_PORT}"
echo "Admin: admin / ${EPMS_BOOTSTRAP_ADMIN_PASSWORD}"
echo "Operator: operator / Operator@Demo2026"
echo "Viewer: viewer / Viewer@Demo2026"
exec python3 app.py
