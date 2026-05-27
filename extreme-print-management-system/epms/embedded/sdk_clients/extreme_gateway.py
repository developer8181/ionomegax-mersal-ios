"""Extreme universal device servlet protocol (deployed on MFD via Java SDK bridge)."""

from __future__ import annotations

from typing import Any

from .http_util import join_url, post_json


class ExtremeGatewayClient:
    """REST contract implemented by `sdk/java/extreme-servlet` on each vendor platform."""

    API_PREFIX = "extreme/sdk/v1"

    def __init__(self, base_url: str, *, timeout: int = 20, verify_tls: bool = True):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verify_tls = verify_tls

    def _url(self, path: str) -> str:
        return join_url(self.base_url, f"{self.API_PREFIX}/{path}")

    def health(self) -> dict[str, Any]:
        return post_json(self._url("health"), {}, timeout=self.timeout, verify_tls=self.verify_tls)

    def authenticate(self, *, username: str, pin: str = "", card_id: str = "") -> dict[str, Any]:
        return post_json(
            self._url("auth"),
            {"username": username, "pin": pin, "card_id": card_id},
            timeout=self.timeout,
            verify_tls=self.verify_tls,
        )

    def release_job(self, job_id: int, *, username: str, session_token: str = "") -> dict[str, Any]:
        return post_json(
            self._url(f"jobs/{job_id}/release"),
            {"username": username, "session_token": session_token},
            timeout=self.timeout,
            verify_tls=self.verify_tls,
        )

    def deny_job(self, job_id: int, *, username: str, reason: str = "", session_token: str = "") -> dict[str, Any]:
        return post_json(
            self._url(f"jobs/{job_id}/deny"),
            {"username": username, "reason": reason, "session_token": session_token},
            timeout=self.timeout,
            verify_tls=self.verify_tls,
        )
