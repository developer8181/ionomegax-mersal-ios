# Mersal Global Platform v6.0 — منصة عالمية موحّدة

## الرؤية

**Mersal v6.0** يرفع المنصة إلى مستوى يوازي أنظمة **CrowdStrike · Microsoft Sentinel · Splunk ES · Palo Alto XSOAR** من حيث البنية الوظيفية — في حزمة واحدة قابلة للنشر على بنيتك.

## القدرات الجديدة

| الوحدة | الوصف |
|--------|--------|
| **Multi-Tenant** | عزل مؤسسات / MSP — `tenants` + `X-Mersal-Tenant` |
| **RBAC** | أدوار: super_admin · soc_admin · analyst · viewer |
| **SIEM Window** | ارتباط نوافذ زمنية (brute force · block storm · lateral) |
| **GRC موسّع** | NIST-CSF + ISO 27001 + SOC 2 |
| **TAXII 2.0** | `MERSAL_TAXII_URL` + `MERSAL_TAXII_COLLECTION` |
| **Reporting** | تصدير CSV تنفيذي / امتثال / حوادث / SIEM |
| **SOAR Webhooks** | تكامل Slack · ServiceNow · Logic Apps |
| **Alert SSE** | `/api/alerts/stream` — بث حي للتنبيهات |

## API رئيسية

- `GET /api/global/dashboard` · `POST /api/global/cycle`
- `GET /api/tenants` · `POST /api/tenants`
- `GET /api/users` · `GET /api/webhooks` · `POST /api/webhooks`
- `GET /api/reports/export?type=executive`
- `POST /api/threat/taxii/sync`

## التشغيل

```bash
cd xtreme-ip-guard
make test
python3 -m xig
```

© Ionomegax · المهندس محمود راسم بياري
