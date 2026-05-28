#!/usr/bin/env python3
# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
"""Ship syslog-style lines to Mersal Log Vault."""

from __future__ import annotations

import json
import os
import sys
import urllib.request


def main() -> None:
    server = os.environ.get("MERSAL_SERVER", "http://127.0.0.1:8090").rstrip("/")
    token = os.environ.get("MERSAL_API_TOKEN", "")
    source = os.environ.get("MERSAL_LOG_SOURCE", "syslog")
    host = os.environ.get("MERSAL_LOG_HOST", "")
    records = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        records.append(
            {
                "source": source,
                "host": host,
                "message": line,
                "severity": 40,
                "raw": line,
            }
        )
    if not records:
        return
    body = json.dumps({"records": records}).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Mersal-Token"] = token
    request = urllib.request.Request(
        f"{server}/api/logs/ingest",
        data=body,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        print(response.read().decode())


if __name__ == "__main__":
    main()
