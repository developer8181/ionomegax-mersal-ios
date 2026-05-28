# Mersal v8.0 — منصة مستقلة متقدمة

## الاستقلال التشغيلي

Mersal v8 يعمل **دورة أمنية كاملة دون أدوات خارجية إلزامية**:

```text
تهديدات (KEV/STIX/TAXII) → فحص ثغرات → SIEM → XDR → SOAR → EDR عميق → تصدير SIEM → posture
```

تشغيل يدوي:

```bash
curl -X POST -H "X-Mersal-Token: $MERSAL_API_TOKEN" \
  http://127.0.0.1:8090/api/platform/autonomous-cycle
```

أو تلقائياً عبر `MERSAL_AUTONOMOUS=1` في المجدول اليومي.

## مكونات v8

| المكون | الوظيفة |
|--------|---------|
| `/api/platform/status` | صحة كل الوحدات + جاهزية مستقلة |
| `/api/platform/backup` | نسخ SQLite للتعافي |
| SIEM Forwarder | تصدير CEF/syslog إلى Splunk/QRadar/Elastic |
| OIDC SSO | Azure AD / Keycloak / Okta |
| Linux Deep EDR | FIM حرج، auth.log، المنافذ |
| Suricata Manager | استيعاب `eve.json` عند التثبيت |
| Docker standalone | PostgreSQL + Mersal |

## نشر مستقل (Docker)

```bash
export MERSAL_SIGNING_SECRET=$(openssl rand -hex 32)
export MERSAL_API_TOKEN=$(openssl rand -hex 24)
export MERSAL_ADMIN_PASSWORD='YourStrongPassphrase!'
./scripts/mersal-standalone-up.sh
```

## SSO (OIDC)

```bash
export MERSAL_OIDC_ISSUER=https://login.microsoftonline.com/TENANT/v2.0
export MERSAL_OIDC_CLIENT_ID=...
export MERSAL_OIDC_CLIENT_SECRET=...
export MERSAL_OIDC_REDIRECT_URI=https://mersal.corp.example/api/auth/oidc/callback
```

## تصدير SIEM

```bash
curl -X POST -H "X-Mersal-Token: $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Splunk","host":"siem.corp","port":514}' \
  http://127.0.0.1:8090/api/integrations/siem/forwarders
```

## ما يميز المنصات العالمية (لا يزال على الخارطة)

- محول PostgreSQL كامل لكل استعلامات التطبيق
- EDR kernel/eBPF
- تكامل SAML و SCIM
- توقيع تحديثات ووكلاء

© Ionomegax Mersal v8.0
