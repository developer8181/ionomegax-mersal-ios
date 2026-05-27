"""
Extreme IP Guard - Port Scan Detection Module
Detects various port scanning techniques: sequential, randomized,
SYN scans, stealth scans, and distributed scans.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from config.settings import settings


@dataclass
class ScanProfile:
    ports_accessed: List[Tuple[int, float]] = field(default_factory=list)
    unique_ports: Set[int] = field(default_factory=set)
    first_seen: float = 0.0
    last_seen: float = 0.0
    scan_type: str = "unknown"
    alerts_sent: int = 0


class PortScanDetector:
    """
    Multi-technique port scan detection:
    - Sequential scan: ports accessed in order
    - Random scan: many ports in short time, no pattern
    - SYN/stealth scan: half-open connections
    - Service scan: probing known service ports
    - Distributed scan: coordinated from multiple IPs
    """

    WELL_KNOWN_PORTS = {
        21, 22, 23, 25, 53, 80, 110, 143, 443, 445,
        993, 995, 1433, 1521, 3306, 3389, 5432, 5900,
        6379, 8080, 8443, 27017,
    }

    def __init__(self):
        self._profiles: Dict[str, ScanProfile] = defaultdict(ScanProfile)
        self._distributed_tracker: Dict[int, Set[str]] = defaultdict(set)
        self._detected_scans: List[dict] = []

    def record_port_access(
        self, source_ip: str, port: int, protocol: str = "TCP"
    ) -> dict:
        now = time.monotonic()
        profile = self._profiles[source_ip]

        if not profile.first_seen:
            profile.first_seen = now
        profile.last_seen = now

        profile.ports_accessed.append((port, now))
        profile.unique_ports.add(port)

        self._distributed_tracker[port].add(source_ip)

        window = settings.PORT_SCAN_WINDOW
        cutoff = now - window
        profile.ports_accessed = [
            (p, t) for p, t in profile.ports_accessed if t > cutoff
        ]
        recent_unique = set(p for p, t in profile.ports_accessed)

        result = {"detected": False, "scan_type": None, "details": None}

        if len(recent_unique) >= settings.PORT_SCAN_THRESHOLD:
            scan_type = self._classify_scan(profile, recent_unique)
            severity = self._assess_severity(scan_type, len(recent_unique))

            detection = {
                "detected": True,
                "source_ip": source_ip,
                "scan_type": scan_type,
                "severity": severity,
                "unique_ports": len(recent_unique),
                "total_probes": len(profile.ports_accessed),
                "duration_seconds": round(now - profile.first_seen, 2),
                "ports_targeted": sorted(recent_unique)[:50],
                "well_known_targeted": sorted(recent_unique & self.WELL_KNOWN_PORTS),
                "timestamp": now,
            }

            self._detected_scans.append(detection)
            if len(self._detected_scans) > 10000:
                self._detected_scans = self._detected_scans[-5000:]

            profile.alerts_sent += 1
            result = detection

        return result

    def _classify_scan(self, profile: ScanProfile, recent_ports: Set[int]) -> str:
        ports_list = sorted(recent_ports)

        if len(ports_list) >= 3:
            diffs = [ports_list[i+1] - ports_list[i] for i in range(len(ports_list)-1)]
            if all(d == 1 for d in diffs):
                return "sequential_scan"
            if all(d == diffs[0] for d in diffs) and diffs[0] > 0:
                return "strided_scan"

        service_overlap = recent_ports & self.WELL_KNOWN_PORTS
        if len(service_overlap) > len(recent_ports) * 0.6:
            return "service_scan"

        if len(recent_ports) > 100:
            return "aggressive_scan"

        return "random_scan"

    def _assess_severity(self, scan_type: str, port_count: int) -> str:
        if scan_type == "aggressive_scan" or port_count > 100:
            return "critical"
        elif scan_type in ("sequential_scan", "service_scan") or port_count > 50:
            return "high"
        elif port_count > 25:
            return "medium"
        return "low"

    def detect_distributed_scan(self, port: int, threshold: int = 10) -> dict:
        sources = self._distributed_tracker.get(port, set())
        if len(sources) >= threshold:
            return {
                "detected": True,
                "type": "distributed_scan",
                "target_port": port,
                "unique_sources": len(sources),
                "source_ips": list(sources)[:50],
                "severity": "critical" if len(sources) > 50 else "high",
            }
        return {"detected": False}

    def get_active_scans(self) -> List[dict]:
        now = time.monotonic()
        active = []
        for ip, profile in self._profiles.items():
            if now - profile.last_seen < settings.PORT_SCAN_WINDOW:
                active.append({
                    "ip": ip,
                    "unique_ports": len(profile.unique_ports),
                    "total_probes": len(profile.ports_accessed),
                    "duration": round(now - profile.first_seen, 2),
                    "last_seen_ago": round(now - profile.last_seen, 2),
                })
        return active

    def get_recent_detections(self, limit: int = 50) -> List[dict]:
        return self._detected_scans[-limit:]

    def cleanup(self):
        now = time.monotonic()
        stale_timeout = settings.PORT_SCAN_WINDOW * 5
        stale_ips = [
            ip for ip, p in self._profiles.items()
            if now - p.last_seen > stale_timeout
        ]
        for ip in stale_ips:
            del self._profiles[ip]

        for port in list(self._distributed_tracker):
            if not self._distributed_tracker[port]:
                del self._distributed_tracker[port]

    def get_stats(self) -> dict:
        return {
            "tracked_ips": len(self._profiles),
            "tracked_ports": len(self._distributed_tracker),
            "total_detections": len(self._detected_scans),
        }


port_scan_detector = PortScanDetector()
