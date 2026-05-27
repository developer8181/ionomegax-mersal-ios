#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
docker build -t mersal-os-builder -f "$ROOT/build/Dockerfile.builder" "$ROOT/build"
docker run --rm --privileged \
  -v "$ROOT:/mersal-os" \
  -w /mersal-os \
  mersal-os-builder \
  bash -c './build/build-iso.sh'
echo "ISO in $ROOT/dist/"
