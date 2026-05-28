# Extreme Cyber Security — Integrated Global Alternative

**Version:** 1.1.0 · **Lineage:** Mersal 8.9 · **Model:** sovereign self-hosted

## Vision

One platform on your infrastructure replacing fragmented global stacks:

| Market class | Examples | ECS |
|--------------|----------|-----|
| EDR/XDR | CrowdStrike · Microsoft Defender | Agent + XDR + isolation |
| SIEM | Splunk · Sentinel | Correlation + windows + export |
| SOAR | Cortex XSOAR · Logic Apps | Playbooks + webhooks |
| GRC | ServiceNow GRC | NIST · ISO27001 · SOC2 |
| Threat intel | Commercial clouds | STIX/TAXII + CISA KEV |
| Identity | Entra ID · Okta | OIDC · SAML · SCIM |

## Activate integrated mode

```bash
cd xtreme-ip-guard
make enterprise-install
source mersal-guard.env
python3 -m xig
```

**One-shot API activation:**

```bash
curl -X POST -H "X-Mersal-Token: $TOKEN" \
  http://127.0.0.1:8090/api/platform/global-alternative/activate
```

## APIs

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/platform/global-alternative` | Global-alternative readiness summary |
| GET | `/api/platform/global-alternative/matrix` | Parity matrix vs major vendors |
| POST | `/api/platform/global-alternative/activate` | Bootstrap + SOC cycle + evidence |
| GET | `/api/platform/unified` | Unified dashboard + `parity_index` |
| POST | `/api/platform/complete-cycle` | Full cycle (no fabric required) |

## Parity index

Computed from **21 capabilities** vs CrowdStrike / Sentinel / Splunk / Palo Alto tiers (`full` · `strong` · `partial` · `roadmap`).

| Index | Tier |
|-------|------|
| ≥ 88 | `global_alternative` |
| ≥ 75 | `enterprise_integrated` |
| ≥ 60 | `pilot_unified` |

## Recommended production environment

See `recommended_production_env()` via `GET /api/platform/global-alternative` — includes `MERSAL_PRODUCTION`, Postgres DSN, TLS, signing keys, autonomous scheduler.

## Honest positioning

ECS is an **integrated architectural alternative**, not a third-party license bundle. For national-scale event rates, scale Postgres and SIEM export. For kernel-class EDR on every OS, plan additional sensor integration per policy.

---

© Extreme Technology · Eng. Mahmoud Rasem Bayari · 2009–2026
