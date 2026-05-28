#!/usr/bin/env bash
# Continue capture while server already running on 8090
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/docs/screenshots"
BASE="http://127.0.0.1:8090/console"
CHROME="${CHROME_BIN:-google-chrome}"

shot() {
  local name="$1" query="$2"
  local dest="$OUT/$name"
  local profile="/tmp/mersal-cap-$$-$name"
  "$CHROME" --headless=new --disable-gpu --no-sandbox \
    --hide-scrollbars --user-data-dir="$profile" \
    --window-size=1440,900 --virtual-time-budget=8000 \
    "--screenshot=$dest" "${BASE}/${query}" 2>/dev/null || true
  rm -rf "$profile"
  if [[ -f "$dest" && $(stat -c%s "$dest") -gt 8000 ]]; then
    echo "OK $name"
  else
    echo "FAIL $name"
  fi
}

mkdir -p "$OUT"
shots=(
  "04-xdr-ar.png|?lang=ar&view=xdr&capture=1"
  "05-fabric-ar.png|?lang=ar&view=fabric&capture=1"
  "06-ai-cortex-ar.png|?lang=ar&view=ai&capture=1"
  "07-endpoints-ar.png|?lang=ar&view=endpoints&capture=1"
  "08-events-ar.png|?lang=ar&view=events&capture=1"
  "09-policies-ar.png|?lang=ar&view=policies&capture=1"
  "10-audit-ar.png|?lang=ar&view=audit&capture=1"
  "11-about-ar.png|?lang=ar&openAbout=1&capture=1"
  "12-overview-en.png|?lang=en&view=overview&capture=1"
  "13-readiness-en.png|?lang=en&view=readiness&capture=1"
  "14-enterprise-en.png|?lang=en&view=enterprise&capture=1"
  "15-xdr-en.png|?lang=en&view=xdr&capture=1"
  "16-fabric-en.png|?lang=en&view=fabric&capture=1"
  "17-ai-cortex-en.png|?lang=en&view=ai&capture=1"
  "18-endpoints-en.png|?lang=en&view=endpoints&capture=1"
  "19-events-en.png|?lang=en&view=events&capture=1"
  "20-about-en.png|?lang=en&openAbout=1&capture=1"
)

for entry in "${shots[@]}"; do
  name="${entry%%|*}"
  query="${entry#*|}"
  [[ -f "$OUT/$name" ]] && [[ $(stat -c%s "$OUT/$name") -gt 8000 ]] && { echo "SKIP $name"; continue; }
  shot "$name" "$query"
done
