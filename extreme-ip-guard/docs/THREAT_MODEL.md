# Extreme IP Guard — Threat Model

## Overview

Extreme IP Guard (EIPG) is a Zero Trust Network Access Control (NAC) platform. This document outlines the threat model for the MVP prototype and the production roadmap.

## Assets

| Asset | Sensitivity | Protection |
| --- | --- | --- |
| Policy rules | Critical | Signed bundles, RBAC (production), audit chain |
| Device registry | High | Authentication, MAC/IP binding, approval workflow |
| Block lists | High | Threat intel feeds, TTL, auto-expiry |
| Access logs | High | Immutable audit chain, SIEM export |
| Agent credentials | Critical | API keys, mTLS (production), key rotation |

## Trust Boundaries

```text
[Internet/Untrusted]
        |
   [Edge Enforcer] ← signed policy bundle
        |
   [Corporate Network Zones]
     ├── secure (high trust)
     ├── dmz (medium trust)
     ├── guest (low trust, quarantine)
     └── iot (isolated micro-segment)
        |
   [Endpoint Agents] → posture reports
        |
   [EIPG Server] ← central policy + audit
```

## Threat Actors

1. **External attacker** — port scanning, brute force, C2 communication
2. **Rogue device** — unauthorized MAC/IP on corporate network
3. **Compromised endpoint** — lateral movement from infected workstation
4. **Insider threat** — policy tampering, unauthorized access grants
5. **Agent impersonation** — fake edge/endpoint agent reporting false posture

## Mitigations (MVP vs Production)

| Threat | MVP | Production |
| --- | --- | --- |
| Unauthorized network access | Policy engine + device approval | 802.1X NAC, DHCP snooping, ARP inspection |
| Port scan / brute force | Behavioral detection + auto-block | IDS/IPS integration, rate limiting at eBPF/XDP |
| Policy tampering | HMAC-signed bundles | mTLS, Ed25519 signatures, hardware security module |
| Rogue agent | Agent heartbeat registry | Mutual TLS, device certificates, attestation |
| Audit log tampering | Hash-chained audit entries | WORM storage, external SIEM replication |
| DDoS on EIPG server | Threading HTTP server | Rate limiting, reverse proxy, HA cluster |

## Fail Modes

- **Fail-closed (default)**: If policy cannot be evaluated, deny access. Recommended for secure zones.
- **Fail-open**: Allow traffic if server unreachable. Only for non-critical guest networks with monitoring.

Configure via edge agent `fail_mode` in production deployments.

## Residual Risks (MVP)

- No authentication on HTTP API (development only)
- SQLite not suitable for high-volume production logging
- Simulated posture checks on endpoint agent
- No real nftables/eBPF enforcement in prototype

These are documented and addressed in the production roadmap.
