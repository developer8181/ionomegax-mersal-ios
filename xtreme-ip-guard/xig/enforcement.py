# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""Local policy enforcement on managed endpoints."""

from __future__ import annotations

import json
import os
import platform
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class EnforcementState:
    isolated: bool = False
    blocked_channels: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    quarantine_dir: str = ""
    last_action: str = ""
    last_reason: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "isolated": self.isolated,
            "blocked_channels": self.blocked_channels,
            "warnings": self.warnings[-20:],
            "quarantine_dir": self.quarantine_dir,
            "last_action": self.last_action,
            "last_reason": self.last_reason,
            "updated_at": self.updated_at,
        }


class LocalEnforcer:
    """Applies server decisions on the endpoint using OS-native hooks where possible."""

    def __init__(self, state_dir: Path | None = None):
        root = state_dir or Path(os.environ.get("MERSAL_STATE_DIR", Path.home() / ".mersal-guard"))
        self.state_dir = root
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / "enforcement.json"
        self.quarantine_dir = self.state_dir / "quarantine"
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> EnforcementState:
        if not self.state_file.is_file():
            return EnforcementState(quarantine_dir=str(self.quarantine_dir))
        try:
            payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return EnforcementState(quarantine_dir=str(self.quarantine_dir))
        return EnforcementState(
            isolated=bool(payload.get("isolated")),
            blocked_channels=list(payload.get("blocked_channels", [])),
            warnings=list(payload.get("warnings", [])),
            quarantine_dir=str(payload.get("quarantine_dir", str(self.quarantine_dir))),
            last_action=str(payload.get("last_action", "")),
            last_reason=str(payload.get("last_reason", "")),
            updated_at=str(payload.get("updated_at", "")),
        )

    def save(self, state: EnforcementState) -> EnforcementState:
        state.updated_at = datetime.now(timezone.utc).isoformat()
        state.quarantine_dir = str(self.quarantine_dir)
        self.state_file.write_text(json.dumps(state.to_dict(), indent=2), encoding="utf-8")
        return state

    def apply(self, action: str, *, reason: str, channel: str = "", resource: str = "") -> EnforcementState:
        state = self.load()
        state.last_action = action
        state.last_reason = reason
        message = f"{action}: {reason}"
        if resource:
            message += f" ({resource})"

        if action == "isolate_endpoint":
            state.isolated = True
            state.blocked_channels = sorted(set(state.blocked_channels) | {"removable_media", "network_upload", "unsanctioned_cloud"})
            self._platform_isolate(True)
        elif action in {"block", "quarantine"}:
            if channel and channel not in state.blocked_channels:
                state.blocked_channels.append(channel)
            if action == "quarantine" and resource:
                self._quarantine_marker(resource, reason)
        elif action == "warn":
            state.warnings.append(message)
        elif action == "allow":
            if state.isolated:
                state.warnings.append("allow received while endpoint marked isolated — still enforcing isolation")
        elif action == "monitor":
            state.warnings.append(f"monitoring: {message}")

        return self.save(state)

    def restore(self) -> EnforcementState:
        state = EnforcementState(quarantine_dir=str(self.quarantine_dir))
        self._platform_isolate(False)
        return self.save(state)

    def should_block_channel(self, channel: str) -> bool:
        state = self.load()
        if state.isolated:
            return True
        return channel in state.blocked_channels

    def _quarantine_marker(self, resource: str, reason: str) -> None:
        marker = self.quarantine_dir / f"hold_{abs(hash(resource)) % 10_000_000}.json"
        marker.write_text(
            json.dumps({"resource": resource, "reason": reason, "platform": platform.system()}, indent=2),
            encoding="utf-8",
        )

    def _platform_isolate(self, isolated: bool) -> None:
        family = platform.system().lower()
        flag_file = self.state_dir / "ISOLATED"
        if isolated:
            flag_file.write_text("isolated\n", encoding="utf-8")
            if family == "linux":
                self._linux_isolation_hint()
        elif flag_file.exists():
            flag_file.unlink(missing_ok=True)

    def _linux_isolation_hint(self) -> None:
        rules = self.state_dir / "99-mersal-guard-usb.rules"
        if rules.exists():
            return
        rules.write_text(
            '# Ionomegax Mersal Guard — optional USB block when endpoint is isolated\n'
            '# Install with root: cp 99-mersal-guard-usb.rules /etc/udev/rules.d/ && udevadm control --reload\n'
            'ACTION=="add", SUBSYSTEM=="usb", ENV{ID_USB_DRIVER}=="usb-storage", RUN+="/bin/logger MersalGuard USB attach while isolated"\n',
            encoding="utf-8",
        )
