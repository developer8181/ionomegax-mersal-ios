"""Organization pricing and retention policies."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .core import PrintCostPolicy


def apply_pricing_rules(
    *,
    base: PrintCostPolicy,
    department: str,
    rules: list[dict[str, Any]],
) -> PrintCostPolicy:
    """Apply the first active department rule, if any."""
    department_key = department.strip().lower()
    for rule in rules:
        if not rule.get("is_active", True):
            continue
        if str(rule.get("department", "")).strip().lower() != department_key:
            continue
        bw = int(rule.get("bw_multiplier_percent", 100))
        color = int(rule.get("color_multiplier_percent", 100))
        duplex_override = rule.get("duplex_discount_override")
        bw_page = max(0, int(base.bw_page_cents * bw / 100))
        color_page = max(0, int(base.color_page_cents * color / 100))
        duplex_discount = base.duplex_discount_percent
        if duplex_override is not None:
            duplex_discount = int(duplex_override)
        return PrintCostPolicy(
            bw_page_cents=bw_page,
            color_page_cents=color_page,
            duplex_discount_percent=duplex_discount,
        )
    return base


def anonymize_document_name(name: str, *, job_id: int | None = None) -> str:
    suffix = f" #{job_id}" if job_id is not None else ""
    return f"[document redacted]{suffix}"


def scrub_job_document(job: dict[str, Any], *, enabled: bool) -> dict[str, Any]:
    if not enabled:
        return job
    redacted = dict(job)
    redacted["document_name"] = anonymize_document_name(
        str(job.get("document_name", "")),
        job_id=int(job["id"]) if job.get("id") is not None else None,
    )
    return redacted
