# Mersal v8.7 — المنصة المتكاملة الكاملة

**الإصدار:** 8.7.0

## نظرة عامة

v8.7 يجمع كل طبقات المنصة في **لوحة تحكم موحّدة** و**دورة SOC واحدة** و**تثبيت بنقرة واحدة**.

## التثبيت الكامل

```bash
cd xtreme-ip-guard
chmod +x scripts/mersal-complete-install.sh
./scripts/mersal-complete-install.sh mersal-guard.env
source mersal-guard.env && python3 -m xig
```

## واجهات API الموحّدة

| Endpoint | الوصف |
|----------|--------|
| `GET /api/platform/unified` | لوحة المنصة الكاملة (صحة + تكامل + اعتماد) |
| `POST /api/platform/complete-cycle` | دورة SOC كاملة + نسخ احتياطي |
| `POST /api/platform/bootstrap-enterprise` | تهيئة مؤسسية (سياسات، SIEM، تهديدات) |
| `GET /api/system/enterprise-readiness` | تقرير اعتماد المؤسسة |

## Command Center

قسم **«التكامل الكامل»** في `/console/`:
- تصنيف الاعتماد والدرجة
- نسيج التكامل (OIDC/SAML/Postgres/Backup)
- أزرار: تهيئة مؤسسية · دورة كاملة

## القدرات المدمجة (v6–v8.7)

- SIEM · XDR · SOAR · EDR · eBPF · Vuln · Threat Intel · Compliance
- OIDC · SAML · SCIM · LDAP
- PostgreSQL HA · PgBouncer · نسخ احتياطي مشفّر
- وكلاء: طابور، تحديثات موقّعة، mTLS
- دورة مستقلة · تصدير SIEM · Suricata

## Docker (مؤسسة كبرى)

```bash
# تكامل + HA
docker compose -f deploy/docker-compose.ha.yml up -d
# أو enterprise صارم
docker compose -f deploy/docker-compose.enterprise.yml up -d
```

## الإصدارات التراكمية

| إصدار | محور |
|-------|------|
| v8.4 | تكامل OIDC/SAML/SCIM/SIEM |
| v8.5 | موثوقية DR/SAML/وكلاء |
| v8.6 | HA Postgres + تقرير اعتماد |
| v8.7 | **منصة موحّدة + واجهة + تثبيت كامل** |
