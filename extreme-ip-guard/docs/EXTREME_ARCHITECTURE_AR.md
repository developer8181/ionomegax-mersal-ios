# المعماريّة المتقدّمة لـ Extreme IP Guard (XIG)

> هذه الوثيقة تصف **التصميم الهندسي الكامل** لنظام Extreme IP Guard: حلٌّ من الجيل القادم لحماية النقاط الطرفيّة ومنع تسرّب البيانات، يأخذ كلّ ما يقدّمه IP Guard ويتجاوزه نحو **Zero Trust + XDR + UEBA + SOAR-lite + PQC-ready**.

النظام مصمَّم ليُبنى تدريجيًا. النموذج المرجعي الموجود في هذا المجلّد (Python stdlib) يثبت صحّة المعماريّة ويُشكّل خطّاً أساسيًا قابلًا للإنتاج لاحقًا (بـ Rust/Go للعميل و FastAPI أو Actix للخادم).

---

## 1. المبادئ التصميميّة العشرة

1. **Assume Breach** — لا نثق بأيّ عميل أو مستخدم افتراضيًا.
2. **Defense in Depth** — كلّ سياسة تُطبَّق على ثلاث طبقات: العميل، البوّابة، الخادم.
3. **Signed Everything** — السياسات والأوامر والترقيعات موقّعة رقميًا (Ed25519).
4. **Tamper-Evident Audit** — كلّ حدث يدخل سلسلة هاش (Hash chain) لا يمكن العبث بها.
5. **Privacy by Design** — تشفير حقول حسّاسة في القاعدة، مع فصل المفاتيح.
6. **Observability First** — كلّ مكوّن يُصدر metrics + traces + structured logs.
7. **API-First** — كلّ ما يمكن فعله من الواجهة يمكن فعله من API موثّق.
8. **Pluggable Detection** — قواعد، سلوك، ذكاء تهديد، YARA، Sigma — كلّها قابلة للتفعيل.
9. **Graceful Degradation** — العميل يعمل بـ Cached policy إن انقطع الخادم.
10. **Future-Proof Crypto** — تصميم crypto-agile جاهز لاستبدال الخوارزميّات.

---

## 2. مخطّط معماري عام

```text
                       ┌─────────────────────────────┐
                       │      SOC / Admin Console    │
                       │  (Web Dashboard, Hunt UI)   │
                       └──────────────┬──────────────┘
                                      │ HTTPS + WebSocket
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       XIG Control Plane                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐   │
│  │   API GW   │  │  Policy    │  │ Detection  │  │ Response /   │   │
│  │  (REST+WS) │  │  Engine    │  │  Engine    │  │  SOAR-lite   │   │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └──────┬───────┘   │
│        │               │               │                 │           │
│        ▼               ▼               ▼                 ▼           │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐   │
│  │ Identity / │  │  Signed    │  │   UEBA     │  │  Playbooks   │   │
│  │  Enrolment │  │  Bundles   │  │  Baselines │  │  Library     │   │
│  └────────────┘  └────────────┘  └────────────┘  └──────────────┘   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ Event Bus (queue / outbox)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Data Plane                                   │
│  Relational store (Users/Assets/Policies) + Append-only Event Log   │
│  + Search Index (Hunt) + Cold Object Store (forensic artefacts)     │
└─────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ mTLS + signed payloads
                              │
                  ┌───────────┴───────────┐
                  │  XIG Endpoint Agents   │
                  │  (Windows/macOS/Linux) │
                  │                        │
                  │  - Device Sensor       │
                  │  - Process Sensor      │
                  │  - Network Sensor      │
                  │  - DLP Scanner         │
                  │  - Screen Recorder     │
                  │  - Response Executor   │
                  └────────────────────────┘
```

---

## 3. مكوّنات النظام بالتفصيل

### 3.1 خادم التحكّم (Control Plane)

- **API Gateway**: REST + WebSocket. يدعم تسجيل العملاء، استلام الأحداث، توزيع السياسات، أوامر الاستجابة.
- **Policy Engine**: تقيّم السياسات وتُنتج **حزم سياسة موقّعة** (Signed Policy Bundles) خاصّة بكلّ عميل.
- **Detection Engine**: ثلاث طبقات:
  - **Rules** (تطابق دقيق / regex / hash).
  - **UEBA Baseline** (نموذج إحصائي بسيط لكلّ مستخدم/جهاز).
  - **Threat Intel** (IOC feeds: hashes, domains, IPs).
- **SOAR-lite**: مكتبة Playbooks (YAML) تربط نوع التنبيه بإجراء (isolate / kill / block_usb / wipe_clipboard / require_mfa).
- **Identity & Enrolment**: إصدار شهادات/توكنز قصيرة العمر، تدوير تلقائيّ، إلغاء فوريّ (revocation).

### 3.2 طبقة البيانات (Data Plane)

| النوع | ما يخزَّن | ملاحظات |
| --- | --- | --- |
| Relational (SQLite/Postgres) | Users, Assets, Policies, Agents, Cases | معاملاتي. |
| Append-only Event Ledger | Telemetry events, alerts, decisions | Hash-chained per shard. |
| Search Index (Tantivy/OpenSearch) | Hunt queries, full-text on logs | اختياري لكنه مهم للـ SOC. |
| Object Store (S3-compatible) | Forensic artefacts, screen recordings, file copies | يفعّل عند الحاجة. |

### 3.3 العميل (Endpoint Agent)

العميل **متعدّد المنصّات** (Win/macOS/Linux). يتألّف من:

- **Core Service** (daemon): يفتح قناة WSS مع الخادم، يستقبل السياسات الموقَّعة، ينفّذ.
- **Sensors**:
  - **Device Sensor**: مراقبة USB/Bluetooth/Camera/Printer عبر `udev` على لينكس، `IOKit` على ماك، `SetupAPI`/`Cfg32` على ويندوز.
  - **Process Sensor**: قراءة `auditd`/eBPF/ETW (لا kernel driver خاص).
  - **Network Sensor**: TCP/UDP flows، DNS، اختياريًا فحص SNI/JA3.
  - **DLP Scanner**: مسح ملفات على القراءة/الكتابة، تطبيق قواعد regex + entropy + EDM (Exact Data Match).
  - **Screen Recorder**: تسجيل عند triggers محدّدة فقط، احترامًا للخصوصيّة.
  - **Response Executor**: ينفّذ Playbook الصادر من الخادم (kill PID, eject USB, isolate NIC).
- **Cache Layer**: نسخة محليّة من السياسة موقَّعة، تعمل offline حتى انتهاء صلاحيتها.

> **ملاحظة**: في النموذج المرجعي ضمن هذا المستودع، العميل مكتوبٌ بـ Python للإثبات فقط. للإنتاج، التوصية: **Rust** (للأداء والذاكرة الآمنة) أو **Go** (لسرعة التطوير).

---

## 4. بروتوكول الاتصال

كلّ شيء فوق **HTTPS/WSS** قياسي، مع توقيع تطبيقيّ إضافي.

### 4.1 التسجيل (Enrolment)

```text
Endpoint                             XIG Server
   │   POST /api/agents/enrol         │
   │   { agent_id, hw_fp, os, pubkey, │
   │     enrol_token (one-time) }     │
   │ ───────────────────────────────▶ │
   │                                  │  verify token, sign cert
   │   200 OK { agent_cert,           │
   │            server_pubkey,        │
   │            policy_bundle,        │
   │            session_key_wrap }    │
   │ ◀─────────────────────────────── │
```

- `enrol_token`: لمرّة واحدة، صلاحيّة قصيرة، يُولَّد من الـ Console.
- `hw_fp`: بصمة عتاديّة (CPU UUID + motherboard serial + first MAC) لربط الشهادة بالجهاز.
- `session_key_wrap`: مفتاح جلسة مغلّف بـ **hybrid X25519 + Kyber-768** عند توفّر libsodium-pq، يتراجع تلقائيًا إلى X25519 فقط إن لم تتوفر.

### 4.2 توزيع السياسات (Pull + Push)

- **Pull**: العميل يطلب `GET /api/policies/bundle?version=N` كلّ X دقيقة.
- **Push**: الخادم يدفع `policy.updated` عبر WebSocket لتفعيل فوريّ.
- كلّ Bundle موقَّع بـ Ed25519 ويحوي:
  - قواعد الجهاز/التطبيق/الشبكة/DLP.
  - قائمة IOC (هاش، نطاق، IP).
  - Playbooks المعتمدة.
  - timestamp + version + signature.

### 4.3 رفع الأحداث (Telemetry)

- العميل يجمّع الأحداث في دفعات (Batches) ويرسلها `POST /api/events` كلّ X ثانية أو عند تجاوز حجم معيّن.
- كلّ دفعة موقَّعة بمفتاح العميل (Ed25519).
- الخادم يضيف الأحداث إلى **سلسلة هاش** ويُرجع `merkle_root` كإيصال (Receipt).

### 4.4 الاستجابة (Response)

- الخادم يضع أمرًا في طابور العميل: `command_id`, `playbook`, `params`, `signature`, `ttl`.
- العميل يلتقطه عبر long-poll أو WS، يتحقّق من التوقيع، ينفّذ، يُعيد نتيجة موقّعة.

---

## 5. نموذج البيانات

### 5.1 الكيانات الأساسيّة

```text
User(id, username, display_name, dept, risk_score, roles)
Asset(id, hostname, os, hw_fp, owner_user_id, criticality, tags)
Agent(id, asset_id, version, status, last_seen, pubkey, cert_serial)
Policy(id, name, scope, version, signature, body_json)
Rule(id, policy_id, kind, expression, severity, mitre_ttp)
Event(id, agent_id, ts, kind, subject, data_json, risk_delta, chain_hash, prev_hash)
Alert(id, ts, severity, title, mitre_ttp, status, agent_id, user_id, event_refs)
Case(id, title, status, owner, created_at, alerts[], notes[])
Playbook(id, name, trigger, actions[], approval_required)
Command(id, agent_id, playbook_id, payload, signature, status, result)
AuditEntry(id, ts, actor, action, target, data, chain_hash, prev_hash)
```

### 5.2 سلسلة الهاش لمنع العبث

كلّ سجل في `events` و `audit` يحوي:

```text
chain_hash = SHA-256( prev_hash || canonical_json(record_without_hashes) )
```

في كلّ ساعة، يُنشَر **Merkle root** لآخر شريحة (Shard) إلى مكان عام (مثلًا داخل بريد إداري + تخزين منفصل) لتأكيد عدم العبث.

---

## 6. محرّك الكشف الهجين

### 6.1 طبقة القواعد (Rules)

كلّ قاعدة JSON/YAML كالتالي:

```yaml
id: R-USB-001
name: "Mass copy to USB"
when:
  kind: file.write
  destination.startswith: "/media/usb"
  pages_or_bytes.gt: 50_000_000  # 50 MB
severity: high
mitre: T1052.001
response: isolate_usb
```

### 6.2 طبقة السلوك (UEBA)

لكلّ مستخدم/جهاز نحفظ:

- متوسّط حجم النقل اليومي.
- ساعات النشاط المعتادة.
- التطبيقات الأكثر تشغيلًا.
- الوجهات الشبكيّة المعتادة.

عند أيّ حدث:

```text
z_score = (value - mean) / stddev
if z_score > 3.0:
    raise behavior_anomaly with risk_delta = clamp(z_score * 5, 0, 50)
```

النموذج المرجعي في `xig/detection.py` يستخدم EWMA بسيطة كي يبقى بدون تبعيّات.

### 6.3 طبقة ذكاء التهديد (TI)

قائمة IOC مدعومة:

- `sha256` لملفات ضارّة.
- `domain` لخوادم C2.
- `ipv4/ipv6` لعناوين ضارّة.
- `ja3` لبصمات TLS.
- `username@email` للتصيّد.

التحديث عبر STIX/TAXII أو CSV. أيّ تطابق ينتج تنبيهًا بـ severity ≥ high.

### 6.4 درجة المخاطر (Risk Score)

لكل مستخدم/أصل، تُعدَّل الدرجة بصيغة EWMA:

```text
risk = (1-α) * risk + α * event_risk_delta,  α = 0.2
```

ودرجة فوق عتبة معيّنة تُفعّل Playbook تلقائيًا (مثلاً MFA إضافي أو عزل مؤقّت).

---

## 7. SOAR-lite: الاستجابة المؤتمتة

أمثلة Playbooks المضمَّنة في النموذج المرجعي:

| Playbook | Trigger | Actions |
| --- | --- | --- |
| `pb-usb-mass-copy` | rule R-USB-001 أو سلوك مماثل | block_usb + alert_admin + screenshot |
| `pb-malware-hash-match` | TI match على sha256 | kill_process + quarantine_file + isolate_host |
| `pb-impossible-travel` | تسجيل دخول من بلدين خلال دقائق | require_mfa + open_case |
| `pb-clipboard-secret` | نسخ بطاقة ائتمان/مفتاح | wipe_clipboard + warn_user + log |
| `pb-after-hours-exfil` | رفع بيانات > 100MB بعد الساعة 9م | hold_traffic + escalate |

كلّ Playbook قابل لطلب موافقة بشريّة (`approval_required: true`) أو التنفيذ التلقائي.

---

## 8. الأمن والخصوصيّة

- **Zero Trust**: لا توجد شبكة موثوقة. كلّ طلب يحوي mTLS + توقيع.
- **PoLP**: أدوار محدّدة (viewer / analyst / admin / auditor / break-glass).
- **Privacy guards**: لقطات الشاشة معطّلة افتراضيًا، تفعّل فقط على trigger موثَّق، مع علامة مائيّة على من شاهد الصورة.
- **Right-to-Audit**: AuditEntry سلسلة هاش، حتّى الإداريّون يُسجَّل عليهم.
- **Crypto agility**: واجهة `xig.crypto` تستعمل خوارزمية اسميّة (`alg_id`) في كلّ شيء موقَّع/مشفَّر، فيمكن تدويرها لاحقًا.
- **Secret zeroization**: مفاتيح الجلسات تُمسح من الذاكرة بمجرّد انتهاء الاستخدام (في الإصدار Rust).

---

## 9. التهديدات النموذجيّة (Threat Model مختصر)

أُجريت دراسة STRIDE مختصرة:

| التهديد | الإجراء المضاد |
| --- | --- |
| Spoofing (عميل مزوّر) | mTLS + hw_fp + توقيع كل دفعة. |
| Tampering (تعديل سياسة) | Bundle موقَّع Ed25519 يتحقّق منه العميل قبل التطبيق. |
| Repudiation (إنكار) | AuditEntry بسلسلة هاش + Merkle root منشور. |
| Information Disclosure | تشفير على disk + الفصل بين السياسات والأحداث. |
| Denial of Service | rate limiting + batching + درجة مخاطر للعملاء المشبوهين. |
| Elevation of Privilege | RBAC + break-glass مُسجَّل علنيًا. |

---

## 10. خريطة الطريق

| المرحلة | المخرج |
| --- | --- |
| **M1** (هذا النموذج) | Server + Agent stub + Dashboard + Detection rules + Audit chain + Tests. |
| **M2** | Rust agent حقيقي على لينكس بـ eBPF + توقيع Ed25519 كامل. |
| **M3** | Postgres + Redis + Search index. تشغيل في k8s. |
| **M4** | تكامل STIX/TAXII + Sigma + YARA + EDR vendor (CrowdStrike/Defender) عبر API. |
| **M5** | تكامل CASB لفحص حركة SaaS + ZTNA broker. |
| **M6** | Hybrid PQC (Kyber+X25519) تشغيل افتراضي. |
| **M7** | SOC AI Copilot: تلخيص الحوادث، اقتراح Playbook، توليد تقارير. |

---

## 11. الفروق الجوهريّة عن IP Guard

| المحور | IP Guard التقليدي | Extreme IP Guard |
| --- | --- | --- |
| النموذج الأمني | Perimeter | Zero Trust |
| العميل | Kernel filters (Win-أولي) | User-mode + eBPF/ETW عبر كل OS |
| البروتوكول | خاص | HTTPS/WSS مفتوح موثّق |
| التوزيع | Push فقط | Pull + Push + Signed bundles |
| الكشف | Rules + قوائم | Rules + UEBA + TI + Risk score |
| الربط | محدود | MITRE ATT&CK على كلّ تنبيه |
| الاستجابة | يدويّ | Playbooks (SOAR-lite) تلقائيّ/شبه تلقائيّ |
| سجل التدقيق | عادي | Hash-chained + Merkle |
| التشفير | AES فقط | AES-GCM + Ed25519 + Hybrid PQC جاهز |
| النشر | On-prem | On-prem + Cloud + Hybrid |
| التكامل | محدود | API-first + Sigma/YARA/STIX/TAXII |
| الخصوصيّة | لقطات شاشة دوريّة | Trigger-based فقط + watermark + audit |
| التوسعة | عمودي | أفقي (stateless + queue) |

---

## 12. ما الذي يُمثّله النموذج المرجعي في هذا المستودع؟

النموذج المرجعي (Python stdlib فقط، بدون أيّ تبعيّة خارجيّة) يُمثّل:

- نواة `xig/` كاملة: core, storage, detection, crypto, policies, audit, agents, server.
- عميل واحد بسيط (`agent/endpoint_agent.py`) يُحاكي ستّ مستشعرات.
- لوحة قيادة ويب SOC-style (`static/`).
- باقة اختبارات (`tests/`).

هو **ليس** بديلاً جاهزًا للإنتاج، لكنه إثبات معماري كامل قابل للاستبدال **مكوّنًا مكوّنًا** بمكوّن إنتاجي حقيقي (Postgres بدل SQLite، Rust agent بدل Python، إلخ) دون كسر التصميم.
