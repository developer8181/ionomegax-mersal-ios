#!/usr/bin/env python3
# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
"""Start server, capture all Command Center screens (AR + EN), exit."""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MERSAL_DB", str(ROOT / "data" / "demo-ui.sqlite3"))
os.environ["MERSAL_DAILY_INTERVAL_SECONDS"] = "999999999"
os.environ["MERSAL_NO_SCHEDULER"] = "1"
os.environ["MERSAL_KEV_FEED_URL"] = ""
os.environ["MERSAL_BOOTSTRAP"] = "0"
os.environ["MERSAL_DEMO_UI"] = "1"

OUT = ROOT / "docs" / "screenshots"
PORT = 8090
BASE = f"http://127.0.0.1:{PORT}"


def wait_server(timeout: float = 25.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE}/api/system/about", timeout=2) as resp:
                if resp.status == 200:
                    return
        except OSError:
            time.sleep(0.4)
    raise RuntimeError("server did not start")


def shot(name: str, query: str, *, wait_ms: int = 10000) -> bool:
    OUT.mkdir(parents=True, exist_ok=True)
    target = f"{BASE}/console/{query}"
    dest = OUT / name
    profile = f"/tmp/mersal-chrome-{os.getpid()}-{name.replace('/', '-')}"
    cmd = [
        os.environ.get("CHROME_BIN", "google-chrome"),
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        f"--user-data-dir={profile}",
        "--window-size=1440,900",
        "--force-device-scale-factor=1",
        f"--virtual-time-budget={min(wait_ms, 8000)}",
        f"--screenshot={dest}",
        target,
    ]
    ok = False
    try:
        subprocess.run(cmd, check=False, timeout=35, capture_output=True)
    except subprocess.TimeoutExpired:
        subprocess.run(["pkill", "-f", profile], check=False)
    if dest.is_file() and dest.stat().st_size > 8000:
        print(f"  OK {name} ({dest.stat().st_size // 1024} KB)")
        ok = True
    else:
        print(f"  FAIL {name}")
    subprocess.run(["rm", "-rf", profile], check=False)
    return ok


def main() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "seed_demo_ui.py")], check=True, cwd=ROOT)
    from xig.server import run

    thread = Thread(target=run, kwargs={"host": "127.0.0.1", "port": PORT}, daemon=True)
    thread.start()
    wait_server()
    time.sleep(2)

    shots = [
        # Arabic — all major sections
        ("01-overview-ar.png", "?lang=ar&view=overview&capture=1", 15000),
        ("02-readiness-ar.png", "?lang=ar&view=readiness&capture=1", 15000),
        ("03-enterprise-ar.png", "?lang=ar&view=enterprise&capture=1", 18000),
        ("04-xdr-ar.png", "?lang=ar&view=xdr&capture=1", 18000),
        ("05-fabric-ar.png", "?lang=ar&view=fabric&capture=1", 18000),
        ("06-ai-cortex-ar.png", "?lang=ar&view=ai&capture=1", 18000),
        ("07-endpoints-ar.png", "?lang=ar&view=endpoints&capture=1", 15000),
        ("08-events-ar.png", "?lang=ar&view=events&capture=1", 15000),
        ("09-policies-ar.png", "?lang=ar&view=policies&capture=1", 15000),
        ("10-audit-ar.png", "?lang=ar&view=audit&capture=1", 15000),
        ("11-about-ar.png", "?lang=ar&openAbout=1&capture=1", 18000),
        # English
        ("12-overview-en.png", "?lang=en&view=overview&capture=1", 15000),
        ("13-readiness-en.png", "?lang=en&view=readiness&capture=1", 15000),
        ("14-enterprise-en.png", "?lang=en&view=enterprise&capture=1", 18000),
        ("15-xdr-en.png", "?lang=en&view=xdr&capture=1", 18000),
        ("16-fabric-en.png", "?lang=en&view=fabric&capture=1", 18000),
        ("17-ai-cortex-en.png", "?lang=en&view=ai&capture=1", 18000),
        ("18-endpoints-en.png", "?lang=en&view=endpoints&capture=1", 15000),
        ("19-events-en.png", "?lang=en&view=events&capture=1", 15000),
        ("20-about-en.png", "?lang=en&openAbout=1&capture=1", 18000),
    ]

    passed = 0
    for name, query, budget in shots:
        if shot(name, query, wait_ms=budget):
            passed += 1

    print(f"\nCaptured {passed}/{len(shots)} → {OUT}")
    if passed < len(shots) // 2:
        sys.exit(1)


if __name__ == "__main__":
    main()
