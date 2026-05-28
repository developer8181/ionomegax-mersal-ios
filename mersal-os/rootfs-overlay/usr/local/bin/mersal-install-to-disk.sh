#!/usr/bin/env bash
# Mersal OS — install live system to local disk (trial/production lab)
set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root."
  exit 1
fi

TARGET="${1:-}"
if [[ -z "${TARGET}" ]]; then
  echo "Usage: mersal-install-to-disk.sh /dev/sdX"
  echo "WARNING: This will ERASE the target disk."
  exit 1
fi

if [[ ! -b "${TARGET}" ]]; then
  echo "Not a block device: ${TARGET}"
  exit 1
fi

echo "Mersal OS install-to-disk -> ${TARGET}"
read -r -p "Type YES to continue: " confirm
[[ "${confirm}" == "YES" ]] || exit 1

LIVE_ROOT="${LIVE_ROOT:-/run/live/medium/live/filesystem.squashfs}"
if [[ -f /run/live/medium/live/filesystem.squashfs ]]; then
  LIVE_ROOT="/"
fi

parted -s "${TARGET}" mklabel gpt
parted -s "${TARGET}" mkpart primary fat32 1MiB 513MiB
parted -s "${TARGET}" set 1 esp on
parted -s "${TARGET}" mkpart primary ext4 513MiB 100%
partprobe "${TARGET}" || true
sleep 2

EFI_PART="${TARGET}1"
ROOT_PART="${TARGET}2"
[[ -b "${EFI_PART}" ]] || EFI_PART="${TARGET}p1"
[[ -b "${ROOT_PART}" ]] || ROOT_PART="${TARGET}p2"

mkfs.vfat -F32 -n MERSAL-EFI "${EFI_PART}"
mkfs.ext4 -L mersal-root "${ROOT_PART}"

MNT=/mnt/mersal-install
mkdir -p "${MNT}"
mount "${ROOT_PART}" "${MNT}"
mkdir -p "${MNT}/boot/efi"
mount "${EFI_PART}" "${MNT}/boot/efi"

echo "Copying live root (rsync)..."
rsync -aHAX --info=progress2 "${LIVE_ROOT}/" "${MNT}/" \
  --exclude=/proc --exclude=/sys --exclude=/dev --exclude=/run --exclude=/tmp \
  --exclude=/mnt --exclude=/media --exclude=/live

cat >"${MNT}/etc/fstab" <<EOF
# Mersal OS installed
${ROOT_PART}  /          ext4  defaults  0 1
${EFI_PART}   /boot/efi  vfat  umask=0077  0 1
EOF

if [[ -d "${MNT}/boot/grub" ]]; then
  grub-install --target=x86_64-efi --efi-directory="${MNT}/boot/efi" --boot-directory="${MNT}/boot" --removable
  grub-mkconfig -o "${MNT}/boot/grub/grub.cfg"
fi

systemctl enable mersal-guard-agent.service mersal-command-center.service mersal-gateway.service \
  --root="${MNT}" 2>/dev/null || true

umount "${MNT}/boot/efi" "${MNT}"
rmdir "${MNT}" 2>/dev/null || true

echo "Mersal OS installed on ${TARGET}. Reboot and remove live media."
