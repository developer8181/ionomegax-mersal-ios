# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Database adapter — SQLite (default) or PostgreSQL via MERSAL_POSTGRES_DSN."""

from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from ..config import postgres_dsn


def uses_postgres() -> bool:
    return bool(postgres_dsn())


class _RowCursor:
    def __init__(self, cursor: Any, *, backend: str) -> None:
        self._cursor = cursor
        self._backend = backend

    def fetchone(self) -> Any:
        row = self._cursor.fetchone()
        if row is None:
            return None
        if self._backend == "postgres":
            return _PgRow(row)
        return row

    def fetchall(self) -> list[Any]:
        rows = self._cursor.fetchall()
        if self._backend == "postgres":
            return [_PgRow(r) for r in rows]
        return list(rows)

    @property
    def rowcount(self) -> int:
        return int(self._cursor.rowcount)

    def __iter__(self) -> Iterator[Any]:
        if self._backend == "postgres":
            return (_PgRow(row) for row in self._cursor)
        return iter(self._cursor)


class _PgRow:
    """sqlite3.Row-like access for psycopg dict rows."""

    def __init__(self, mapping: dict[str, Any]) -> None:
        self._data = mapping

    def __getitem__(self, key: str | int) -> Any:
        if isinstance(key, int):
            return list(self._data.values())[key]
        return self._data[key]

    def keys(self) -> list[str]:
        return list(self._data.keys())


class DbConnection:
    """Unified connection: sqlite3 or PostgreSQL."""

    def __init__(self, raw: Any, *, backend: str) -> None:
        self._raw = raw
        self._backend = backend

    def execute(self, sql: str, params: tuple | list = ()) -> _RowCursor:
        sql = self._adapt_sql(sql)
        if self._backend == "postgres":
            cur = self._raw.cursor()
            cur.execute(sql, params)
            return _RowCursor(cur, backend="postgres")
        return _RowCursor(self._raw.execute(sql, params), backend="sqlite")

    def executescript(self, script: str) -> None:
        if self._backend == "postgres":
            for stmt in _split_sql(script):
                if stmt.strip():
                    self.execute(stmt)
            return
        self._raw.executescript(script)

    def commit(self) -> None:
        self._raw.commit()

    def rollback(self) -> None:
        self._raw.rollback()

    def __enter__(self) -> DbConnection:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        if self._backend == "postgres":
            self._raw.close()

    @staticmethod
    def _adapt_sql(sql: str) -> str:
        from .sql_dialect import adapt_sql

        return adapt_sql(sql)


def _split_sql(script: str) -> list[str]:
    return [part.strip() for part in script.split(";") if part.strip()]


def open_database(path: Path) -> DbConnection:
    if uses_postgres():
        return _open_postgres(postgres_dsn())
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return DbConnection(conn, backend="sqlite")


def _open_postgres(dsn: str) -> DbConnection:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise RuntimeError("PostgreSQL requires: pip install 'psycopg[binary]'") from exc
    raw = psycopg.connect(dsn, row_factory=dict_row)
    raw.autocommit = False
    return DbConnection(raw, backend="postgres")


def adapt_ddl_for_postgres(ddl: str) -> str:
    ddl = re.sub(
        r"(\w+)\s+INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT",
        r"\1 SERIAL PRIMARY KEY",
        ddl,
        flags=re.IGNORECASE,
    )
    return ddl
