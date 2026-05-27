# Extreme IP Guard

نظام أمني متقدم لحماية البنية التحتية من المخاطر المرتبطة بعناوين IP مع نهج **Zero Trust + Adaptive AI Defense**.

هذا المجلد يقدم:

1. نواة تنفيذية عملية (`risk_engine.py`) لاتخاذ قرارات أمنية فورية.
2. اختبارات (`tests/test_risk_engine.py`) لضمان دقة القرارات.
3. تصور معماري احترافي قابل للتوسع (`architecture_ar.md`).

## الهدف

بناء منصة حديثة تتجاوز أنظمة "IP Guard" التقليدية عبر:

- دمج معلومات التهديدات (Threat Intelligence).
- تحليل سلوكي لحظي (Behavior + Velocity + Impossible Travel).
- قرارات ديناميكية متعددة: `allow`, `throttle`, `challenge_mfa`, `block`.
- سياسات متغيرة بحسب حساسية الخدمة وليس سياسة واحدة جامدة.

## تشغيل الاختبارات

```bash
cd /workspace/extreme-ip-guard
python3 -m unittest discover -s tests
```

## مثال استخدام سريع

```python
from risk_engine import ExtremeIPGuardEngine, RiskSignal

engine = ExtremeIPGuardEngine()
signal = RiskSignal(
    ip="203.0.113.45",
    intel_score=82,
    failed_auth_attempts=7,
    requests_per_minute=180,
    geo_velocity_kmph=980,
    impossible_travel=True,
    tor_exit_node=False,
    known_botnet=False,
    device_trust_score=35,
    endpoint_sensitivity=3,
)

assessment = engine.assess(signal)
print(assessment.decision, assessment.score, assessment.reasons)
```

## ملاحظة هندسية

النسخة الحالية هي MVP ذكي وخفيف بدون تبعيات خارجية. في الإنتاج، ينصح بربط هذا المحرك مع:

- API Gateway / WAF
- SIEM/SOAR
- OPA Policy Engine
- STIX/TAXII threat feeds
- eBPF edge sensors
