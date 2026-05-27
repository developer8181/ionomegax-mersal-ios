# محولات الطابعات المدمجة (Embedded Adapters)

## الهدف

توفير واجهة موحدة لجميع المنصات بينما يبقى تكامل SDK الخاص بكل مصنع في حزمة منفصلة.

## الواجهة الموحدة

الملف `epms/embedded/base.py` يعرّف:

- `authenticate(username, pin, card_id)`
- `list_held_jobs(username)`
- `release_job(job_id, username)`
- `deny_job(job_id, username, reason)`

## المحولات الحالية

| المصنع | الملف | الحالة |
| --- | --- | --- |
| HP | `epms/embedded/hp.py` | محاكاة OXP + تحكم عبر السيرفر |
| Canon | `epms/embedded/canon.py` | محاكاة MEAP + تحكم عبر السيرفر |
| باقي المصنعين | `HPAdapter(vendor=...)` | بروتوكول موحد حتى بناء SDK |
| غير المدعوم | `epms/embedded/gateway.py` | Release Station / IPP |

## أوامر Printer Controller

```bash
python3 printer_controller.py login --vendor hp --username finance --pin 1234
python3 printer_controller.py list-held --vendor canon --username finance
python3 printer_controller.py release --vendor hp --job-id 3 --username finance
python3 printer_controller.py ipp-jobs --printer-uri ipp://192.0.2.10/ipp/print
```

## دمج SDK حقيقي

1. أنشئ حزمة Java/Native حسب منصة المصنع.
2. استبدل `_simulate_device_ack` و `_oxp_presence_check` بنداءات HTTP/SDK فعلية.
3. احتفظ بنفس توقيع `EmbeddedAdapter` حتى لا يتغير Extreme Server.
