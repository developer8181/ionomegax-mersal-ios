#!/usr/bin/env bash
# Sync Mersal OS payload into live-build includes.chroot
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"
INCLUDES="${LB_INCLUDES:-$ROOT/build/live-work/config/includes.chroot}"

echo "Syncing includes -> $INCLUDES"
rm -rf "$INCLUDES"
mkdir -p \
  "$INCLUDES/opt/mersal-guard" \
  "$INCLUDES/opt/mersal-os/core" \
  "$INCLUDES/opt/mersal-os/gateway" \
  "$INCLUDES/opt/mersal-os/update-channel" \
  "$INCLUDES/usr/share/mersal-brand" \
  "$INCLUDES/usr/local/bin" \
  "$INCLUDES/etc/mersal-os" \
  "$INCLUDES/etc/mersal-guard" \
  "$INCLUDES/etc/suricata"

# Platform payload
rsync -a --exclude '__pycache__' --exclude 'data' --exclude 'tests' \
  "$REPO/xtreme-ip-guard/" "$INCLUDES/opt/mersal-guard/"

# Mersal OS modules
rsync -a "$ROOT/core/" "$INCLUDES/opt/mersal-os/core/"
rsync -a "$ROOT/gateway/" "$INCLUDES/opt/mersal-os/gateway/"
rsync -a "$ROOT/update-channel/" "$INCLUDES/opt/mersal-os/update-channel/"
rsync -a "$ROOT/brand/" "$INCLUDES/usr/share/mersal-brand/"

# Rootfs overlay
rsync -a "$ROOT/rootfs-overlay/" "$INCLUDES/"

# Gateway configs
cp "$ROOT/gateway/nftables-mersal.conf" "$INCLUDES/etc/nftables.conf"
cp "$ROOT/gateway/suricata-mersal.yaml" "$INCLUDES/etc/suricata/suricata.yaml" 2>/dev/null || \
  mkdir -p "$INCLUDES/etc/suricata" && cp "$ROOT/gateway/suricata-mersal.yaml" "$INCLUDES/etc/suricata/suricata.yaml"

# Brand assets (Mersal + Extreme unified)
mkdir -p "$INCLUDES/usr/share/pixmaps" "$INCLUDES/opt/mersal-guard/web"
GUARD_WEB="$REPO/xtreme-ip-guard/web"
for asset in logo.svg logo-unified.svg logo-ecs.svg extreme-logo.svg extreme-logo-dark.svg ecs-theme.css; do
  if [ -f "$GUARD_WEB/$asset" ]; then
    cp "$GUARD_WEB/$asset" "$INCLUDES/opt/mersal-guard/web/$asset"
  fi
done
for png in mersal-os-logo.png mersal-platform-unified.png extreme-technology-logo.png mersal-icon.svg; do
  if [ -f "$ROOT/brand/assets/$png" ]; then
    cp "$ROOT/brand/assets/$png" "$INCLUDES/usr/share/pixmaps/$png"
    [ "$png" = "mersal-os-logo.png" ] && cp "$ROOT/brand/assets/$png" "$INCLUDES/usr/share/pixmaps/mersal-os-logo.png"
  fi
done
if [ -f "$ROOT/brand/assets/mersal-platform-unified.png" ]; then
  cp "$ROOT/brand/assets/mersal-platform-unified.png" "$INCLUDES/usr/share/pixmaps/mersal-os-boot-logo.png" 2>/dev/null || true
fi

# Live username for casper
mkdir -p "$INCLUDES/../includes.binary/live-config" 2>/dev/null || mkdir -p "$(dirname "$INCLUDES")/includes.binary/live-config"
LIVE_CFG="$(dirname "$INCLUDES")/includes.binary/live-config"
mkdir -p "$LIVE_CFG"
echo "mersal" > "$LIVE_CFG/username"
echo "Mersal OS Operator" > "$LIVE_CFG/user-fullname"
openssl passwd -6 -salt mersal mersal | sed 's/^/mersal:/' > "$LIVE_CFG/user-password" || echo 'mersal:$6$mersal$placeholder' > "$LIVE_CFG/user-password"

echo "Includes sync complete."
