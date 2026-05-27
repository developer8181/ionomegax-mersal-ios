# معمارية Xtreme IP Guard

## الهدف

بناء نظام أمني مؤسسي مستقل باسم:

**Xtreme IP Guard**

النظام مستوحى من فئة IP Guard، لكنه مصمم بعقلية أحدث: Zero Trust، DLP ذكي، Privacy-by-Design، واستجابة آلية للحوادث.

## مخطط عالي المستوى

```text
Endpoint Device
  - Xtreme Endpoint Agent
  - OS-specific Sensors
  - Local Policy Cache
        |
        | HTTPS / mTLS / Event API
        v
Xtreme Command Center  <------>  Data Vault
  - API Gateway                   - Events
  - Policy Brain                  - Policies
  - Admin Console                 - Audit Logs
  - Case Management               - Endpoint Inventory
        |
        | Integrations
        v
SIEM / SOAR / XDR / IAM / AD / LDAP / MDM / Ticketing
```

## 1. Xtreme Command Center

الخادم المركزي ولوحة التحكم.

المسؤوليات:

- إدارة الأجهزة والوكلاء.
- إدارة السياسات.
- استقبال الأحداث.
- حساب المخاطر.
- إصدار قرارات المنع أو العزل.
- إدارة التحقيقات والحالات.
- التقارير والامتثال.
- التكامل مع الأنظمة الخارجية.

في النسخة الحالية داخل المستودع:

- `app.py`
- `xig/server.py`
- `xig/storage.py`

## 2. Xtreme Policy Brain

محرك السياسات هو عقل النظام.

يدمج بين:

- قواعد ثابتة مفهومة وقابلة للتدقيق.
- تصنيف البيانات.
- درجة ثقة الجهاز.
- درجة خطورة الحدث.
- قناة خروج البيانات.
- مؤشرات السلوك غير الطبيعي.

أمثلة قرارات:

| الحالة | القرار |
| --- | --- |
| ملف public إلى موقع معروف | allow |
| ملف internal إلى USB | monitor |
| ملف confidential إلى بريد شخصي | quarantine |
| ملف secret إلى USB | block |
| بيانات credential إلى وجهة مجهولة | isolate endpoint |

في النسخة الحالية:

- `xig/core.py`

## 3. Xtreme Endpoint Agent

الوكيل الذي يثبت على أجهزة المستخدمين.

المهام الإنتاجية المتوقعة:

- إرسال heartbeat.
- تطبيق سياسات محلية عند انقطاع الاتصال.
- مراقبة قنوات تسرب البيانات.
- مراقبة العمليات والتطبيقات.
- منع أو تحذير المستخدم عند الحاجة.
- إرسال telemetry مختصرة وآمنة.
- تنفيذ أوامر العزل أو الاستعادة.

النسخة الحالية:

- `agent.py`

وهي CLI Prototype لإثبات البروتوكول والقرارات فقط.

## 4. Telemetry Model

كل حدث يجب أن يكون normalized حتى يستطيع الخادم اتخاذ قرار موحد.

مثال:

```json
{
  "endpoint_id": "laptop-001",
  "actor": "sara",
  "event_type": "file_copy",
  "channel": "removable_media",
  "resource": "/finance/payroll.xlsx",
  "classification": "secret",
  "destination": "usb:Kingston",
  "severity": 25,
  "behavior_flags": ["after_hours"]
}
```

الحقول المهمة:

- `endpoint_id`: هوية الجهاز.
- `actor`: المستخدم أو الحساب.
- `event_type`: نوع الحدث.
- `channel`: قناة الخروج أو الاستخدام.
- `resource`: المورد المتأثر.
- `classification`: حساسية البيانات.
- `destination`: الوجهة.
- `behavior_flags`: مؤشرات سياقية.

## 5. Policy Actions

الأفعال المدعومة في النواة الحالية:

| Action | المعنى |
| --- | --- |
| `allow` | السماح بدون تصعيد |
| `monitor` | تسجيل ومراقبة |
| `warn` | تحذير المستخدم أو المسؤول |
| `block` | منع العملية |
| `quarantine` | احتجاز الحدث/الملف للمراجعة |
| `isolate_endpoint` | عزل الجهاز منطقيًا داخل النظام |

ملاحظة: العزل الحالي في الـ prototype هو حالة داخل قاعدة البيانات فقط. العزل الحقيقي يحتاج تكاملًا مع EDR/Firewall/MDM أو قدرات OS-level آمنة وموقعة.

## 6. Data Classification

التصنيفات المقترحة:

- `public`
- `internal`
- `confidential`
- `secret`
- `source_code`
- `credential`

يمكن لاحقًا ربطها مع:

- Microsoft Purview.
- Google Workspace labels.
- Git repository metadata.
- OCR/content inspection.
- قواعد regex وfingerprinting.

## 7. Endpoint Trust

كل جهاز له `trust_score` من 0 إلى 100.

عوامل خفض الثقة:

- غياب آخر heartbeat.
- نظام غير محدث.
- Agent tampering.
- تشغيل برامج غير موقعة.
- اتصال من شبكة غير موثوقة.
- سلوك غير طبيعي.

عوامل رفع الثقة:

- تحديثات سليمة.
- تشفير القرص.
- EDR فعال.
- MFA وdevice compliance.
- Agent سليم وموقع.

## 8. أمن المنصة نفسها

في الإنتاج يجب تطبيق:

- mTLS بين الوكلاء والخادم.
- توقيع الوكيل والتحديثات.
- Tamper protection.
- RBAC/ABAC للمسؤولين.
- Audit log غير قابل للتلاعب.
- تشفير البيانات الحساسة.
- فصل صلاحيات التحقيق عن الإدارة العامة.
- Rate limiting وreplay protection.

## 9. التكاملات المستقبلية

| التكامل | الغرض |
| --- | --- |
| AD/LDAP/Entra ID | المستخدمون والمجموعات |
| SIEM | إرسال أحداث عالية القيمة |
| SOAR | playbooks واستجابة آلية |
| EDR/XDR | عزل حقيقي وتحقيق متقدم |
| MDM | حالة الجهاز والامتثال |
| Ticketing | إنشاء حالات تحقيق |
| CASB/SASE | سياسات cloud وweb |

## 10. مراحل التطوير التقنية المقترحة

بدون تقديرات زمنية، يمكن تقسيم التطوير إلى طبقات:

1. **Foundation**: API، قاعدة بيانات، نموذج endpoint/event/policy.
2. **Endpoint Agent Core**: heartbeat، cache، telemetry، update channel.
3. **Policy Enforcement**: تحذير/منع محلي حسب نظام التشغيل.
4. **DLP Sensors**: USB، clipboard، print، browser/cloud، file movement.
5. **Admin Console**: سياسات، أجهزة، أحداث، تحقيقات.
6. **Security Hardening**: mTLS، RBAC، audit، signing.
7. **Integrations**: SIEM/SOAR/EDR/IAM/MDM.
8. **Intelligence Layer**: anomaly detection، risk baselines، noise reduction.

## 11. حدود النسخة الحالية

النسخة الموجودة الآن Prototype فقط:

- لا تتحكم فعليًا في USB أو الشبكة.
- لا تثبت وكيلًا دائمًا.
- لا تحتوي UI رسومية بعد.
- لا تحتوي authentication production-grade.
- هدفها إثبات نموذج السياسات والـ API ومسار telemetry.

## 12. المبدأ الاحترافي

Xtreme IP Guard يجب أن يبنى كمنصة دفاعية مسؤولة:

- حماية المؤسسة بدون انتهاك غير ضروري لخصوصية الموظف.
- قرارات قابلة للتفسير.
- سجلات تحقيق دقيقة.
- أقل صلاحيات ممكنة على الجهاز.
- قدرة على التوسع لآلاف الأجهزة بدون ضجيج أمني.
