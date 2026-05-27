"""Environment-driven configuration for production deployments."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path
    pg_dsn: str | None
    agent_token: str | None
    session_secret: str
    require_auth: bool
    anonymize_documents: bool
    audit_retention_days: int
    tls_cert: Path | None
    tls_key: Path | None
    site_id: str
    upstream_url: str
    host: str
    port: int
    bootstrap_admin_password: str | None

    @classmethod
    def from_environ(cls, *, project_root: Path, default_db: Path) -> Settings:
        tls_cert = os.environ.get("EPMS_TLS_CERT", "").strip()
        tls_key = os.environ.get("EPMS_TLS_KEY", "").strip()
        return cls(
            db_path=Path(os.environ.get("EPMS_DB", str(default_db))),
            pg_dsn=os.environ.get("EPMS_PG_DSN", "").strip() or None,
            agent_token=os.environ.get("EPMS_AGENT_TOKEN", "").strip() or None,
            session_secret=os.environ.get("EPMS_SESSION_SECRET", "change-me-in-production"),
            require_auth=os.environ.get("EPMS_REQUIRE_AUTH", "").lower() in {"1", "true", "yes"},
            anonymize_documents=os.environ.get("EPMS_ANONYMIZE_DOCS", "").lower() in {"1", "true", "yes"},
            audit_retention_days=max(1, int(os.environ.get("EPMS_AUDIT_RETENTION_DAYS", "365"))),
            tls_cert=Path(tls_cert) if tls_cert else None,
            tls_key=Path(tls_key) if tls_key else None,
            site_id=os.environ.get("EPMS_SITE_ID", "site-local").strip() or "site-local",
            upstream_url=os.environ.get("EPMS_UPSTREAM_URL", "http://127.0.0.1:8080").rstrip("/"),
            host=os.environ.get("EPMS_HOST", "127.0.0.1"),
            port=int(os.environ.get("EPMS_PORT", "8080")),
            bootstrap_admin_password=os.environ.get("EPMS_BOOTSTRAP_ADMIN_PASSWORD", "").strip() or None,
        )
