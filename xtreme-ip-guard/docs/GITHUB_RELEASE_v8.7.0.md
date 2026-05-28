# Mersal Guard v8.7.0 — Complete Unified Platform

**Tag:** `v8.7.0`  
**Base:** `develop` (includes v8.4 → v8.7)

## Highlights

- **Unified control plane** — `GET /api/platform/unified`, complete SOC cycle, enterprise bootstrap
- **Enterprise reliability (v8.5)** — PostgreSQL backup/restore, SAML verify, agent queue, RBAC platform permissions
- **HA & adoption (v8.6)** — PgBouncer compose, enterprise readiness scorecard, SCIM admin tokens
- **Global integration (v8.4)** — OIDC JWKS, SCIM lifecycle, SIEM cursor, XDR→SOAR bridge

## Quick start

```bash
cd xtreme-ip-guard
./scripts/mersal-complete-install.sh mersal-guard.env
source mersal-guard.env && python3 -m xig
```

Open: http://127.0.0.1:8090/console/

## Docker

```bash
docker compose -f deploy/docker-compose.ha.yml up -d
```

## Tests

95+ unit/integration tests (`make test`)
