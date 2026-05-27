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

# Logo
if [ -f "$ROOT/brand/assets/mersal-os-logo.png" ]; then
  mkdir -p "$INCLUDES/usr/share/pixmaps"
  cp "$ROOT/brand/assets/mersal-os-logo.png" "$INCLUDES/usr/share/pixmaps/mersal-os-logo.png"
fi

# Live username for casper
mkdir -p "$INCLUDES/../includes.binary/live-config" 2>/dev/null || mkdir -p "$(dirname "$INCLUDES")/includes.binary/live-config"
LIVE_CFG="$(dirname "$INCLUDES")/includes.binary/live-config"
mkdir -p "$LIVE_CFG"
echo "mersal" > "$LIVE_CFG/username"
echo "Mersal OS Operator" > "$LIVE_CFG/user-fullname"
openssl passwd -6 -salt mersal mersal | sed 's/^/mersal:/' > "$LIVE_CFG/user-password" || echo 'mersal:$6$mersal$placeholder' > "$LIVE_CFG/user-password"

echo "Includes sync complete."
