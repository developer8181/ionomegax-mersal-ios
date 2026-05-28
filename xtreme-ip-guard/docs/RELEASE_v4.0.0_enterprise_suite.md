# v4.0.0 — Mersal Enterprise Security Suite

Unified alternative architecture: **EDR + SIEM + SOAR + VM + GRC + Network + AI** in one platform.

## Modules

- Mersal SIEM (correlation rules, alerts)
- Mersal EDR (process, network flows, FIM)
- Mersal Incident Response (cases, timeline)
- Mersal Compliance (NIST-CSF)
- Mersal Network Security (nftables policy)
- Mersal Global Security Fabric (existing stack)

## APIs

`/api/enterprise/dashboard`, `/api/siem/alerts`, `/api/incidents`, `/api/compliance`, `/api/edr/detections`, `/api/network/flows`

## Tests

48 passing.

```bash
make build-all
```
