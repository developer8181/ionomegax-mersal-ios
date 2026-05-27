# Extreme Print Management System

Extreme Print Management System is a private, self-hosted print-control prototype inspired by enterprise print-management products such as PaperCut. It tracks users, printers, quotas, job costs, held jobs, agents, printer-controller metadata, and simple reports.

The project is intentionally standalone and does not modify the existing Monal application in this repository.

## Current capabilities

- User balances, monthly quotas, overdraft limits, and manual credit.
- Printer capability rules for color and duplex printing.
- Automatic job pricing by pages, copies, color mode, and duplex discount.
- Quota enforcement that prints, holds, or denies jobs.
- Admin release/deny flow for held jobs.
- SQLite persistence with demo seed data.
- Browser dashboard with recent jobs and usage reports.
- Agent heartbeat API for client agents and printer controllers.
- Client Agent CLI prototype for workstation-side balance checks and print-job submission.
- Printer Controller CLI prototype for embedded/gateway-side platform metadata and held-job actions.
- No external runtime dependencies; it uses Python's standard library.

## Product components

The intended product is a distributed system, not one monolithic app:

| Component | Prototype file | Production role |
| --- | --- | --- |
| Extreme Server | `app.py`, `epms/server.py` | Central API, admin UI, policies, quotas, reports, storage |
| Extreme Client Agent | `client_agent.py` | User balance, popups, direct-print monitoring, account selection |
| Extreme Print Provider | future service | Windows Print Server / Linux CUPS spooler monitoring |
| Extreme Printer Controller | `printer_controller.py` | Embedded MFD app or gateway controller for release/deny/device login |
| Extreme Site Server | future service | Offline branch cache and later sync |

See the Arabic study and architecture notes:

- `docs/PAPERCUT_STUDY_AR.md`
- `docs/EXTREME_ARCHITECTURE_AR.md`

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

## Run the Client Agent prototype

In another terminal while the server is running:

```bash
cd extreme-print-management-system
python3 client_agent.py heartbeat --direct-monitor
python3 client_agent.py balance --user sara
python3 client_agent.py submit-job --user sara --printer-id 1 --document report.pdf --pages 4 --duplex
```

## Run the Printer Controller prototype

```bash
cd extreme-print-management-system
python3 printer_controller.py platforms
python3 printer_controller.py heartbeat --vendor hp --model "FutureSmart MFP" --device-address 192.0.2.50
python3 printer_controller.py release --job-id 1
```

Real embedded support must be implemented per vendor SDK/platform. The prototype includes a shared adapter registry for HP OXP/Workpath, Canon MEAP, Ricoh SmartSDK, Xerox EIP, Sharp OSA, Konica Minolta OpenAPI, Toshiba e-BRIDGE, Kyocera HyPAS, Lexmark eSF, Epson Open Connect, and a generic gateway fallback.

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/dashboard` | Dashboard totals and reports |
| `GET` | `/api/users` | List users and balances |
| `GET` | `/api/printers` | List printers and capabilities |
| `GET` | `/api/jobs` | List recent print jobs |
| `GET` | `/api/agents` | List registered server/client/provider/controller agents |
| `GET` | `/api/printer-platforms` | List supported embedded/gateway platform profiles |
| `POST` | `/api/jobs` | Submit a simulated print job |
| `POST` | `/api/jobs/{id}/release` | Release a held job |
| `POST` | `/api/jobs/{id}/deny` | Deny a held job |
| `POST` | `/api/users/{id}/credit` | Add balance to a user |
| `POST` | `/api/quotas/reset` | Reset active users to monthly quotas |
| `POST` | `/api/agents/heartbeat` | Register or refresh an agent/controller |

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

This is a working MVP foundation. For production use, the next engineering work should add authentication, role-based authorization, real print-server integration such as Windows spooler/CUPS/IPP, vendor SDK integrations for embedded devices, audit-log retention policies, organization-specific pricing rules, PostgreSQL support, TLS certificates for agents, and deployment hardening.
