# Mersal Guard v3.0 — نسخة تجريبية إنتاجية متكاملة

## ما الذي تغيّر في الإصدار 3.0

| المكوّن | الوصف الحقيقي |
|---------|----------------|
| **وضع الإنتاج** | `MERSAL_PRODUCTION=1` — بدون بيانات وهمية إلا إذا فعّلت `MERSAL_DEMO_UI=1` |
| **Bootstrap** | سياسات مؤسسية + مزامنة CISA KEV + فحص ثغرات + دورة يومية |
| **CISA KEV** | تغذية ثغرات مستغَلة معروفة من حكومة أمريكا |
| **EDR-lite** | مراقبة عمليات Linux + تنبيهات أنماط مشبوهة |
| **nmap** | اكتشاف منافذ عند توفر `nmap` على خادم الإدارة |
| **جاهزية** | `GET /api/system/readiness` — تقرير فحوصات حقيقي |
| **TLS / mTLS** | `scripts/generate-tls.sh` + شهادات وكيل اختيارية |

## تشغيل سريع (تطوير)

```bash
cd xtreme-ip-guard
python3 -m unittest discover -s tests -v
export MERSAL_DB=data/trial.sqlite3
python3 -m xig.server
```

## تثبيت إنتاجي (Linux)

```bash
cd xtreme-ip-guard
sudo bash scripts/install-production.sh
```

## Docker إنتاجي

```bash
cd xtreme-ip-guard/deploy
MERSAL_ADMIN_PASSWORD='your-secret' docker compose up -d --build
```

## واجهة Command Center

- `http://HOST:8090/console/`
- معلومات النظام: `/api/system/about`
- جاهزية الإنتاج: `/api/system/readiness`

## حدود صريحة (صدق تقني)

- ليس بديلاً كاملاً لـ CrowdStrike / Nessus / SOC مؤسسي
- فحص الثغرات: ارتباط منافذ + CVE + KEV + misconfig — وليس مسحاً عميقاً لكل حزمة
- الذكاء الاصطناعي: تحليل محلي/heuristic وليس LLM سحابي

---

© 2009–2026 Extreme Technology — المهندس محمود راسم بياري — رام الله، فلسطين
