"""Shared platform abstractions for Mersal endpoint agents."""

from __future__ import annotations

import getpass
import os
import platform
import socket
import sys
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class PlatformProfile:
    """Normalized host identity reported with every heartbeat."""

    platform_id: str
    family: str
    machine: str
    hostname: str
    os_name: str
    os_version: str
    architecture: str
    username: str
    python_version: str
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    security_features: dict[str, Any] = field(default_factory=dict)
    sensors: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SensorEvent:
    """Defensive telemetry discovered on the endpoint."""

    event_type: str
    channel: str
    resource: str
    classification: str = "internal"
    destination: str = ""
    process: str = ""
    severity: int = 15
    behavior_flags: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)


def collect_profile() -> PlatformProfile:
    family = _normalize_family(platform.system())
    builder = _PROFILE_BUILDERS.get(family, _generic_profile)
    return builder()


def collect_sensor_events() -> list[SensorEvent]:
    family = _normalize_family(platform.system())
    collector = _SENSOR_COLLECTORS.get(family, _generic_sensors)
    return collector()


def _normalize_family(system_name: str) -> str:
    lowered = system_name.lower()
    if lowered == "darwin":
        return "darwin"
    if lowered == "windows":
        return "windows"
    if lowered == "linux":
        return "linux"
    return lowered


def _generic_profile() -> PlatformProfile:
    return PlatformProfile(
        platform_id=_normalize_family(platform.system()),
        family=_normalize_family(platform.system()),
        machine=platform.machine(),
        hostname=socket.gethostname(),
        os_name=platform.platform(),
        os_version=platform.version(),
        architecture=platform.machine(),
        username=_safe_username(),
        python_version=sys.version.split()[0],
        capabilities=("heartbeat", "telemetry"),
        security_features={},
        sensors={},
    )


def _safe_username() -> str:
    try:
        return getpass.getuser()
    except Exception:  # noqa: BLE001 - defensive agent must not crash on identity lookup
        return os.environ.get("USER", os.environ.get("USERNAME", "unknown"))


_PROFILE_BUILDERS: dict[str, Callable[[], PlatformProfile]] = {}
_SENSOR_COLLECTORS: dict[str, Callable[[], list[SensorEvent]]] = {}


def _generic_sensors() -> list[SensorEvent]:
    return []


def register_platform(
    family: str,
    *,
    profile_builder: Callable[[], PlatformProfile],
    sensor_collector: Callable[[], list[SensorEvent]],
) -> None:
    _PROFILE_BUILDERS[family] = profile_builder
    _SENSOR_COLLECTORS[family] = sensor_collector
