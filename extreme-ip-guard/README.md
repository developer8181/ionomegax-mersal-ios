# Extreme IP Guard

**Extreme IP Guard** is a next-generation Zero Trust Network Access Control (NAC) platform — an evolution beyond traditional IP Guard systems. It combines device identity, micro-segmentation, behavioral threat detection, signed policy distribution, and immutable audit logging in a self-hosted, agent-based architecture.

The project is standalone and does not modify the Monal application in this repository.

## Beyond traditional IP Guard

| Capability | Traditional IP Guard | Extreme IP Guard |
| --- | --- | --- |
| MAC/IP binding | Yes | Yes + device posture + trust scoring |
| Allow/deny lists | Static | Dynamic + threat intel + auto-response TTL |
| NAC | 802.1X | Zero Trust continuous verification + SDP-ready |
| Threat detection | Basic | Behavioral engine (port scan, brute force, auto-block) |
| Segmentation | VLAN-based | Policy-driven zones (secure, dmz, guest, iot) |
| Audit | Local logs | Hash-chained immutable audit trail |
| Enforcement | Firewall scripts | nftables / eBPF-XDP / WFP / Envoy (production) |
| Policy sync | Manual | Signed policy bundles with version control |

## Current capabilities

- Zero Trust policy engine (CIDR, port, protocol, zone, time window, trust score)
- Device registry with MAC/IP binding and approval workflow
- Active block lists (manual, threat intel, auto-response)
- Behavioral threat detection (port scan, brute force escalation)
- Access evaluation API with full decision logging
- Signed policy bundles for edge agent distribution
- Hash-chained audit trail
- Micro-segmentation zones (secure, dmz, guest, iot)
- Admin dashboard (Arabic UI)
- Edge Enforcer, Endpoint Agent, and Flow Sensor CLI prototypes
- SQLite persistence with demo seed data
- No external runtime dependencies (Python standard library only)

## Product components

| Component | Prototype file | Production role |
| --- | --- | --- |
| Extreme IP Guard Server | `app.py`, `eipg/server.py` | Central policy engine, threat intel, audit, admin UI |
| Extreme Edge Enforcer | `edge_agent.py` | Gateway firewall enforcement (nftables/eBPF-XDP) |
| Extreme Endpoint Agent | `endpoint_agent.py` | Workstation NAC, posture, USB control |
| Extreme Flow Sensor | `flow_sensor.py` | NetFlow/Zeek/Suricata telemetry ingestion |
| Extreme Site Server | future | Branch offline cache and sync |
| Extreme NAC Gateway | future | 802.1X/RADIUS integration |

See architecture and threat model docs:

- `docs/EXTREME_IP_GUARD_ARCHITECTURE_AR.md`
- `docs/THREAT_MODEL.md`

## Run locally

```bash
cd extreme-ip-guard
python3 app.py
```

Open:

```text
http://127.0.0.1:8090
```

Default database:

```text
extreme-ip-guard/data/extreme-ip-guard.sqlite3
```

Custom database:

```bash
EIPG_DB=/path/to/eipg.sqlite3 python3 app.py
```

## Run agents

Edge Enforcer:

```bash
python3 edge_agent.py heartbeat --backend nftables
python3 edge_agent.py pull-policy --simulate-rules
python3 edge_agent.py evaluate --source-ip 10.0.1.50 --destination-ip 8.8.8.8 --port 443
```

Endpoint Agent:

```bash
python3 endpoint_agent.py register --device-id dev-laptop-001 --zone secure --owner ahmed
python3 endpoint_agent.py heartbeat
python3 endpoint_agent.py check-access --destination-ip 8.8.8.8 --port 443
```

Flow Sensor:

```bash
python3 flow_sensor.py heartbeat
python3 flow_sensor.py ingest --source-ip 10.0.1.50 --destination-ip 8.8.8.8 --port 443
python3 flow_sensor.py simulate-scan --source-ip 203.0.113.99
python3 flow_sensor.py brute-force --source-ip 203.0.113.88 --attempts 10
```

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/dashboard` | Dashboard statistics |
| `GET` | `/api/zones` | Network micro-segments |
| `GET` | `/api/devices` | Registered devices |
| `GET` | `/api/policies` | Active policies |
| `GET` | `/api/blocks` | Active blocks |
| `GET` | `/api/events` | Security events |
| `GET` | `/api/access-log` | Access decisions |
| `GET` | `/api/agents` | Registered agents |
| `GET` | `/api/audit` | Hash-chained audit trail |
| `GET` | `/api/policy-bundle` | Signed policy bundle for agents |
| `GET` | `/api/enforcement-backends` | Supported enforcement backends |
| `POST` | `/api/evaluate` | Evaluate network access |
| `POST` | `/api/devices` | Register a device |
| `POST` | `/api/devices/{id}/approve` | Approve pending device |
| `POST` | `/api/policies` | Create a policy |
| `POST` | `/api/blocks` | Block IP or CIDR |
| `POST` | `/api/events` | Record security event |
| `POST` | `/api/flows` | Ingest flow telemetry |
| `POST` | `/api/brute-force` | Report brute-force attempt |
| `POST` | `/api/agents/heartbeat` | Agent check-in |

Example access evaluation:

```bash
curl -X POST http://127.0.0.1:8090/api/evaluate \
  -H 'Content-Type: application/json' \
  -d '{
    "source_ip": "10.0.1.50",
    "destination_ip": "8.8.8.8",
    "destination_port": 443,
    "protocol": "tcp",
    "device_id": "dev-laptop-001"
  }'
```

## Tests

```bash
cd extreme-ip-guard
python3 -m unittest discover -s tests
```

## Next production steps

Authentication and RBAC, mTLS for agents, PostgreSQL, real nftables/eBPF enforcement module, 802.1X/RADIUS NAC integration, DHCP snooping, threat intel feed connectors, SIEM export, high-availability deployment, and post-quantum agent authentication.
