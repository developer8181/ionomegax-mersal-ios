# معمارية Extreme IP Guard

## الهدف

بناء نظام **Extreme IP Guard** — منصة تحكم متقدمة في الوصول الشبكي (NAC) تتجاوز أنظمة IP Guard التقليدية بتقنيات Zero Trust وكشف التهديدات السلوكي والتقسيم الدقيق للشبكة (Micro-Segmentation).

## مقارنة مع IP Guard التقليدي

| القدرة | IP Guard التقليدي | Extreme IP Guard |
| --- | --- | --- |
| ربط MAC/IP | ✓ | ✓ + Device Identity + Posture |
| قائمة بيضاء/سوداء | ✓ | ✓ + Threat Intelligence + TTL |
| NAC / 802.1X | ✓ | ✓ + SDP + Zero Trust |
| DHCP Integration | ✓ | ✓ + DHCP Snooping (production) |
| USB Control | ✓ | ✓ via Endpoint Agent |
| كشف التهديدات | محدود | Behavioral AI + Auto-Response |
| Micro-Segmentation | ✗ | ✓ Zones (secure/dmz/guest/iot) |
| Audit | سجلات | Hash-chained immutable audit |
| Enforcement | Firewall rules | nftables / eBPF-XDP / WFP / Envoy |
| Policy Distribution | ملفات محلية | Signed policy bundles |

## المكونات

```text
                    ┌─────────────────────────┐
                    │   Extreme IP Guard      │
                    │   Server (Central)      │
                    │   - Policy Engine       │
                    │   - Threat Intelligence │
                    │   - Audit Chain         │
                    │   - Admin Dashboard     │
                    └───────────┬─────────────┘
                                │ HTTPS JSON API
            ┌───────────────────┼───────────────────┐
            │                   │                   │
    ┌───────▼───────┐  ┌───────▼───────┐  ┌───────▼───────┐
    │ Edge Enforcer │  │ Endpoint Agent│  │ Flow Sensor   │
    │ nftables/eBPF │  │ Posture/USB   │  │ NetFlow/Zeek  │
    └───────┬───────┘  └───────┬───────┘  └───────┬───────┘
            │                   │                   │
    ┌───────▼───────────────────▼───────────────────▼───────┐
    │              Corporate Network Zones                   │
    │  secure │ dmz │ guest (quarantine) │ iot (isolated)   │
    └───────────────────────────────────────────────────────┘
```

## 1. Extreme IP Guard Server

المسؤوليات:

- محرك سياسات Zero Trust (CIDR, port, protocol, zone, time, trust score)
- سجل الأجهزة والموافقة عليها
- قوائم الحظر (يدوي + threat intel + auto-response)
- كشف التهديدات السلوكي (port scan, brute force)
- سلسلة تدقيق hash-chained
- توزيع policy bundles موقّعة
- لوحة إدارة عربية/إنجليزية

الملفات:

- `app.py`, `eipg/server.py`, `eipg/storage.py`, `eipg/core.py`, `eipg/threat.py`

## 2. Extreme Edge Enforcer

برنامج على بوابة الشبكة أو Firewall.

المهام:

- سحب policy bundle موقّع
- تطبيق قواعد nftables / eBPF-XDP / iptables
- تقييم traffic flows في الوقت الفعلي
- Rate limiting و DDoS mitigation

الملف: `edge_agent.py`

## 3. Extreme Endpoint Agent

برنامج على أجهزة المستخدمين.

المهام:

- تسجيل هوية الجهاز (MAC, IP, hostname)
- تقرير Posture (تشفير القرص, AV, TPM attestation)
- USB/Bluetooth peripheral control
- Zero Trust continuous verification

الملف: `endpoint_agent.py`

## 4. Extreme Flow Sensor

جامع تيليميتري الشبكة.

المهام:

- استقبال NetFlow/IPFIX, Zeek, Suricata
- كشف port scan و brute force
- إرسال events لمحرك التهديدات

الملف: `flow_sensor.py`

## 5. Extreme Site Server (مستقبلي)

- Cache محلي للسياسات في الفروع
- Sync عند عودة الاتصال
- Fail-closed / fail-open configurable

## محرك السياسات

```text
Request → Block List Check → Device Trust → Threat Score → Policy Rules → Decision
                ↓ fail              ↓ low trust        ↓ high threat
              DENY                  skip rule          AUTO-DENY
```

الأولويات:

1. Block critical threats (priority 1000)
2. Zone-specific rules (secure, guest, iot)
3. Service rules (HTTPS, DNS)
4. Default deny (Zero Trust)

## التقنيات المستقبلية

| التقنية | الغرض |
| --- | --- |
| eBPF/XDP | Inline drop at line rate |
| Software-Defined Perimeter | Dark network, SPA |
| Post-Quantum Crypto | Agent authentication (Kyber/Dilithium) |
| Hardware Attestation | TPM/Secure Enclave device trust |
| ML Anomaly Detection | Baseline behavioral models |
| SIEM Integration | Splunk, Elastic, Wazuh export |

## API الرئيسية

| Method | Endpoint | الغرض |
| --- | --- | --- |
| GET | `/api/dashboard` | إحصائيات |
| GET | `/api/policies` | السياسات |
| POST | `/api/evaluate` | تقييم وصول |
| POST | `/api/devices` | تسجيل جهاز |
| POST | `/api/blocks` | حظر IP/CIDR |
| POST | `/api/flows` | تيليميتري + كشف |
| GET | `/api/policy-bundle` | حزمة سياسات موقّعة |
| POST | `/api/agents/heartbeat` | تسجيل agents |

## خطوات الإنتاج

1. Authentication + RBAC + mTLS
2. PostgreSQL + log retention
3. nftables/eBPF enforcement module
4. 802.1X / RADIUS integration
5. DHCP snooping + ARP inspection
6. Threat intel feed connectors (AbuseIPDB, OTX)
7. High-availability cluster
