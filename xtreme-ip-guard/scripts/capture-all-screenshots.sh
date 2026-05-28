#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export MERSAL_DB="$ROOT/data/demo-ui.sqlite3"
export MERSAL_NO_SCHEDULER=1 MERSAL_KEV_FEED_URL="" MERSAL_BOOTSTRAP=0 MERSAL_DEMO_UI=1
export CHROME_BIN="${CHROME_BIN:-google-chrome}"

python3 scripts/seed_demo_ui.py
fuser -k 8090/tcp 2>/dev/null || true
sleep 1

python3 app.py &
SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT

for i in $(seq 1 40); do
  curl -sf http://127.0.0.1:8090/api/system/about >/dev/null && break
  sleep 0.5
done

OUT="$ROOT/docs/screenshots"
mkdir -p "$OUT"
CHROME="$CHROME_BIN"

capture() {
  local file="$1" query="$2"
  local path="$OUT/$file"
  local prof="/tmp/mcap-$$-${file}"
  timeout 25 "$CHROME" --headless=new --disable-gpu --no-sandbox \
    --hide-scrollbars --user-data-dir="$prof" \
    --window-size=1440,900 --virtual-time-budget=6000 \
    "--screenshot=$path" "http://127.0.0.1:8090/console/?${query}" 2>/dev/null || true
  rm -rf "$prof"
  if [[ -s "$path" ]] && [[ $(stat -c%s "$path") -gt 5000 ]]; then
    echo "OK $file"
  else
    echo "FAIL $file"
  fi
}

capture "01-overview-ar.png" "lang=ar&view=overview&capture=1"
capture "02-readiness-ar.png" "lang=ar&view=readiness&capture=1"
capture "03-enterprise-ar.png" "lang=ar&view=enterprise&capture=1"
capture "04-xdr-ar.png" "lang=ar&view=xdr&capture=1"
capture "05-fabric-ar.png" "lang=ar&view=fabric&capture=1"
capture "06-ai-cortex-ar.png" "lang=ar&view=ai&capture=1"
capture "07-endpoints-ar.png" "lang=ar&view=endpoints&capture=1"
capture "08-events-ar.png" "lang=ar&view=events&capture=1"
capture "09-policies-ar.png" "lang=ar&view=policies&capture=1"
capture "10-audit-ar.png" "lang=ar&view=audit&capture=1"
capture "11-about-ar.png" "lang=ar&openAbout=1&capture=1"
capture "12-overview-en.png" "lang=en&view=overview&capture=1"
capture "13-readiness-en.png" "lang=en&view=readiness&capture=1"
capture "14-enterprise-en.png" "lang=en&view=enterprise&capture=1"
capture "15-xdr-en.png" "lang=en&view=xdr&capture=1"
capture "16-fabric-en.png" "lang=en&view=fabric&capture=1"
capture "17-ai-cortex-en.png" "lang=en&view=ai&capture=1"
capture "18-endpoints-en.png" "lang=en&view=endpoints&capture=1"
capture "19-events-en.png" "lang=en&view=events&capture=1"
capture "20-about-en.png" "lang=en&openAbout=1&capture=1"

ls -la "$OUT"/*.png | wc -l
echo "Done"
