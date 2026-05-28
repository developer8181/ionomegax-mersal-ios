#!/usr/bin/env python3
"""Initialize PostgreSQL schema for Mersal HA deployments."""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from xig.db.adapter import adapt_ddl_for_postgres, open_database
from xig.storage import Database


def main() -> None:
    dsn = os.environ.get("MERSAL_POSTGRES_DSN", "").strip()
    if not dsn:
        print("Set MERSAL_POSTGRES_DSN", file=sys.stderr)
        sys.exit(1)
    os.environ["MERSAL_POSTGRES_DSN"] = dsn
    db = Database(os.environ.get("MERSAL_DB", "data/mersal-pg-bridge.sqlite3"))
    db.init_schema()
    db.ensure_rbac_seed()
    print("PostgreSQL schema initialized via Mersal migrations.")


if __name__ == "__main__":
    main()
