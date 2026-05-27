#!/usr/bin/env bash
# Build Mersal OS hybrid ISO (Debian bookworm live)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist"
WORK="$ROOT/build/live-work"
ARCH="${MERSAL_ARCH:-amd64}"

export DEBIAN_FRONTEND=noninteractive

echo "=== Mersal OS ISO Build ==="
echo "Powered by Extreme Technology Company"

mkdir -p "$DIST"
rm -rf "$WORK"
mkdir -p "$WORK"

if ! command -v lb >/dev/null 2>&1; then
  echo "Installing live-build..."
  sudo apt-get update -qq
  sudo apt-get install -y -qq live-build debootstrap squashfs-tools xorriso isolinux syslinux-utils grub-pc-bin grub-efi-amd64-bin rsync openssl
fi

cd "$WORK"
lb config noauto \
  --mode debian \
  --distribution bookworm \
  --architectures "$ARCH" \
  --binary-images iso-hybrid \
  --debian-installer false \
  --archive-areas "main contrib non-free non-free-firmware" \
  --mirror-bootstrap "http://deb.debian.org/debian" \
  --mirror-chroot "http://deb.debian.org/debian" \
  --mirror-binary "http://deb.debian.org/debian" \
  --security false \
  --bootappend-live "boot=live components quiet splash hostname=mersal-os username=mersal" \
  --memtest none \
  --iso-application "Mersal OS" \
  --iso-volume "MERSAL_OS_1_0" \
  --iso-preparer "Extreme Technology Company" \
  --iso-publisher "Ionomegax" \
  --win32-loader false

mkdir -p config/package-lists config/hooks/normal config/archives
cp "$ROOT/build/package-lists/mersal.list.chroot" config/package-lists/mersal.list.chroot
cp "$ROOT/build/archives/debian.list.chroot" config/archives/debian.list.chroot
cp "$ROOT/build/archives/debian.list.binary" config/archives/debian.list.binary
cp "$ROOT/build/hooks/0001-fix-apt-security.chroot" config/hooks/normal/0001-fix-apt-security.chroot
cp "$ROOT/build/hooks/0100-mersal.chroot" config/hooks/normal/0100-mersal.chroot
chmod +x config/hooks/normal/*.chroot

# Patch any legacy live-build suite paths before image assembly
find config -type f 2>/dev/null | while read -r file; do
  if grep -q 'bookworm/updates' "$file" 2>/dev/null; then
    sed -i 's|bookworm/updates|bookworm-security|g' "$file"
  fi
done

export LB_INCLUDES="$WORK/config/includes.chroot"
"$ROOT/build/sync-includes.sh"

echo "Starting live-build (this may take 20-60 minutes)..."
sudo lb build 2>&1 | tee "$ROOT/build/build.log"

ISO="$(find . -maxdepth 1 -name 'live-image-*.hybrid.iso' | head -1)"
if [ -z "$ISO" ]; then
  echo "ERROR: ISO not found. See build/build.log"
  exit 1
fi

STAMP="$(date +%Y%m%d)"
OUT="$DIST/mersal-os-${STAMP}-${ARCH}.iso"
cp "$ISO" "$OUT"
( cd "$DIST" && sha256sum "$(basename "$OUT")" > "$(basename "$OUT").sha256" )

echo ""
echo "SUCCESS: $OUT"
ls -lh "$OUT"
cat "$OUT.sha256"
