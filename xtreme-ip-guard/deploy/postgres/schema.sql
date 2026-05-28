-- Mersal PostgreSQL schema (reference for HA deployments)
-- Application default remains SQLite; set MERSAL_POSTGRES_DSN when using this stack.

CREATE TABLE IF NOT EXISTS platform_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT INTO platform_meta (key, value) VALUES ('schema', 'mersal-v8-reference')
ON CONFLICT (key) DO NOTHING;

-- Full table DDL is applied by mersal migrations when PG adapter is enabled.
-- Use: python3 scripts/init-postgres.py (future) or replicate from SQLite migrations.
