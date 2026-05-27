"""Vendor-native HTTP SDK implementations with Extreme servlet fallback."""

from __future__ import annotations

from typing import Any, Callable

from .device_client import DeviceAuthResult, DeviceClient, DeviceJobAction
from .extreme_gateway import ExtremeGatewayClient
from .http_util import join_url, post_json, post_xml


def _auth_from_response(data: dict[str, Any], username: str) -> DeviceAuthResult:
    return DeviceAuthResult(
        ok=bool(data.get("ok", True)),
        username=str(data.get("username", username)),
        session_token=str(data.get("session_token", data.get("token", ""))),
        message=str(data.get("message", "authenticated")),
        raw=data,
    )


def _action_from_response(data: dict[str, Any], *, job_id: int, action: str) -> DeviceJobAction:
    return DeviceJobAction(
        ok=bool(data.get("ok", True)),
        job_id=job_id,
        action=action,
        message=str(data.get("message", action)),
        raw=data,
    )


class VendorHttpClient(DeviceClient):
    def __init__(
        self,
        *,
        vendor: str,
        protocol: str,
        native_handshake_path: str,
        native_auth_path: str,
        native_release_path: str,
        native_deny_path: str,
        base_url: str,
        native_handshake_builder: Callable[[], dict[str, Any]] | None = None,
        native_auth_builder: Callable[[str, str, str], dict[str, Any]] | None = None,
        use_xml_auth: bool = False,
        **kwargs: Any,
    ):
        super().__init__(base_url=base_url, **kwargs)
        self.vendor = vendor
        self.protocol = protocol
        self.native_handshake_path = native_handshake_path
        self.native_auth_path = native_auth_path
        self.native_release_path = native_release_path
        self.native_deny_path = native_deny_path
        self.native_handshake_builder = native_handshake_builder or (lambda: {"application": "ExtremePrint"})
        self.native_auth_builder = native_auth_builder
        self.use_xml_auth = use_xml_auth
        self._gateway = ExtremeGatewayClient(base_url, timeout=self.timeout, verify_tls=self.verify_tls)
        self._session_token = ""

    def handshake(self) -> dict[str, Any]:
        try:
            data = self._gateway.health()
            return {"mode": "extreme-servlet", "vendor": self.vendor, **data}
        except RuntimeError as extreme_error:
            try:
                if self.use_xml_auth:
                    post_xml(
                        join_url(self.base_url, self.native_handshake_path),
                        self._build_openapi_ping_xml(),
                        verify_tls=self.verify_tls,
                    )
                    return {"mode": "native-xml", "vendor": self.vendor, "handshake": "ok"}
                payload = self.native_handshake_builder()
                data = post_json(
                    join_url(self.base_url, self.native_handshake_path),
                    payload,
                    timeout=self.timeout,
                    verify_tls=self.verify_tls,
                )
                return {"mode": "native-json", "vendor": self.vendor, **data}
            except RuntimeError as native_error:
                raise RuntimeError(
                    f"{self.vendor} SDK handshake failed (extreme servlet and native). "
                    f"extreme={extreme_error}; native={native_error}"
                ) from native_error

    def authenticate(self, *, username: str, pin: str = "", card_id: str = "") -> DeviceAuthResult:
        try:
            data = self._gateway.authenticate(username=username, pin=pin, card_id=card_id)
            result = _auth_from_response(data, username)
            self._session_token = result.session_token
            return result
        except RuntimeError:
            if self.use_xml_auth:
                post_xml(
                    join_url(self.base_url, self.native_auth_path),
                    self._build_openapi_auth_xml(username, pin, card_id),
                    verify_tls=self.verify_tls,
                )
                self._session_token = f"xml-{username}"
                return DeviceAuthResult(ok=True, username=username, session_token=self._session_token, message="native-xml")
            body = (
                self.native_auth_builder(username, pin, card_id)
                if self.native_auth_builder
                else {"username": username, "pin": pin, "card_id": card_id}
            )
            data = post_json(
                join_url(self.base_url, self.native_auth_path),
                body,
                timeout=self.timeout,
                verify_tls=self.verify_tls,
            )
            result = _auth_from_response(data, username)
            self._session_token = result.session_token
            return result

    def release_job(self, job_id: int, *, username: str, session_token: str = "") -> DeviceJobAction:
        token = session_token or self._session_token
        try:
            data = self._gateway.release_job(job_id, username=username, session_token=token)
            return _action_from_response(data, job_id=job_id, action="release")
        except RuntimeError:
            data = post_json(
                join_url(self.base_url, self.native_release_path.format(job_id=job_id)),
                {"username": username, "session_token": token, "job_id": job_id},
                timeout=self.timeout,
                verify_tls=self.verify_tls,
            )
            return _action_from_response(data, job_id=job_id, action="release")

    def deny_job(self, job_id: int, *, username: str, reason: str = "", session_token: str = "") -> DeviceJobAction:
        token = session_token or self._session_token
        try:
            data = self._gateway.deny_job(job_id, username=username, reason=reason, session_token=token)
            return _action_from_response(data, job_id=job_id, action="deny")
        except RuntimeError:
            data = post_json(
                join_url(self.base_url, self.native_deny_path.format(job_id=job_id)),
                {"username": username, "reason": reason, "session_token": token, "job_id": job_id},
                timeout=self.timeout,
                verify_tls=self.verify_tls,
            )
            return _action_from_response(data, job_id=job_id, action="deny")

    @staticmethod
    def _build_openapi_ping_xml() -> str:
        return """<?xml version="1.0" encoding="UTF-8"?>
<OpenAPI><Request><DeviceDescription/></Request></OpenAPI>"""

    @staticmethod
    def _build_openapi_auth_xml(username: str, pin: str, card_id: str) -> str:
        credential = card_id or pin or username
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<OpenAPI><Request><Login><UserName>{username}</UserName><Password>{credential}</Password></Login></Request></OpenAPI>"""


def build_hp_client(base_url: str, **kwargs: Any) -> VendorHttpClient:
    return VendorHttpClient(
        vendor="hp",
        protocol="hp-oxp-http",
        native_handshake_path="hp/oxp/v1/deviceInfo",
        native_auth_path="hp/oxp/v1/authenticate",
        native_release_path="hp/oxp/v1/jobs/{job_id}/release",
        native_deny_path="hp/oxp/v1/jobs/{job_id}/deny",
        base_url=base_url,
        native_handshake_builder=lambda: {"applicationId": "ExtremePrint", "capability": "release"},
        **kwargs,
    )


def build_canon_client(base_url: str, **kwargs: Any) -> VendorHttpClient:
    return VendorHttpClient(
        vendor="canon",
        protocol="canon-meap-http",
        native_handshake_path="canon/meap/v1/application",
        native_auth_path="canon/meap/v1/login",
        native_release_path="canon/meap/v1/print/jobs/{job_id}/release",
        native_deny_path="canon/meap/v1/print/jobs/{job_id}/cancel",
        base_url=base_url,
        **kwargs,
    )


def build_ricoh_client(base_url: str, **kwargs: Any) -> VendorHttpClient:
    return VendorHttpClient(
        vendor="ricoh",
        protocol="ricoh-smartsdk-http",
        native_handshake_path="rws/extreme/handshake",
        native_auth_path="rws/extreme/auth",
        native_release_path="rws/extreme/jobs/{job_id}/release",
        native_deny_path="rws/extreme/jobs/{job_id}/deny",
        base_url=base_url,
        **kwargs,
    )


def build_xerox_client(base_url: str, **kwargs: Any) -> VendorHttpClient:
    return VendorHttpClient(
        vendor="xerox",
        protocol="xerox-eip-http",
        native_handshake_path="eip/extreme/DeviceCapabilities",
        native_auth_path="eip/extreme/Authenticate",
        native_release_path="eip/extreme/Jobs/{job_id}/Release",
        native_deny_path="eip/extreme/Jobs/{job_id}/Cancel",
        base_url=base_url,
        **kwargs,
    )


def build_konica_client(base_url: str, **kwargs: Any) -> VendorHttpClient:
    return VendorHttpClient(
        vendor="konica-minolta",
        protocol="km-openapi-xml",
        native_handshake_path="OpenAPI",
        native_auth_path="OpenAPI",
        native_release_path="OpenAPI/jobs/{job_id}/release",
        native_deny_path="OpenAPI/jobs/{job_id}/deny",
        base_url=base_url,
        use_xml_auth=True,
        **kwargs,
    )


def build_kyocera_client(base_url: str, **kwargs: Any) -> VendorHttpClient:
    return VendorHttpClient(
        vendor="kyocera",
        protocol="kyocera-hypas-http",
        native_handshake_path="hypas/extreme/device",
        native_auth_path="hypas/extreme/login",
        native_release_path="hypas/extreme/jobs/{job_id}/release",
        native_deny_path="hypas/extreme/jobs/{job_id}/deny",
        base_url=base_url,
        **kwargs,
    )


def build_lexmark_client(base_url: str, **kwargs: Any) -> VendorHttpClient:
    return VendorHttpClient(
        vendor="lexmark",
        protocol="lexmark-esf-http",
        native_handshake_path="esf/extreme/capabilities",
        native_auth_path="esf/extreme/auth",
        native_release_path="esf/extreme/jobs/{job_id}/release",
        native_deny_path="esf/extreme/jobs/{job_id}/deny",
        base_url=base_url,
        **kwargs,
    )


def build_olivetti_client(base_url: str, **kwargs: Any) -> VendorHttpClient:
    return VendorHttpClient(
        vendor="olivetti",
        protocol="olivetti-connect-http",
        native_handshake_path="olivetti/connect/v1/device",
        native_auth_path="olivetti/connect/v1/auth",
        native_release_path="olivetti/connect/v1/jobs/{job_id}/release",
        native_deny_path="olivetti/connect/v1/jobs/{job_id}/deny",
        base_url=base_url,
        **kwargs,
    )
