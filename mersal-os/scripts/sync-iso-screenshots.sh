#!/usr/bin/env bash
# Sync latest Extreme Cyber Security Command Center captures into mersal-os/docs/screenshots
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"
SRC="$REPO/xtreme-ip-guard/docs/screenshots"
DST="$ROOT/docs/screenshots"

mkdir -p "$DST"

copy() {
  local src_name="$1"
  local dst_name="$2"
  if [ -f "$SRC/$src_name" ]; then
    cp "$SRC/$src_name" "$DST/$dst_name"
    echo "  OK $dst_name"
  else
    echo "  SKIP missing $src_name"
  fi
}

echo "Syncing platform screenshots -> $DST"
copy "01-overview-ar.png" "01-command-center-ar.png"
copy "03-enterprise-ar.png" "05-enterprise-integration-ar.png"
copy "04-xdr-ar.png" "06-xdr-ar.png"
copy "11-about-ar.png" "07-about-ar.png"
copy "12-overview-en.png" "08-command-center-en.png"
copy "20-about-en.png" "09-about-en.png"

if [ -f "$REPO/xtreme-ip-guard/web/logo-ecs.svg" ]; then
  if command -v google-chrome >/dev/null 2>&1; then
    chrome="$(command -v google-chrome)"
    prof="/tmp/mersal-ecs-logo-$$"
    timeout 15 "$chrome" --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
      --user-data-dir="$prof" --window-size=512,512 \
      --screenshot="$DST/03-brand-ecs-logo.png" \
      "file://$REPO/xtreme-ip-guard/web/logo-ecs.svg" 2>/dev/null || true
    rm -rf "$prof"
    [ -f "$DST/03-brand-ecs-logo.png" ] && echo "  OK 03-brand-ecs-logo.png"
  fi
fi

if [ -f "$ROOT/brand/assets/mersal-os-logo.png" ]; then
  cp "$ROOT/brand/assets/mersal-os-logo.png" "$DST/03-brand-logo.png"
  echo "  OK 03-brand-logo.png"
fi

if command -v convert >/dev/null 2>&1; then
  convert -size 1280x720 xc:'#0a0f1a' -gravity center \
    -fill '#00e5bf' -font DejaVu-Sans -pointsize 28 \
    -annotate 0 "Mersal OS 6.0.0 — Extreme Cyber Security Edition\n\nmersal-status · Live ISO\n© Extreme Technology" \
    "$DST/04-terminal-status.png" 2>/dev/null && echo "  OK 04-terminal-status.png"
fi

echo "Done. $(ls -1 "$DST"/*.png 2>/dev/null | wc -l) PNG files in $DST"
