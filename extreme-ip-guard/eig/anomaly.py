"""UEBA-style behavioral anomaly scoring (prototype, no ML dependencies)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class BehaviorBaseline:
    """Rolling baseline for a user or endpoint entity."""

    event_counts: dict[str, int]
    hour_histogram: list[int]
    last_updated: str


def _parse_hour(timestamp: str) -> int:
    try:
        normalized = timestamp.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).hour
    except ValueError:
        return datetime.utcnow().hour


class AnomalyEngine:
    """Detect deviations from learned baselines using lightweight statistics."""

    def __init__(self) -> None:
        self._baselines: dict[str, BehaviorBaseline] = {}

    def record(self, entity_id: str, *, category: str, timestamp: str) -> None:
        baseline = self._baselines.get(entity_id)
        if baseline is None:
            baseline = BehaviorBaseline(
                event_counts=defaultdict(int),
                hour_histogram=[0] * 24,
                last_updated=timestamp,
            )
            self._baselines[entity_id] = baseline
        baseline.event_counts[category] = baseline.event_counts.get(category, 0) + 1
        baseline.hour_histogram[_parse_hour(timestamp)] += 1
        baseline.last_updated = timestamp

    def score(self, entity_id: str, *, category: str, timestamp: str) -> dict[str, Any]:
        """Return anomaly score 0–100 and human-readable signals."""
        baseline = self._baselines.get(entity_id)
        if baseline is None:
            return {"score": 0, "signals": ["no_baseline_yet"], "is_anomalous": False}

        total = sum(baseline.event_counts.values()) or 1
        category_share = baseline.event_counts.get(category, 0) / total
        hour = _parse_hour(timestamp)
        hour_events = baseline.hour_histogram[hour]
        hour_total = sum(baseline.hour_histogram) or 1
        hour_share = hour_events / hour_total

        signals: list[str] = []
        score = 0

        # Rare category for this entity
        if category_share < 0.05 and total > 10:
            score += 35
            signals.append("rare_event_category")

        # Activity outside typical hours (<2% of history at this hour)
        if hour_share < 0.02 and hour_total > 5:
            score += 30
            signals.append("off_hours_activity")

        # Burst: many events in same category recently
        if baseline.event_counts.get(category, 0) > max(20, total * 0.5):
            score += 25
            signals.append("category_burst")

        score = min(100, score)
        return {
            "score": score,
            "signals": signals or ["within_baseline"],
            "is_anomalous": score >= 40,
        }
