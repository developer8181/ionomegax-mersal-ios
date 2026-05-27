"""Built-in Extreme device servlet — MFD integration without Java on the printer.

Implements the same contract as sdk/java/extreme-servlet so Printer Controllers can point
device_address to the Extreme Server URL.
"""

from __future__ import annotations

import secrets
from typing import Any

from .storage import Database

PREFIX = "/extreme/sdk/v1"
_DEVICE_SESSIONS: dict[str, str] = {}


def _session_for(username: str) -> str:
    token = secrets.token_urlsafe(24)
    _DEVICE_SESSIONS[token] = username
    return token


def _validate_session(username: str, session_token: str) -> bool:
    return _DEVICE_SESSIONS.get(session_token) == username


def handle_get(path: str, database: Database) -> dict[str, Any] | None:
    if path == f"{PREFIX}/health":
        return {
            "ok": True,
            "product": "Extreme Print Management System",
            "api": "v1",
            "servlet": "python-embedded",
            "users": len(database.list_users()),
            "printers": len(database.list_printers()),
        }
    return None


def handle_post(
    path: str,
    database: Database,
    payload: dict[str, Any],
    *,
    anonymize: bool,
) -> dict[str, Any] | None:
    if path == f"{PREFIX}/auth":
        username = str(payload.get("username", "")).strip()
        users = database.list_users()
        if not any(row["username"] == username for row in users):
            raise ValueError(f"unknown user: {username}")
        token = _session_for(username)
        return {"ok": True, "username": username, "session_token": token, "servlet": "python-embedded"}

    if "/jobs/" in path and path.endswith("/release"):
        job_id = int(path.rsplit("/", 2)[-2])
        username = str(payload.get("username", ""))
        token = str(payload.get("session_token", ""))
        if token and not _validate_session(username, token):
            raise ValueError("invalid device session")
        job = database.release_job_as_user(job_id, username=username)
        return {"ok": True, "job": job}

    if "/jobs/" in path and path.endswith("/deny"):
        job_id = int(path.rsplit("/", 2)[-2])
        username = str(payload.get("username", "")).strip()
        token = str(payload.get("session_token", ""))
        if token and not _validate_session(username, token):
            raise ValueError("invalid device session")
        held_ids = {int(row["id"]) for row in database.list_held_jobs_for_user(username=username)}
        if job_id not in held_ids:
            raise ValueError("job does not belong to this user or is not held")
        job = database.deny_job(job_id, reason=str(payload.get("reason", "Denied at device")))
        return {"ok": True, "job": job}

    return None
