# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Database backup for disaster recovery — independent of cloud."""

from __future__ import annotations

import hashlib
import secrets
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class BackupManager:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def create_backup(self, *, dest_dir: str | None = None) -> dict[str, Any]:
        src = Path(self.db.path)
        out_dir = Path(dest_dir or src.parent / "backups")
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_id = f"bkp-{secrets.token_hex(6)}"
        dest = out_dir / f"{backup_id}-{src.name}"
        shutil.copy2(src, dest)
        digest = hashlib.sha256(dest.read_bytes()).hexdigest()
        meta = self.db.register_backup(backup_id, str(dest), size_bytes=dest.stat().st_size, checksum=digest)
        return meta

    def list_backups(self) -> list[dict[str, Any]]:
        return self.db.list_platform_backups()
