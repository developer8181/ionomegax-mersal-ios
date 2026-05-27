# Extreme IP Guard

Extreme IP Guard is a private, self-hosted endpoint protection and data-loss
prevention prototype inspired by enterprise products such as IP-guard, but
designed around modern Zero Trust, transparent telemetry, risk scoring,
auditable response, and privacy-by-design controls.

The project is intentionally standalone and does not modify the existing Monal
application in this repository.

## Safety and ethics boundary

This prototype is for legitimate defensive administration on assets you own or
are authorized to manage. It does **not** include stealth surveillance,
keylogging, credential theft, exploit delivery, persistence bypasses, or covert
network interception. Production deployments must provide user notice, legal
review, role-based access, retention controls, and tamper-evident audit logs.

## Current capabilities

- Endpoint asset inventory and visible agent heartbeat.
- IP address classification without active scanning.
- Risk scoring from encryption, EDR, firewall, patch age, vulnerabilities,
  failed logins, DLP incidents, public exposure, sensitive local data, and
  unusual outbound volume.
- Policy action recommendations: allow, monitor, restrict, or isolate.
- Simulated DLP decisions for public, internal, confidential, and secret data.
- Manual asset isolate/restore API for response orchestration prototypes.
- SQLite persistence with demo seed data.
- Browser dashboard for assets, policies, risk distribution, and DLP events.
- Endpoint Agent CLI prototype for transparent posture and DLP event submission.
- No external runtime dependencies; it uses Python's standard library.

## Product components

| Component | Prototype file | Production role |
| --- | --- | --- |
| Extreme Control Plane | `app.py`, `eipg/server.py` | Central API, dashboard, policies, audit, integrations |
| Extreme Risk Engine | `eipg/core.py` | Risk scoring, DLP decisions, response recommendations |
| Extreme Data Store | `eipg/storage.py` | Assets, policies, events, audit, reporting |
| Extreme Endpoint Agent | `endpoint_agent.py` | Transparent workstation/server posture and event telemetry |
| Extreme Response Orchestrator | API prototype | EDR/NAC/SASE/SIEM/SOAR integrations |
| Extreme Governance Layer | docs | Privacy, consent, retention, and administrative controls |

See the Arabic architecture and governance notes:

- `docs/EXTREME_IP_GUARD_ARCHITECTURE_AR.md`
- `docs/SECURITY_PRIVACY_AR.md`

## Run locally

```bash
cd extreme-ip-guard-system
python3 app.py
```

Then open:

```text
http://127.0.0.1:8090
```

The default database is created at:

```text
extreme-ip-guard-system/data/extreme-ip-guard.sqlite3
```

To use a different database file:

```bash
EIPG_DB=/path/to/extreme-ip-guard.sqlite3 python3 app.py
```

## Run the Endpoint Agent prototype

In another terminal while the server is running:

```bash
cd extreme-ip-guard-system
python3 endpoint_agent.py heartbeat \
  --asset-id laptop-001 \
  --owner sara \
  --department Finance \
  --ip-address 10.20.1.42 \
  --sensitive-data

python3 endpoint_agent.py dlp-event \
  --asset-ref laptop-001 \
  --username sara \
  --channel external_upload \
  --sensitivity confidential \
  --destination personal-cloud.example \
  --bytes-count 1048576
```

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/dashboard` | Dashboard totals, distributions, recent assets/events |
| `GET` | `/api/assets` | List assets by highest risk |
| `GET` | `/api/policies` | List active baseline policies |
| `GET` | `/api/dlp-events` | List recent DLP decisions |
| `GET` | `/api/audit-log` | List audit records |
| `POST` | `/api/assets/heartbeat` | Register or refresh endpoint posture |
| `POST` | `/api/dlp-events` | Submit a simulated data movement event |
| `POST` | `/api/assets/{id}/isolate` | Mark an asset isolated |
| `POST` | `/api/assets/{id}/restore` | Restore an asset to healthy status |

Example asset heartbeat:

```bash
curl -X POST http://127.0.0.1:8090/api/assets/heartbeat \
  -H 'Content-Type: application/json' \
  -d '{
    "asset_id": "server-007",
    "hostname": "legacy-branch-server",
    "owner": "IT Operations",
    "department": "Infrastructure",
    "ip_address": "203.0.113.10",
    "os_name": "Ubuntu Server",
    "agent_version": "0.1.0",
    "posture": {
      "encryption_enabled": false,
      "edr_enabled": false,
      "firewall_enabled": true,
      "os_patch_age_days": 104,
      "critical_vulns": 2,
      "high_vulns": 4,
      "external_ip_exposure": true,
      "unusual_egress_mb": 512
    }
  }'
```

## Tests

```bash
cd extreme-ip-guard-system
python3 -m unittest discover -s tests
```

## Next production steps

This is a working MVP foundation. Production work should add SSO, MFA, RBAC,
tenant isolation, signed agent enrollment, mutual TLS, PostgreSQL, immutable
audit storage, SIEM/SOAR connectors, EDR/NAC integrations, privacy workflows,
policy versioning, approval queues, enterprise reporting, and deployment
hardening.

