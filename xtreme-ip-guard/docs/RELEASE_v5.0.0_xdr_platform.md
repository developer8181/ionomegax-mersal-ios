# v5.0.0 — Mersal XDR Platform

## New capabilities

- **Mersal XDR** — cross-layer correlation (SIEM + EDR + Vuln + Suricata) with auto-isolate
- **Mersal Log Vault** — centralized log ingest + search API
- **Suricata IDS** — eve.json ingestion + MITRE mapping
- **YARA engine** — built-in hunting rules on processes
- **MITRE ATT&CK** tags on SIEM alerts

## APIs

- `POST /api/xdr/correlate`
- `GET /api/xdr/findings`
- `POST /api/logs/ingest` · `GET /api/logs/search`
- `POST /api/suricata/ingest`

## Scripts

- `scripts/mersal-suricata-sync.py`
- `scripts/mersal-log-shipper.py`

## Tests

51+ unit tests

```bash
make test
```
