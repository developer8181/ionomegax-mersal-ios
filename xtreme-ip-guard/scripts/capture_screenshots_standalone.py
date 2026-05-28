#!/usr/bin/env python3
"""Start server, capture screenshots, exit — self-contained."""

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

OUT = ROOT / "docs" / "screenshots"
PORT = 8090
BASE = f"http://127.0.0.1:{PORT}"


def wait_server(timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE}/api/system/about", timeout=2) as resp:
                if resp.status == 200:
                    return
        except OSError:
            time.sleep(0.4)
    raise RuntimeError("server did not start")


def shot(name: str, query: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    target = f"{BASE}/console/{query}"
    dest = OUT / name
    profile = f"/tmp/mersal-chrome-{os.getpid()}-{name}"
    cmd = [
        os.environ.get("CHROME_BIN", "google-chrome"),
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--user-data-dir={profile}",
        "--window-size=1440,920",
        "--virtual-time-budget=8000",
        f"--screenshot={dest}",
        target,
    ]
    try:
        subprocess.run(cmd, check=False, timeout=45)
    except subprocess.TimeoutExpired:
        subprocess.run(["pkill", "-f", f"user-data-dir={profile}"], check=False)
    if dest.is_file() and dest.stat().st_size > 1000:
        print(f"  OK {name} ({dest.stat().st_size} bytes)")
    else:
        print(f"  FAIL {name}")


def main() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "seed_demo_ui.py")], check=True, cwd=ROOT)
    from xig.server import run

    thread = Thread(target=run, kwargs={"host": "127.0.0.1", "port": PORT}, daemon=True)
    thread.start()
    wait_server()
    time.sleep(1.5)

    shots = [
        ("01-command-center-overview-ar.png", "?lang=ar&view=overview"),
        ("02-global-fabric-ar.png", "?lang=ar&view=fabric"),
        ("03-neural-cortex-ar.png", "?lang=ar&view=ai"),
        ("04-command-center-en.png", "?lang=en&view=overview"),
        ("05-endpoints-threats-ar.png", "?lang=ar&view=events"),
        ("06-about-system-ar.png", "?lang=ar&openAbout=1"),
    ]
    for name, query in shots:
        shot(name, query)
    print(f"Done → {OUT}")


if __name__ == "__main__":
    main()
