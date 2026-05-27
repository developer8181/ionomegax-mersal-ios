"""HTTP helpers for embedded device SDK clients (stdlib only)."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from typing import Any
from xml.etree import ElementTree as ET


def http_request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    timeout: int = 20,
    verify_tls: bool = True,
) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    context = None if verify_tls else ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            response_headers = {key.lower(): value for key, value in response.headers.items()}
            return response.status, response_headers, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, {key.lower(): value for key, value in exc.headers.items()}, exc.read()
    except urllib.error.URLError as exc:
        raise RuntimeError(f"device unreachable: {exc.reason}") from exc


def post_json(url: str, payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json; charset=utf-8", "Accept": "application/json"}
    status, _, raw = http_request(url, method="POST", headers=headers, body=body, **kwargs)
    text = raw.decode("utf-8", errors="replace")
    if status >= 400:
        raise RuntimeError(f"device HTTP {status}: {text[:500]}")
    if not text.strip():
        return {"ok": True, "status": status}
    return json.loads(text)


def post_xml(url: str, xml_body: str, soap_action: str = "", **kwargs: Any) -> ET.Element:
    headers = {"Content-Type": "text/xml; charset=utf-8"}
    if soap_action:
        headers["SOAPAction"] = soap_action
    status, _, raw = http_request(url, method="POST", headers=headers, body=xml_body.encode("utf-8"), **kwargs)
    text = raw.decode("utf-8", errors="replace")
    if status >= 400:
        raise RuntimeError(f"device HTTP {status}: {text[:500]}")
    return ET.fromstring(text)


def join_url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")
