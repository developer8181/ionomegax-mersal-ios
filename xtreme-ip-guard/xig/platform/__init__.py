"""Cross-platform endpoint telemetry for Mersal Guard."""

from . import _bootstrap  # noqa: F401 - register linux/windows/darwin handlers
from .base import PlatformProfile, SensorEvent, collect_profile, collect_sensor_events

__all__ = [
    "PlatformProfile",
    "SensorEvent",
    "collect_profile",
    "collect_sensor_events",
]
