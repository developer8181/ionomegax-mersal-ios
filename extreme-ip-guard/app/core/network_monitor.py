"""
Extreme IP Guard - Real-Time Network Monitor
Async network monitoring with pattern detection.
"""

import asyncio
import psutil
import time
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass, field


@dataclass
class NetworkSnapshot:
    timestamp: float
    bytes_sent: int
    bytes_recv: int
    packets_sent: int
    packets_recv: int
    connections_active: int
    connections_established: int
    connections_listening: int
    cpu_percent: float
    memory_percent: float
    bandwidth_in_mbps: float = 0.0
    bandwidth_out_mbps: float = 0.0


@dataclass
class ConnectionInfo:
    local_addr: str
    local_port: int
    remote_addr: str
    remote_port: int
    status: str
    pid: Optional[int]
    process_name: str = "unknown"


class NetworkMonitor:
    """Real-time network state monitoring with anomaly detection."""

    def __init__(self, history_size: int = 300):
        self.history: deque = deque(maxlen=history_size)
        self.alerts: deque = deque(maxlen=1000)
        self._previous_counters = None
        self._previous_time = None
        self._running = False
        self._baseline_bandwidth_in = 0.0
        self._baseline_bandwidth_out = 0.0
        self._anomaly_threshold = 3.0

    async def capture_snapshot(self) -> NetworkSnapshot:
        net = psutil.net_io_counters()
        conns = psutil.net_connections(kind='inet')
        cpu = psutil.cpu_percent(interval=0)
        mem = psutil.virtual_memory().percent

        established = sum(1 for c in conns if c.status == 'ESTABLISHED')
        listening = sum(1 for c in conns if c.status == 'LISTEN')
        active = len(conns)

        now = time.time()
        bw_in = 0.0
        bw_out = 0.0

        if self._previous_counters and self._previous_time:
            dt = now - self._previous_time
            if dt > 0:
                bw_in = (net.bytes_recv - self._previous_counters.bytes_recv) * 8 / dt / 1_000_000
                bw_out = (net.bytes_sent - self._previous_counters.bytes_sent) * 8 / dt / 1_000_000

        self._previous_counters = net
        self._previous_time = now

        snapshot = NetworkSnapshot(
            timestamp=now,
            bytes_sent=net.bytes_sent,
            bytes_recv=net.bytes_recv,
            packets_sent=net.packets_sent,
            packets_recv=net.packets_recv,
            connections_active=active,
            connections_established=established,
            connections_listening=listening,
            cpu_percent=cpu,
            memory_percent=mem,
            bandwidth_in_mbps=round(bw_in, 3),
            bandwidth_out_mbps=round(bw_out, 3),
        )

        self.history.append(snapshot)
        return snapshot

    def get_active_connections(self) -> List[ConnectionInfo]:
        connections = []
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == 'ESTABLISHED' and conn.raddr:
                    pname = "unknown"
                    if conn.pid:
                        try:
                            pname = psutil.Process(conn.pid).name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    connections.append(ConnectionInfo(
                        local_addr=conn.laddr.ip if conn.laddr else "",
                        local_port=conn.laddr.port if conn.laddr else 0,
                        remote_addr=conn.raddr.ip if conn.raddr else "",
                        remote_port=conn.raddr.port if conn.raddr else 0,
                        status=conn.status,
                        pid=conn.pid,
                        process_name=pname,
                    ))
        except (psutil.AccessDenied, PermissionError):
            pass
        return connections

    def get_system_stats(self) -> Dict:
        cpu_freq = psutil.cpu_freq()
        disk = psutil.disk_usage('/')
        boot_time = psutil.boot_time()

        return {
            "cpu": {
                "percent": psutil.cpu_percent(interval=0),
                "count": psutil.cpu_count(),
                "freq_mhz": cpu_freq.current if cpu_freq else 0,
            },
            "memory": {
                "total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
                "percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "percent": round(disk.percent, 1),
            },
            "network": {
                "bytes_sent": psutil.net_io_counters().bytes_sent,
                "bytes_recv": psutil.net_io_counters().bytes_recv,
            },
            "uptime_hours": round((time.time() - boot_time) / 3600, 2),
        }

    def get_bandwidth_history(self, points: int = 60) -> Dict:
        snapshots = list(self.history)[-points:]
        return {
            "timestamps": [s.timestamp for s in snapshots],
            "bandwidth_in": [s.bandwidth_in_mbps for s in snapshots],
            "bandwidth_out": [s.bandwidth_out_mbps for s in snapshots],
            "connections": [s.connections_active for s in snapshots],
            "cpu": [s.cpu_percent for s in snapshots],
            "memory": [s.memory_percent for s in snapshots],
        }

    def detect_anomalies(self) -> List[Dict]:
        if len(self.history) < 10:
            return []

        anomalies = []
        recent = list(self.history)[-10:]
        latest = recent[-1]

        avg_bw_in = sum(s.bandwidth_in_mbps for s in recent[:-1]) / max(len(recent) - 1, 1)
        avg_bw_out = sum(s.bandwidth_out_mbps for s in recent[:-1]) / max(len(recent) - 1, 1)
        avg_conns = sum(s.connections_active for s in recent[:-1]) / max(len(recent) - 1, 1)

        if avg_bw_in > 0 and latest.bandwidth_in_mbps > avg_bw_in * self._anomaly_threshold:
            anomalies.append({
                "type": "bandwidth_spike_in",
                "severity": "high",
                "message": f"Inbound bandwidth spike: {latest.bandwidth_in_mbps:.2f} Mbps (avg: {avg_bw_in:.2f})",
                "timestamp": latest.timestamp,
            })

        if avg_bw_out > 0 and latest.bandwidth_out_mbps > avg_bw_out * self._anomaly_threshold:
            anomalies.append({
                "type": "bandwidth_spike_out",
                "severity": "high",
                "message": f"Outbound bandwidth spike: {latest.bandwidth_out_mbps:.2f} Mbps (avg: {avg_bw_out:.2f})",
                "timestamp": latest.timestamp,
            })

        if avg_conns > 0 and latest.connections_active > avg_conns * 2:
            anomalies.append({
                "type": "connection_surge",
                "severity": "medium",
                "message": f"Connection surge detected: {latest.connections_active} (avg: {avg_conns:.0f})",
                "timestamp": latest.timestamp,
            })

        if latest.cpu_percent > 90:
            anomalies.append({
                "type": "high_cpu",
                "severity": "warning",
                "message": f"CPU usage critical: {latest.cpu_percent}%",
                "timestamp": latest.timestamp,
            })

        if latest.memory_percent > 90:
            anomalies.append({
                "type": "high_memory",
                "severity": "warning",
                "message": f"Memory usage critical: {latest.memory_percent}%",
                "timestamp": latest.timestamp,
            })

        return anomalies


network_monitor = NetworkMonitor()
