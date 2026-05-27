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
- Print Provider CLI prototype for print-server/gateway spool events with an offline queue.
- Printer Controller CLI prototype for embedded/gateway-side platform metadata and held-job actions.
- Enterprise demo mode with polished command-center UI, readiness indicators, agent mesh, and source intelligence.
- No external runtime dependencies; it uses Python's standard library.

## Product components

The intended product is a distributed system, not one monolithic app:

| Component | Prototype file | Production role |
| --- | --- | --- |
| Extreme Server | `app.py`, `epms/server.py` | Central API, admin UI, policies, quotas, reports, storage |
| Extreme Client Agent | `client_agent.py` | User balance, popups, direct-print monitoring, account selection |
| Extreme Print Provider | `print_provider.py` | Windows Print Server / Linux CUPS spooler monitoring and offline queue |
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

For inspection from another machine or a cloud forwarded port, bind to all interfaces:

```bash
python3 -c "from epms.server import run; run(host='0.0.0.0', port=8080)"
```

In the dashboard, click **Load enterprise demo** to reset the local demo database with a full enterprise scenario.

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

## Run the Print Provider prototype

The Print Provider is the component that belongs on a print server or local gateway. In this prototype it accepts simulated spool events and submits them to the server.

```bash
cd extreme-print-management-system
python3 print_provider.py heartbeat --spooler cups --queue-name "Main Office HP,Library BW"
python3 print_provider.py submit-event --user-id 1 --printer-id 1 --document invoice.pdf --pages 10 --copies 1 --duplex
python3 print_provider.py queue-status
python3 print_provider.py flush-queue
```

If the server is unavailable, submitted events are stored in:

```text
data/print-provider-offline.jsonl
```

and can be replayed later with `flush-queue`.

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
| `GET` | `/api/readiness` | Demo readiness report for server and agent components |
| `POST` | `/api/jobs` | Submit a simulated print job |
| `POST` | `/api/jobs/{id}/release` | Release a held job |
| `POST` | `/api/jobs/{id}/deny` | Deny a held job |
| `POST` | `/api/users/{id}/credit` | Add balance to a user |
| `POST` | `/api/quotas/reset` | Reset active users to monthly quotas |
| `POST` | `/api/agents/heartbeat` | Register or refresh an agent/controller |
| `POST` | `/api/demo/reset` | Reset and load the enterprise demo scenario |

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
    "account": "Finance",
    "source": "print-provider",
    "agent_id": "print-provider-main-server"
  }'
```

## Tests

```bash
cd extreme-print-management-system
python3 -m unittest discover -s tests
```

## Next production steps

This is a working MVP foundation. For production use, the next engineering work should add authentication, role-based authorization, real print-server integration such as Windows spooler/CUPS/IPP, vendor SDK integrations for embedded devices, audit-log retention policies, organization-specific pricing rules, PostgreSQL support, TLS certificates for agents, and deployment hardening.
