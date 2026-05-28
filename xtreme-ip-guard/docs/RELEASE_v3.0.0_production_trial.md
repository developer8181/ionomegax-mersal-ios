# Release v3.0.0 — Production Trial (Mersal Global Security Fabric)

## Highlights

- **Production mode** — real policies and bootstrap; demo data only with `MERSAL_DEMO_UI=1`
- **CISA KEV** — live Known Exploited Vulnerabilities catalog sync
- **EDR-lite** — Linux process monitoring and suspicious-pattern alerts
- **Vulnerability engine** — agent telemetry + optional `nmap` + port/CVE correlation
- **Readiness API** — `GET /api/system/readiness` for honest go-live checks
- **Installers** — `scripts/install-production.sh`, `scripts/generate-tls.sh`
- **Mersal OS** — `mersal-install-to-disk.sh` for lab disk installs

## Quick start

```bash
cd xtreme-ip-guard
export MERSAL_PRODUCTION=1 MERSAL_API_TOKEN=your-token MERSAL_BOOTSTRAP=1
export MERSAL_DB=data/trial.sqlite3
python3 app.py
# https://127.0.0.1:8090/console/  (or http if TLS not set)
```

## Tests

35 unit tests — `python3 -m unittest discover -s tests -v`

---

Ionomegax · Extreme Technology · Eng. Mahmoud Rasem Bayari · © 2009–2026
