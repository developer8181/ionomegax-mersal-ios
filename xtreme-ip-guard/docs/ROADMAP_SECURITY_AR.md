# خارطة طريق الأمن — Mersal Guard & Mersal OS

## v7.0 Enterprise (بنك / حكومة) — منجز

- [x] RBAC مُطبَّق على API · `MERSAL_ENTERPRISE=1`
- [x] عزل `tenant_id` · سجل تدقيق hash chain
- [x] LDAP / libYARA / TLS+mTLS (اختياري عبر `requirements.txt`)

## المرحلة الحالية (v2.0)

- [x] Mersal Guard — وكلاء، سياسات، عزل، تدقيق
- [x] Mersal Neural Cortex — تعلم، شذوذ، تنبؤ، IOC
- [x] **Mersal Global Security Fabric** — فحص ثغرات، STIX، SOAR، posture، مجدول يومي
- [x] Mersal OS ISO تجريبي (Live)
- [x] GitHub Release للتوزيعة

## المرحلة التالية

| الأولوية | المكوّن | الهدف |
|----------|---------|--------|
| P0 | توقيع ISO + تثبيت دائم | إنتاج على القرص |
| P0 | mTLS للوكلاء | مصادقة نقل آمن |
| P1 | Suricata/IDS في Mersal OS | مراقبة شبكة |
| P1 | STIX/TAXII feeds | تهديدات حية |
| P2 | ONNX على الوكيل | تصنيف ملفات محلي |
| P2 | LDAP/SSO للوحة | هوية مؤسسية |
| P3 | SOAR playbooks | أتمتة استجابة |

## مقارنة صادقة

| Fortinet/Palo Alto class | Mersal (اليوم) |
|--------------------------|----------------|
| NGFW + IPS + SD-WAN | Gateway تجريبي |
| EDR + XDR | وكيل + Cortex heuristic |
| Global threat cloud | IOC محلية |
| 24/7 SOC | Command Center ذاتي |

**الهدف:** منصة عربية/عالمية قابلة للتوسع — وليس ادعاءً فوريًا بمنافسة كاملة لعمالقة الصناعة.

---

Extreme Technology Company · Ionomegax
