"""Risk prediction and breach probability estimation."""

from __future__ import annotations

import math
from typing import Sequence


def exponential_moving_average(values: Sequence[float], alpha: float = 0.35) -> float:
    if not values:
        return 0.0
    ema = values[0]
    for value in values[1:]:
        ema = alpha * value + (1 - alpha) * ema
    return ema


def predict_risk_trend(recent_risks: Sequence[float], *, horizon_hours: int = 24) -> dict[str, float]:
    """Simple trend extrapolation from recent risk scores (defensive heuristic)."""
    if not recent_risks:
        return {"predicted_risk": 25.0, "breach_probability": 0.05, "trend_slope": 0.0}

    ema = exponential_moving_average(list(recent_risks))
    if len(recent_risks) >= 3:
        slope = (recent_risks[0] - recent_risks[-1]) / max(len(recent_risks) - 1, 1)
    else:
        slope = 0.0

    hours_factor = min(horizon_hours / 24.0, 2.0)
    predicted = max(0.0, min(100.0, ema + slope * hours_factor * 4))
    breach_probability = 1.0 / (1.0 + math.exp(-(predicted - 55) / 8.0))
    return {
        "predicted_risk": round(predicted, 2),
        "breach_probability": round(breach_probability, 4),
        "trend_slope": round(slope, 3),
    }
