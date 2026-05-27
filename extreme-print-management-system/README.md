# Extreme Print Management System

Extreme Print Management System is a private, self-hosted print-control prototype inspired by enterprise print-management products. It tracks users, printers, quotas, job costs, held jobs, and simple reports.

The project is intentionally standalone and does not modify the existing Monal application in this repository.

## Current capabilities

- User balances, monthly quotas, overdraft limits, and manual credit.
- Printer capability rules for color and duplex printing.
- Automatic job pricing by pages, copies, color mode, and duplex discount.
- Quota enforcement that prints, holds, or denies jobs.
- Admin release/deny flow for held jobs.
- SQLite persistence with demo seed data.
- Browser dashboard with recent jobs and usage reports.
- No external runtime dependencies; it uses Python's standard library.

## Run locally

```bash
cd extreme-print-management-system
python3 app.py
```

Then open:

```text
http://127.0.0.1:8080
```

The default database is created at:

```text
extreme-print-management-system/data/extreme-print-management.sqlite3
```

To use a different database file:

```bash
EPMS_DB=/path/to/epms.sqlite3 python3 app.py
```

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/dashboard` | Dashboard totals and reports |
| `GET` | `/api/users` | List users and balances |
| `GET` | `/api/printers` | List printers and capabilities |
| `GET` | `/api/jobs` | List recent print jobs |
| `POST` | `/api/jobs` | Submit a simulated print job |
| `POST` | `/api/jobs/{id}/release` | Release a held job |
| `POST` | `/api/jobs/{id}/deny` | Deny a held job |
| `POST` | `/api/users/{id}/credit` | Add balance to a user |
| `POST` | `/api/quotas/reset` | Reset active users to monthly quotas |

Example job submission:

```bash
curl -X POST http://127.0.0.1:8080/api/jobs \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 1,
    "printer_id": 1,
    "document_name": "invoice.pdf",
    "pages": 10,
    "copies": 2,
    "color": true,
    "duplex": true,
    "account": "Finance"
  }'
```

## Tests

```bash
cd extreme-print-management-system
python3 -m unittest discover -s tests
```

## Next production steps

This is a working MVP foundation. For production use, the next engineering work should add authentication, role-based authorization, real print-server integration such as CUPS/IPP, audit-log retention policies, organization-specific pricing rules, and deployment hardening.
