# إصدار تجريبي v2.0.0-demo — واجهة مصرية مستقبلية

## ما الجديد

- **واجهة Command Center** بتصميم مصري مستقبلي (ذهب · لapis · أهرامات · هيروغليفية)
- خطوط Cairo + Orbitron
- غرفة عمليات القاهرة · DEFCON · ساعة حية
- بيانات عرض غنية للوحة (ثغرات، SOAR، AI، أحداث)

## التشغيل

```bash
cd xtreme-ip-guard
python3 scripts/seed_demo_ui.py
export MERSAL_DB=data/demo-ui.sqlite3
python3 -m xig.server
# http://127.0.0.1:8090/console/
```

## اللقطات

مجلد `docs/screenshots/` — مرفوعة مع إصدار GitHub `v2.0.0-demo-ui`.
