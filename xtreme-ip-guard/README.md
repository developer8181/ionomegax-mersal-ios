# Ionomegax Mersal Global Security Platform

<p align="center">
  <img src="web/logo-unified.svg" alt="Mersal by Extreme Technology" height="72" />
  <br />
  <strong>Powered by Extreme Technology Company</strong>
</p>

**Mersal v8.9** is a **complete unified cybersecurity platform** with **advanced operational reliability** (trust score, SLA tier, stale-agent detection, compliance evidence packs) for banks, government, and large enterprises — **unified control plane**, PostgreSQL HA (PgBouncer), SAML/OIDC/SCIM, signed agent updates, eBPF EDR, autonomous SOC cycle, DR backup/restore, enterprise adoption scorecard — plus **XDR**, **SIEM**, **SOAR**, **EDR**, **Log Vault**, **GRC**, **multi-tenant RBAC**, and **Neural Cortex AI**, with an Arabic/English **Command Center** and agents for Linux, Windows, macOS, and **Mersal OS 8.7**.

Designed by **Eng. Mahmoud Rasem Bayari** · **Ionomegax** · **Mersal** (مرسال).

| Resource | Link |
|----------|------|
| **Master guide (AR)** | [docs/PLATFORM_MASTER_AR.md](docs/PLATFORM_MASTER_AR.md) |
| v8.7 Complete platform (AR) | [docs/MERSAL_v8_7_COMPLETE_PLATFORM_AR.md](docs/MERSAL_v8_7_COMPLETE_PLATFORM_AR.md) |
| v8.6 Enterprise HA (AR) | [docs/MERSAL_v8_6_ENTERPRISE_HA_AR.md](docs/MERSAL_v8_6_ENTERPRISE_HA_AR.md) |
| v8.5 Reliability (AR) | [docs/MERSAL_v8_5_ENTERPRISE_RELIABILITY_AR.md](docs/MERSAL_v8_5_ENTERPRISE_RELIABILITY_AR.md) |
| v8.4 Integration (AR) | [docs/MERSAL_v8_4_GLOBAL_INTEGRATION_AR.md](docs/MERSAL_v8_4_GLOBAL_INTEGRATION_AR.md) |
| v8.2 Complete (AR) | [docs/MERSAL_v8_2_COMPLETE_AR.md](docs/MERSAL_v8_2_COMPLETE_AR.md) |
| v8 Standalone (AR) | [docs/MERSAL_v8_STANDALONE_AR.md](docs/MERSAL_v8_STANDALONE_AR.md) |
| Professional (AR) | [docs/MERSAL_PROFESSIONAL_CYBERSECURITY_AR.md](docs/MERSAL_PROFESSIONAL_CYBERSECURITY_AR.md) |
| Enterprise v7 (AR) | [docs/MERSAL_ENTERPRISE_v7_BANK_GOV_AR.md](docs/MERSAL_ENTERPRISE_v7_BANK_GOV_AR.md) |
| v6 Global (AR) | [docs/MERSAL_GLOBAL_v6_AR.md](docs/MERSAL_GLOBAL_v6_AR.md) |
| v6 Global (EN) | [docs/MERSAL_GLOBAL_v6_EN.md](docs/MERSAL_GLOBAL_v6_EN.md) |
| Light UI release | [docs/GITHUB_RELEASE_v6_ui_light.md](docs/GITHUB_RELEASE_v6_ui_light.md) |
| Screenshots (22) | [docs/screenshots/README.md](docs/screenshots/README.md) |
| Latest release | [GitHub Releases](https://github.com/developer8181/ionomegax-mersal-ios/releases) |

## Copyright

Designed and developed by **Eng. Mahmoud Rasem Bayari**, Cybersecurity Systems Engineer — Ramallah, Palestine. Founder of **Extreme Technology Company**. **All rights reserved © 2009–2026**. See [COPYRIGHT.md](COPYRIGHT.md) and Command Center → **About the System** / **معلومات عن النظام**.

## Platform stack

| Layer | Role |
| --- | --- |
| Mersal Command Center | Central API, policy engine, Arabic/English console |
| Mersal XDR | Cross-layer correlation (`xig/xdr/`) |
| Mersal SIEM | Alerts, MITRE ATT&CK (`xig/siem/`) |
| Mersal Log Vault | Log ingest & search (`xig/logvault/`) |
| Mersal Global Security Fabric | Vuln scan, threat intel, SOAR (`xig/fabric/`) |
| Mersal Neural Cortex | AI learning, anomaly detection (`xig/ai/`) |
| Mersal Policy Brain | Risk scoring and DLP decisions (`xig/core.py`) |
| Mersal Data Vault | SQLite persistence (`xig/storage.py`) |
| Mersal Endpoint Agent | OS sensors, heartbeat daemon, enforcement (`agent.py`, `xig/agent_runtime.py`) |
| OS adapters | Linux (procfs/sysfs), Windows (PowerShell/WMI), macOS (diskutil) |

## Integrated build (recommended)

```bash
cd xtreme-ip-guard
make build-all    # unit tests + smoke verify + optional Docker
make verify       # tests + HTTP smoke only
```

Production trial:

```bash
make production-env
source mersal-guard.production.env
python3 app.py
# or: python3 -m xig
```

Public summary: `GET /api/platform/summary`  
Readiness (no auth): `GET /api/system/readiness`  
Enterprise adoption: `GET /api/system/enterprise-readiness`  
Unified dashboard (auth): `GET /api/platform/unified`  
Build metadata: `GET /api/system/build`

**Enterprise install:** `make enterprise-install`

See [docs/PRODUCTION_TRIAL_AR.md](docs/PRODUCTION_TRIAL_AR.md) and [docs/BUILD_INTEGRATED_AR.md](docs/BUILD_INTEGRATED_AR.md).

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

Or full production install with TLS:

```bash
sudo bash scripts/install-production.sh
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
| `GET` | `/api/system/readiness` | Production readiness report |
| `GET` | `/api/system/build` | Build version and git metadata |
| `GET` | `/api/threat/intel` | Threat intel + CISA KEV summary |
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
