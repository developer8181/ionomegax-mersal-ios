# Mersal Guard v8.8.0 — Release channel on develop

**Tag:** `v8.8.0`

## Changes

- `develop` merged with full v8.4–v8.7 platform stack
- Public `GET /api/platform/summary` for status pages
- Mersal OS release metadata synced to platform 8.7+
- `make enterprise-install` target
- Master platform documentation

## Install

```bash
make enterprise-install
source mersal-guard.env && python3 -m xig
```
