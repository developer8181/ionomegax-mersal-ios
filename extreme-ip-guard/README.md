# Extreme IP Guard

**Extreme IP Guard (EIG)** is a self-hosted, next-generation internal security platform inspired by enterprise suites such as IP-guard. It combines data-loss prevention, network control, endpoint posture, Zero Trust session checks, behavioral anomaly scoring (UEBA prototype), MITRE ATT&CK–mapped policies, and a hash-linked immutable audit chain.

The project is standalone and does not modify the Monal XMPP client in this repository.

## Why Extreme vs classic IP-guard style products

| Capability | Classic internal security suites | Extreme IP Guard direction |
| --- | --- | --- |
| Trust model | Perimeter-oriented | Zero Trust continuous verification |
| Detection | Static rules | Policy rules + UEBA risk scoring |
| Audit | Standard DB logs | SHA-256 chained audit entries |
| Response | Block / alert | `allow` → `warn` → `block` → `quarantine` → `isolate` |
| Integration | Closed consoles | MITRE tags, SOAR hooks (planned), SIEM export (planned) |

## Current capabilities (v0.1 prototype)

- Central SOC dashboard (Arabic RTL UI).
- Policy engine with DLP, network, USB, web, application, identity, and print categories.
- Security event ingestion with automatic incident creation.
- Endpoint risk scoring from trust + recent events + anomaly score.
- Agent heartbeat API for endpoint and network sensor agents.
- Zero Trust session gate API.
- Quarantine / release workflow for endpoints.
- SQLite persistence with demo seed data.
- CLI prototypes: `client_agent.py`, `network_sensor.py`.
- Unit tests; no third-party Python dependencies.

## Product components

| Component | Prototype | Production role |
| --- | --- | --- |
| Extreme Server | `app.py`, `eig/server.py` | SOC console, policies, incidents, audit |
| Extreme Endpoint Agent | `client_agent.py` | DLP, USB, app/web telemetry |
| Extreme Network Sensor | `network_sensor.py` | Lateral movement, rogue device, port policy |
| Extreme DLP Probe | planned | Deep content inspection |
| Extreme Site Gateway | planned | Branch policy cache and sync |

Arabic documentation:

- `docs/IPGUARD_STUDY_AR.md`
- `docs/EXTREME_ARCHITECTURE_AR.md`

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

Custom database path:

```bash
EIG_DB=/path/to/eig.sqlite3 python3 app.py
```

## Agent examples

```bash
# Endpoint heartbeat
python3 client_agent.py --action heartbeat

# Simulate DLP event
python3 client_agent.py --action simulate-dlp

# Network rogue connection
python3 network_sensor.py --scenario rogue-connect

# Zero Trust check from CLI
python3 client_agent.py --action zt-check
```

## Tests

```bash
cd extreme-ip-guard
python3 -m unittest discover -s tests -v
```

## License

Same repository license as the parent project unless stated otherwise.
