# تنزيل SDK الرسمية — دليل Extreme Print

## لماذا لا يمكن تنزيلها تلقائياً بالكامل؟

حزم SDK الخاصة بـ HP وCanon وRicoh وXerox وKonica Minolta وKyocera وLexmark وOlivetti **ملكية فكرية محمية**. التوزيع يتم فقط عبر:

- بوابات المطورين بعد تسجيل الحساب
- موافقة برنامج الشريك (Partner)
- أحياناً رسوم ترخيص (مثل Canon MEAP)

لا يوجد رابط عام واحد يسمح بتنزيل كل الملفات بدون تسجيل دخول.

## ماذا يفعل المشروع بدلاً من ذلك؟

```bash
cd extreme-print-management-system
python3 scripts/download_vendor_sdks.py --all
```

هذا السكربت:

1. يبني **جسر Extreme Java** (`*-bridge.jar`) من الكود الموجود في `sdk/java/`
2. ينشئ **stub** للتطوير المحلي فقط (ليست SDK رسمية)
3. يستورد أي JAR وضعتها أنت في `sdk/jars/incoming/`
4. يعرض روابط البوابات الرسمية لكل شركة

## خطواتك لكل شركة

| الشركة | البوابة |
|--------|---------|
| HP | https://developers.hp.com/ |
| Canon | https://developers.canon-europe.com/ |
| Ricoh | https://www.ricoh-ap.com/sdk/ |
| Xerox | https://developer.xerox.com/ |
| Konica Minolta | https://www.konicaminolta.com/business/support/developers/index.html |
| Kyocera | بوابة شريك Kyocera Document Solutions |
| Lexmark | https://developer.lexmark.com/ |
| Olivetti | بوابة Olivetti / موزعك المحلي |

بعد التحميل اليدوي: انسخ الملفات إلى `sdk/jars/incoming/` ثم نفّذ `--import-incoming`.

## التحقق

```bash
ls -la sdk/jars/
curl http://127.0.0.1:8080/api/sdk/vendors
```
