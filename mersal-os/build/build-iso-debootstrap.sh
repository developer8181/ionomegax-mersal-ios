#!/usr/bin/env bash
# Mersal OS — debootstrap-based live ISO (non-interactive)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"
DIST="$ROOT/dist"
WORK="${MERSAL_DEBOOT_WORK:-$ROOT/build/debootstrap-work}"
CHROOT="$WORK/chroot"
ISO_DIR="$WORK/iso"
ARCH="${MERSAL_ARCH:-amd64}"

export DEBIAN_FRONTEND=noninteractive

echo "=== Mersal OS debootstrap ISO ==="
mkdir -p "$DIST" "$ISO_DIR/live"
sudo mkdir -p "$ISO_DIR/live"

if [ "${MERSAL_DEBOOT_CLEAN:-1}" = "1" ]; then
  sudo umount -lf "$CHROOT/dev/pts" "$CHROOT/dev" "$CHROOT/proc" "$CHROOT/sys" 2>/dev/null || true
  sudo rm -rf "$WORK"
fi
mkdir -p "$CHROOT" "$ISO_DIR"

PKGS="linux-image-amd64,live-boot,live-config,live-config-systemd,live-tools,systemd-sysv,initramfs-tools,sudo,python3,curl,openssl,ca-certificates,nftables,ifupdown,dhcpcd5,iproute2,rsync"

if [ ! -f "$CHROOT/debootstrap/debootstrap.log" ]; then
  echo "Bootstrapping Debian bookworm with packages..."
  sudo debootstrap --arch="$ARCH" --include="$PKGS" bookworm "$CHROOT" http://deb.debian.org/debian
fi

sudo tee "$CHROOT/etc/apt/sources.list" >/dev/null <<'EOF'
deb http://deb.debian.org/debian bookworm main contrib non-free non-free-firmware
deb http://deb.debian.org/debian bookworm-updates main contrib non-free non-free-firmware
EOF

sudo mount --bind /dev "$CHROOT/dev"
sudo mount --bind /dev/pts "$CHROOT/dev/pts"
sudo mount -t proc proc "$CHROOT/proc"
sudo mount -t sysfs sys "$CHROOT/sys"
cleanup() {
  sudo umount -lf "$CHROOT/dev/pts" "$CHROOT/dev" "$CHROOT/proc" "$CHROOT/sys" 2>/dev/null || true
}
trap cleanup EXIT

# Mersal payload
sudo mkdir -p "$CHROOT/opt/mersal-guard" "$CHROOT/opt/mersal-os" "$CHROOT/var/lib/mersal-guard"
sudo rsync -a --exclude '__pycache__' --exclude data --exclude tests \
  "$REPO/xtreme-ip-guard/" "$CHROOT/opt/mersal-guard/"
sudo rsync -a "$ROOT/core/" "$CHROOT/opt/mersal-os/core/"
sudo rsync -a "$ROOT/gateway/" "$CHROOT/opt/mersal-os/gateway/"
sudo rsync -a "$ROOT/update-channel/" "$CHROOT/opt/mersal-os/update-channel/"
sudo rsync -a "$ROOT/rootfs-overlay/" "$CHROOT/"
sudo cp "$ROOT/gateway/nftables-mersal.conf" "$CHROOT/etc/nftables.conf"

sudo chmod +x "$CHROOT/usr/local/bin/"* 2>/dev/null || true
sudo chmod +x "$CHROOT/opt/mersal-os/update-channel/server.py" 2>/dev/null || true

if ! sudo chroot "$CHROOT" id mersal >/dev/null 2>&1; then
  sudo chroot "$CHROOT" useradd -m -s /bin/bash -G sudo mersal
fi
echo "mersal:mersal" | sudo chroot "$CHROOT" chpasswd

sudo chroot "$CHROOT" systemctl enable mersal-command-center.service mersal-guard-agent.service mersal-gateway.service mersal-update-orbit.service

sudo chroot "$CHROOT" apt-get clean

KERNEL="$(ls -1 "$CHROOT"/boot/vmlinuz-* | sort -V | tail -1)"
INITRD="$(ls -1 "$CHROOT"/boot/initrd.img-* | sort -V | tail -1)"
sudo cp "$KERNEL" "$ISO_DIR/vmlinuz"
sudo cp "$INITRD" "$ISO_DIR/initrd"
echo "Building squashfs (may take several minutes)..."
sudo mkdir -p "$ISO_DIR/live"
sudo mksquashfs "$CHROOT" "$ISO_DIR/live/filesystem.squashfs" -comp xz -e boot -noappend -processors "$(nproc)"
sudo tee "$ISO_DIR/live/filesystem.size" >/dev/null <<< "$(sudo du -sx --block-size=1 "$CHROOT" | cut -f1)"

sudo apt-get install -y -qq isolinux syslinux-utils xorriso 2>/dev/null || true
sudo mkdir -p "$ISO_DIR/isolinux"
if [ -f /usr/lib/ISOLINUX/isolinux.bin ]; then
  sudo cp /usr/lib/ISOLINUX/isolinux.bin "$ISO_DIR/isolinux/"
  sudo cp /usr/lib/syslinux/modules/bios/ldlinux.c32 "$ISO_DIR/isolinux/" 2>/dev/null || true
elif [ -f /usr/lib/syslinux/modules/bios/isolinux.bin ]; then
  sudo cp /usr/lib/syslinux/modules/bios/isolinux.bin "$ISO_DIR/isolinux/"
fi

sudo tee "$ISO_DIR/isolinux/isolinux.cfg" >/dev/null <<'CFG'
DEFAULT mersal
LABEL mersal
  KERNEL /vmlinuz
  APPEND initrd=/initrd boot=live components username=mersal hostname=mersal-os quiet splash
CFG

STAMP="$(date +%Y%m%d)"
FINAL="$DIST/mersal-os-${STAMP}-${ARCH}.iso"
sudo xorriso -as mkisofs -iso-level 3 -full-iso9660-filenames -volid MERSAL_OS \
  -eltorito-boot isolinux/isolinux.bin -eltorito-catalog isolinux/boot.cat \
  -no-emul-boot -boot-load-size 4 -boot-info-table \
  -output "$FINAL" "$ISO_DIR"
sudo chown "$(id -u):$(id -g)" "$FINAL" 2>/dev/null || true

( cd "$DIST" && sha256sum "$(basename "$FINAL")" > "$(basename "$FINAL").sha256" )
echo "SUCCESS: $FINAL"
ls -lh "$FINAL"
