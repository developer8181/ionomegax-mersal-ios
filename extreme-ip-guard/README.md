# Extreme IP Guard

Extreme IP Guard is a private, self-hosted cyber-defense prototype for controlling risky IP communications with a stronger zero-trust and adaptive-response model than traditional IP control products. It focuses on endpoint egress risk, network identity, policy-driven enforcement, incident generation, and operator visibility.

The project is intentionally standalone and does not modify the existing Monal application in this repository.

## Current MVP capabilities

- Asset inventory with trust score, segment, posture, and last-seen IP.
- Adaptive risk scoring for outbound IP events using reputation, TOR usage, geo anomalies, burst behavior, risky ports, process context, and asset criticality.
- Policy engine with trusted networks, blocked ports, blocked countries, and enforcement thresholds.
- Automated outcomes: `allow`, `observe`, `challenge`, `block`, or `quarantine`.
- Incident creation for disruptive or high-risk events.
- Agent heartbeat API for sensors, edge enforcers, site relays, and deception nodes.
- Browser dashboard for assets, policies, incidents, events, and risk reports.
- CLI sensor prototype for heartbeat and simulated event submission.
- SQLite persistence with demo seed data.
- No external runtime dependencies; it uses Python's standard library only.

## Product components

| Component | Prototype file | Production role |
| --- | --- | --- |
| Extreme IP Guard Server | `app.py`, `xipg/server.py` | Central API, dashboard, policies, incidents, storage |
| Extreme IP Sensor | `sensor_agent.py` | Endpoint or gateway telemetry, risk signals, heartbeat |
| Extreme Edge Enforcer | future service | eBPF / WFP / Network Extension / ZTNA inline enforcement |
| Extreme Site Relay | future service | Local buffering, branch failover, offline sync |
| Extreme Deception Mesh | future service | Sinkholes, decoys, tripwires, rapid threat confirmation |

See the Arabic architecture note:

- `docs/EXTREME_IP_GUARD_ARCHITECTURE_AR.md`

## Run locally

```bash
cd extreme-ip-guard
python3 app.py
```

Then open:

```text
http://127.0.0.1:8090
```

The default database is created at:

```text
extreme-ip-guard/data/extreme-ip-guard.sqlite3
```

To use a different database file:

```bash
XIPG_DB=/path/to/xipg.sqlite3 python3 app.py
```

## Run the sensor prototype

In another terminal while the server is running:

```bash
cd extreme-ip-guard
python3 sensor_agent.py profiles
python3 sensor_agent.py heartbeat --agent-id sensor-finance-01 --control-profile windows-wfp
python3 sensor_agent.py simulate-event \
  --asset-id 1 \
  --destination-ip 203.0.113.45 \
  --destination-port 445 \
  --country RU \
  --process-name powershell.exe \
  --ip-reputation-score 92 \
  --geo-anomaly \
  --burst-connections 240
```

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/dashboard` | Dashboard totals and risk reports |
| `GET` | `/api/assets` | List protected assets and posture |
| `GET` | `/api/policies` | List active protection policies |
| `GET` | `/api/events` | List recent network events |
| `GET` | `/api/incidents` | List generated incidents |
| `GET` | `/api/agents` | List registered agents |
| `GET` | `/api/control-profiles` | List supported enforcement profiles |
| `POST` | `/api/events` | Submit a network telemetry event |
| `POST` | `/api/agents/heartbeat` | Register or refresh an agent |
| `POST` | `/api/assets/{id}/quarantine` | Force an asset into quarantine posture |
| `POST` | `/api/incidents/{id}/resolve` | Resolve an incident |

Example event submission:

```bash
curl -X POST http://127.0.0.1:8090/api/events \
  -H 'Content-Type: application/json' \
  -d '{
    "asset_id": 1,
    "source_ip": "10.10.20.17",
    "destination_ip": "203.0.113.45",
    "destination_port": 445,
    "protocol": "tcp",
    "country": "RU",
    "bytes_out": 24500000,
    "bytes_in": 1200000,
    "process_name": "powershell.exe",
    "ip_reputation_score": 92,
    "tor_exit_node": false,
    "geo_anomaly": true,
    "burst_connections": 240
  }'
```

## Tests

```bash
cd extreme-ip-guard
python3 -m unittest discover -s tests
```

## Strategic direction

This MVP proves the system shape. For production use, the next engineering work should add:

- Mutual TLS, device certificates, and signed agent identities.
- Real endpoint enforcement adapters for Linux eBPF, Windows WFP/ETW, and macOS Network Extension.
- Threat-intelligence ingestion for ASN, domain, JA3/JA4, and malware infrastructure feeds.
- Behavioral baselining, graph analytics, and UEBA-style deviation detection.
- Site relay replication and store-and-forward for disconnected branches.
- PostgreSQL, RBAC, tamper-evident audit trails, and retention controls.
- Playbooks for sinkhole redirect, adaptive segmentation, MFA challenge, and SOAR integration.
