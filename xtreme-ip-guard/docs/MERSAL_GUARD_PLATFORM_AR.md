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

## حدود الإصدار 1.0

ما زال يتطلب تكاملًا إضافيًا للإنتاج الكامل:

- مصادقة مؤسسية (LDAP/Entra) وmTLS
- وكيل موقّع كخدمة نظام على Windows/macOS
- منع USB فعلي عبر سياسات MDM/EDR
- قاعدة بيانات HA وSIEM

الإصدار الحالي مناسب للنشر التجريبي الداخلي، إثبات السياسات، وإدارة أسطول من مركز قيادة واحد.
