#!/usr/bin/env bash
# Full integrated build: tests, env template, optional Docker image.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

echo "=== Mersal Guard integrated build ==="
python3 -m unittest discover -s tests -v

if [[ ! -f mersal-guard.production.env ]]; then
  bash scripts/provision.sh mersal-guard.production.env
  {
    echo "export MERSAL_PRODUCTION=1"
    echo "export MERSAL_BOOTSTRAP=1"
    echo "export MERSAL_KEV_FEED_URL=https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
  } >> mersal-guard.production.env
fi

bash scripts/verify-build.sh

if command -v docker >/dev/null 2>&1; then
  echo "Building Docker image..."
  docker compose -f deploy/docker-compose.yml build
fi

COMMIT="$(git -C "${ROOT}" rev-parse --short HEAD 2>/dev/null || echo local)"
echo ""
echo "Build OK — Mersal Guard v3.0 (${COMMIT})"
echo "  make run"
echo "  source mersal-guard.production.env && python3 app.py"
