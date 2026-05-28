# Mersal v8.2.0 — Independent Advanced Security Platform

## Release highlights

- **v8.0** Autonomous SOC cycle · SIEM CEF/syslog export · OIDC SSO · Suricata ingest · Docker HA stack
- **v8.1** Mandatory auth · RBAC · agent keys · rate limits · audit hash chain
- **v8.2** PostgreSQL adapter · SAML · SCIM · signed update channel · eBPF server probe

## Quick start

```bash
cd xtreme-ip-guard
pip install -r requirements.txt
cp mersal-guard.organization.example.env mersal-guard.env
# edit secrets
source mersal-guard.env
./scripts/provision-organization.sh
python3 -m xig
```

## Docker standalone

```bash
export MERSAL_SIGNING_SECRET=$(openssl rand -hex 32)
export MERSAL_API_TOKEN=$(openssl rand -hex 24)
export MERSAL_ADMIN_PASSWORD='YourStrongPassphrase!'
./scripts/mersal-standalone-up.sh
```

## Docs

- [MERSAL_v8_2_COMPLETE_AR.md](MERSAL_v8_2_COMPLETE_AR.md)
- [MERSAL_v8_STANDALONE_AR.md](MERSAL_v8_STANDALONE_AR.md)
- [MERSAL_PROFESSIONAL_CYBERSECURITY_AR.md](MERSAL_PROFESSIONAL_CYBERSECURITY_AR.md)

© Extreme Technology · Ionomegax Mersal
