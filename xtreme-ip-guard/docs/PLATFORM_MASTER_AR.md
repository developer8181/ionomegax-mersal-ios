# Mersal — المنصة المتكاملة الكاملة (دليل رئيسي)

**الإصدار الحالي:** 8.8.0 · **المنتج:** Ionomegax Mersal Global Security Platform

## التثبيت السريع

```bash
cd xtreme-ip-guard
make enterprise-install
source mersal-guard.env && python3 -m xig
```

## الوحدات المدمجة

| الوحدة | API / مسار |
|--------|------------|
| Command Center | `/console/` |
| لوحة موحّدة | `GET /api/platform/unified` |
| جاهزية | `GET /api/system/readiness` |
| اعتماد مؤسسة | `GET /api/system/enterprise-readiness` |
| دورة كاملة | `POST /api/platform/complete-cycle` |
| تهيئة | `POST /api/platform/bootstrap-enterprise` |
| XDR | `/api/xdr/` |
| SIEM | `/api/siem/` |
| SOAR | `/api/soar/` |
| Enterprise | `/api/enterprise/` |

## الإصدارات

| Doc | محتوى |
|-----|--------|
| [MERSAL_v8_7_COMPLETE_PLATFORM_AR.md](MERSAL_v8_7_COMPLETE_PLATFORM_AR.md) | منصة موحّدة |
| [MERSAL_v8_6_ENTERPRISE_HA_AR.md](MERSAL_v8_6_ENTERPRISE_HA_AR.md) | HA Postgres |
| [MERSAL_v8_5_ENTERPRISE_RELIABILITY_AR.md](MERSAL_v8_5_ENTERPRISE_RELIABILITY_AR.md) | DR/وكلاء |
| [MERSAL_v8_4_GLOBAL_INTEGRATION_AR.md](MERSAL_v8_4_GLOBAL_INTEGRATION_AR.md) | SSO/SIEM |

## Docker

- `deploy/docker-compose.yml` — SQLite
- `deploy/docker-compose.standalone.yml` — Postgres
- `deploy/docker-compose.ha.yml` — Postgres + PgBouncer
- `deploy/docker-compose.enterprise.yml` — مؤسسة صارمة

## Mersal OS

ISO يتضمن المنصة في `/opt/mersal-guard` — راجع `mersal-os/docs/BUILD_ISO_AR.md`.
