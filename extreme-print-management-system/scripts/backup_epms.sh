#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB="${EPMS_DB:-$ROOT/data/extreme-print-management.sqlite3}"
BACKUP_DIR="${EPMS_BACKUP_DIR:-$ROOT/data/backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"

mkdir -p "$BACKUP_DIR"
DEST="$BACKUP_DIR/epms-$STAMP.sqlite3"

if [[ ! -f "$DB" ]]; then
  echo "Database not found: $DB" >&2
  exit 1
fi

sqlite3 "$DB" ".backup '$DEST'"
echo "Backup written to $DEST"
