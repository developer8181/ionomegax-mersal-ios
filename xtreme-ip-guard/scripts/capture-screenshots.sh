#!/usr/bin/env bash
# Capture Command Center screenshots for GitHub release.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT="${ROOT}/docs/screenshots"
DB="${ROOT}/data/demo-ui.sqlite3"
PORT="${MERSAL_PORT:-8090}"
URL="http://127.0.0.1:${PORT}/console/"

mkdir -p "$OUT" data
export MERSAL_DB="$DB"
export MERSAL_DAILY_INTERVAL_SECONDS=999999

python3 scripts/seed_demo_ui.py

# Start server in background
python3 -m xig.server &
SRV_PID=$!
cleanup() { kill "$SRV_PID" 2>/dev/null || true; }
trap cleanup EXIT

for _ in $(seq 1 30); do
  if curl -sf "${URL}" >/dev/null 2>&1; then break; fi
  sleep 0.5
done
sleep 2

CHROME="${CHROME_BIN:-google-chrome}"
CHROME_FLAGS=(--headless=new --disable-gpu --hide-scrollbars --no-sandbox
  --user-data-dir="/tmp/mersal-chrome-$$" --window-size=1440,920)

shot() {
  local file="$1"
  local target="$2"
  "$CHROME" "${CHROME_FLAGS[@]}" --screenshot="$OUT/$file" "$target" 2>/dev/null || \
  "$CHROME" --headless --disable-gpu --no-sandbox \
    --user-data-dir="/tmp/mersal-chrome-$$" --window-size=1440,920 \
    --screenshot="$OUT/$file" "$target"
  echo "  ✓ $file"
}

shot "01-command-center-overview-ar.png" "${URL}?lang=ar&view=overview"
shot "02-global-fabric-ar.png" "${URL}?lang=ar&view=fabric"
shot "03-neural-cortex-ar.png" "${URL}?lang=ar&view=ai"
shot "04-command-center-en.png" "${URL}?lang=en&view=overview"
shot "05-endpoints-threats-ar.png" "${URL}?lang=ar&view=events"
shot "06-about-system-ar.png" "${URL}?lang=ar&openAbout=1"

echo "Screenshots saved to $OUT"
