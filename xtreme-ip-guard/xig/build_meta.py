# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Build metadata for reproducible integrated releases."""

from __future__ import annotations

import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .config import is_production, tls_enabled


def build_info() -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    commit = _git_revision(root)
    return {
        "product": "Mersal Global Security Fabric",
        "platform": "mersal-guard",
        "version": __version__,
        "git_commit": commit,
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "python": platform.python_version(),
        "host_os": platform.platform(),
        "production_mode": is_production(),
        "tls_enabled": tls_enabled(),
        "components": [
            "command_center",
            "endpoint_agent",
            "neural_cortex",
            "siem",
            "edr",
            "incident_response",
            "compliance",
            "network_security",
            "vulnerability_scanner",
            "cisa_kev_feed",
            "soar",
            "security_scheduler",
        ],
    }


def _git_revision(root: Path) -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=root,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            .strip()
            or "unknown"
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
