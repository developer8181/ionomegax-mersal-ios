"""Minimal IPP 2.0 client helpers for generic network printers."""

from __future__ import annotations

import re
import struct
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

# IPP tags (subset)
TAG_OPERATION_ATTRIBUTES = 0x01
TAG_END_OF_ATTRIBUTES = 0x03
TAG_INTEGER = 0x21
TAG_ENUM = 0x23
TAG_URI = 0x45
TAG_CHARSET = 0x47
TAG_KEYWORD = 0x44

VAL_CHARSET_UTF8 = b"utf-8\x00"
VAL_LANGUAGE_EN = b"en-us\x00"

OP_GET_JOBS = 0x000A
GROUP_OPERATION = 0x01


@dataclass(frozen=True)
class IppJob:
    job_id: int
    job_name: str
    state: str
    printer_uri: str


def _attribute(name: bytes, value_tag: int, value: bytes) -> bytes:
    return bytes([value_tag, len(name)]) + name + struct.pack(">H", len(value)) + value


def build_get_jobs_request(*, printer_uri: str) -> bytes:
    """Build a binary IPP Get-Jobs request."""
    version = b"\x02\x00"
    operation = struct.pack(">H", OP_GET_JOBS)
    request_id = struct.pack(">I", 1)
    attributes = b"".join(
        [
            bytes([TAG_OPERATION_ATTRIBUTES]),
            _attribute(b"attributes-charset", TAG_CHARSET, VAL_CHARSET_UTF8),
            _attribute(b"attributes-natural-language", TAG_CHARSET, VAL_LANGUAGE_EN),
            _attribute(b"printer-uri", TAG_URI, printer_uri.encode("utf-8") + b"\x00"),
            _attribute(b"requested-attributes", TAG_KEYWORD, b"job-id\x00"),
            _attribute(b"requested-attributes", TAG_KEYWORD, b"job-name\x00"),
            _attribute(b"requested-attributes", TAG_KEYWORD, b"job-state\x00"),
            bytes([TAG_END_OF_ATTRIBUTES]),
        ]
    )
    return version + operation + request_id + attributes


def parse_get_jobs_response(payload: bytes) -> list[IppJob]:
    """Parse job-id / job-name / job-state tuples from a simplified IPP response."""
    text = payload.decode("utf-8", errors="ignore")
    ids = [int(value) for value in re.findall(r"job-id[^\d]*(\d+)", text)]
    names = re.findall(r"job-name[^\w]*([\w .\-]+)", text)
    states = re.findall(r"job-state[^\d]*(\d+)", text)
    state_map = {"3": "pending", "4": "processing", "5": "stopped", "6": "canceled", "7": "aborted", "9": "completed"}
    jobs: list[IppJob] = []
    for index, job_id in enumerate(ids):
        name = names[index] if index < len(names) else f"Job {job_id}"
        raw_state = states[index] if index < len(states) else "4"
        jobs.append(
            IppJob(
                job_id=job_id,
                job_name=name.strip(),
                state=state_map.get(raw_state, "unknown"),
                printer_uri="",
            )
        )
    return jobs


def ipp_get_jobs(printer_uri: str, *, timeout: int = 10) -> list[IppJob]:
    """Send Get-Jobs to an IPP endpoint."""
    body = build_get_jobs_request(printer_uri=printer_uri)
    request = urllib.request.Request(
        printer_uri,
        data=body,
        headers={"Content-Type": "application/ipp"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return parse_get_jobs_response(response.read())
    except urllib.error.URLError as exc:
        raise RuntimeError(f"IPP request failed: {exc.reason}") from exc
