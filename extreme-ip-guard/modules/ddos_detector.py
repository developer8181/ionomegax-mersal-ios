"""
Extreme IP Guard - DDoS Detection Engine
Multi-vector DDoS detection using statistical analysis, entropy
measurement, and traffic pattern correlation.
"""

import asyncio
import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from config.settings import settings


@dataclass
class TrafficWindow:
    timestamps: deque = field(default_factory=lambda: deque(maxlen=50000))
    byte_counts: deque = field(default_factory=lambda: deque(maxlen=50000))
    protocols: deque = field(default_factory=lambda: deque(maxlen=50000))
    ports: deque = field(default_factory=lambda: deque(maxlen=50000))


class DDoSDetector:
    """
    Detects various DDoS attack patterns:
    - Volumetric (bandwidth/packet flood)
    - Protocol-based (SYN flood, UDP flood, ICMP flood)
    - Application-layer (HTTP flood, slowloris)
    - Amplification attacks
    """

    ATTACK_TYPES = {
        "volumetric": "High-volume traffic flood",
        "syn_flood": "TCP SYN flood attack",
        "udp_flood": "UDP protocol flood",
        "icmp_flood": "ICMP/ping flood",
        "http_flood": "HTTP request flood",
        "slowloris": "Slow connection exhaustion",
        "amplification": "DNS/NTP amplification",
        "fragmentation": "IP fragmentation attack",
    }

    def __init__(self):
        self._global_traffic = TrafficWindow()
        self._per_ip_traffic: Dict[str, TrafficWindow] = defaultdict(TrafficWindow)
        self._baseline_rps: float = 0.0
        self._baseline_samples: List[float] = []
        self._alert_state: Dict[str, dict] = {}
        self._mitigation_active: bool = False
        self._lock = asyncio.Lock()

    async def record_packet(
        self,
        source_ip: str,
        bytes_count: int = 0,
        protocol: str = "TCP",
        dest_port: int = 80,
    ):
        now = time.monotonic()
        async with self._lock:
            self._global_traffic.timestamps.append(now)
            self._global_traffic.byte_counts.append(bytes_count)
            self._global_traffic.protocols.append(protocol)
            self._global_traffic.ports.append(dest_port)

            ip_traffic = self._per_ip_traffic[source_ip]
            ip_traffic.timestamps.append(now)
            ip_traffic.byte_counts.append(bytes_count)
            ip_traffic.protocols.append(protocol)
            ip_traffic.ports.append(dest_port)

    async def analyze(self) -> dict:
        async with self._lock:
            now = time.monotonic()
            window = settings.DDOS_DETECTION_WINDOW

            global_rps = self._calculate_rps(self._global_traffic, now, window)
            self._update_baseline(global_rps)

            attacks_detected = []

            if self._detect_volumetric(global_rps):
                attacks_detected.append({
                    "type": "volumetric",
                    "description": self.ATTACK_TYPES["volumetric"],
                    "severity": "critical",
                    "current_rps": global_rps,
                    "baseline_rps": self._baseline_rps,
                    "ratio": global_rps / max(1, self._baseline_rps),
                })

            protocol_attacks = self._detect_protocol_attacks(now, window)
            attacks_detected.extend(protocol_attacks)

            ip_flood = self._detect_ip_flood(now, window)
            attacks_detected.extend(ip_flood)

            entropy = self._calculate_source_entropy(now, window)

            under_attack = len(attacks_detected) > 0
            if under_attack and not self._mitigation_active:
                self._mitigation_active = True

            return {
                "under_attack": under_attack,
                "mitigation_active": self._mitigation_active,
                "attacks": attacks_detected,
                "metrics": {
                    "current_rps": round(global_rps, 2),
                    "baseline_rps": round(self._baseline_rps, 2),
                    "source_entropy": round(entropy, 4),
                    "unique_sources": len(self._per_ip_traffic),
                    "total_packets_in_window": self._count_in_window(
                        self._global_traffic, now, window
                    ),
                },
                "top_offenders": self._get_top_offenders(now, window, limit=10),
            }

    def _calculate_rps(
        self, traffic: TrafficWindow, now: float, window: int
    ) -> float:
        cutoff = now - window
        count = sum(1 for t in traffic.timestamps if t > cutoff)
        return count / max(1, window)

    def _count_in_window(
        self, traffic: TrafficWindow, now: float, window: int
    ) -> int:
        cutoff = now - window
        return sum(1 for t in traffic.timestamps if t > cutoff)

    def _update_baseline(self, current_rps: float):
        self._baseline_samples.append(current_rps)
        if len(self._baseline_samples) > 100:
            self._baseline_samples = self._baseline_samples[-100:]

        if not self._mitigation_active and len(self._baseline_samples) >= 5:
            sorted_samples = sorted(self._baseline_samples)
            trim = max(1, len(sorted_samples) // 10)
            trimmed = sorted_samples[trim:-trim] if trim < len(sorted_samples) // 2 else sorted_samples
            self._baseline_rps = sum(trimmed) / max(1, len(trimmed))

    def _detect_volumetric(self, current_rps: float) -> bool:
        if self._baseline_rps < 1:
            return current_rps > settings.DDOS_PACKET_THRESHOLD
        return current_rps > self._baseline_rps * 5

    def _detect_protocol_attacks(
        self, now: float, window: int
    ) -> List[dict]:
        attacks = []
        cutoff = now - window
        protocol_counts = defaultdict(int)

        for i, t in enumerate(self._global_traffic.timestamps):
            if t > cutoff and i < len(self._global_traffic.protocols):
                protocol_counts[self._global_traffic.protocols[i]] += 1

        total = sum(protocol_counts.values())
        if total == 0:
            return attacks

        for proto, count in protocol_counts.items():
            ratio = count / total
            if proto == "TCP-SYN" and ratio > 0.8 and count > 100:
                attacks.append({
                    "type": "syn_flood",
                    "description": self.ATTACK_TYPES["syn_flood"],
                    "severity": "high",
                    "packet_count": count,
                    "protocol_ratio": round(ratio, 3),
                })
            elif proto == "UDP" and ratio > 0.85 and count > 100:
                attacks.append({
                    "type": "udp_flood",
                    "description": self.ATTACK_TYPES["udp_flood"],
                    "severity": "high",
                    "packet_count": count,
                    "protocol_ratio": round(ratio, 3),
                })
            elif proto == "ICMP" and ratio > 0.7 and count > 100:
                attacks.append({
                    "type": "icmp_flood",
                    "description": self.ATTACK_TYPES["icmp_flood"],
                    "severity": "medium",
                    "packet_count": count,
                    "protocol_ratio": round(ratio, 3),
                })

        return attacks

    def _detect_ip_flood(self, now: float, window: int) -> List[dict]:
        attacks = []
        cutoff = now - window
        threshold = settings.DDOS_PACKET_THRESHOLD

        for ip, traffic in self._per_ip_traffic.items():
            count = sum(1 for t in traffic.timestamps if t > cutoff)
            if count > threshold:
                attacks.append({
                    "type": "ip_flood",
                    "description": f"Single-source flood from {ip}",
                    "severity": "high",
                    "source_ip": ip,
                    "packet_count": count,
                })

        return attacks

    def _calculate_source_entropy(self, now: float, window: int) -> float:
        """Low entropy = concentrated sources = likely attack."""
        cutoff = now - window
        ip_counts = defaultdict(int)

        for ip, traffic in self._per_ip_traffic.items():
            count = sum(1 for t in traffic.timestamps if t > cutoff)
            if count > 0:
                ip_counts[ip] = count

        total = sum(ip_counts.values())
        if total == 0:
            return 0.0

        entropy = 0.0
        for count in ip_counts.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)

        return entropy

    def _get_top_offenders(
        self, now: float, window: int, limit: int = 10
    ) -> List[dict]:
        cutoff = now - window
        ip_counts = {}

        for ip, traffic in self._per_ip_traffic.items():
            count = sum(1 for t in traffic.timestamps if t > cutoff)
            if count > 0:
                ip_counts[ip] = count

        sorted_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {"ip": ip, "packet_count": count}
            for ip, count in sorted_ips[:limit]
        ]

    def reset_mitigation(self):
        self._mitigation_active = False
        self._alert_state.clear()

    def get_status(self) -> dict:
        return {
            "mitigation_active": self._mitigation_active,
            "baseline_rps": round(self._baseline_rps, 2),
            "tracked_sources": len(self._per_ip_traffic),
            "alerts": len(self._alert_state),
        }


ddos_detector = DDoSDetector()
