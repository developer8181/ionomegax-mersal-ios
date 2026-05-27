"""Base classes for embedded and gateway printer controllers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DeviceSession:
    username: str
    display_name: str
    auth_method: str
    device_address: str


@dataclass(frozen=True)
class HeldJobView:
    job_id: int
    document_name: str
    printer_name: str
    pages: int
    cost_cents: int
    status: str


class EmbeddedAdapter(ABC):
    """Vendor-neutral controller interface implemented per platform or gateway."""

    vendor: str = "generic"
    platform: str = ""

    def __init__(self, *, server_url: str, agent_token: str = "", device_address: str = ""):
        self.server_url = server_url.rstrip("/")
        self.agent_token = agent_token
        self.device_address = device_address.strip()

    @abstractmethod
    def authenticate(self, *, username: str, pin: str = "", card_id: str = "") -> DeviceSession:
        raise NotImplementedError

    @abstractmethod
    def list_held_jobs(self, *, username: str) -> list[HeldJobView]:
        raise NotImplementedError

    @abstractmethod
    def release_job(self, job_id: int, *, username: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def deny_job(self, job_id: int, *, username: str, reason: str = "") -> dict[str, Any]:
        raise NotImplementedError

    def device_capabilities(self) -> dict[str, Any]:
        return {"vendor": self.vendor, "platform": self.platform, "device_address": self.device_address}
