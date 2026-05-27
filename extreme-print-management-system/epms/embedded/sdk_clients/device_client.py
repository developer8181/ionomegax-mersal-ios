"""Base device SDK client contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DeviceAuthResult:
    ok: bool
    username: str
    session_token: str = ""
    message: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeviceJobAction:
    ok: bool
    job_id: int
    action: str
    message: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class DeviceClient(ABC):
    vendor: str = "generic"
    protocol: str = "http"

    def __init__(self, *, base_url: str, timeout: int = 20, verify_tls: bool = True):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verify_tls = verify_tls

    @abstractmethod
    def handshake(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def authenticate(self, *, username: str, pin: str = "", card_id: str = "") -> DeviceAuthResult:
        raise NotImplementedError

    @abstractmethod
    def release_job(self, job_id: int, *, username: str, session_token: str = "") -> DeviceJobAction:
        raise NotImplementedError

    @abstractmethod
    def deny_job(self, job_id: int, *, username: str, reason: str = "", session_token: str = "") -> DeviceJobAction:
        raise NotImplementedError

    def capabilities(self) -> dict[str, Any]:
        return {"vendor": self.vendor, "protocol": self.protocol, "base_url": self.base_url}
