"""Optional Java SDK bridge launcher (when vendor JARs are installed)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

SDK_ROOT = Path(__file__).resolve().parents[2] / "sdk"
JAR_DIR = SDK_ROOT / "jars"


def jar_path_for_vendor(vendor: str) -> Path | None:
    key = vendor.replace("-", "")
    patterns = [f"{vendor}-bridge.jar", f"{key}-bridge.jar", f"{vendor}-sdk.jar"]
    for name in patterns:
        candidate = JAR_DIR / name
        if candidate.exists():
            return candidate
    return None


def invoke_java_bridge(
    vendor: str,
    operation: str,
    *,
    username: str = "",
    job_id: int = 0,
    device_url: str = "",
) -> dict:
    """Run prebuilt Java bridge JAR if present."""
    jar = jar_path_for_vendor(vendor)
    if jar is None:
        raise FileNotFoundError(
            f"No Java bridge JAR for {vendor}. Build sdk/java/{vendor} and copy to sdk/jars/"
        )
    cmd = [
        os.environ.get("EPMS_JAVA", "java"),
        "-jar",
        str(jar),
        operation,
        "--vendor",
        vendor,
        "--username",
        username,
        "--job-id",
        str(job_id),
        "--device-url",
        device_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "java bridge failed")
    return json.loads(result.stdout or "{}")
