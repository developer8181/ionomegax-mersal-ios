"""Windows endpoint sensors via WMI and PowerShell (no extra dependencies)."""

from __future__ import annotations

import json
import platform
import socket
import subprocess
import sys
from typing import Any

from .base import PlatformProfile, SensorEvent, _safe_username, register_platform


def build_windows_profile() -> PlatformProfile:
    sensors = {
        "volumes": _powershell_json(
            "Get-Volume | Select-Object DriveLetter,FileSystemLabel,Size,SizeRemaining | ConvertTo-Json -Compress"
        ),
        "removable": _powershell_json(
            "Get-CimInstance Win32_LogicalDisk -Filter \"DriveType=2\" | "
            "Select-Object DeviceID,VolumeName,FileSystem,Size | ConvertTo-Json -Compress"
        ),
    }
    security = {
        "bitlocker": _powershell_json(
            "Get-BitLockerVolume -ErrorAction SilentlyContinue | "
            "Select-Object MountPoint,VolumeStatus,ProtectionStatus | ConvertTo-Json -Compress"
        ),
        "defender": _powershell_json(
            "Get-MpComputerStatus -ErrorAction SilentlyContinue | "
            "Select-Object AMServiceEnabled,RealTimeProtectionEnabled | ConvertTo-Json -Compress"
        ),
    }
    return PlatformProfile(
        platform_id="windows",
        family="windows",
        machine=platform.machine(),
        hostname=socket.gethostname(),
        os_name=platform.platform(),
        os_version=platform.version(),
        architecture=platform.machine(),
        username=_safe_username(),
        python_version=sys.version.split()[0],
        capabilities=(
            "heartbeat",
            "telemetry",
            "removable_media",
            "volume_monitor",
            "local_enforcement",
            "powershell_bridge",
        ),
        security_features=security,
        sensors=sensors,
    )


def collect_windows_sensors() -> list[SensorEvent]:
    events: list[SensorEvent] = []
    removable = _powershell_json(
        "Get-CimInstance Win32_LogicalDisk -Filter \"DriveType=2\" | "
        "Select-Object DeviceID,VolumeName | ConvertTo-Json -Compress"
    )
    disks = removable if isinstance(removable, list) else ([removable] if removable else [])
    for disk in disks:
        if not isinstance(disk, dict):
            continue
        device = str(disk.get("DeviceID", "removable"))
        events.append(
            SensorEvent(
                event_type="device_attached",
                channel="removable_media",
                resource=device,
                classification="internal",
                destination=str(disk.get("VolumeName", "")),
                severity=20,
                metadata=disk,
            )
        )
    return events


def _powershell_json(script: str) -> Any:
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=12,
        )
        if completed.returncode != 0 or not completed.stdout.strip():
            return []
        return json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return []


register_platform("windows", profile_builder=build_windows_profile, sensor_collector=collect_windows_sensors)
