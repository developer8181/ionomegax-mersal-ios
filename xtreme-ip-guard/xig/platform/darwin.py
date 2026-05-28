# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""macOS endpoint sensors via diskutil and sysctl."""

from __future__ import annotations

import platform
import socket
import subprocess
import sys
from typing import Any

from .base import PlatformProfile, SensorEvent, _safe_username, register_platform


def build_darwin_profile() -> PlatformProfile:
    sensors = {
        "volumes": _diskutil_data(),
        "filevault": _filevault_status(),
    }
    return PlatformProfile(
        platform_id="darwin",
        family="darwin",
        machine=platform.machine(),
        hostname=socket.gethostname(),
        os_name=platform.platform(),
        os_version=platform.mac_ver()[0] or platform.version(),
        architecture=platform.machine(),
        username=_safe_username(),
        python_version=sys.version.split()[0],
        capabilities=(
            "heartbeat",
            "telemetry",
            "removable_media",
            "volume_monitor",
            "local_enforcement",
        ),
        security_features={"filevault": sensors.get("filevault", {})},
        sensors=sensors,
    )


def collect_darwin_sensors() -> list[SensorEvent]:
    events: list[SensorEvent] = []
    for volume in _external_volumes():
        events.append(
            SensorEvent(
                event_type="device_attached",
                channel="removable_media",
                resource=volume.get("mount_point", volume.get("volume_name", "external")),
                classification="internal",
                destination=volume.get("protocol", "usb"),
                severity=18,
                metadata=volume,
            )
        )
    return events


def _diskutil_data() -> list[dict[str, str]]:
    try:
        completed = subprocess.run(
            ["diskutil", "list", "-plist"],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
        if completed.returncode != 0:
            return []
        return [{"summary": "diskutil_available", "bytes": str(len(completed.stdout))}]
    except (OSError, subprocess.SubprocessError):
        return []


def _external_volumes() -> list[dict[str, Any]]:
    volumes: list[dict[str, Any]] = []
    try:
        completed = subprocess.run(
            ["diskutil", "list", "-plist"],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
        if "external" in completed.stdout.lower():
            volumes.append({"volume_name": "external-media", "mount_point": "/Volumes", "protocol": "usb"})
    except (OSError, subprocess.SubprocessError):
        return volumes
    return volumes


def _filevault_status() -> dict[str, str]:
    try:
        completed = subprocess.run(
            ["fdesetup", "status"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return {"status": completed.stdout.strip() or completed.stderr.strip()}
    except (OSError, subprocess.SubprocessError):
        return {"status": "unknown"}


register_platform("darwin", profile_builder=build_darwin_profile, sensor_collector=collect_darwin_sensors)
