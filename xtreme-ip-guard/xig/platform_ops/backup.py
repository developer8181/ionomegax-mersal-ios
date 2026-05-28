# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Database backup for disaster recovery — SQLite file copy or PostgreSQL pg_dump."""

from __future__ import annotations

import hashlib
import os
import secrets
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..config import encryption_at_rest_enabled, postgres_dsn
from ..db.adapter import uses_postgres

if TYPE_CHECKING:
    from ..storage import Database


class BackupManager:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def create_backup(self, *, dest_dir: str | None = None) -> dict[str, Any]:
        out_dir = Path(dest_dir or self._default_backup_dir())
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_id = f"bkp-{secrets.token_hex(6)}"

        if uses_postgres():
            dest = out_dir / f"{backup_id}-mersal.pgdump"
            self._pg_dump(dest)
        else:
            src = Path(self.db.path)
            dest = out_dir / f"{backup_id}-{src.name}"
            shutil.copy2(src, dest)

        if encryption_at_rest_enabled():
            dest = self._encrypt_file(dest)

        digest = hashlib.sha256(dest.read_bytes()).hexdigest()
        meta = self.db.register_backup(
            backup_id,
            str(dest),
            size_bytes=dest.stat().st_size,
            checksum=digest,
        )
        meta["encrypted"] = encryption_at_rest_enabled()
        meta["backend"] = "postgres" if uses_postgres() else "sqlite"
        self._prune_old_backups(out_dir)
        return meta

    def list_backups(self) -> list[dict[str, Any]]:
        return self.db.list_platform_backups()

    def restore_backup(self, backup_id: str) -> dict[str, Any]:
        record = self._find_backup(backup_id)
        if not record:
            return {"error": "backup not found"}
        path = Path(str(record["path"]))
        if not path.is_file():
            return {"error": "backup file missing"}
        if path.suffix == ".enc":
            path = self._decrypt_file(path)
        if uses_postgres():
            self._pg_restore(path)
            return {"restored": True, "backup_id": backup_id, "backend": "postgres"}
        shutil.copy2(path, Path(self.db.path))
        return {"restored": True, "backup_id": backup_id, "backend": "sqlite"}

    def health(self) -> dict[str, Any]:
        backups = self.list_backups()
        latest = backups[0] if backups else None
        age_hours = None
        if latest and latest.get("created_at"):
            try:
                raw = str(latest["created_at"])
                created = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                age_hours = (datetime.now(timezone.utc) - created).total_seconds() / 3600
            except ValueError:
                age_hours = None
        retention = int(os.environ.get("MERSAL_BACKUP_RETENTION_DAYS", "30"))
        ok = latest is not None and (age_hours is None or age_hours <= retention * 24)
        return {
            "ok": ok,
            "count": len(backups),
            "latest": latest,
            "age_hours": age_hours,
            "retention_days": retention,
            "backend": "postgres" if uses_postgres() else "sqlite",
        }

    def _find_backup(self, backup_id: str) -> dict[str, Any] | None:
        for row in self.list_backups():
            if str(row.get("backup_id")) == backup_id:
                return row
        return None

    @staticmethod
    def _default_backup_dir() -> Path:
        from ..config import data_directory

        return data_directory() / "backups"

    @staticmethod
    def _pg_dump(dest: Path) -> None:
        dsn = postgres_dsn()
        subprocess.run(
            ["pg_dump", dsn, "-Fc", "-f", str(dest)],
            check=True,
            capture_output=True,
            timeout=600,
        )

    @staticmethod
    def _pg_restore(path: Path) -> None:
        dsn = postgres_dsn()
        subprocess.run(
            ["pg_restore", "--clean", "--if-exists", "-d", dsn, str(path)],
            check=True,
            capture_output=True,
            timeout=900,
        )

    @staticmethod
    def _encrypt_file(path: Path) -> Path:
        from cryptography.fernet import Fernet

        key = os.environ.get("MERSAL_BACKUP_ENCRYPTION_KEY", "").strip()
        if not key:
            raise ValueError("MERSAL_BACKUP_ENCRYPTION_KEY required when MERSAL_DB_ENCRYPTION=1")
        if len(key) != 44:
            raise ValueError("MERSAL_BACKUP_ENCRYPTION_KEY must be a 44-char Fernet key")
        fernet = Fernet(key.encode())
        enc_path = path.with_suffix(path.suffix + ".enc")
        enc_path.write_bytes(fernet.encrypt(path.read_bytes()))
        path.unlink(missing_ok=True)
        return enc_path

    @staticmethod
    def _decrypt_file(path: Path) -> Path:
        from cryptography.fernet import Fernet

        key = os.environ.get("MERSAL_BACKUP_ENCRYPTION_KEY", "").strip()
        fernet = Fernet(key.encode())
        plain = path.with_suffix("")
        plain.write_bytes(fernet.decrypt(path.read_bytes()))
        return plain

    @staticmethod
    def _prune_old_backups(out_dir: Path) -> None:
        retention_days = int(os.environ.get("MERSAL_BACKUP_RETENTION_DAYS", "30"))
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        for path in out_dir.iterdir():
            if not path.is_file():
                continue
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                path.unlink(missing_ok=True)
