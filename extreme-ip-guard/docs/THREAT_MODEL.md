# Threat Model — Extreme IP Guard

STRIDE-style model for the XIG control plane and endpoint agent.

## Trust boundaries

1. **Endpoint <-> Server** (network).
2. **Admin Console <-> Server** (network).
3. **Server <-> Data Plane** (process / disk).
4. **Endpoint Agent <-> Operating System** (privilege).
5. **Auditor <-> Audit Chain** (read-only).

## Assets

| Asset | Why it matters |
| --- | --- |
| Endpoint events (telemetry) | Investigation, attribution, compliance. |
| Policy bundles | Defines what the agent enforces. |
| Audit trail | Legal & regulatory evidence. |
| Agent private key | Identity of the endpoint. |
| Server signing key | Authority over every endpoint. |
| Forensic artefacts | Sensitive personal/business data. |

## STRIDE

### Spoofing
- **Risk:** Attacker impersonates an agent to feed false events or poison UEBA baselines.
- **Mitigation:** mTLS, hardware fingerprint binding, signed enrolment tokens, per-agent Ed25519 key on every event batch.

### Tampering
- **Risk:** Malicious admin or insider edits past events.
- **Mitigation:** Append-only event ledger, SHA-256 hash chain, hourly Merkle root published to a separate channel.

### Repudiation
- **Risk:** Admin denies running a destructive playbook.
- **Mitigation:** All admin actions hit `audit_entries` with hash chain; break-glass requires dual control and is highlighted in the UI.

### Information Disclosure
- **Risk:** Screen recordings or DLP samples leak.
- **Mitigation:** Encrypted at rest using the storage encryption key; access requires `auditor` role; every view is logged.

### Denial of Service
- **Risk:** Rogue agent floods the server with events.
- **Mitigation:** Per-agent token bucket, exponential backoff response, automatic agent quarantine if its risk score exceeds threshold.

### Elevation of Privilege
- **Risk:** Analyst escalates to admin via misconfigured roles.
- **Mitigation:** RBAC with explicit role list (`viewer`, `analyst`, `admin`, `auditor`, `break-glass`); changes are logged and require admin role itself.

## Out-of-scope (for the reference implementation)
- Side-channel attacks on the host OS.
- Supply-chain compromise of the agent binary distribution (handled at M2 with reproducible builds).
- HSM-backed signing keys (planned for M3).
