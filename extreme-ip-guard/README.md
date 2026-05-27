# Extreme IP Guard (XIG)

> **Next-generation endpoint protection & data-loss prevention** — built as a
> futuristic successor to legacy IP Guard. Zero Trust by default, XDR-style
> telemetry, UEBA risk scoring, MITRE ATT&CK mapping, tamper-evident audit,
> SOAR-lite automated response, and crypto-agile primitives ready for the
> post-quantum era.

This directory is a fully standalone, self-hosted reference implementation. It
deliberately depends only on Python's standard library so it runs anywhere
without setup, while still exercising the entire control-plane / agent
contract end to end.

The product brief, threat model, and full architecture (in Arabic and
English) live in [`docs/`](./docs).

---

## Highlights

- **Zero-Trust enrolment** — every agent registers with a one-time token, a
  hardware fingerprint, and a per-agent signing secret.
- **Hybrid detection engine** — explicit rules + EWMA-based UEBA baselines +
  threat-intel IOC lookups, all returning MITRE ATT&CK technique ids.
- **Tamper-evident audit** — every event and every admin action goes through
  an append-only hash chain (`SHA-256(prev || canonical_json(record))`) that
  the API can replay on demand. Merkle checkpoints supported for off-host
  anchoring.
- **SOAR-lite playbooks** — alerts automatically queue signed response
  commands (`block_usb`, `kill_process`, `quarantine_file`, `wipe_clipboard`,
  `isolate_host`, …) that an agent fetches and acknowledges.
- **Crypto-agile primitives** — every signature and password hash carries an
  algorithm identifier so the scheme can be rotated (HMAC-SHA256 today,
  Ed25519 + hybrid X25519/Kyber-768 in production).
- **Reference SOC dashboard** — modern dark-theme UI with live threat
  timeline, MITRE coverage chart, risk leaderboards, audit ledger, agent
  registry, and an IOC composer.

---

## بالعربيّة (Brief)

Extreme IP Guard هو نظام جيل قادم لحماية النقاط الطرفيّة ومنع تسرّب البيانات،
مستلهَم من نظام IP Guard لكنه يتجاوزه بمعماريّة Zero Trust وكشف هجين
(قواعد + سلوك + ذكاء تهديد) وسجل تدقيق مقاوم للعبث (Hash chain)
وأتمتة استجابة (SOAR-lite) مع إدارة مفاتيح قابلة للتدوير وجاهزة للتشفير ما
بعد الكمّي (PQC).

الوثائق الكاملة بالعربيّة في:

- `docs/IPGUARD_STUDY_AR.md` — دراسة معمّقة لنظام IP Guard.
- `docs/EXTREME_ARCHITECTURE_AR.md` — التصميم المعماري الكامل لـ Extreme IP Guard.

---

## Project layout

```
extreme-ip-guard/
├── app.py                     # control-plane entry point
├── console.py                 # operator CLI
├── xig/                       # control-plane core (pure stdlib)
│   ├── core.py                # domain types, MITRE table, risk math
│   ├── crypto.py              # HMAC/PBKDF2/hash-chain primitives
│   ├── policies.py            # rules, IOCs, playbooks, predicate DSL
│   ├── detection.py           # hybrid detection engine (rules + UEBA + TI)
│   ├── audit.py               # tamper-evident chain & verification
│   ├── storage.py             # SQLite-backed state, command queue
│   └── server.py              # REST API + static file server
├── agent/                     # reference endpoint agent + sensors
│   ├── sensors.py
│   └── endpoint_agent.py
├── static/                    # SOC dashboard (HTML/CSS/JS)
├── docs/                      # Arabic study + architecture + threat model
├── config/                    # example deployment configs
└── tests/                     # unittest suite (core, crypto, detection, …)
```

---

## Run the control plane

```bash
cd extreme-ip-guard
python3 app.py
```

The console then becomes available at:

```text
http://127.0.0.1:8090
```

Default seeded console users (password equals the username):

| Username  | Role     |
|-----------|----------|
| admin     | admin    |
| analyst   | analyst  |
| auditor   | auditor  |
| sara      | viewer   |

Override the database location:

```bash
XIG_DB=/path/to/xig.sqlite3 python3 app.py
```

---

## Enrol an endpoint and exercise the pipeline

In a second terminal, while the server is running:

```bash
cd extreme-ip-guard

# 1) Console issues a one-time enrolment token.
python3 console.py issue-token --hostname WS-LAB-01

# Take the value of `enrol_token` from the JSON output.

# 2) Reference agent enrols against that token.
python3 -m agent.endpoint_agent enrol --token <PASTE_TOKEN>

# 3) Heartbeat to confirm liveness.
python3 -m agent.endpoint_agent heartbeat

# 4) Emit a single simulated sensor event.
python3 -m agent.endpoint_agent emit usb_mass_copy --user sara

# 5) Fire a full deterministic "attack storm" populated dashboard.
python3 -m agent.endpoint_agent storm --user sara

# 6) Fetch and acknowledge the queued response commands.
python3 -m agent.endpoint_agent poll --complete
```

Now refresh the dashboard — alerts, MITRE coverage, user/asset risk
leaderboards, and the audit ledger are all populated.

---

## REST API summary

| Method | Endpoint                              | Purpose                                              |
|--------|---------------------------------------|------------------------------------------------------|
| GET    | `/api/dashboard`                      | Totals, top risky users/assets, MITRE coverage.      |
| GET    | `/api/users`                          | Console users with blended risk scores.              |
| GET    | `/api/assets`                         | Asset inventory with risk bands.                     |
| GET    | `/api/agents`                         | Enrolled endpoint agents.                            |
| GET    | `/api/alerts`                         | Latest alerts (severity, MITRE, status).             |
| GET    | `/api/events`                         | Last 200 telemetry events.                           |
| GET    | `/api/audit`                          | Last 100 audit entries (hash-chained).               |
| GET    | `/api/audit/verify`                   | Replay the audit chain.                              |
| GET    | `/api/events/verify`                  | Replay the event chain.                              |
| GET    | `/api/policies`                       | Published policy versions.                           |
| GET    | `/api/iocs`                           | Known threat-intel indicators.                       |
| GET    | `/api/commands?agent_id=…`            | Inspect queued/dispatched commands.                  |
| GET    | `/api/agents/poll?agent_id=…`         | Agent long-poll for response commands.               |
| POST   | `/api/agents/enrol-tokens`            | Issue a one-time enrolment token.                    |
| POST   | `/api/agents/enrol`                   | Enrol an agent using a token.                        |
| POST   | `/api/agents/heartbeat`               | Liveness ping.                                       |
| POST   | `/api/events`                         | Ingest a telemetry event.                            |
| POST   | `/api/commands/complete`              | Agent reports completion of a queued command.        |
| POST   | `/api/iocs`                           | Add a new threat-intel indicator.                    |
| POST   | `/api/policies/publish`               | Publish a new signed policy bundle.                  |
| POST   | `/api/alerts/{uid}/status`            | Change alert status (`new`/`acknowledged`/…).        |
| POST   | `/api/auth/login`                     | Authenticate a console user (PBKDF2).                |

Example: ingest an event manually.

```bash
curl -X POST http://127.0.0.1:8090/api/events \
  -H 'Content-Type: application/json' \
  -d '{
    "agent_id": "agent-int-01",
    "kind": "network.connect",
    "subject": "net",
    "data": {"domain": "malware-c2.example", "ip": "203.0.113.66"}
  }'
```

---

## Run the tests

```bash
cd extreme-ip-guard
python3 -m unittest discover -s tests -v
```

The suite covers the core domain, the crypto primitives, the policy DSL,
the detection engine, the audit chain, the storage layer, and the HTTP
server.

---

## Migration from the IP Guard model to XIG

A side-by-side comparison and the full migration story lives in
`docs/EXTREME_ARCHITECTURE_AR.md` §11. The TL;DR:

| Axis | IP Guard | Extreme IP Guard |
|------|----------|------------------|
| Trust model | Perimeter | Zero Trust |
| Detection | Rules + lists | Rules + UEBA + threat intel + risk |
| Audit | Plain logs | Hash-chained, Merkle-checkpointed |
| Response | Manual | SOAR-lite playbooks |
| Crypto | AES only | Crypto-agile, PQC-ready primitives |
| Integration | Limited | API-first, MITRE/Sigma/STIX-friendly |
| Scaling | Vertical | Horizontal (stateless API + queue) |

---

## What this reference build is — and is not

It **is** a faithful proof of the architecture:

- complete control-plane contract,
- full audit chain implementation,
- working detection engine,
- end-to-end agent enrolment, telemetry, and response,
- self-contained SOC dashboard.

It **is not** a production binary. For deployment the agent should be a
hardened Rust/Go binary with eBPF/ETW sensors, mTLS, sandboxed plugins, and
HSM-backed signing keys, and the storage layer should be Postgres + a search
index (OpenSearch/Tantivy) behind a real reverse proxy.

The intent is that every component can be replaced **independently** without
breaking the contract documented in `docs/EXTREME_ARCHITECTURE_AR.md`.
