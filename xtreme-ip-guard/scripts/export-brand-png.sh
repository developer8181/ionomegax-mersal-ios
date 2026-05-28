#!/usr/bin/env bash
# Export unified brand PNGs for Mersal OS ISO and docs
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MERSAL_OS="$(cd "$ROOT/../mersal-os" && pwd)"
WEB="$ROOT/web"
OUT="$MERSAL_OS/brand/assets"
mkdir -p "$OUT"
command -v rsvg-convert >/dev/null || { echo "Install librsvg2-bin"; exit 1; }
rsvg-convert -w 512 -h 512 "$WEB/logo.svg" -o "$OUT/mersal-os-logo.png"
rsvg-convert -w 720 -h 176 "$WEB/logo-unified.svg" -o "$OUT/mersal-platform-unified.png"
rsvg-convert -w 640 -h 240 "$WEB/extreme-logo-dark.svg" -o "$OUT/extreme-technology-logo.png"
cp "$OUT/mersal-platform-unified.png" "$OUT/mersal-os-boot-logo.png"
echo "Brand PNGs written to $OUT"
