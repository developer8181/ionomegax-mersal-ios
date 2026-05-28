#!/usr/bin/env bash
# Start Mersal v8 standalone stack (Docker Compose).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/deploy"

if [[ -z "${MERSAL_SIGNING_SECRET:-}" ]] || [[ -z "${MERSAL_API_TOKEN:-}" ]]; then
  echo "Export MERSAL_SIGNING_SECRET and MERSAL_API_TOKEN before starting." >&2
  exit 1
fi

docker compose -f docker-compose.standalone.yml up -d --build
echo "Mersal standalone: https://localhost:8090/console/ (configure TLS in production)"
