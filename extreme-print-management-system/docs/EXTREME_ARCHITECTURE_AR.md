# معمارية Extreme Print Management System

## الهدف

بناء نظام خاص لإدارة الطباعة شبيه بفكرة PaperCut، لكن باسم وهوية مستقلة:

**Extreme Print Management System**

النظام يجب أن يتكون من برامج منفصلة تعمل معًا:

1. **Extreme Server**: الخادم المركزي ولوحة الإدارة.
2. **Extreme Client Agent**: برنامج العميل على أجهزة المستخدمين.
3. **Extreme Print Provider**: برنامج على خادم الطباعة أو جهاز وسيط.
4. **Extreme Printer Controller**: برنامج/تطبيق مدمج داخل الطابعات المدعومة أو gateway خارجي للطابعات غير المدعومة.
5. **Extreme Site Server**: خيار لاحق للفروع والعمل بدون اتصال مؤقت.

## مخطط عالي المستوى

```text
User Workstation
  - Client Agent
  - Direct Print Monitor
        |
        | HTTPS / Agent API
        v
Extreme Server  <------>  Database
        ^
        | HTTPS / Provider API
        |
Print Server / Gateway
  - Print Provider
  - CUPS / Windows Spooler Adapter
        |
        v
Printer / MFD
  - Embedded Controller when supported
  - Network/SNMP/IPP control when embedded is not supported
```

## 1. Extreme Server

المسؤوليات:

- إدارة المستخدمين والمجموعات.
- إدارة الطابعات والأجهزة.
- تسعير الطباعة.
- الحصص والرصيد وoverdraft.
- المهام: printed, held, denied.
- release queue.
- التقارير.
- audit logs.
- استقبال أحداث agents.
- إصدار قرارات السياسة.

النسخة الحالية في المستودع:

- `app.py`
- `epms/server.py`
- `epms/storage.py`
- `epms/core.py`
- `static/`

## 2. Extreme Client Agent

برنامج يثبت على أجهزة المستخدمين.

المهام:

- عرض رصيد المستخدم.
- عرض تنبيهات عند انخفاض الرصيد.
- إرسال print job metadata عند الطباعة المباشرة.
- طلب اختيار account/project قبل الطباعة.
- إرسال heartbeat للخادم.
- مستقبلًا: تكامل مع Windows/macOS/Linux print APIs.

النسخة الحالية:

- `client_agent.py`

وهي نسخة CLI/Prototype لإثبات بروتوكول العميل.

## 3. Extreme Print Provider

برنامج يثبت على:

- Windows Print Server.
- Linux CUPS server.
- macOS print host.
- جهاز وسيط قريب من الطابعة.

المهام:

- مراقبة spooler أو CUPS queue.
- استخراج metadata.
- إرسال الأحداث للسيرفر.
- تطبيق قرار الخادم.
- حفظ queue محلي مؤقت عند انقطاع الاتصال.

النسخة الحالية مدمجة ضمن مفهوم `printer_controller.py` كبداية، ويجب فصلها لاحقًا عندما يبدأ التكامل الحقيقي مع أنظمة الطباعة.

## 4. Extreme Printer Controller

هذا هو الجزء الخاص بالطابعات نفسها.

### 4.1 الأجهزة التي تدعم Embedded Apps

يتم بناء Adapter لكل منصة:

- HP OXP / Workpath.
- Canon MEAP.
- Ricoh SmartSDK.
- Xerox EIP.
- Sharp OSA.
- Konica Minolta OpenAPI.
- Toshiba e-BRIDGE.
- Kyocera HyPAS.
- Lexmark eSF.
- Epson Open Connect.

كل Adapter مسؤول عن:

- تسجيل الجهاز في السيرفر.
- تسجيل دخول المستخدم.
- عرض held jobs.
- تنفيذ release/deny.
- تسجيل copy/scan/fax عند توفر SDK.

### 4.2 الأجهزة التي لا تدعم Embedded Apps

لا يمكن تحميل تطبيق داخلها. البدائل:

- Print Server Gateway.
- Release Station بجانب الطابعة.
- IPP/SNMP/PJL control حسب الإمكانات.
- تسجيل ومحاسبة فقط بدون شاشة داخلية.

## 5. بروتوكول الاتصال المقترح

كل المكونات تتصل بالسيرفر عبر HTTPS JSON API.

أمثلة رسائل:

### Agent heartbeat

```json
{
  "agent_id": "client-laptop-001",
  "agent_type": "client",
  "hostname": "LAPTOP-001",
  "version": "0.1.0"
}
```

### Print job event

```json
{
  "source": "client-agent",
  "user_id": 1,
  "printer_id": 2,
  "document_name": "invoice.pdf",
  "pages": 10,
  "copies": 1,
  "color": true,
  "duplex": true,
  "account": "Finance"
}
```

### Printer controller metadata

```json
{
  "vendor": "hp",
  "platform": "oxp",
  "model": "FutureSmart MFP",
  "capabilities": ["release", "copy_tracking", "scan_tracking", "card_auth"]
}
```

## 6. سياسة دعم كل أنواع الطابعات

الدعم الكامل لكل الأنواع لا يعني وجود ملف واحد يثبت على كل جهاز. الدعم الصحيح يكون:

- Core API واحد.
- واجهة مستخدم موحدة.
- Vendor adapters متعددة.
- Fallback gateway للطابعات غير القابلة للتضمين.

بهذه الطريقة يمكن للنظام أن يدعم أساطيل مختلطة من الطابعات دون ادعاء تقني غير واقعي.

## 7. ترتيب التنفيذ المقترح

1. تثبيت Server API وقاعدة البيانات.
2. إضافة Agent registration وheartbeat.
3. بناء Client Agent فعلي على Windows/macOS/Linux.
4. بناء CUPS Print Provider.
5. بناء Windows Print Provider.
6. بناء Release Station ويب/تابلت.
7. اختيار أول Vendor Embedded Adapter حسب الطابعات المتوفرة فعليًا.
8. إضافة Site Server للفروع.
9. إضافة PostgreSQL وRBAC وTLS وشهادات agents.

## 8. قرارات تصميم مهمة

- لا توجد تبعيات خارجية في MVP الحالي لتسهيل التشغيل.
- الإنتاج يجب أن ينتقل إلى إطار API أقوى مثل FastAPI أو Django أو Go/Rust service.
- SQLite مناسب للتجربة؛ PostgreSQL مناسب للإنتاج.
- أسماء المستندات قد تكون بيانات حساسة، لذلك يجب توفير خيار anonymization.
- كل عمليات الرصيد يجب أن تسجل كtransactions غير قابلة للتعديل.
