"""Windows Print Spooler adapter for the Extreme Print Provider."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from .print_provider import SpoolEvent

# Example `Get-PrintJob` table output (simplified for tests and documentation).
WINDOWS_JOB_LINE = re.compile(
    r"^(?P<job_id>\d+)\s+(?P<user>\S+)\s+(?P<document>.+?)\s+(?P<pages>\d+)\s+(?P<status>\S+)$"
)


@dataclass(frozen=True)
class WindowsPrintJob:
    job_id: str
    username: str
    document_name: str
    pages: int
    status: str
    queue_name: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_print_jobs(output: str, *, queue_name: str) -> list[WindowsPrintJob]:
    jobs: list[WindowsPrintJob] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.lower().startswith("id "):
            continue
        match = WINDOWS_JOB_LINE.match(line)
        if not match:
            continue
        jobs.append(
            WindowsPrintJob(
                job_id=match.group("job_id"),
                username=match.group("user"),
                document_name=match.group("document").strip(),
                pages=int(match.group("pages")),
                status=match.group("status"),
                queue_name=queue_name,
            )
        )
    return jobs


def windows_job_to_spool_event(
    job: WindowsPrintJob,
    *,
    user_map: dict[str, int],
    printer_map: dict[str, int],
    account: str,
    agent_id: str,
) -> SpoolEvent:
    if job.username not in user_map:
        raise ValueError(f"Windows user is not mapped to an Extreme user: {job.username}")
    if job.queue_name not in printer_map:
        raise ValueError(f"Windows queue is not mapped to an Extreme printer: {job.queue_name}")
    return SpoolEvent(
        user_id=int(user_map[job.username]),
        printer_id=int(printer_map[job.queue_name]),
        document_name=job.document_name,
        pages=job.pages,
        copies=1,
        color=False,
        duplex=False,
        account=account,
        source="print-provider",
        agent_id=agent_id,
        spool_id=f"win-{job.queue_name}-{job.job_id}",
    )
