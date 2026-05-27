# Ionomegax Mersal Guard

**Ionomegax Mersal Guard** is an integrated endpoint protection and data-loss-prevention platform. It is not a JSON-only API: it ships a full **Mersal Command Center** web console, a continuous **Mersal Endpoint Agent** for Linux, Windows, and macOS, and **local policy enforcement** on managed hosts.

The product brand is **Ionomegax** · **Mersal Guard** (مرسال — حماية نقاط النهاية).

## Platform stack

| Layer | Role |
| --- | --- |
| Mersal Command Center | Central API, policy engine, Arabic/English console |
| Mersal Policy Brain | Risk scoring and DLP decisions (`xig/core.py`) |
| Mersal Data Vault | SQLite persistence (`xig/storage.py`) |
| Mersal Endpoint Agent | OS sensors, heartbeat daemon, enforcement (`agent.py`, `xig/agent_runtime.py`) |
| OS adapters | Linux (procfs/sysfs), Windows (PowerShell/WMI), macOS (diskutil) |

## Quick start

### 1. Start the server

```bash
cd xtreme-ip-guard
python3 app.py
```

Open the console:

```text
http://127.0.0.1:8090/console/
```

### Production provisioning

```bash
./scripts/provision.sh mersal-guard.env
source mersal-guard.env
python3 app.py
```

This enables API token auth for agents and admin login for the Command Center.

Optional TLS:

```bash
export MERSAL_TLS_CERT=/path/to/fullchain.pem
export MERSAL_TLS_KEY=/path/to/privkey.pem
python3 app.py
```

### Docker

```bash
./scripts/provision.sh mersal-guard.env
docker compose -f deploy/docker-compose.yml up --build
```

### 2. Run the endpoint agent (daemon)

Edit `config/agent.json`, then:

```bash
python3 agent.py daemon --config config/agent.json
```

One-shot commands:

```bash
python3 agent.py profile
python3 agent.py sensors
python3 agent.py heartbeat --endpoint-id laptop-001 --owner sara
python3 agent.py status
```

### 3. Linux production install

```bash
chmod +x scripts/install-linux.sh
./scripts/install-linux.sh
```

## API (selected)

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/console/` | Command Center UI |
| `GET` | `/api/auth/status` | Whether authentication is required |
| `POST` | `/api/auth/login` | Admin session token |
| `GET` | `/api/audit` | Administrative audit trail |
| `GET` | `/api/brand` | Product branding metadata |
| `GET` | `/api/dashboard` | Console metrics |
| `GET` | `/api/endpoints/{id}/directives` | Policies + isolation for agents |
| `POST` | `/api/agents/heartbeat` | Agent registration |
| `POST` | `/api/events` | Telemetry + policy decision |

Use header `X-Mersal-Token` when `MERSAL_API_TOKEN` is set.

## Tests

```bash
cd xtreme-ip-guard
python3 -m unittest discover -s tests
```

## Security note

Mersal Guard is a defensive platform. Local enforcement writes state under `~/.mersal-guard` and optional Linux udev hints. Full USB/network blocking requires administrator-approved OS integration (EDR, MDM, firewall). Always deploy with signed agents, least privilege, and customer authorization.

## Documentation

- `docs/MERSAL_GUARD_PLATFORM_AR.md`
- `docs/XTREME_IP_GUARD_ARCHITECTURE_AR.md` (legacy study notes)
