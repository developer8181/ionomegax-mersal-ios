# معمارية Mersal Holonic Security Fabric

## الفكرة الجديدة

بدل تكديس أدوات منفصلة (جدار + DLP + SIEM + VPN)، **Mersal OS** يبني **نسيج أمني هولوني**:

كل عقدة (مركز، فرع، جهاز) **ذاتية** لكنها **متزامنة** عبر **Policy Mesh**.

```text
┌──────────────── Holon: المركز ────────────────┐
│ Command Center · Update Orbit · SIEM ingest   │
└───────────────────────┬───────────────────────┘
                        │ Policy Mesh (mTLS)
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   Holon: فرع A    Holon: فرع B    Holon: Endpoint
   Gateway UTM      Gateway UTM      Mersal Guard
```

## المكوّنات

| الاسم | الدور |
| --- | --- |
| **Trust Fabric** | درجة ثقة لحظية لكل جهاز/شبكة/مستخدم |
| **Policy Mesh** | نشر سياسة واحدة باتجاهين (مركز ↔ حافة) |
| **Update Orbit** | تحديثات موقّعة: تهديدات، IPS، DLP |
| **Response Cortex** | قرار واحد: عزل في الشبكة + على الجهاز |

## لماذا مختلف عن Fortinet/NethServer؟

- Fortinet: صندوق شبكة قوي، DLP غالبًا منفصل.
- NethServer: خادم خدمات، ليس توزيعة سطح مكتب/حافة موحّدة.
- **Mersal OS**: توزيعة + وكيل + بوابة + قناة تحديث **بسياسة واحدة**.
