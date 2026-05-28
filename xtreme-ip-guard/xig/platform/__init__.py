# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""Cross-platform endpoint telemetry for Mersal Guard."""

from . import _bootstrap  # noqa: F401 - register linux/windows/darwin handlers
from .base import PlatformProfile, SensorEvent, collect_profile, collect_sensor_events

__all__ = [
    "PlatformProfile",
    "SensorEvent",
    "collect_profile",
    "collect_sensor_events",
]
