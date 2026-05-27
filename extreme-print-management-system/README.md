# Extreme Print Management System

Extreme Print Management System is a private, self-hosted print-management platform inspired by enterprise products such as PaperCut. It tracks users, printers, quotas, job costs, held jobs, distributed agents, printer-controller metadata, audit logs, and operational reports.

The project is intentionally standalone and does not modify the existing Monal application in this repository.

## Production capabilities

- User balances, monthly quotas, overdraft limits, and manual credit.
- Department-based pricing rules with per-department multipliers.
- Printer capability rules for color and duplex printing.
- Automatic job pricing by pages, copies, color mode, and duplex discount.
- Quota enforcement that prints, holds, or denies jobs.
- Admin release/deny flow and user-facing **Release Station** (`/release`).
- Immutable transaction ledger for debits, credits, and quota resets.
- SQLite persistence (default) with PostgreSQL reference schema for external DB deployments.
- Optional admin authentication with RBAC roles (`superadmin`, `admin`, `operator`, `viewer`).
- Optional agent API token enforcement (`EPMS_AGENT_TOKEN`).
- Optional TLS termination (`EPMS_TLS_CERT`, `EPMS_TLS_KEY`).
- Optional document-name anonymization for privacy (`EPMS_ANONYMIZE_DOCS`).
- Configurable audit-log retention with purge API.
- Browser dashboard (Arabic/English, RTL) with admin sign-in.
- Distributed agents: Client, Print Provider (CUPS + Windows export), Printer Controller, Site Server.
- Docker Compose deployment scaffold.
- **55 automated tests** — stdlib only for runtime.
- **Production mode** (`EPMS_PRODUCTION=1`) with config validation, security headers, and provisioning script.
- **Built-in device servlet** (`/extreme/sdk/v1/*`) — MFD controllers can use the server URL directly.
- Embedded vendor adapter framework (HP OXP, Canon MEAP, gateway fallback) — see `docs/EMBEDDED_ADAPTERS_AR.md`.
- Minimal IPP Get-Jobs client for generic network printers.

## Product components

| Component | File | Role |
| --- | --- | --- |
| Extreme Server | `app.py`, `epms/server.py` | Central API, admin UI, policies, quotas, reports |
| Extreme Client Agent | `client_agent.py` | Workstation balance, direct-print monitor, job submission |
| Extreme Print Provider | `print_provider.py` | CUPS / Windows spooler gateway with offline queue |
| Extreme Printer Controller | `printer_controller.py` | Embedded MFD / gateway release and device metadata |
| Extreme Site Server | `site_server.py` | Branch offline cache and upstream sync outbox |
| Release Station | `release_station/` | Tablet/kiosk UI for users to release held jobs |

Architecture notes (Arabic):

- `docs/PAPERCUT_STUDY_AR.md`
- `docs/EXTREME_ARCHITECTURE_AR.md`

## Production deploy (recommended)

```bash
cd extreme-print-management-system
bash scripts/provision_production.sh
set -a && source deploy/production.generated.env && set +a
python3 app_production.py
```

See `docs/PRODUCTION_READY_AR.md` — includes device servlet at `/extreme/sdk/v1/`, Docker, backups, and checklist API.

## Quick start (development)

```bash
cd extreme-print-management-system
python3 app.py
```

Open `http://127.0.0.1:8080` — Release Station at `http://127.0.0.1:8080/release`.

### VPS / سيرفر خاص

تثبيت إنتاجي على Ubuntu/Debian: [docs/VPS_INSTALL_AR.md](docs/VPS_INSTALL_AR.md)

```bash
sudo bash scripts/install_on_vps.sh --method docker --domain print.example.com --email you@example.com
```

Production-style environment (see `deploy/production.example.env`):

```bash
export EPMS_HOST=0.0.0.0
export EPMS_REQUIRE_AUTH=true
export EPMS_SESSION_SECRET='long-random-secret'
export EPMS_AGENT_TOKEN='long-random-agent-token'
export EPMS_BOOTSTRAP_ADMIN_PASSWORD='your-admin-password'
export EPMS_ANONYMIZE_DOCS=true
python3 app.py
```

Default database: `data/extreme-print-management.sqlite3`

## Docker

```bash
cd extreme-print-management-system/deploy
docker compose up --build
```

## Site Server (branch / offline)

```bash
python3 site_server.py heartbeat
python3 site_server.py cache-job --user-id 1 --printer-id 1 --document branch.pdf --pages 5
python3 site_server.py sync
python3 site_server.py pull-snapshot
```

## Print Provider

```bash
python3 print_provider.py cups-discover
python3 print_provider.py cups-poll --user-map config/cups-user-map.example.json --printer-map config/cups-printer-map.example.json
python3 print_provider.py windows-poll --queue-name HQ_Printer --jobs-file jobs.txt --user-map config/cups-user-map.example.json --printer-map config/cups-printer-map.example.json
```

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/login` | Admin sign-in |
| `POST` | `/api/auth/logout` | End admin session |
| `GET` | `/api/auth/me` | Current admin session |
| `GET` | `/api/dashboard` | Dashboard totals |
| `GET` | `/api/pricing-rules` | Department pricing rules |
| `POST` | `/api/pricing-rules` | Upsert pricing rule |
| `POST` | `/api/audit-logs/purge` | Apply retention policy |
| `GET` | `/api/release/held/{username}` | Held jobs for Release Station |
| `POST` | `/api/release/jobs/{id}/release` | User release at device |
| `GET` | `/api/health` | Liveness / database health |
| `GET` | `/api/readiness` | Production readiness report |
| `POST` | `/api/devices/login` | MFD user login via embedded adapter |
| … | (see previous endpoints) | jobs, users, printers, agents, demo reset |

Privileged endpoints honor `EPMS_REQUIRE_AUTH` and the `X-EPMS-Session` header (or `epms_session` cookie).

## Tests

```bash
cd extreme-print-management-system
python3 -m unittest discover -s tests
```

## Vendor SDK pack

Full SDK integration for **HP, Canon, Ricoh, Xerox, Konica Minolta, Kyocera, Lexmark, Olivetti**:

- Python HTTP clients: `epms/embedded/sdk_clients/` (Extreme servlet + native vendor paths)
- Java servlet + per-vendor bridges: `sdk/java/`
- Official vendor JARs: place in `sdk/jars/` (from manufacturer partner portal)

```bash
curl http://127.0.0.1:8080/api/sdk/vendors
python3 printer_controller.py login --vendor kyocera --username sara --device-address https://mfd.local/
```

Certified on-device binaries still come from each manufacturer; EPMS ships the integration layer and build scaffolds.
