"""Shared SDK-enabled embedded adapter base with real device HTTP clients."""

from __future__ import annotations

from typing import Any, ClassVar

from epms.agents import platform_profile

from .base import DeviceSession, HeldJobView
from .gateway import GatewayAdapter
from .sdk_clients.registry import get_device_client
from .sdk_registry import SdkRuntime, get_sdk_runtime, is_sdk_active


class VendorSDKAdapter(GatewayAdapter):
    """Production SDK bridge: Extreme Server policy + vendor device HTTP/SDK protocol."""

    vendor_key: ClassVar[str] = "generic"
    sdk_module: ClassVar[str] = "epms.embedded.sdk_base"
    printer_prefix: ClassVar[str] = ""
    auth_pin_label: ClassVar[str] = "pin"
    auth_card_label: ClassVar[str] = "card"
    require_https_device: ClassVar[bool] = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vendor = self.vendor_key
        self.platform = platform_profile(self.vendor_key)["platform"]
        self._sdk: SdkRuntime = get_sdk_runtime(self.vendor_key)
        self._device_client = None
        self._device_session_token = ""

    def _get_device_client(self):
        if not self.device_address:
            return None
        if self._device_client is None:
            self._device_client = get_device_client(
                self.vendor_key,
                self.device_address,
                verify_tls=self.device_address.startswith("https://"),
            )
        return self._device_client

    def authenticate(self, *, username: str, pin: str = "", card_id: str = "") -> DeviceSession:
        if not is_sdk_active(self.vendor_key):
            raise RuntimeError(f"SDK is not active for vendor: {self.vendor_key}")
        session = super().authenticate(username=username, pin=pin, card_id=card_id)
        device_auth = None
        client = self._get_device_client()
        if client is not None:
            device_auth = client.authenticate(username=username, pin=pin, card_id=card_id)
            self._device_session_token = device_auth.session_token
        auth_method = f"{self.vendor_key}-{self.auth_card_label}" if card_id else f"{self.vendor_key}-{self.auth_pin_label}"
        return DeviceSession(
            username=session.username,
            display_name=session.display_name,
            auth_method=auth_method,
            device_address=self.device_address or f"{self.vendor_key}-sdk-local",
        )

    def _sdk_handshake(self) -> dict[str, Any]:
        if self.require_https_device and not self.device_address.startswith(("http://", "https://")):
            raise ValueError(f"{self.vendor_key} device_address must be an http(s) URL when SDK is active")
        client = self._get_device_client()
        if client is None:
            return {
                "vendor": self.vendor_key,
                "platform": self.platform,
                "sdk_status": self._sdk.status,
                "handshake": "server-only",
            }
        handshake = client.handshake()
        return {
            "vendor": self.vendor_key,
            "platform": self.platform,
            "sdk_status": "integrated",
            "sdk_version": self._sdk.version,
            "endpoint": self.device_address,
            "device_handshake": handshake,
        }

    def list_held_jobs(self, *, username: str) -> list[HeldJobView]:
        prefix = self.printer_prefix or self.vendor_key.title()
        jobs = super().list_held_jobs(username=username)
        return [
            HeldJobView(
                job_id=job.job_id,
                document_name=job.document_name,
                printer_name=f"{prefix} {job.printer_name}".strip(),
                pages=job.pages,
                cost_cents=job.cost_cents,
                status=job.status,
            )
            for job in jobs
        ]

    def release_job(self, job_id: int, *, username: str) -> dict[str, Any]:
        device_result = None
        client = self._get_device_client()
        if client is not None:
            device_result = client.release_job(
                job_id,
                username=username,
                session_token=self._device_session_token,
            )
        result = super().release_job(job_id, username=username)
        return {**result, "device_ack": self._device_ack("release", job_id, device_result)}

    def deny_job(self, job_id: int, *, username: str, reason: str = "") -> dict[str, Any]:
        device_result = None
        client = self._get_device_client()
        if client is not None:
            device_result = client.deny_job(
                job_id,
                username=username,
                reason=reason,
                session_token=self._device_session_token,
            )
        result = super().deny_job(job_id, username=username, reason=reason)
        return {**result, "device_ack": self._device_ack("deny", job_id, device_result)}

    def _device_ack(self, action: str, job_id: int, device_result: Any = None) -> dict[str, Any]:
        ack: dict[str, Any] = {
            **self._sdk.to_dict(),
            "action": action,
            "job_id": job_id,
            "sdk_module": self.sdk_module,
            "integration": "http-native",
            "device_endpoint": self.device_address or None,
        }
        if device_result is not None:
            ack["device_result"] = {
                "ok": device_result.ok,
                "message": device_result.message,
                "raw": device_result.raw,
            }
        return ack

    def device_capabilities(self) -> dict[str, Any]:
        profile = platform_profile(self.vendor_key)
        client = self._get_device_client()
        return {
            **super().device_capabilities(),
            "vendor": self.vendor_key,
            "platform": self.platform,
            "embedded": profile["embedded"],
            "capabilities": profile["capabilities"],
            "sdk_module": self.sdk_module,
            "sdk": {**self._sdk.to_dict(), "integration": "http-native" if client else "server-only"},
            "device_protocol": client.protocol if client else None,
        }
