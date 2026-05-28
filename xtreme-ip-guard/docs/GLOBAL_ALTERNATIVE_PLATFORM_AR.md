# Extreme Cyber Security — بديل عالمي متكامل

**الإصدار:** 1.1.0 · **السلسلة:** Mersal 8.9 · **النموذج:** استضافة ذاتية سيادية

## الرؤية

منصة **واحدة** على بنيتك التحتية تجمع ما يشتريه المؤسس عادةً من عدة منتجات عالمية:

| فئة السوق | أمثلة | ECS |
|-----------|--------|-----|
| EDR/XDR | CrowdStrike · Defender | وكيل + XDR + عزل |
| SIEM | Splunk · Sentinel | ارتباط + نوافذ + تصدير |
| SOAR | XSOAR · Logic Apps | مسارات + webhooks |
| GRC | ServiceNow GRC | NIST · ISO · SOC2 |
| TI | Feeds سحابية | STIX/TAXII + KEV |
| IdP | Entra/Okta | OIDC · SAML · SCIM |

## تفعيل الوضع المتكامل

```bash
cd xtreme-ip-guard
make enterprise-install
source mersal-guard.env
python3 -m xig
```

**تفعيل بنقرة واحدة (API):**

```bash
curl -X POST -H "X-Mersal-Token: $TOKEN" \
  http://127.0.0.1:8090/api/platform/global-alternative/activate
```

## واجهات API

| Method | Route | الوصف |
|--------|-------|--------|
| GET | `/api/platform/global-alternative` | ملخص الجاهزية كبديل عالمي |
| GET | `/api/platform/global-alternative/matrix` | جدول المقارنة مع العمالقة |
| POST | `/api/platform/global-alternative/activate` | تهيئة + دورة SOC + أدلة |
| GET | `/api/platform/unified` | لوحة موحّدة + `parity_index` |
| POST | `/api/platform/complete-cycle` | دورة كاملة (بدون اشتراط fabric) |

## مؤشر التكافؤ (Parity Index)

يحسب من **21 قدرة** مقابل CrowdStrike / Sentinel / Splunk / Palo Alto:

- **full** — تكافؤ تشغيلي في المنصة الموحّدة  
- **strong** — قوي مع فجوات حجم/سحابة  
- **partial** — متوفر لكن ليس بنفس عمق السحابة  
- **roadmap** — خارج النطاق الحالي (مثل MSSP مُدار)

| المؤشر | المستوى |
|--------|---------|
| ≥ 88 | `global_alternative` |
| ≥ 75 | `enterprise_integrated` |
| ≥ 60 | `pilot_unified` |

## متغيرات الإنتاج الموصى بها

```bash
MERSAL_PRODUCTION=1
MERSAL_ENTERPRISE=1
MERSAL_ENTERPRISE_STRICT=1
MERSAL_POSTGRES_DSN=postgresql://...
MERSAL_TLS_CERT=...
MERSAL_TLS_KEY=...
MERSAL_UPDATE_SIGNING_KEY=...
MERSAL_AUTONOMOUS=1
```

## صدق تقني

ECS **بديل معمارية متكامل** — وليس ترخيصاً لمنتجات الطرف الثالث. للبيئات ذات ملايين الأحداث/ثانية: قم بتوسيع Postgres، تصدير SIEM، واختبار HA. للـ EDR عميق في النواة على كل OS: خطط تكامل kernel إضافي حسب السياسة.

---

© Extreme Technology · المهندس محمود راسم بياري · 2009–2026
