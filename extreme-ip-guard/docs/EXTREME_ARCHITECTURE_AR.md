# معمارية Extreme IP Guard

## الرؤية

**Extreme IP Guard (EIG)** — منصة أمن داخلية ذاتية الاستضافة، تجمع DLP ومراقبة الشبكة وأمان نقاط النهاية وZero Trust وتحليل السلوك (UEBA)، مع تدقيق غير قابل للتلاعب.

## المكونات

```text
                    ┌─────────────────────────────────────┐
                    │         Extreme Server (SOC)         │
                    │  Policy Engine · Risk · Incidents    │
                    │  Audit Chain · SQLite · REST API     │
                    └──────────────┬──────────────────────┘
                                   │ HTTPS / JSON
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         v                         v                         v
  Endpoint Agent            Network Sensor              Site Gateway
  (client_agent.py)         (network_sensor.py)         (مخطط)
  DLP · USB · App · Web     Lateral · Port policy       فرع · cache سياسات
         │                         │
         └──────────── eBPF / OS hooks (إنتاج) ─────────┘
```

### 1. Extreme Server

- API: `/api/events`, `/api/agents/heartbeat`, `/api/zero-trust/check`
- محرك سياسات مع ربط **MITRE ATT&CK**
- **UEBA** خفيف (`eig/anomaly.py`)
- **Risk score** مركب لكل endpoint
- **Audit chain** SHA-256 متسلسل
- لوحة SOC: `static/` (عربي RTL)

الملفات: `app.py`, `eig/server.py`, `eig/storage.py`, `eig/core.py`

### 2. Extreme Endpoint Agent

- Heartbeat + device posture
- إرسال أحداث DLP / USB / تطبيقات
- مستقبلًا: تكامل Win/macOS/Linux، حظر USB عبر driver policy

الملف: `client_agent.py`

### 3. Extreme Network Sensor

- اكتشاف اتصال غير مصرح، port scan، عزل الشريحة guest
- مستقبلًا: NetFlow/IPFIX، NAC integration

الملف: `network_sensor.py`

### 4. Extreme DLP Probe (مخطط)

- فحص عميق للبريد وملفات المشاركات
- تصنيف محتوى (ML) — مرحلة لاحقة

### 5. Extreme Site Gateway (مخطط)

- تخزين سياسات للفروع
- مزامنة أحداث عند عودة الاتصال

## محرك القرار الأمني

```text
حدث خام → تصنيف (category) → مطابقة سياسة (regex + MITRE)
         → UEBA anomaly score
         → composite risk
         → إجراء: allow | warn | block | quarantine | isolate
         → حادثة SOC + سجل audit chain
```

## Zero Trust

كل جلسة تمر بفحص:

- تشفير القرص، AV، التصحيحات، صحة الوكيل
- MFA للمستخدم
- قطاع الشبكة (corporate vs guest/dmz)

API: `POST /api/zero-trust/check`

## التقنيات «من المستقبل» (خطافات في النموذج)

| التقنية | التطبيق في EIG |
| --- | --- |
| Zero Trust | فحص جلسة مستمر |
| UEBA | AnomalyEngine بدون ML ثقيلة |
| Immutable audit | `audit_chain.py` |
| Post-quantum | `policies.example.json` → hybrid TLS |
| eBPF | تصنيف أحداث جاهز للربط |
| SOAR | webhook في config (تنفيذ لاحق) |
| MITRE | كل قاعدة لها `mitre_technique` |

## التشغيل

```bash
cd extreme-ip-guard
python3 app.py
# http://127.0.0.1:8090

python3 client_agent.py --action heartbeat
python3 network_sensor.py --scenario port-scan
python3 -m unittest discover -s tests
```

## خارطة طريق الإنتاج

1. mTLS بين الوكلاء والخادم
2. تكامل Active Directory / OIDC
3. نماذج ML للـ DLP (على الخادم)
4. وكيل eBPF لـ Linux
5. موصل SIEM (CEF/JSON)
6. Site Gateway للفروع
