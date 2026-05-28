# Ionomegax Mersal XDR — المنصة الأمنية المؤسسية

## عن المؤسسة والمنتج

**Ionomegax** تقدّم **Mersal XDR Enterprise Platform** — منصة أمن سيبراني موحّدة صُمّمت وطُوّرت بالكامل بواسطة **المهندس محمود راسم بياري**، مهندس أنظمة الحماية في **رام الله، فلسطين**، ومؤسس **شركة Extreme Technology (إكستريم تكنولوجي)**.

جميع الحقوق محفوظة © 2009–2026. العلامة التجارية: **Mersal** · **Mersal OS** · **Mersal Command Center**.

---

## الرؤية

بديل معمارية متكامل لمجموعة أدوات منفصلة (EDR + SIEM + SOAR + إدارة ثغرات + GRC + IDS + تجميع سجلات)، في **منصة واحدة** تعمل على بنيتك التحتية مع واجهة قيادة ثنائية اللغة (العربية / الإنجليزية).

---

## المكوّنات الرئيسية

| الوحدة | الوظيفة |
|--------|---------|
| **Mersal Command Center** | غرفة عمليات عالمية — لوحات حية، RTL/LTR |
| **Mersal XDR** | ارتباط SIEM + EDR + ثغرات + Suricata — عزل تلقائي |
| **Mersal SIEM** | قواعد ارتباط + تنبيهات + MITRE ATT&CK |
| **Mersal EDR** | عمليات، شبكة، YARA، سلامة ملفات |
| **Mersal Log Vault** | تجميع وبحث السجلات |
| **Mersal IDS** | استيراد تنبيهات Suricata |
| **Mersal Neural Cortex** | تعلم سلوكي، تنبؤ، قرار دفاعي |
| **Mersal SOAR** | Playbooks واستجابة آلية |
| **Mersal Compliance** | تقييم NIST-CSF |
| **Mersal Endpoint Agent** | Linux · Windows · macOS · Mersal OS |

---

## لقطات الواجهة (v5.0)

| # | الملف | الشاشة |
|---|--------|--------|
| 1 | `01-overview-ar.png` | نظرة عامة — عربي |
| 2 | `02-readiness-ar.png` | جاهزية الإنتاج |
| 3 | `03-enterprise-ar.png` | المنصة المؤسسية |
| 4 | `04-xdr-ar.png` | Mersal XDR |
| 5 | `05-fabric-ar.png` | المنصة العالمية |
| 6 | `06-ai-cortex-ar.png` | الذكاء الاصطناعي |
| 7 | `07-endpoints-ar.png` | نقاط النهاية والوكلاء |
| 8 | `08-events-ar.png` | الأحداث |
| 9 | `09-policies-ar.png` | السياسات |
| 10 | `10-audit-ar.png` | التدقيق |
| 11 | `11-about-ar.png` | معلومات عن النظام |
| 12–20 | `12-*` … `20-*` | نفس الشاشات — English |

```bash
cd xtreme-ip-guard
./scripts/capture-all-screenshots.sh
python3 app.py
# http://127.0.0.1:8090/console/
```

---

## التشغيل السريع

```bash
make build-all
source mersal-guard.production.env
python3 -m xig
```

---

© Extreme Technology · المهندس محمود راسم بياري · رام الله، فلسطين
