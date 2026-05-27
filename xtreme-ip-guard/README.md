# Xtreme IP Guard

Xtreme IP Guard is a standalone defensive endpoint-control and DLP prototype inspired by enterprise products such as IP-guard, but designed as a modern zero-trust platform rather than a simple monitoring tool.

The project is intentionally standalone and does not modify the existing Monal application in this repository.

## Current prototype capabilities

- Central Xtreme Server with a JSON API.
- SQLite persistence with demo seed data.
- Endpoint/agent heartbeat registration.
- Normalized endpoint telemetry ingestion.
- Deterministic risk scoring for DLP and endpoint events.
- Policy decisions: allow, monitor, warn, block, quarantine, isolate endpoint.
- CLI endpoint agent prototype for heartbeat and simulated telemetry.
- No external runtime dependencies; it uses Python's standard library.

## Product components

| Component | Prototype file | Production role |
| --- | --- | --- |
| Xtreme Command Center | `app.py`, `xig/server.py` | Central API, dashboard, policy engine, audit store, integrations |
| Xtreme Policy Brain | `xig/core.py` | Risk scoring, DLP policy decisions, future AI-assisted analytics |
| Xtreme Data Vault | `xig/storage.py` | Prototype SQLite storage; production would use HA SQL + event stream |
| Xtreme Endpoint Agent | `agent.py` | Workstation telemetry, policy enforcement, user prompts |
| Xtreme Response Orchestrator | future service | Isolation, quarantine, SOAR, EDR/XDR integrations |
| Xtreme Site Node | future service | Branch cache, offline enforcement, local event buffering |

See the Arabic architecture notes:

- `docs/XTREME_IP_GUARD_ARCHITECTURE_AR.md`
- `docs/IP_GUARD_STUDY_AR.md`

## Run locally

```bash
cd xtreme-ip-guard
python3 app.py
```

Then open:

```text
http://127.0.0.1:8090
```

The default database is created at:

```text
xtreme-ip-guard/data/xtreme-ip-guard.sqlite3
```

To use a different database file:

```bash
XIG_DB=/path/to/xig.sqlite3 python3 app.py
```

## Run the endpoint agent prototype

In another terminal while the server is running:

```bash
cd xtreme-ip-guard
python3 agent.py heartbeat --endpoint-id laptop-001 --owner sara
python3 agent.py simulate-event \
  --endpoint-id laptop-001 \
  --actor sara \
  --event-type file_copy \
  --channel removable_media \
  --classification secret \
  --resource /finance/payroll.xlsx \
  --destination usb:Kingston \
  --severity 25
```

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/dashboard` | Totals, recent events, action summary |
| `GET` | `/api/endpoints` | Registered endpoints and isolation state |
| `GET` | `/api/events` | Recent normalized security events |
| `GET` | `/api/policies` | Active and inactive policy rules |
| `GET` | `/api/agents` | Registered endpoint agents |
| `POST` | `/api/agents/heartbeat` | Register or refresh an endpoint agent |
| `POST` | `/api/events` | Ingest endpoint/DLP telemetry and evaluate policy |
| `POST` | `/api/policies` | Create a policy rule |
| `POST` | `/api/endpoints/{id}/isolate` | Mark an endpoint as isolated |
| `POST` | `/api/endpoints/{id}/restore` | Restore an isolated endpoint |

Example event submission:

```bash
curl -X POST http://127.0.0.1:8090/api/events \
  -H 'Content-Type: application/json' \
  -d '{
    "endpoint_id": "laptop-001",
    "actor": "sara",
    "event_type": "file_copy",
    "channel": "removable_media",
    "resource": "/finance/payroll.xlsx",
    "classification": "secret",
    "destination": "usb:Kingston",
    "severity": 25
  }'
```

## Tests

```bash
cd xtreme-ip-guard
python3 -m unittest discover -s tests
```

## Security note

This is a defensive prototype. It does not install kernel drivers, intercept live traffic, exfiltrate data, or perform destructive endpoint actions. Production enforcement must use signed agents, least privilege, tamper protection, audited administrative workflows, and explicit customer authorization.
