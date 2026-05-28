# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""SOAR engine — executes playbooks on security triggers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..core import PolicyRule
from .playbooks import DEFAULT_PLAYBOOKS, playbook_config

if TYPE_CHECKING:
    from ..storage import Database


class SoarEngine:
    def __init__(self, database: "Database") -> None:
        self.db = database
        self.db.ensure_soar_playbooks()

    def on_event_ingested(self, event_row: dict[str, Any]) -> list[dict[str, Any]]:
        runs: list[dict[str, Any]] = []
        metadata = event_row.get("metadata") or {}
        ai_meta = metadata.get("ai") or {}
        risk = int(event_row.get("risk_score", 0))
        endpoint_id = str(event_row["endpoint_id"])

        if ai_meta.get("ai_escalated"):
            runs.append(self._run("SOAR-AI-EXFIL", endpoint_id, event_row, risk_score=risk))

        if ai_meta.get("ioc_hits"):
            runs.append(self._run("SOAR-IOC-BLOCK", endpoint_id, event_row, ioc=ai_meta["ioc_hits"][0]))

        if risk >= 90:
            runs.append(self._run("SOAR-HIGH-RISK-ISOLATE", endpoint_id, event_row, risk_score=risk))

        return [run for run in runs if run]

    def on_vuln_finding(self, finding: dict[str, Any]) -> dict[str, Any] | None:
        if float(finding.get("severity", 0)) < 9.0:
            return None
        endpoint_id = str(finding["endpoint_id"])
        return self._run(
            "SOAR-CRITICAL-VULN",
            endpoint_id,
            finding,
            cve_id=finding.get("cve_id"),
            severity=finding.get("severity"),
        )

    def _run(self, playbook_id: str, endpoint_id: str, trigger_ref: dict[str, Any], **ctx: Any) -> dict[str, Any]:
        playbook = next((p for p in DEFAULT_PLAYBOOKS if p.playbook_id == playbook_id), None)
        if playbook is None or not playbook.enabled:
            return {}

        config = playbook_config(playbook_id)
        actions: list[str] = []

        if playbook_id == "SOAR-CRITICAL-VULN":
            self.db.set_endpoint_isolation(endpoint_id, True)
            actions.append("isolate_endpoint")

        elif playbook_id == "SOAR-AI-EXFIL":
            if int(ctx.get("risk_score", 0)) >= int(config.get("min_risk", 70)):
                self.db.set_endpoint_isolation(endpoint_id, True)
                actions.append("quarantine_via_isolate")

        elif playbook_id == "SOAR-HIGH-RISK-ISOLATE":
            if int(ctx.get("risk_score", 0)) >= int(config.get("min_risk", 90)):
                self.db.set_endpoint_isolation(endpoint_id, True)
                actions.append("isolate_endpoint")

        elif playbook_id == "SOAR-IOC-BLOCK":
            ioc = ctx.get("ioc") or {}
            indicator = str(ioc.get("indicator", "unknown"))
            rule_id = f"SOAR-BLOCK-{indicator[:24].upper().replace('.', '-')}"
            try:
                self.db.create_policy(
                    PolicyRule(
                        rule_id=rule_id,
                        name=f"SOAR: Block IOC {indicator}",
                        action="block",
                        destination_contains=indicator,
                        reason=f"Auto-created by SOAR after IOC match: {indicator}",
                    )
                )
                actions.append(f"policy:{rule_id}")
            except Exception:  # noqa: BLE001 - policy may already exist
                actions.append(f"policy_exists:{rule_id}")

        return self.db.record_soar_run(
            playbook_id=playbook_id,
            endpoint_id=endpoint_id,
            trigger_ref=trigger_ref,
            actions=actions,
            status="completed" if actions else "skipped",
        )
