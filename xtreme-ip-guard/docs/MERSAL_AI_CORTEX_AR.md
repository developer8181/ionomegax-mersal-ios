# Mersal Neural Cortex — عقل الأمن التكيفي

**Ionomegax Mersal Guard v1.2** · مدعوم من **Extreme Technology Company**

## نظرة عامة

**Mersal Neural Cortex** طبقة ذكاء دفاعي مدمجة في منصة Mersal Guard. لا تستبدل SOC/SIEM كاملًا، بل تضيف:

| القدرة | الوصف |
|--------|--------|
| **تعلم سلوكي** | خط أساس إحصائي متصل (Welford) لكل endpoint × قناة × تصنيف |
| **كشف شذوذ** | z-score على درجة المخاطرة مقارنة بالسلوك المعتاد |
| **تنبؤ** | EMA + ميل الاتجاه → مخاطر متوقعة واحتمال اختراق |
| **تهديدات** | مطابقة IOC محلية (نطاقات/تصنيفات عالية الخطورة) |
| **قرار** | دمج مع محرك السياسات — تصعيد تلقائي (warn → quarantine → isolate) |

## واجهات API

| Method | Path | الوصف |
|--------|------|--------|
| GET | `/api/ai/dashboard` | لوحة Cortex: رؤى، تنبؤات، سياسات مقترحة |
| GET | `/api/ai/insights` | آخر رؤى AI |
| GET | `/api/ai/predictions` | آخر تنبؤات |
| POST | `/api/ai/train` | `{ "limit": 200 }` — إعادة تدريب الخطوط الأساسية من السجل |

## Command Center

قسم **الذكاء الاصطناعي** في `/console/` يعرض الإحصاءات والرؤى وزر **تدريب من السجل**.

## حدود واقعية

- نماذج **محلية/heuristic** — ليست LLM سحابية.
- IOC افتراضية للتجربة — يجب ربط feeds حقيقية للإنتاج.
- التعلم يحتاج حجم أحداث كافٍ (≥5 عينات للشذوذ الموثوق).

## التطوير القادم

- ربط Sigma/YARA وML ONNX على الوكيل
- تغذية threat intel خارجية (STIX/TAXII)
- تكامل Mersal OS ISO مع Cortex مفعّل افتراضيًا

---

Ionomegax · Mersal Guard · Extreme Technology
