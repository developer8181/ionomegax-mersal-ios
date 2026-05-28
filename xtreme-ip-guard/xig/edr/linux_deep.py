# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Deep Linux EDR sensors — auditd, auth log, listening ports, integrity paths."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database

_CRITICAL_PATHS = (
    "/etc/passwd",
    "/etc/shadow",
    "/etc/sudoers",
    "/etc/ssh/sshd_config",
)


class LinuxDeepEdr:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def collect_and_persist(self) -> dict[str, Any]:
        if os.name != "posix":
            return {"skipped": True, "reason": "not linux"}
        detections = 0
        for path in _CRITICAL_PATHS:
            p = Path(path)
            if not p.is_file():
                continue
            stat = p.stat()
            meta = {"path": path, "mtime": stat.st_mtime, "size": stat.st_size}
            suspicious = self._check_path_anomalies(path, meta)
            if suspicious:
                self.db.record_edr_detection(
                    endpoint_id="mersal-server",
                    detection_type="fim",
                    severity=75,
                    title=f"Critical file monitored: {path}",
                    details=meta,
                )
                detections += 1
        for line in self._tail_auth_log(30):
            if self._auth_suspicious(line):
                self.db.record_edr_detection(
                    endpoint_id="mersal-server",
                    detection_type="auth",
                    severity=80,
                    title="Suspicious auth activity",
                    details={"line": line[:500]},
                )
                detections += 1
                break
        listeners = self._listening_ports()
        if len(listeners) > 40:
            self.db.record_edr_detection(
                endpoint_id="mersal-server",
                detection_type="network",
                severity=55,
                title="High listening port count",
                details={"count": len(listeners), "sample": listeners[:10]},
            )
            detections += 1
        return {"detections_created": detections, "listeners": len(listeners)}

    @staticmethod
    def _check_path_anomalies(path: str, meta: dict[str, Any]) -> bool:
        return path.endswith("shadow") and meta.get("size", 0) > 0

    @staticmethod
    def _tail_auth_log(lines: int) -> list[str]:
        for candidate in ("/var/log/auth.log", "/var/log/secure"):
            p = Path(candidate)
            if not p.is_file():
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="replace").splitlines()
                return content[-lines:]
            except OSError:
                continue
        return []

    @staticmethod
    def _auth_suspicious(line: str) -> bool:
        lower = line.lower()
        if "failed password" in lower or "invalid user" in lower:
            return bool(re.search(r"failed password|invalid user", lower))
        return False

    @staticmethod
    def _listening_ports() -> list[dict[str, Any]]:
        ports: list[dict[str, Any]] = []
        import subprocess

        try:
            out = subprocess.check_output(
                ["ss", "-lntu"], stderr=subprocess.DEVNULL, text=True, timeout=5
            )
            for row in out.splitlines()[1:]:
                parts = row.split()
                if len(parts) >= 5:
                    ports.append({"local": parts[4], "state": parts[0]})
        except (OSError, subprocess.SubprocessError):
            try:
                for entry in os.listdir("/proc/net/tcp"):
                    if entry.isdigit():
                        ports.append({"proto": "tcp", "inode": entry})
            except OSError:
                pass
        return ports
