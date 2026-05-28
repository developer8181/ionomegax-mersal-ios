# بناء متكامل — Mersal Guard v3.1

## أوامر البناء

| الأمر | الوظيفة |
|-------|---------|
| `make test` | جميع اختبارات الوحدة (39+) |
| `make verify` | اختبارات + تحقق HTTP حي |
| `make build-all` | اختبارات + verify + Docker (إن وُجد) |
| `make production-env` | إنشاء ملف بيئة إنتاج |
| `sudo bash scripts/install-production.sh` | تثبيت Linux كامل مع TLS |

## مكونات الإصدار المتكامل

1. **Command Center** — واجهة عربية/إنجليزية + لوحة جاهزية
2. **Endpoint Agent** — heartbeat، حساسات، EDR-lite، إنفاذ محلي
3. **Fabric** — ثغرات، KEV، SOAR، مجدول يومي
4. **Neural Cortex** — تعلم، تنبؤ، قرار
5. **Mersal OS** — ISO + `mersal-install-to-disk.sh`

## التحقق بعد البناء

```bash
curl -s http://127.0.0.1:8090/api/system/build | python3 -m json.tool
curl -s http://127.0.0.1:8090/api/system/readiness | python3 -m json.tool
```

## Mersal OS

```bash
cd mersal-os
make iso   # أو build-iso-docker.sh
```

يتضمن المنصة من `xtreme-ip-guard/` عبر `build/sync-includes.sh`.

---

© 2009–2026 Extreme Technology — المهندس محمود راسم بياري
