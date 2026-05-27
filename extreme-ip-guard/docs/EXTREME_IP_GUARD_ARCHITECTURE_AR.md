# معمارية Extreme IP Guard

## الرؤية

الهدف ليس مجرد "حظر IP" أو "قائمة سماح/منع" تقليدية، بل بناء منصة أمن سيبراني حديثة تتمحور حول:

- **هوية الاتصال** وليس فقط عنوان IP.
- **Zero Trust Egress** لحماية الخروج الشبكي من الأجهزة والخوادم.
- **Adaptive Response** بحيث يقرر النظام: مراقبة، تحدي، حظر، أو عزل.
- **تحليل سلوكي** يدمج السمعة، الجغرافيا، العملية المولدة للاتصال، حجم النقل، والانفجار المفاجئ في الجلسات.
- **تصميم قابل للتطور** إلى eBPF وWFP وNetwork Extension وZTNA وDeception.

## الاسم المعتمد

**Extreme IP Guard**

الاسم يعكس منتجاً احترافياً مستقلاً بقدرات هجومية دفاعية من منظور الحماية الاستباقية، وليس مجرد أداة تسجيل أو فلترة ثابتة.

## الفلسفة الأمنية

النظام في صورته المتقدمة يجب أن يجيب عن الأسئلة التالية لكل اتصال:

1. من هو الأصل الذي أنشأ الاتصال؟
2. أي عملية أو خدمة أنشأت هذا السلوك؟
3. إلى أي IP أو شبكة أو دولة يتجه الاتصال؟
4. هل الوجهة معروفة أو موثوقة أو عالية الخطورة؟
5. هل السلوك طبيعي بالنسبة لهذا الأصل أم يمثل انحرافاً؟
6. ما هو الإجراء الأقل كلفة والأعلى فعالية: سماح، مراقبة، تحدي، حظر، أم عزل؟

## المكونات الأساسية

### 1. Extreme IP Guard Server

الخادم المركزي، وهو العقل الأساسي للمنصة.

مسؤولياته:

- إدارة الأصول `assets`.
- إدارة السياسات `policies`.
- استقبال أحداث الشبكة `events`.
- إنشاء الحوادث `incidents`.
- حساب درجات الخطر.
- إصدار قرارات الاستجابة.
- عرض لوحة التحكم والتقارير.
- تسجيل heartbeat من الوكلاء.

### 2. Extreme IP Sensor

عامل خفيف على endpoint أو gateway يرسل telemetry إلى الخادم.

المهام:

- جمع metadata للاتصالات.
- ربط الاتصال بالعملية أو المستخدم عندما يكون ذلك ممكناً.
- إرسال heartbeat دوري.
- تطبيق وضع المراقبة فقط أو المشاركة في الإنفاذ لاحقاً.

### 3. Extreme Edge Enforcer

وحدة إنفاذ متقدمة، يمكن أن تعمل لاحقاً عبر:

- Linux eBPF
- Windows WFP + ETW
- macOS Network Extension
- Gateway inline proxy / firewall API
- SD-WAN / ZTNA enforcement plane

المهام:

- حظر جلسات محددة.
- عزل أصل داخل microsegment محدود.
- إعادة توجيه اتصال إلى sinkhole.
- تفعيل challenge أو step-up auth عند الحاجة.

### 4. Extreme Site Relay

مكوّن اختياري للفروع والمواقع البعيدة.

المهام:

- Buffering للأحداث عند انقطاع الربط مع المركز.
- Cache للسياسات النشطة.
- استمرارية قرارات الحماية محلياً.
- مزامنة مؤجلة عند عودة الاتصال.

### 5. Extreme Deception Mesh

طبقة مستقبلية متقدمة.

المهام:

- Honeypots موجهة.
- IP sinkholes.
- Decoy services.
- تأكيد سريع للنشاط المعادي ورفع دقة القرار.

## المخطط عالي المستوى

```text
Endpoint / Server / Gateway
  - Extreme IP Sensor
  - Optional Edge Enforcer
          |
          | HTTPS / Signed Agent API
          v
Extreme IP Guard Server  <------>  Database / Threat Intel / Audit
          ^
          |
          | Branch relay sync / policy cache
          |
    Extreme Site Relay

Optional future plane:
  Deception Mesh / Sinkholes / Decoy Services
```

## خط معالجة القرار الأمني

عند وصول حدث جديد، يقوم النظام بالخطوات التالية:

1. التحقق من الأصل والهوية والسياسة النشطة.
2. تطبيع عناوين IP والشبكات.
3. تقييم:
   - سمعة الـ IP.
   - البلد أو المنطقة.
   - الميناء المستهدف.
   - العملية المنشئة للاتصال.
   - حجم البيانات الخارجة.
   - burst في عدد الجلسات.
   - قيمة الأصل وcriticality.
4. حساب درجة خطر موحدة.
5. تحويل الدرجة إلى:
   - `allow`
   - `observe`
   - `challenge`
   - `block`
   - `quarantine`
6. إنشاء incident عندما تكون الاستجابة disruptive أو عند وصول الخطر إلى مستوى متوسط فأعلى حسب السياسة.
7. تخفيض trust score وتحديث posture للأصل تلقائياً.

## لماذا هذا أفضل من الأنظمة التقليدية

الأنظمة التقليدية تعتمد كثيراً على:

- قوائم IP ثابتة.
- قواعد يدوية كثيرة.
- غياب ربط قوي بين الاتصال والأصل والسياق.
- استجابة ثنائية: allow أو block.

أما هذا التصميم فيعتمد على:

- **Scored decisions** بدل القرارات الجامدة.
- **Context-aware enforcement**.
- **Asset posture** و**trust score**.
- القدرة على التوسع إلى **identity-driven network defense**.
- جاهزية طبيعية للدمج مع **SOAR / SIEM / Threat Intel**.

## وضعية الـ MVP الحالية في المستودع

النسخة الحالية داخل `extreme-ip-guard/` توفر:

- قاعدة بيانات SQLite.
- Server API عبر Python stdlib.
- Dashboard ويب بسيطة.
- محرك تقييم مخاطر.
- تسجيل assets/policies/events/incidents/agents.
- CLI sensor لإرسال heartbeat ومحاكاة أحداث.

هذه النسخة مناسبة كبداية تشغيلية لإثبات الفكرة والاتجاه المعماري.

## خارطة التطور القادمة

### المرحلة التالية تقنياً

- شهادات أجهزة mTLS.
- توقيع الرسائل بين الوكلاء والخادم.
- Threat intelligence feeds حقيقية.
- ASN / Geo / JA3 / JA4 / DNS correlation.
- Baselines سلوكية لكل أصل.
- Playbooks تلقائية للعزل الجزئي أو الكامل.

### المرحلة المتقدمة

- eBPF sensors في Linux.
- Windows kernel + ETW correlation.
- Network graph analytics.
- ZTNA-aware segmentation.
- Deception fabric.
- Risk-aware policy compiler.

### المرحلة المستقبلية جداً

- قرارات policy قابلة للتفسير explainable.
- Adaptive trust mesh بين الهويات والأصول.
- Federated detection across sites.
- Autonomous containment مع حواجز أمان تمنع overreaction.

## ملاحظة مهمة

النسخة الحالية **ليست منتج EDR كامل** ولا جدار ناري جاهز للإنتاج، لكنها أساس معماري سليم واحترافي لإنشاء منتج **Extreme IP Guard** بمسار تطور واقعي وقابل للتنفيذ.
