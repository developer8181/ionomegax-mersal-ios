# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""Online behavioral baselines — learns normal risk per endpoint signal."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class OnlineStats:
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def update(self, value: float) -> None:
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.m2 += delta * delta2

    @property
    def variance(self) -> float:
        if self.count < 2:
            return 0.0
        return self.m2 / (self.count - 1)

    @property
    def stddev(self) -> float:
        return math.sqrt(max(self.variance, 1e-6))

    def z_score(self, value: float) -> float:
        if self.count < 5:
            return 0.0
        return (value - self.mean) / self.stddev

    def to_dict(self) -> dict[str, float | int]:
        return {"count": self.count, "mean": round(self.mean, 3), "stddev": round(self.stddev, 3)}

    @classmethod
    def from_row(cls, count: int, mean: float, m2: float) -> "OnlineStats":
        stats = cls()
        stats.count = count
        stats.mean = mean
        stats.m2 = m2
        return stats
