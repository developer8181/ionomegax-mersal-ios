# Extreme Print — جاهز للإنتاج

## التثبيت السريع

```bash
cd extreme-print-management-system
bash scripts/provision_production.sh
set -a && source deploy/production.generated.env && set +a
python3 app_production.py
```

## التحقق

| فحص | الأمر |
|-----|--------|
| الصحة | `curl http://127.0.0.1:8080/api/health` |
| الجاهزية | `curl http://127.0.0.1:8080/api/readiness` |
| قائمة الإنتاج | `curl http://127.0.0.1:8080/api/production/checklist` |
| Servlet الجهاز | `curl http://127.0.0.1:8080/extreme/sdk/v1/health` |

## Docker

```bash
export EPMS_SESSION_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export EPMS_AGENT_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
docker compose -f deploy/docker-compose.production.yml up --build -d
```

## ما يفعّله وضع الإنتاج (`EPMS_PRODUCTION=1`)

- يفرض `EPMS_REQUIRE_AUTH` و `EPMS_AGENT_TOKEN` وسر جلسة قوي
- يعطّل `demo reset` عبر API
- لا يحمّل بيانات demo افتراضياً (ما لم تُفعّل `EPMS_SEED_DEMO=1`)
- رؤوس أمان HTTP إضافية
- **Servlet مدمج** على السيرفر: `/extreme/sdk/v1/*` — لا حاجة لـ Java على الطابعة إذا وجّهت `device_address` إلى السيرفر

## النسخ الاحتياطي

```bash
bash scripts/backup_epms.sh
```

## SDK المصنعين

ضع JAR الرسمية في `sdk/jars/incoming/` ثم:

```bash
python3 scripts/download_vendor_sdks.py --import-incoming
```
