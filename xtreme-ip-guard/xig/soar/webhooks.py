# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""SOAR outbound webhooks — integrate ServiceNow, Slack, Teams, custom SOAR."""

from __future__ import annotations

import hashlib
import hmac
import json
import urllib.error
import urllib.request
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class WebhookDispatcher:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def dispatch(self, event_type: str, payload: dict[str, Any], *, tenant_id: str = "default") -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for hook in self.db.list_webhooks(tenant_id=tenant_id, enabled_only=True):
            events = hook.get("events") or []
            if events and event_type not in events:
                continue
            results.append(self._post(hook, event_type, payload))
        return results

    def _post(self, hook: dict[str, Any], event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps({"event": event_type, "payload": payload, "source": "mersal-soar"}, sort_keys=True).encode()
        headers = {"Content-Type": "application/json", "User-Agent": "Mersal-SOAR/6.0"}
        secret = str(hook.get("secret", ""))
        if secret:
            sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
            headers["X-Mersal-Signature"] = sig
        req = urllib.request.Request(str(hook["url"]), data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return {"webhook_id": hook["webhook_id"], "status": resp.status, "ok": True}
        except urllib.error.URLError as exc:
            return {"webhook_id": hook["webhook_id"], "status": 0, "ok": False, "error": str(exc)}
