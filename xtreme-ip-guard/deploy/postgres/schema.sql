-- Mersal Guard — PostgreSQL reference schema
-- Apply via: python3 scripts/init-postgres-schema.py
-- Requires MERSAL_POSTGRES_DSN

-- Core tables are created by xig.storage init_schema() with dialect adaptation.
-- This file documents required extensions and tuning for large institutions.

-- CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Recommended connection pool sizing for 10k+ endpoints:
-- max_connections = 200
-- shared_buffers = 256MB
