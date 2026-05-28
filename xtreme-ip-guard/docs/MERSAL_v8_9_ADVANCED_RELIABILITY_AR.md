# Mersal v8.9 — موثوقية متقدمة واعتماد تشغيلي

**الإصدار:** 8.9.0

## الجديد

| الميزة | الوصف |
|--------|--------|
| **محرك الموثوقية** | درجة ثقة تشغيلية 0–100 + تصنيف SLA (gold/silver/bronze) |
| **وكلاء منقطعين** | كشف `last_seen` + تنبيهات SIEM تلقائية |
| **حزمة أدلة امتثال** | `GET /api/compliance/evidence-pack` + SHA256 للنزاهة |
| **جلسات مؤسسية** | TTL 8 ساعات في الإنتاج (قابل للتعديل) |
| **دورة كاملة** | فحص موثوقية + تنبيهات ضمن `complete-cycle` |

## API

```http
GET  /api/platform/reliability
POST /api/platform/reliability/scan
GET  /api/compliance/evidence-pack
```

## متغيرات

```bash
export MERSAL_AGENT_STALE_SECONDS=300
export MERSAL_SESSION_TTL_SECONDS=28800
```

## هدف الاعتماد

- `dependable_for_operations: true` في تقرير الموثوقية
- `trust_score >= 75` + سلسلة تدقيق صالحة
- `tier: production` أو `regulated` في enterprise-readiness
