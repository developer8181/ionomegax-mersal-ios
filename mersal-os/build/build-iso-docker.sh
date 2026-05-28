#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$ROOT/.." && pwd)"
docker build -t mersal-os-builder -f "$ROOT/build/Dockerfile.builder" "$ROOT/build"
docker run --rm --privileged \
  -v "$REPO:/repo" \
  -w /repo/mersal-os \
  mersal-os-builder \
  bash -c 'apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq live-build debootstrap squashfs-tools xorriso isolinux syslinux-utils grub-pc-bin grub-efi-amd64-bin rsync openssl ca-certificates && ./build/build-iso.sh'
echo "ISO in $ROOT/dist/"
