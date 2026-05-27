"""Optional PostgreSQL backend using pg8000 (pure Python)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .storage import Database


def open_postgres_database(dsn: str) -> Database:
    try:
        import pg8000.dbapi  # type: ignore[import-untyped]
    except ImportError as exc:
        raise RuntimeError(
            "PostgreSQL support requires pg8000. Install with: pip install pg8000"
        ) from exc

    from .storage import Database

    connection = pg8000.dbapi.connect(dsn)
    return PostgresDatabase(connection, dsn=dsn)


class PostgresDatabase:
    """Thin adapter: production deployments should prefer the SQLite Database until full PG port lands."""

    def __init__(self, connection: object, *, dsn: str):
        self._connection = connection
        self.path = dsn  # compatibility with Database.path checks

    def __getattr__(self, name: str):
        raise RuntimeError(
            "PostgreSQL adapter is scaffolded for deployment wiring. "
            "Use SQLite (EPMS_DB) or run migrations manually with deploy/postgres/schema.sql"
        )
