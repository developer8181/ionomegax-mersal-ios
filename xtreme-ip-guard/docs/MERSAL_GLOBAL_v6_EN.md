# Mersal Global Platform v6.0

Unified **world-class** cybersecurity platform: XDR, SIEM, SOAR, GRC, multi-tenant SOC, RBAC, TAXII, and live alert streaming.

## vs. legacy stacks

| Legacy | Mersal v6 |
|--------|-----------|
| CrowdStrike + Sentinel + Splunk + XSOAR | Single platform |
| Workspace / index isolation | Native multi-tenant |
| Splunk ES correlation | Real-time + window rules |
| Separate GRC tool | NIST + ISO27001 + SOC2 |

See `GET /api/global/matrix` for full comparison.

## Environment

- `MERSAL_ADMIN_PASSWORD` — seeds RBAC admin user
- `MERSAL_TAXII_URL` — optional TAXII 2.0 server
- `MERSAL_TAXII_COLLECTION` — collection ID (default: `default`)
