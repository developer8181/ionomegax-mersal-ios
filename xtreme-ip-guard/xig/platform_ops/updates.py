# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Signed update manifests — agents and platform verify integrity before apply."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class UpdateChannel:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def _signing_key(self) -> bytes:
        from ..config import enterprise_strict

        key = os.environ.get("MERSAL_UPDATE_SIGNING_KEY", "").strip()
        if not key and not enterprise_strict():
            key = os.environ.get("MERSAL_SIGNING_SECRET", "") or os.environ.get("MERSAL_API_TOKEN", "")
        if not key:
            raise ValueError("MERSAL_UPDATE_SIGNING_KEY required for enterprise supply chain")
        return key.encode()

    def publish_manifest(
        self,
        *,
        component: str,
        version: str,
        artifact_url: str,
        checksum_sha256: str,
    ) -> dict[str, Any]:
        manifest_id = f"upd-{secrets.token_hex(8)}"
        body = json.dumps(
            {
                "manifest_id": manifest_id,
                "component": component,
                "version": version,
                "artifact_url": artifact_url,
                "checksum_sha256": checksum_sha256,
            },
            sort_keys=True,
        )
        signature = hmac.new(self._signing_key(), body.encode(), hashlib.sha256).hexdigest()
        return self.db.save_update_manifest(
            manifest_id=manifest_id,
            component=component,
            version=version,
            artifact_url=artifact_url,
            checksum_sha256=checksum_sha256,
            signature=signature,
        )

    def verify_manifest(self, manifest: dict[str, Any]) -> bool:
        body = json.dumps(
            {
                "manifest_id": manifest["manifest_id"],
                "component": manifest["component"],
                "version": manifest["version"],
                "artifact_url": manifest["artifact_url"],
                "checksum_sha256": manifest["checksum_sha256"],
            },
            sort_keys=True,
        )
        expected = hmac.new(self._signing_key(), body.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, str(manifest.get("signature", "")))

    def latest_for(self, component: str) -> dict[str, Any] | None:
        return self.db.latest_update_manifest(component)
