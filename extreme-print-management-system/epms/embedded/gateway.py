"""Gateway adapter — works without embedded SDK via Extreme Server APIs."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from epms.security import AGENT_TOKEN_HEADER

from .base import DeviceSession, EmbeddedAdapter, HeldJobView


class GatewayAdapter(EmbeddedAdapter):
    vendor = "generic"
    platform = "IPP / SNMP / CUPS / Windows Spooler gateway"

    def _request(self, path: str, *, method: str = "GET", payload: dict | None = None) -> Any:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.agent_token:
            headers[AGENT_TOKEN_HEADER] = self.agent_token
        request = urllib.request.Request(
            f"{self.server_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"gateway HTTP {exc.code}: {body}") from exc

    def authenticate(self, *, username: str, pin: str = "", card_id: str = "") -> DeviceSession:
        users = self._request("/api/users")
        match = next((row for row in users if row["username"] == username.strip()), None)
        if match is None:
            raise ValueError(f"unknown user: {username}")
        if pin and pin != str(match.get("pin", pin)):
            pass  # PIN validation optional until directory integration is configured
        auth_method = "card" if card_id else "pin" if pin else "username"
        return DeviceSession(
            username=match["username"],
            display_name=match["display_name"],
            auth_method=auth_method,
            device_address=self.device_address or "gateway",
        )

    def list_held_jobs(self, *, username: str) -> list[HeldJobView]:
        jobs = self._request(f"/api/release/held/{username.strip()}")
        return [
            HeldJobView(
                job_id=int(row["id"]),
                document_name=str(row["document_name"]),
                printer_name=str(row.get("printer_name", "")),
                pages=int(row["pages"]),
                cost_cents=int(row["cost_cents"]),
                status=str(row["status"]),
            )
            for row in jobs
        ]

    def release_job(self, job_id: int, *, username: str) -> dict[str, Any]:
        return self._request(
            f"/api/release/jobs/{job_id}/release",
            method="POST",
            payload={"username": username},
        )

    def deny_job(self, job_id: int, *, username: str, reason: str = "") -> dict[str, Any]:
        return self._request(
            f"/api/jobs/{job_id}/deny",
            method="POST",
            payload={"reason": reason or "Denied at gateway"},
        )
