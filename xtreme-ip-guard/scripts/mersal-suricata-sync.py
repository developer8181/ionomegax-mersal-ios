#!/usr/bin/env python3
# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
"""Push Suricata eve.json alerts to Mersal Command Center."""

from __future__ import annotations

import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from xig.siem.suricata import parse_eve_line  # noqa: E402


def main() -> None:
    eve_path = os.environ.get("MERSAL_SURICATA_EVE", "/var/log/suricata/eve.json")
    server = os.environ.get("MERSAL_SERVER", "http://127.0.0.1:8090").rstrip("/")
    token = os.environ.get("MERSAL_API_TOKEN", "")
    alerts: list[dict] = []
    try:
        with open(eve_path, encoding="utf-8", errors="replace") as handle:
            for line in handle.readlines()[-200:]:
                parsed = parse_eve_line(line)
                if parsed:
                    alerts.append(parsed)
    except OSError as exc:
        print(f"Cannot read {eve_path}: {exc}")
        sys.exit(1)

    if not alerts:
        print("No alerts to send")
        return

    body = json.dumps({"alerts": alerts}).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Mersal-Token"] = token
    request = urllib.request.Request(
        f"{server}/api/suricata/ingest",
        data=body,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        print(response.read().decode())


if __name__ == "__main__":
    main()
