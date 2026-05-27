"""Registry mapping vendors to device SDK HTTP clients."""

from __future__ import annotations

from typing import Any, Callable

from epms.agents import normalize_vendor

from .device_client import DeviceClient
from .vendor_impl import (
    build_canon_client,
    build_hp_client,
    build_konica_client,
    build_kyocera_client,
    build_lexmark_client,
    build_olivetti_client,
    build_ricoh_client,
    build_xerox_client,
)

_BUILDERS: dict[str, Callable[..., DeviceClient]] = {
    "hp": build_hp_client,
    "canon": build_canon_client,
    "ricoh": build_ricoh_client,
    "xerox": build_xerox_client,
    "konica-minolta": build_konica_client,
    "kyocera": build_kyocera_client,
    "lexmark": build_lexmark_client,
    "olivetti": build_olivetti_client,
}

_PROTOCOLS: dict[str, str] = {
    "hp": "hp-oxp-http",
    "canon": "canon-meap-http",
    "ricoh": "ricoh-smartsdk-http",
    "xerox": "xerox-eip-http",
    "konica-minolta": "km-openapi-xml",
    "kyocera": "kyocera-hypas-http",
    "lexmark": "lexmark-esf-http",
    "olivetti": "olivetti-connect-http",
}


def get_device_client(vendor: str, base_url: str, **kwargs: Any) -> DeviceClient:
    key = normalize_vendor(vendor)
    builder = _BUILDERS.get(key)
    if builder is None:
        raise ValueError(f"no device SDK client for vendor: {vendor}")
    return builder(base_url, **kwargs)


def list_device_clients() -> list[dict[str, str]]:
    return [
        {"vendor": vendor, "protocol": _PROTOCOLS[vendor], "java_module": f"sdk/java/{vendor}"}
        for vendor in sorted(_BUILDERS)
    ]
