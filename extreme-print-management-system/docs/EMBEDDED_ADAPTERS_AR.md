# محولات الطابعات المدمجة (Embedded Adapters)

## الهدف

توفير واجهة موحدة لجميع المنصات بينما يبقى تكامل SDK الخاص بكل مصنع في حزمة منفصلة.

## الواجهة الموحدة

الملف `epms/embedded/base.py` يعرّف:

- `authenticate(username, pin, card_id)`
- `list_held_jobs(username)`
- `release_job(job_id, username)`
- `deny_job(job_id, username, reason)`

## المحولات الحالية (SDK مفعّل)

| المصنع | الملف | المنصة | حالة SDK |
| --- | --- | --- | --- |
| Kyocera | `epms/embedded/kyocera.py` | HyPAS | **active** |
| Olivetti | `epms/embedded/olivetti.py` | Olivetti Connect | **active** |
| Xerox | `epms/embedded/xerox.py` | EIP | **active** |
| Lexmark | `epms/embedded/lexmark.py` | eSF | **active** |
| Ricoh | `epms/embedded/ricoh.py` | SmartSDK | **active** |
| Konica Minolta | `epms/embedded/konica.py` | OpenAPI | **active** |
| HP | `epms/embedded/hp.py` | OXP / Workpath | **active** |
| Canon | `epms/embedded/canon.py` | MEAP | **active** |
| غير المدعوم | `epms/embedded/gateway.py` | Gateway | بدون SDK |

### تفعيل / تعطيل SDK

```bash
export EPMS_SDK_ALL=active
export EPMS_SDK_KYOCERA=active
export EPMS_SDK_OLIVETTI=disable   # لتعطيل مصنع واحد
```

قائمة SDK عبر API: `GET /api/sdk/vendors`

## أوامر Printer Controller

```bash
python3 printer_controller.py login --vendor kyocera --username finance --pin 1234 --device-address https://mfd.local/hypas
python3 printer_controller.py login --vendor olivetti --username finance --device-address https://mfd.local/connect
python3 printer_controller.py list-held --vendor xerox --username finance
python3 printer_controller.py release --vendor ricoh --job-id 3 --username finance
python3 printer_controller.py login --vendor konica-minolta --username finance --device-address https://mfd.local/km/openapi
```

## طبقات التكامل الحالية

| الطبقة | المسار | الوصف |
| --- | --- | --- |
| Python HTTP | `epms/embedded/sdk_clients/` | اتصال HTTP حقيقي بالجهاز (Servlet Extreme أو مسارات المصنع) |
| Java Servlet | `sdk/java/extreme-servlet/` | REST موحد على الجهاز |
| Java Bridge | `sdk/java/<vendor>/` | جسر لربط JAR المصنع الرسمي |
| JARs | `sdk/jars/` | ضع ملفات SDK الرسمية هنا ثم ابنِ الـ bridge |

## تفعيل على الطابعة

1. انسخ JAR المصنع إلى `sdk/jars/`.
2. ابنِ مشروع `sdk/java/<vendor>/` بأدوات المصنع.
3. ثبّت Servlet على الجهاز أو وجّه `device_address` إلى بوابة HTTP.
4. شغّل: `python3 printer_controller.py login --vendor ricoh --username USER --device-address https://IP/`

## ملاحظة

بدون JAR المصنع الرسمي، يعمل النظام عبر **HTTP + Extreme Servlet**. مع JAR المصنع، يُستدعى عبر **Java bridge** (`epms/embedded/java_bridge.py`).
