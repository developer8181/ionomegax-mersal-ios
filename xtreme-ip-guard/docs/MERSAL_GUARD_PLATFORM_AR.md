# Ionomegax Mersal Guard — المنصة المتكاملة

## ما تغيّر عن النسخة السابقة؟

النسخة السابقة (**Xtreme IP Guard**) كانت نموذجًا أوليًا: API JSON فقط ووكيل CLI يحاكي الأحداث.

**Mersal Guard** (ضمن علامة **Ionomegax**) أصبحت منصة متكاملة:

| المكوّن | الوصف |
| --- | --- |
| مركز قيادة ميرسال | واجهة ويب عربية/إنجليزية على `/console/` |
| وكيل نقطة النهاية | خدمة `daemon` مع heartbeat دوري |
| مستشعرات أنظمة التشغيل | Linux وWindows وmacOS |
| فرض محلي | حظر قنوات، عزل منطقي، مجلد حجر |
| نشر Linux | systemd + سكربت تثبيت |

## أنظمة التشغيل المدعومة

- **Linux**: قراءة `/proc/mounts`، أجهزة USB عبر `/dev/disk/by-id`، منافذ عبر `ss`
- **Windows**: أقراص قابلة للإزالة وBitLocker/Defender عبر PowerShell
- **macOS**: `diskutil` وFileVault عبر `fdesetup`

## التشغيل

```bash
cd xtreme-ip-guard
python3 app.py
# المتصفح: http://127.0.0.1:8090/console/

python3 agent.py daemon --config config/agent.json
```

## العلامة التجارية

- الشركة: **Ionomegax**
- المنتج: **Mersal Guard**
- مركز القيادة: **Mersal Command Center**
- الوكيل: **Mersal Endpoint Agent**

## الإصدار 1.1 — ما أُضيف

| الميزة | الوصف |
| --- | --- |
| تسجيل المسؤول | `MERSAL_ADMIN_USER` / `MERSAL_ADMIN_PASSWORD` + `/api/auth/login` |
| رمز API للوكلاء | `MERSAL_API_TOKEN` + رأس `X-Mersal-Token` |
| سجل التدقيق | جدول `audit_log` + عرض في المركز |
| إدارة من الواجهة | عزل/استعادة الأجهزة، إضافة سياسات |
| TLS اختياري | `MERSAL_TLS_CERT` و `MERSAL_TLS_KEY` |
| التجهيز | `scripts/provision.sh` يولّد ملف أسرار |
| Docker | `deploy/Dockerfile` و `docker-compose.yml` |
| CI | GitHub Actions `mersal-guard-tests.yml` |

```bash
./scripts/provision.sh mersal-guard.env
source mersal-guard.env
python3 app.py
```

## حدود ما زالت مفتوحة

- LDAP/Entra ID
- وكيل موقّع رسميًا من المتجر
- منع USB عبر MDM/EDR
- قاعدة بيانات HA وSIEM

المنصة مناسبة للنشر الداخلي وإدارة الأسطول من مركز قيادة واحد.
