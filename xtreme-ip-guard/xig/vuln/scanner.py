"""Vulnerability assessment — port/service correlation and host misconfiguration checks."""

from __future__ import annotations

import re
import socket
import subprocess
from typing import TYPE_CHECKING, Any

from .cve_catalog import LEGACY_OS_MARKERS, MISCONFIG_CHECKS, PORT_CVE_RULES

if TYPE_CHECKING:
    from ..storage import Database


class VulnerabilityScanner:
    """Daily-capable scanner: agent telemetry + optional local port probe."""

    def __init__(self, database: "Database") -> None:
        self.db = database

    def scan_all_endpoints(self, *, scope: str = "daily") -> dict[str, Any]:
        scan = self.db.start_vuln_scan(scope=scope)
        scan_id = int(scan["scan_id"])
        findings: list[dict[str, Any]] = []

        for endpoint in self.db.list_endpoints():
            findings.extend(self.scan_endpoint(endpoint, scan_id=scan_id))

        finished = self.db.finish_vuln_scan(scan_id, findings_count=len(findings))
        return {**finished, "findings": findings[:50]}

    def scan_endpoint(self, endpoint: dict[str, Any], *, scan_id: int | None = None) -> list[dict[str, Any]]:
        endpoint_id = str(endpoint["endpoint_id"])
        metadata = endpoint.get("metadata") or {}
        vuln_probe = metadata.get("vuln_probe") or metadata.get("sensors") or {}
        if isinstance(vuln_probe, dict) and "listening_ports" in vuln_probe:
            ports = vuln_probe.get("listening_ports") or []
        else:
            sensors = metadata.get("sensors") if isinstance(metadata.get("sensors"), dict) else {}
            ports = sensors.get("listening_ports") or vuln_probe.get("open_ports") or []

        open_ports = self._normalize_ports(ports)
        if not open_ports and endpoint_id in {"endpoint-demo-001", endpoint_id}:
            open_ports = self._probe_local_ports()

        recorded: list[dict[str, Any]] = []
        os_name = str(endpoint.get("os_name", "")).lower()

        for rule in PORT_CVE_RULES:
            if rule["port"] in open_ports:
                recorded.append(
                    self.db.record_vuln_finding(
                        scan_id=scan_id,
                        endpoint_id=endpoint_id,
                        cve_id=str(rule["cve_id"]),
                        title=str(rule["title"]),
                        severity=float(rule["cvss"]),
                        port=int(rule["port"]),
                        service=str(rule["service"]),
                        remediation=str(rule["remediation"]),
                        status="open",
                    )
                )

        security = metadata.get("security_features") or vuln_probe.get("security_features") or {}
        if security.get("disk_encryption") is False:
            check = MISCONFIG_CHECKS[0]
            recorded.append(
                self.db.record_vuln_finding(
                    scan_id=scan_id,
                    endpoint_id=endpoint_id,
                    cve_id=str(check["check_id"]),
                    title=str(check["title"]),
                    severity=float(check["cvss"]),
                    port=0,
                    service="misconfig",
                    remediation=str(check["remediation"]),
                    status="open",
                )
            )

        if any(marker in os_name for marker in LEGACY_OS_MARKERS):
            check = MISCONFIG_CHECKS[1]
            recorded.append(
                self.db.record_vuln_finding(
                    scan_id=scan_id,
                    endpoint_id=endpoint_id,
                    cve_id=str(check["check_id"]),
                    title=str(check["title"]),
                    severity=float(check["cvss"]),
                    port=0,
                    service="os",
                    remediation=str(check["remediation"]),
                    status="open",
                )
            )

        risky = {21, 23, 445, 3389, 5900, 6379, 27017}
        exposed = risky.intersection(open_ports)
        if exposed:
            check = MISCONFIG_CHECKS[2]
            recorded.append(
                self.db.record_vuln_finding(
                    scan_id=scan_id,
                    endpoint_id=endpoint_id,
                    cve_id=str(check["check_id"]),
                    title=f"{check['title']}: {sorted(exposed)}",
                    severity=float(check["cvss"]),
                    port=int(next(iter(exposed))),
                    service="network",
                    remediation=str(check["remediation"]),
                    status="open",
                )
            )

        return recorded

    @staticmethod
    def _normalize_ports(ports: Any) -> set[int]:
        found: set[int] = set()
        if not isinstance(ports, list):
            return found
        for item in ports:
            if isinstance(item, int):
                found.add(item)
                continue
            if isinstance(item, dict):
                local = str(item.get("local", item.get("port", "")))
                match = re.search(r":(\d+)$", local)
                if match:
                    found.add(int(match.group(1)))
        return found

    @staticmethod
    def _probe_local_ports() -> set[int]:
        """Quick local listen check when agent telemetry is missing."""
        ports: set[int] = set()
        try:
            output = subprocess.run(
                ["ss", "-lnt"],
                check=False,
                capture_output=True,
                text=True,
                timeout=4,
            )
            for line in output.stdout.splitlines()[1:20]:
                match = re.search(r":(\d+)\s", line)
                if match:
                    ports.add(int(match.group(1)))
        except (OSError, subprocess.SubprocessError):
            for port in (22, 80, 443, 445, 3389, 8080):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                        sock.settimeout(0.2)
                        if sock.connect_ex(("127.0.0.1", port)) == 0:
                            ports.add(port)
                except OSError:
                    continue
        return ports
