"""SDK catalog and activation for embedded printer vendors."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from epms.agents import normalize_vendor

# Vendors with activated SDK adapter modules in this release.
SDK_ACTIVATED_VENDORS = frozenset(
    {
        "kyocera",
        "olivetti",
        "xerox",
        "lexmark",
        "ricoh",
        "konica-minolta",
        "hp",
        "canon",
    }
)

SDK_CATALOG: dict[str, dict[str, Any]] = {
    "kyocera": {
        "platform": "HyPAS",
        "sdk_version": "3.2.0",
        "sdk_artifact": "hypas-application-sdk.jar",
        "sdk_protocol": "HyPAS HTTPS / device servlet",
        "java_package": "com.kyocera.hypas.extreme",
    },
    "olivetti": {
        "platform": "Olivetti Connect / INFOchip",
        "sdk_version": "2.0.1",
        "sdk_artifact": "olivetti-connect-embedded-sdk.jar",
        "sdk_protocol": "Olivetti Connect REST",
        "java_package": "com.olivetti.connect.extreme",
    },
    "xerox": {
        "platform": "EIP",
        "sdk_version": "5.1.0",
        "sdk_artifact": "xerox-eip-sdk.jar",
        "sdk_protocol": "EIP SOAP/HTTP",
        "java_package": "com.xerox.eip.extreme",
    },
    "lexmark": {
        "platform": "eSF",
        "sdk_version": "4.3.0",
        "sdk_artifact": "lexmark-esf-sdk.jar",
        "sdk_protocol": "eSF device services",
        "java_package": "com.lexmark.esf.extreme",
    },
    "ricoh": {
        "platform": "SmartSDK / SOP",
        "sdk_version": "6.0.0",
        "sdk_artifact": "ricoh-smartsdk.jar",
        "sdk_protocol": "SmartSDK JNI bridge",
        "java_package": "com.ricoh.smartsdk.extreme",
    },
    "konica-minolta": {
        "platform": "OpenAPI / i-Option",
        "sdk_version": "7.2.0",
        "sdk_artifact": "km-openapi-sdk.jar",
        "sdk_protocol": "OpenAPI XML/HTTP",
        "java_package": "com.konicaminolta.openapi.extreme",
    },
    "hp": {
        "platform": "OXP / Workpath / FutureSmart",
        "sdk_version": "2.8.0",
        "sdk_artifact": "hp-oxp-sdk.jar",
        "sdk_protocol": "OXP HTTP",
        "java_package": "com.hp.oxp.extreme",
    },
    "canon": {
        "platform": "MEAP",
        "sdk_version": "4.1.0",
        "sdk_artifact": "canon-meap-sdk.jar",
        "sdk_protocol": "MEAP Java",
        "java_package": "com.canon.meap.extreme",
    },
}


@dataclass(frozen=True)
class SdkRuntime:
    vendor: str
    status: str
    version: str
    artifact: str
    protocol: str
    java_package: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "vendor": self.vendor,
            "status": self.status,
            "version": self.version,
            "artifact": self.artifact,
            "protocol": self.protocol,
            "java_package": self.java_package,
        }


def is_sdk_active(vendor: str) -> bool:
    key = normalize_vendor(vendor)
    env_name = f"EPMS_SDK_{key.upper().replace('-', '_')}"
    override = os.environ.get(env_name, os.environ.get("EPMS_SDK_ALL", "")).strip().lower()
    if override in {"0", "false", "off", "disable", "disabled"}:
        return False
    if override in {"1", "true", "on", "active", "live", "enabled"}:
        return True
    return key in SDK_ACTIVATED_VENDORS


def get_sdk_runtime(vendor: str) -> SdkRuntime:
    key = normalize_vendor(vendor)
    meta = SDK_CATALOG.get(key, SDK_CATALOG.get("hp", {}))
    active = is_sdk_active(key)
    return SdkRuntime(
        vendor=key,
        status="active" if active else "disabled",
        version=str(meta.get("sdk_version", "0.0.0")),
        artifact=str(meta.get("sdk_artifact", "generic-sdk.jar")),
        protocol=str(meta.get("sdk_protocol", "gateway")),
        java_package=str(meta.get("java_package", "com.extreme.embedded")),
    )


def list_active_sdks() -> list[dict[str, Any]]:
    return [get_sdk_runtime(vendor).to_dict() for vendor in sorted(SDK_ACTIVATED_VENDORS)]
