#!/usr/bin/env python3
"""Initialize or verify PostgreSQL schema for Mersal HA deployments."""
from __future__ import annotations

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from xig.platform_ops.postgres_health import postgres_cluster_health
from xig.storage import Database


def main() -> None:
    parser = argparse.ArgumentParser(description="Mersal PostgreSQL schema")
    parser.add_argument("--verify", action="store_true", help="Only verify connectivity and schema health")
    args = parser.parse_args()

    dsn = os.environ.get("MERSAL_POSTGRES_DSN", "").strip()
    if not dsn:
        print("Set MERSAL_POSTGRES_DSN", file=sys.stderr)
        sys.exit(1)
    os.environ["MERSAL_POSTGRES_DSN"] = dsn

    health = postgres_cluster_health()
    if args.verify:
        print(health)
        sys.exit(0 if health.get("ok") else 2)

    db = Database(os.environ.get("MERSAL_DB", "data/mersal-pg-bridge.sqlite3"))
    db.init_schema()
    db.ensure_rbac_seed()
    print("PostgreSQL schema initialized via Mersal migrations.")
    print(postgres_cluster_health())


if __name__ == "__main__":
    main()
