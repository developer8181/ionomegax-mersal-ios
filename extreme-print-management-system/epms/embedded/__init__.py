"""Embedded printer controller adapters with activated vendor SDKs."""

from __future__ import annotations

from epms.agents import normalize_vendor

from .base import EmbeddedAdapter
from .canon import CanonMEAPAdapter
from .gateway import GatewayAdapter
from .hp import HPAdapter
from .konica import KonicaMinoltaOpenAPIAdapter
from .kyocera import KyoceraHyPASAdapter
from .lexmark import LexmarkESFAdapter
from .olivetti import OlivettiConnectAdapter
from .ricoh import RicohSmartSDKAdapter
from .sdk_registry import get_sdk_runtime, is_sdk_active, list_active_sdks
from .xerox import XeroxEIPAdapter

_ADAPTERS: dict[str, type[EmbeddedAdapter]] = {
    "hp": HPAdapter,
    "canon": CanonMEAPAdapter,
    "kyocera": KyoceraHyPASAdapter,
    "olivetti": OlivettiConnectAdapter,
    "xerox": XeroxEIPAdapter,
    "lexmark": LexmarkESFAdapter,
    "ricoh": RicohSmartSDKAdapter,
    "konica-minolta": KonicaMinoltaOpenAPIAdapter,
    "generic": GatewayAdapter,
}


def get_adapter(*, vendor: str, server_url: str, agent_token: str = "", device_address: str = "") -> EmbeddedAdapter:
    key = normalize_vendor(vendor)
    adapter_cls = _ADAPTERS.get(key, GatewayAdapter)
    return adapter_cls(server_url=server_url, agent_token=agent_token, device_address=device_address)
