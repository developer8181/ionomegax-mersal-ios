# Extreme IP Guard — REST API reference

The control plane speaks JSON over HTTP/1.1 (`application/json; charset=utf-8`). Every endpoint is also reachable from the operator CLI (`console.py`) and the reference agent (`agent/endpoint_agent.py`).

## Conventions

- Every timestamp is ISO-8601 UTC (`YYYY-MM-DDTHH:MM:SS.sssZ`).
- Errors are returned as `{"error": "..."}` with the appropriate HTTP status code.
- Mutating endpoints accept an `actor` field; if omitted, the audit log records `"console"`.

## Health / dashboard

### `GET /api/dashboard`

Returns aggregate totals, MITRE coverage, and the top risky users/assets.

```json
{
  "totals": {
    "agents": 3,
    "assets": 5,
    "users": 4,
    "events": 123,
    "alerts": 17,
    "open_alerts": 4,
    "high_alerts": 6
  },
  "top_users": [{"display_name": "Sara from Finance", "department": "Finance", "risk_score": 41.2, "risk_band": "medium"}],
  "top_assets": [{"hostname": "WS-ADMIN-01", "criticality": "high", "risk_score": 38.5, "risk_band": "medium"}],
  "mitre": [{"mitre": "T1052.001", "hits": 5}],
  "audit": [{"ts": "...", "actor": "console", "action": "policy.published", "target": "v2"}]
}
```

## Agents

### `POST /api/agents/enrol-tokens`

Issues a one-time enrolment token.

```json
{ "hostname": "WS-LAB-01", "criticality": "normal" }
```

### `POST /api/agents/enrol`

Consumes a token, returns the agent's signing secret and the current signed policy bundle.

```json
{
  "enrol_token": "…",
  "agent_id": "agent-lab-01",
  "hw_fp": "hwfp-deadbeef",
  "os_name": "Linux 6.12",
  "version": "0.1.0-ref"
}
```

### `POST /api/agents/heartbeat`

```json
{ "agent_id": "agent-lab-01", "version": "0.1.0-ref" }
```

### `GET /api/agents`

Lists every active agent and its blended risk band.

### `GET /api/agents/poll?agent_id=…`

Long-poll endpoint that returns and `dispatches` queued response commands.

## Telemetry

### `POST /api/events`

```json
{
  "agent_id": "agent-lab-01",
  "kind": "file.write",
  "subject": "usb",
  "data": {"path": "/media/usb/dump.zip", "bytes": 80000000}
}
```

`ts` is optional and is set by the server when omitted.

Response includes the resulting alerts and any commands queued by the SOAR-lite engine:

```json
{
  "chain_hash": "…",
  "alerts": [{"alert_uid": "AL-…", "severity": "high", "rule_id": "R-USB-001", "mitre": "T1052.001"}],
  "commands_queued": [{"command_uid": "CMD-…", "playbook": "pb-usb-mass-copy"}]
}
```

### `GET /api/events`

Returns the last 200 events with their stored hashes.

### `GET /api/events/verify`

Replays the event hash chain and returns `{"chain": "events", "intact": true/false, "broken_at": -1, "count": N}`.

## Alerts

### `GET /api/alerts`

Returns the latest 100 alerts.

### `POST /api/alerts/{uid}/status`

```json
{ "status": "acknowledged" }
```

Valid statuses: `new`, `acknowledged`, `resolved`, `false_positive`.

## Commands (SOAR-lite)

### `GET /api/commands?agent_id=&status=`

Lists commands, optionally filtered by agent and/or status.

### `POST /api/commands/complete`

```json
{ "command_uid": "CMD-…", "status": "succeeded", "result": {"…": "…"} }
```

## Threat intel

### `GET /api/iocs`

Lists the indicators currently loaded into the detection engine.

### `POST /api/iocs`

```json
{ "kind": "domain", "value": "evil.example" }
```

Supported kinds: `sha256`, `domain`, `ipv4`, `ipv6`, `ja3`.

## Policies

### `GET /api/policies`

Returns all published bundle versions.

### `POST /api/policies/publish`

Publishes the bundled default policy and increments the version.

## Audit

### `GET /api/audit`

Returns the latest 100 hash-chained audit entries (admin actions, policy publications, alert workflow, command queue).

### `GET /api/audit/verify`

Replays the audit chain.

## Authentication

### `POST /api/auth/login`

```json
{ "username": "admin", "password": "admin" }
```

Returns `{id, username, display_name, role}` on success, `401` otherwise. Passwords are verified with PBKDF2-HMAC-SHA256 (240k iterations by default).
