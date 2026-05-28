# Mersal v8.6 — HA وجاهزية المؤسسات الكبرى

**الإصدار:** 8.6.0

## الجديد

| المكوّن | الوصف |
|---------|--------|
| **تقرير الاعتماد** | `GET /api/system/enterprise-readiness` — درجة وتصنيف (evaluation → regulated) |
| **PostgreSQL HA** | فحص عنقود + تأخر replication، `deploy/docker-compose.ha.yml` (PgBouncer) |
| **SIEM TLS** | بروتوكول `syslog_tls` للتوجيه إلى Splunk/QRadar |
| **SCIM إداري** | `POST /api/admin/scim-tokens` لإصدار رموز تزويد |
| **وكيل** | `MERSAL_AGENT_AUTO_APPLY=1` لتطبيق التحديثات المجهّزة |
| **توقيع الإصدارات** | `scripts/sign-release-manifest.py` لـ ISO/حزم الوكلاء |

## نشر HA

```bash
cd xtreme-ip-guard
export MERSAL_PG_PASSWORD=...
export MERSAL_SIGNING_SECRET=...
docker compose -f deploy/docker-compose.ha.yml up -d
python3 scripts/init-postgres-schema.py --verify
```

## replica (اختياري)

```bash
export MERSAL_PG_REPLICA_DSN=postgresql://mersal@replica:5432/mersal
```

## تقييم الجاهزية

```bash
curl -s http://127.0.0.1:8090/api/system/enterprise-readiness | jq .tier,.percent,.recommendations
```

هدف المؤسسة الكبرى: `tier` = **production** أو **regulated** مع `ready_for_large_institution: true`.
