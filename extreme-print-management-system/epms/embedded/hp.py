"""HP OXP / Workpath / FutureSmart adapter (SDK-ready simulation layer)."""

from __future__ import annotations

from typing import Any

from epms.agents import platform_profile

from .gateway import GatewayAdapter
from .base import DeviceSession, HeldJobView


class HPAdapter(GatewayAdapter):
    """Uses Extreme Server for job control; device_address reserved for future OXP HTTP hooks."""

    def __init__(self, *, vendor: str = "hp", **kwargs):
        super().__init__(**kwargs)
        self.vendor = vendor
        self.platform = platform_profile(vendor)["platform"]

    def authenticate(self, *, username: str, pin: str = "", card_id: str = "") -> DeviceSession:
        session = super().authenticate(username=username, pin=pin, card_id=card_id)
        if self.device_address:
            self._oxp_presence_check()
        return DeviceSession(
            username=session.username,
            display_name=session.display_name,
            auth_method="card" if card_id else "hp-pin",
            device_address=self.device_address or "hp-simulated",
        )

    def _oxp_presence_check(self) -> None:
        """Placeholder for OXP device handshake — production SDK replaces this."""
        if not self.device_address.startswith(("http://", "https://")):
            raise ValueError("HP device_address must be an http(s) URL for OXP gateway mode")

    def list_held_jobs(self, *, username: str) -> list[HeldJobView]:
        jobs = super().list_held_jobs(username=username)
        return [
            HeldJobView(
                job_id=job.job_id,
                document_name=job.document_name,
                printer_name=f"HP {job.printer_name}".strip(),
                pages=job.pages,
                cost_cents=job.cost_cents,
                status=job.status,
            )
            for job in jobs
        ]

    def release_job(self, job_id: int, *, username: str) -> dict[str, Any]:
        result = super().release_job(job_id, username=username)
        return {**result, "device_ack": self._simulate_device_ack("release", job_id)}

    def deny_job(self, job_id: int, *, username: str, reason: str = "") -> dict[str, Any]:
        result = super().deny_job(job_id, username=username, reason=reason)
        return {**result, "device_ack": self._simulate_device_ack("deny", job_id)}

    def _simulate_device_ack(self, action: str, job_id: int) -> dict[str, Any]:
        return {
            "vendor": self.vendor,
            "platform": self.platform,
            "action": action,
            "job_id": job_id,
            "oxp_endpoint": self.device_address or None,
            "sdk_status": "simulated",
        }

    def device_capabilities(self) -> dict[str, Any]:
        profile = platform_profile(self.vendor)
        return {
            **super().device_capabilities(),
            "embedded": profile["embedded"],
            "capabilities": profile["capabilities"],
            "sdk_module": "epms.embedded.hp",
            "sdk_status": "simulated",
        }
