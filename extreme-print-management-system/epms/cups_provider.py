"""CUPS integration helpers for the Extreme Print Provider."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .print_provider import SpoolEvent

LPSTAT_JOB_RE = re.compile(r"^(?P<job_ref>\S+)\s+(?P<user>\S+)\s+(?P<size>\d+)\s+(?P<submitted>.+)$")


@dataclass(frozen=True)
class CupsPrinter:
    queue_name: str
    status: str
    enabled: bool
    raw: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CupsJob:
    queue_name: str
    job_ref: str
    username: str
    size_bytes: int
    submitted_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SeenJobStore:
    """Small JSON state file used to avoid resubmitting the same CUPS job."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def read(self) -> set[str]:
        if not self.path.exists():
            return set()
        with self.path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return set(data.get("seen_jobs", []))

    def write(self, seen_jobs: set[str]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump({"seen_jobs": sorted(seen_jobs)}, handle, indent=2)
        tmp_path.replace(self.path)


def run_lpstat(*args: str) -> str:
    try:
        result = subprocess.run(
            ["lpstat", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("CUPS lpstat command was not found on this system") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or "lpstat failed"
        raise RuntimeError(message) from exc
    return result.stdout


def discover_cups_printers(lpstat_output: str | None = None) -> list[CupsPrinter]:
    output = lpstat_output if lpstat_output is not None else run_lpstat("-p")
    printers: list[CupsPrinter] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line.startswith("printer "):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        queue_name = parts[1]
        enabled = "disabled" not in line.lower()
        if " is idle" in line:
            status = "idle"
        elif " now printing" in line:
            status = "printing"
        elif " disabled" in line.lower():
            status = "disabled"
        else:
            status = "unknown"
        printers.append(CupsPrinter(queue_name=queue_name, status=status, enabled=enabled, raw=line))
    return printers


def list_cups_jobs(lpstat_output: str | None = None) -> list[CupsJob]:
    output = lpstat_output if lpstat_output is not None else run_lpstat("-W", "all", "-o")
    jobs: list[CupsJob] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = LPSTAT_JOB_RE.match(line)
        if not match:
            continue
        job_ref = match.group("job_ref")
        queue_name = job_ref.rsplit("-", 1)[0]
        jobs.append(
            CupsJob(
                queue_name=queue_name,
                job_ref=job_ref,
                username=match.group("user"),
                size_bytes=int(match.group("size")),
                submitted_at=match.group("submitted"),
            )
        )
    return jobs


def cups_job_to_spool_event(
    job: CupsJob,
    *,
    user_map: dict[str, int],
    printer_map: dict[str, int],
    default_pages: int,
    account: str,
    agent_id: str,
) -> SpoolEvent:
    if job.username not in user_map:
        raise ValueError(f"CUPS user is not mapped to an Extreme user: {job.username}")
    if job.queue_name not in printer_map:
        raise ValueError(f"CUPS queue is not mapped to an Extreme printer: {job.queue_name}")
    return SpoolEvent(
        user_id=int(user_map[job.username]),
        printer_id=int(printer_map[job.queue_name]),
        document_name=f"CUPS job {job.job_ref}",
        pages=default_pages,
        copies=1,
        color=False,
        duplex=False,
        account=account,
        source="print-provider",
        agent_id=agent_id,
        spool_id=job.job_ref,
    )
