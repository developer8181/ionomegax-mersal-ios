# Mersal Global Security Fabric v2.0

**Ionomegax** · مدعوم من **Extreme Technology Company**

## المنصة الموحدة

| الطبقة | الوظيفة |
|--------|---------|
| **Mersal Neural Cortex** | تعلم، شذوذ، تنبؤ، قرار AI |
| **Vulnerability Management** | فحص يومي، CVE، misconfig |
| **Threat Intelligence** | STIX محلي + مزامنة + IOC |
| **SOAR** | playbooks تلقائية (عزل، سياسات) |
| **Security Posture** | درجة أمن 0–100 (A–F) |
| **Daily Scheduler** | دورة يومية آلية عند تشغيل الخادم |

## الدورة اليومية (تلقائية)

1. مزامنة تهديدات (builtin + STIX global)  
2. فحص ثغرات لكل endpoints  
3. تدريب Cortex من السجل  
4. حساب درجة الأمن  

متغير البيئة: `MERSAL_DAILY_INTERVAL_SECONDS` (افتراضي 86400 = 24 ساعة).

## API

| Method | Path |
|--------|------|
| GET | `/api/fabric/dashboard` |
| POST | `/api/fabric/daily` |
| POST | `/api/vuln/scan` |
| GET | `/api/vuln/findings` |
| POST | `/api/threat/sync` |
| GET | `/api/soar/runs` |
| GET | `/api/posture` |

## الوكيل

يرسل `vuln_probe` مع كل heartbeat: منافذ مفتوحة، تشفير القرص، OS.

## تشغيل

```bash
cd xtreme-ip-guard
python3 -m xig.server
# Command Center → المنصة العالمية → دورة يومية / فحص ثغرات
```

## حدود

- فحص الثغرات: ارتباط CVE + منافذ (ليس Nessus كاملًا).  
- STIX: parser مبسّط؛ للإنتاج استخدم feeds رسمية.  
- SOAR: playbooks أساسية؛ توسّع حسب الحاجة.

---

الهدف: **أقوى إطار عربي/عالمي قابل للنمو** — مع صدق تقني حول الفجوة أمام عمالقة الصناعة.
