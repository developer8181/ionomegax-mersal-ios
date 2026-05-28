# Mersal v8.2 — اكتمال المنصة المستقلة

## الجديد في v8.2

| القدرة | الوصف |
|--------|--------|
| **PostgreSQL** | `MERSAL_POSTGRES_DSN` — محول قاعدة بيانات موحّد مع SQLite |
| **SAML 2.0** | `/api/auth/saml/login` + `/api/auth/saml/acs` |
| **SCIM 2.0** | `/api/scim/v2/Users` — تزويد مستخدمين تلقائي |
| **قناة تحديث موقّعة** | `/api/updates/publish` + `/api/updates/latest` |
| **eBPF probe** | جمع برامج kernel عند توفر `bpftool` |

## PostgreSQL HA

```bash
export MERSAL_POSTGRES_DSN=postgresql://mersal:secret@localhost:5432/mersal
python3 scripts/init-postgres-schema.py
python3 -m xig
```

أو:

```bash
./scripts/mersal-standalone-up.sh
```

## SAML

```bash
export MERSAL_SAML_SSO_URL=https://idp.example/saml/sso
export MERSAL_SAML_ENTITY_ID=mersal-sp
```

## SCIM

```bash
export MERSAL_SCIM_TOKEN=$(openssl rand -hex 24)
curl -H "Authorization: Bearer $MERSAL_SCIM_TOKEN" \
  http://127.0.0.1:8090/api/scim/v2/Users
```

## تحديثات موقّعة

```bash
export MERSAL_UPDATE_SIGNING_KEY=$(openssl rand -hex 32)
curl -X POST -H "X-Mersal-Token: $MERSAL_API_TOKEN" \
  -d '{"component":"agent","version":"8.2.0","artifact_url":"https://...","checksum_sha256":"..."}' \
  http://127.0.0.1:8090/api/updates/publish
```

© Ionomegax Mersal v8.2
