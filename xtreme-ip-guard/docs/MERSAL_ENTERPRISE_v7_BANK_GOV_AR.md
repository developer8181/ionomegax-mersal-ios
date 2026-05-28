# Mersal v7.0 — Enterprise · بنك · حكومة

## ما الجديد في v7

| القدرة | الوصف |
|--------|--------|
| **MERSAL_ENTERPRISE=1** | ملف تعريف صارم: إنتاج + أسرار إلزامية |
| **RBAC مُطبَّق** | كل مسار API يُربط بصلاحية (viewer لا يعزل، analyst لا يكتب سياسات) |
| **عزل المستأجرين** | فلترة endpoints/events/policies/siem/incidents حسب `tenant_id` |
| **سجل تدقيق متسلسل** | SHA-256 hash chain — `GET /api/audit/verify` |
| **جلسات موقّعة** | Token يحمل `role` + `tenant_id` |
| **LDAP اختياري** | Active Directory عبر `ldap3` |
| **YARA أصلي** | `yara-python` عند التثبيت (regex احتياطي) |
| **TLS + mTLS للوكلاء** | `MERSAL_AGENT_MTLS=1` |

## التثبيت السريع

```bash
cd xtreme-ip-guard
pip install -r requirements.txt   # اختياري: ldap3, yara-python, psycopg
./scripts/provision-enterprise.sh
source mersal-guard.enterprise.env   # بعد تعديل الأسرار
python3 -m xig
```

## فحص الجاهزية

```bash
curl -sk https://127.0.0.1:8090/api/system/readiness
curl -sk -H "X-Mersal-Token: $MERSAL_API_TOKEN" https://127.0.0.1:8090/api/audit/verify
```

## ما زال مطلوباً للإنتاج الوطني الكامل

- PostgreSQL HA + موازن حمل (بدل SQLite لآلاف النقاط)
- تكامل kernel/eBPF EDR
- Suricata مُدار على Mersal OS
- SSO SAML/OIDC
- توقيع ISO ووكلاء
- شهادات FIPS / HSM

راجع `docs/ROADMAP_SECURITY_AR.md` للمرحلة التالية.

© 2009–2026 Extreme Technology Company · Ionomegax Mersal
