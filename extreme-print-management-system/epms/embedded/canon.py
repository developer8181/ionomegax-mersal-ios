"""Canon MEAP adapter (SDK-ready simulation layer)."""

from __future__ import annotations

from typing import Any

from epms.agents import platform_profile

from .base import DeviceSession, HeldJobView
from .hp import HPAdapter


class CanonMEAPAdapter(HPAdapter):
    vendor = "canon"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.platform = platform_profile("canon")["platform"]

    def authenticate(self, *, username: str, pin: str = "", card_id: str = "") -> DeviceSession:
        session = super().authenticate(username=username, pin=pin, card_id=card_id)
        return DeviceSession(
            username=session.username,
            display_name=session.display_name,
            auth_method="meap-card" if card_id else "meap-pin",
            device_address=self.device_address or "canon-meap-simulated",
        )

    def list_held_jobs(self, *, username: str) -> list[HeldJobView]:
        jobs = super().list_held_jobs(username=username)
        return [
            HeldJobView(
                job_id=job.job_id,
                document_name=job.document_name,
                printer_name=f"Canon {job.printer_name}".strip(),
                pages=job.pages,
                cost_cents=job.cost_cents,
                status=job.status,
            )
            for job in jobs
        ]

    def device_capabilities(self) -> dict[str, Any]:
        profile = platform_profile("canon")
        return {
            **super().device_capabilities(),
            "vendor": self.vendor,
            "platform": self.platform,
            "embedded": profile["embedded"],
            "capabilities": profile["capabilities"],
            "sdk_module": "epms.embedded.canon",
        }
