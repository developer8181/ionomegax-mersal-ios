# Mersal v8.4 — منصة تكامل عالمية

**الإصدار:** 8.4.0  
**الطبقة:** تكامل مؤسسي موحّد (Identity + Data + Operations + XDR/SOAR)

## ما الجديد

| المكوّن | التحسين |
|---------|---------|
| **PostgreSQL** | طبقة `sql_dialect` — `INSERT OR IGNORE` → `ON CONFLICT`, نوافذ زمنية متوافقة، `RETURNING event_id` عند الإدخال |
| **OIDC** | تحقق `id_token` عبر JWKS (RS256/PS256) مع `MERSAL_OIDC_STRICT` |
| **SAML** | طلب AuthnRequest حقيقي (HTTP-Redirect + deflate) بدل placeholder |
| **SCIM** | GET/PATCH/DELETE لمستخدم واحد، تعطيل وتغيير دور |
| **SIEM** | تقدّم cursor + إزالة تكرار الإرسال |
| **Scheduler** | دورة `autonomous_cycle` كاملة يومياً عند `MERSAL_AUTONOMOUS=1` |
| **XDR→SOAR** | جسر تنفيذ `isolate_endpoint` من نتائج XDR |
| **Integration Hub** | `GET /api/platform/integrations` — مصفوفة التكامل الموحّدة |

## تشغيل

```bash
cd xtreme-ip-guard
export MERSAL_ENTERPRISE=1 MERSAL_PRODUCTION=1
export MERSAL_AUTONOMOUS=1
python3 -m xig
```

- **حالة المنصة:** `GET /api/platform/status`
- **التكامل:** `GET /api/platform/integrations`
- **الجاهزية:** `GET /api/system/readiness`

## PostgreSQL (اختياري)

```bash
export MERSAL_POSTGRES_DSN="postgresql://mersal:secret@localhost:5432/mersal"
python3 scripts/init-postgres-schema.py
```

## حدود صادقة

v8.4 يقرّب المنصة من **تكامل عالمي self-hosted** (SIEM + IdP + SCIM + XDR/SOAR) لكنها **ليست** بديلاً كاملاً لـ CrowdStrike/Sentinel/Splunk Enterprise بدون: EDR kernel كامل، SAML موقّع xmlsec، HA PostgreSQL مُختبر بالكامل في الإنتاج.
