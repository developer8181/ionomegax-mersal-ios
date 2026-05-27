"""Embedded printer controller adapters."""

from __future__ import annotations

from epms.agents import normalize_vendor

from .base import EmbeddedAdapter
from .canon import CanonMEAPAdapter
from .gateway import GatewayAdapter
from .hp import HPAdapter

_ADAPTERS: dict[str, type[EmbeddedAdapter]] = {
    "hp": HPAdapter,
    "canon": CanonMEAPAdapter,
    "ricoh": HPAdapter,
    "xerox": HPAdapter,
    "sharp": HPAdapter,
    "konica-minolta": HPAdapter,
    "toshiba": HPAdapter,
    "kyocera": HPAdapter,
    "lexmark": HPAdapter,
    "epson": HPAdapter,
    "generic": GatewayAdapter,
}


def get_adapter(*, vendor: str, server_url: str, agent_token: str = "", device_address: str = "") -> EmbeddedAdapter:
    key = normalize_vendor(vendor)
    if key == "canon":
        return CanonMEAPAdapter(server_url=server_url, agent_token=agent_token, device_address=device_address)
    if key != "generic" and key in _ADAPTERS and _ADAPTERS[key] is HPAdapter:
        return HPAdapter(
            vendor=key,
            server_url=server_url,
            agent_token=agent_token,
            device_address=device_address,
        )
    adapter_cls = _ADAPTERS.get(key, GatewayAdapter)
    return adapter_cls(server_url=server_url, agent_token=agent_token, device_address=device_address)
