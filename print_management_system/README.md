# Private Print Management MVP

This is a small, self-hosted print management prototype for organizations that
need private control over users, printers, print queues, quotas, and release
decisions. It is inspired by common print-management workflows, but it does not
copy any proprietary product internals or branding.

The MVP is intentionally dependency-free and uses:

- Python standard library HTTP server
- SQLite for local persistence
- JSON APIs for integration with print agents, admin panels, or kiosks

## Features

- Manage users with page quotas.
- Register printers and mark whether they support color.
- Submit print jobs with page count, copy count, color, and duplex metadata.
- Reject jobs when the user has insufficient quota.
- Reject color jobs on black-and-white printers.
- Release or cancel queued jobs.
- Refund quota when a queued job is cancelled.
- Keep an audit trail for created users, printers, and job state changes.
- Basic HTML dashboard at `/`.

## Run locally

```bash
cd print_management_system
python3 -m print_mgmt.app --db ./print_management.sqlite3 --host 127.0.0.1 --port 8080
```

Open:

```text
http://127.0.0.1:8080/
```

## API examples

Create a user:

```bash
curl -X POST http://127.0.0.1:8080/api/users \
  -H 'Content-Type: application/json' \
  -d '{"username":"sara","display_name":"Sara","quota_pages":100}'
```

Create a printer:

```bash
curl -X POST http://127.0.0.1:8080/api/printers \
  -H 'Content-Type: application/json' \
  -d '{"name":"Office A","location":"First floor","supports_color":true}'
```

Submit a job:

```bash
curl -X POST http://127.0.0.1:8080/api/jobs \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1,"printer_id":1,"title":"report.pdf","pages":12,"copies":1,"color":false,"duplex":true}'
```

Release a queued job:

```bash
curl -X POST http://127.0.0.1:8080/api/jobs/1/release
```

Cancel a queued job and refund quota:

```bash
curl -X POST http://127.0.0.1:8080/api/jobs/1/cancel
```

## Test

```bash
cd print_management_system
PYTHONPATH=. python3 -m unittest discover -s tests
```

## Next production steps

Before using this in a real environment, add:

- Authentication and role-based access control.
- HTTPS termination and secure cookie/session handling.
- Integration with CUPS, IPP, Windows Print Server, or printer vendor APIs.
- A print-agent service installed near printers to report real job status.
- Tenant/site separation if multiple branches are managed.
- Backup, retention, and audit export policies.
- Admin UI forms instead of the current read-only dashboard.
