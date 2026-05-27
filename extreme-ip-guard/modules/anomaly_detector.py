"""
Extreme IP Guard - Anomaly Detection Engine
Statistical anomaly detection using Z-score analysis, moving averages,
and pattern deviation for identifying unusual network behavior.
"""

import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from config.settings import settings


@dataclass
class MetricStream:
    values: deque = field(default_factory=lambda: deque(maxlen=1000))
    timestamps: deque = field(default_factory=lambda: deque(maxlen=1000))
    mean: float = 0.0
    variance: float = 0.0
    count: int = 0

    def update_stats(self):
        if len(self.values) < 2:
            return
        self.count = len(self.values)
        self.mean = sum(self.values) / self.count
        self.variance = sum((x - self.mean) ** 2 for x in self.values) / self.count

    @property
    def std_dev(self) -> float:
        return math.sqrt(max(0, self.variance))


class AnomalyDetector:
    """
    Detects anomalies across multiple dimensions:
    - Request rate anomalies (sudden spikes/drops)
    - Payload size anomalies
    - Geographic anomalies (impossible travel)
    - Protocol distribution anomalies
    - Temporal anomalies (unusual hours)
    - Behavioral fingerprint deviation
    """

    def __init__(self):
        self._ip_metrics: Dict[str, Dict[str, MetricStream]] = defaultdict(
            lambda: defaultdict(MetricStream)
        )
        self._global_metrics: Dict[str, MetricStream] = defaultdict(MetricStream)
        self._anomalies: List[dict] = []
        self._sensitivity = settings.ANOMALY_SENSITIVITY

    def record_metric(
        self,
        ip: str,
        metric_name: str,
        value: float,
        is_global: bool = False,
    ) -> Optional[dict]:
        now = time.monotonic()

        if is_global:
            stream = self._global_metrics[metric_name]
        else:
            stream = self._ip_metrics[ip][metric_name]

        stream.values.append(value)
        stream.timestamps.append(now)
        stream.update_stats()

        anomaly = self._check_zscore(ip, metric_name, value, stream)
        if anomaly:
            self._anomalies.append(anomaly)
            if len(self._anomalies) > 10000:
                self._anomalies = self._anomalies[-5000:]
        return anomaly

    def _check_zscore(
        self, ip: str, metric_name: str, value: float, stream: MetricStream
    ) -> Optional[dict]:
        if stream.count < 10:
            return None

        std = stream.std_dev
        if std == 0:
            return None

        zscore = abs(value - stream.mean) / std

        if zscore > self._sensitivity:
            severity = self._zscore_to_severity(zscore)
            direction = "above" if value > stream.mean else "below"

            return {
                "type": "statistical_anomaly",
                "ip": ip,
                "metric": metric_name,
                "value": round(value, 4),
                "mean": round(stream.mean, 4),
                "std_dev": round(std, 4),
                "z_score": round(zscore, 4),
                "direction": direction,
                "severity": severity,
                "deviation_pct": round(
                    abs(value - stream.mean) / max(0.001, abs(stream.mean)) * 100, 2
                ),
                "timestamp": time.monotonic(),
            }
        return None

    def _zscore_to_severity(self, zscore: float) -> str:
        if zscore > 5.0:
            return "critical"
        elif zscore > 4.0:
            return "high"
        elif zscore > 3.0:
            return "medium"
        return "low"

    def check_impossible_travel(
        self,
        ip: str,
        lat: float,
        lon: float,
        prev_lat: float,
        prev_lon: float,
        time_delta_seconds: float,
    ) -> Optional[dict]:
        distance_km = self._haversine(lat, lon, prev_lat, prev_lon)
        speed_kmh = (distance_km / max(1, time_delta_seconds)) * 3600

        if speed_kmh > 1000:
            anomaly = {
                "type": "impossible_travel",
                "ip": ip,
                "distance_km": round(distance_km, 2),
                "time_delta_seconds": round(time_delta_seconds, 2),
                "implied_speed_kmh": round(speed_kmh, 2),
                "severity": "high",
                "from_location": {"lat": prev_lat, "lon": prev_lon},
                "to_location": {"lat": lat, "lon": lon},
                "timestamp": time.monotonic(),
            }
            self._anomalies.append(anomaly)
            return anomaly
        return None

    def _haversine(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def check_temporal_anomaly(
        self, ip: str, hour_of_day: int, day_of_week: int
    ) -> Optional[dict]:
        """Flag access at unusual hours based on historical pattern."""
        metric_key = f"hour_{hour_of_day}"
        stream = self._ip_metrics[ip].get(metric_key)
        if not stream or stream.count < 20:
            return None

        if stream.mean < 0.1 and stream.count > 50:
            return {
                "type": "temporal_anomaly",
                "ip": ip,
                "hour": hour_of_day,
                "day_of_week": day_of_week,
                "severity": "medium",
                "description": f"Access at unusual hour ({hour_of_day}:00)",
                "timestamp": time.monotonic(),
            }
        return None

    def get_ip_profile(self, ip: str) -> dict:
        metrics = self._ip_metrics.get(ip, {})
        return {
            "ip": ip,
            "metrics": {
                name: {
                    "mean": round(s.mean, 4),
                    "std_dev": round(s.std_dev, 4),
                    "count": s.count,
                    "latest": round(s.values[-1], 4) if s.values else None,
                }
                for name, s in metrics.items()
            },
        }

    def get_recent_anomalies(self, limit: int = 50) -> List[dict]:
        return self._anomalies[-limit:]

    def get_stats(self) -> dict:
        return {
            "tracked_ips": len(self._ip_metrics),
            "global_metrics": len(self._global_metrics),
            "total_anomalies": len(self._anomalies),
            "sensitivity": self._sensitivity,
        }


anomaly_detector = AnomalyDetector()
