# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""Linux endpoint sensors using procfs, sysfs, and mount tables."""

from __future__ import annotations

import platform
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

from .base import PlatformProfile, SensorEvent, _safe_username, register_platform
from .vuln_probe import collect_vuln_probe
from ..edr.process_intel import collect_running_processes, suspicious_process_events


def build_linux_profile() -> PlatformProfile:
    security = {
        "selinux": _file_exists("/sys/fs/selinux/enforce"),
        "apparmor": _file_exists("/sys/kernel/security/apparmor"),
        "disk_encryption": _detect_luks(),
    }
    processes = collect_running_processes(limit=25)
    sensors = {
        "mounts": _read_mounts(),
        "removable": _removable_devices(),
        "listening_ports": _listening_ports_sample(),
        "vuln_probe": collect_vuln_probe(security),
        "processes": processes,
        "process_count": len(processes),
    }
    return PlatformProfile(
        platform_id="linux",
        family="linux",
        machine=platform.machine(),
        hostname=socket.gethostname(),
        os_name=platform.platform(),
        os_version=_linux_os_release(),
        architecture=platform.machine(),
        username=_safe_username(),
        python_version=sys.version.split()[0],
        capabilities=(
            "heartbeat",
            "telemetry",
            "mount_monitor",
            "removable_media",
            "process_sample",
            "local_enforcement",
            "vulnerability_probe",
            "edr_process_intel",
        ),
        security_features=security,
        sensors=sensors,
    )


def collect_linux_sensors() -> list[SensorEvent]:
    events: list[SensorEvent] = []
    for device in _removable_devices():
        events.append(
            SensorEvent(
                event_type="device_attached",
                channel="removable_media",
                resource=device.get("node", "unknown"),
                classification="internal",
                destination=device.get("mountpoint", ""),
                severity=20,
                behavior_flags=("new_process",) if device.get("mountpoint") else tuple(),
                metadata=device,
            )
        )
    for mount in _read_mounts():
        if mount.get("fstype") in {"cifs", "nfs", "nfs4", "fuse.sshfs"}:
            events.append(
                SensorEvent(
                    event_type="network_mount",
                    channel="network_upload",
                    resource=mount.get("mountpoint", ""),
                    classification="internal",
                    destination=mount.get("source", ""),
                    severity=18,
                    metadata=mount,
                )
            )
    processes = collect_running_processes(limit=30)
    events.extend(suspicious_process_events(processes))
    return events


def _linux_os_release() -> str:
    path = Path("/etc/os-release")
    if not path.is_file():
        return platform.version()
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"')
    return values.get("PRETTY_NAME", platform.version())


def _read_mounts() -> list[dict[str, str]]:
    mounts: list[dict[str, str]] = []
    try:
        with open("/proc/mounts", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                parts = line.split()
                if len(parts) < 3:
                    continue
                mounts.append({"source": parts[0], "mountpoint": parts[1], "fstype": parts[2]})
    except OSError:
        return mounts
    return mounts[:40]


def _removable_devices() -> list[dict[str, Any]]:
    devices: list[dict[str, Any]] = []
    by_id = Path("/dev/disk/by-id")
    if not by_id.is_dir():
        return devices
    for entry in sorted(by_id.iterdir())[:30]:
        name = entry.name.lower()
        if "usb" not in name and "mmc" not in name:
            continue
        try:
            target = entry.resolve()
        except OSError:
            target = entry
        mountpoint = _mountpoint_for_device(str(target))
        devices.append(
            {
                "id": entry.name,
                "node": str(target),
                "bus": "usb" if "usb" in name else "mmc",
                "mountpoint": mountpoint,
            }
        )
    return devices


def _mountpoint_for_device(node: str) -> str:
    for mount in _read_mounts():
        if mount.get("source") == node:
            return mount["mountpoint"]
    return ""


def _listening_ports_sample() -> list[dict[str, int | str]]:
    ports: list[dict[str, int | str]] = []
    try:
        output = subprocess.run(
            ["ss", "-lnt"],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
        for line in output.stdout.splitlines()[1:6]:
            parts = line.split()
            if len(parts) >= 4:
                ports.append({"local": parts[3], "state": parts[0]})
    except (OSError, subprocess.SubprocessError):
        return ports
    return ports


def _detect_luks() -> bool:
    return Path("/dev/mapper").is_dir() and any(Path("/dev/mapper").glob("*"))


def _file_exists(path: str) -> bool:
    return Path(path).exists()


register_platform("linux", profile_builder=build_linux_profile, sensor_collector=collect_linux_sensors)
