#!/usr/bin/env bash
# Publish Mersal release to GitHub (requires gh CLI + GITHUB_TOKEN).
set -euo pipefail
VERSION="${1:-8.3.0}"
TAG="v${VERSION}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BODY_FILE="$ROOT/docs/GITHUB_RELEASE_v${VERSION}.md"

if [[ ! -f "$BODY_FILE" ]]; then
  BODY_FILE="$ROOT/docs/GITHUB_RELEASE_v8.2.0.md"
  TAG="v8.2.0"
fi

if ! command -v gh >/dev/null; then
  echo "Install GitHub CLI: https://cli.github.com/" >&2
  exit 1
fi

gh release create "$TAG" \
  --repo developer8181/ionomegax-mersal-ios \
  --title "Mersal ${TAG} — Advanced Independent Security Platform" \
  --notes-file "$BODY_FILE" \
  --target cursor/mersal-enterprise-bank-gov-eef7 \
  --draft \
  || gh release edit "$TAG" --notes-file "$BODY_FILE"

echo "Release $TAG ready (draft)."
