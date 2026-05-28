# Mersal Enterprise Security Suite v4.0 — بديل مؤسسي متكامل

## الرؤية

**Mersal** ليست أداة تجريبية واحدة، بل **منصة أمن سيبراني موحّدة** تجمع ما يشتريه المؤسس عادةً من عدة منتجات:

| القدرة التقليدية | منتجات السوق | Mersal v4.0 |
|------------------|--------------|-------------|
| EDR | CrowdStrike, Defender | عمليات + شبكة + FIM |
| SIEM | Splunk, QRadar | قواعد ارتباط + تنبيهات SOC |
| SOAR | XSOAR, Cortex | Playbooks + عزل تلقائي |
| إدارة ثغرات | Nessus, Qualys | فحص يومي + CISA KEV |
| تهديدات | Feeds منفصلة | STIX + KEV حكومي |
| GRC / امتثال | منصات منفصلة | NIST-CSF مدمج |
| DLP | Symantec DLP | سياسات + إنفاذ وكيل |
| AI أمني | إضافات سحابية | Neural Cortex محلي |

## الوحدات المدمجة

1. **Mersal SIEM** — `xig/siem/` — 7 قواعد ارتباط، تنبيهات، ربط بالحوادث  
2. **Mersal EDR** — عمليات، اتصالات شبكة، سلامة ملفات حرجة  
3. **Mersal Incident Response** — حوادث، خط زمني، إغلاق SOC  
4. **Mersal Compliance** — تقييم NIST-CSF من بيانات حية  
5. **Mersal Network Security** — سياسات nftables مولّدة  
6. **Mersal Global Security Fabric** — AI، ثغرات، SOAR، مجدول  

## واجهات API

- `GET /api/enterprise/dashboard`
- `GET /api/enterprise/matrix`
- `POST /api/enterprise/cycle`
- `GET /api/siem/alerts`
- `GET /api/incidents`
- `GET /api/compliance`
- `GET /api/edr/detections`
- `GET /api/network/flows`

## البناء والتشغيل

```bash
cd xtreme-ip-guard
make build-all
source mersal-guard.production.env   # بعد make production-env
python3 -m xig
```

## صدق تقني (مهم)

Mersal v4.0 **بديل معمارية متكامل** يعمل على بنيتك التحتية — وليس نسخة مرخّصة من منتجات الطرف الثالث. للبيئات الحرجة جداً (بنوك، دفاع، ملايين الأحداث/ثانية) قد تحتاج توسعات: تجميع سجلات موزّع، تحليل سلوكي عميق على كل ملف، وشهادات امتثال رسمية من جهة ثالثة.

---

© 2009–2026 Extreme Technology — المهندس محمود راسم بياري
