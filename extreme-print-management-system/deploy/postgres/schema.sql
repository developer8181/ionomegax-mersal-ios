-- Reference PostgreSQL schema for external DB deployments.
-- The application runtime currently uses SQLite via EPMS_DB.

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    department TEXT NOT NULL DEFAULT 'General',
    balance_cents INTEGER NOT NULL DEFAULT 0,
    monthly_quota_cents INTEGER NOT NULL DEFAULT 0,
    overdraft_cents INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS print_jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    printer_id INTEGER NOT NULL,
    document_name TEXT NOT NULL,
    pages INTEGER NOT NULL,
    copies INTEGER NOT NULL,
    color BOOLEAN NOT NULL,
    duplex BOOLEAN NOT NULL,
    account TEXT NOT NULL DEFAULT 'Personal',
    cost_cents INTEGER NOT NULL,
    status TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'web',
    agent_id TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
