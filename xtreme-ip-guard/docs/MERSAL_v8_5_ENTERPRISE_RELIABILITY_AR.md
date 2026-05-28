# Mersal v8.5 — موثوقية المؤسسات الكبرى

**الإصدار:** 8.5.0  
**الهدف:** منصة متكاملة قابلة للاعتماد في البنوك والحكومات والشركات الكبرى (آلاف النقاط الطرفية)

## القدرات الجديدة

| المحور | التفاصيل |
|--------|----------|
| **نسخ احتياطي DR** | SQLite نسخ ملف / PostgreSQL `pg_dump`، تشفير اختياري، استعادة، جدولة يومية |
| **SAML موثوق** | Conditions/Audience + توقيع xmlsec عند `MERSAL_SAML_IDP_CERT` |
| **OIDC/SAML أدوار** | `MERSAL_GROUP_ROLE_MAP` يربط مجموعات AD/Okta بالأدوار |
| **وكيل مرن** | طابور أحداث على القرص، تحديثات موقّعة staged، mTLS إلزامي عند التفعيل |
| **RBAC منصة** | `platform.read/write`, `updates.publish`, `integrations.admin` |
| **تشغيل صارم** | `MERSAL_ENTERPRISE_STRICT=1` يفرض TLS + Postgres + مفتاح تحديث منفصل |
| **Docker مؤسسي** | `deploy/docker-compose.enterprise.yml` |

## نشر مؤسسة كبرى

```bash
export MERSAL_ENTERPRISE=1
export MERSAL_PRODUCTION=1
export MERSAL_ENTERPRISE_STRICT=1
export MERSAL_POSTGRES_DSN="postgresql://..."
export MERSAL_TLS_CERT=/etc/mersal/tls.crt
export MERSAL_TLS_KEY=/etc/mersal/tls.key
export MERSAL_UPDATE_SIGNING_KEY="$(openssl rand -hex 32)"
export MERSAL_GROUP_ROLE_MAP='{"SOC-Admins":"soc_admin","Auditors":"viewer"}'
export MERSAL_SAML_IDP_CERT="$(cat idp.pem)"
docker compose -f deploy/docker-compose.enterprise.yml up -d
```

## واجهات API

- `GET /api/platform/integrations` — مصفوفة التكامل + صحة النسخ الاحتياطي
- `POST /api/platform/integrations/probe/{backup|updates|saml|postgres}`
- `POST /api/platform/restore` — `{"backup_id":"bkp-..."}`
- `GET /api/updates/latest` — يتطلب وكيلاً أو مصادقة منصة

## حدود صادقة

v8.5 يجهّز **اعتماد مؤسسي self-hosted**؛ لا يزال يلزم اختبار حمل على Postgres HA فعلي، توقيع ISO، وEDR kernel كامل للمقارنة مع CrowdStrike/Sentinel في البيئات الوطنية الكبرى جداً.
