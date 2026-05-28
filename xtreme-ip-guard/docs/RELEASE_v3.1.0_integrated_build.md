# v3.1.0 — Integrated Build

## New in this release

- **Makefile** + `scripts/build-all.sh` + `scripts/verify-build.sh` — one-command integrated build
- **`python3 -m xig`** — standard module entry point
- **`GET /api/system/build`** — version, git commit, component list
- **`GET /api/threat/intel`** — CISA KEV + source breakdown
- **KEV correlation** — vulnerability findings prioritized when CVE is in KEV catalog
- **Command Center** — production readiness panel, threat intel section, KEV tags on CVEs
- **HTTP integration tests** — live server smoke suite
- **Mersal OS** — production env on command center service, install-to-disk in hook

## Build

```bash
make build-all
```

41 tests passing.
