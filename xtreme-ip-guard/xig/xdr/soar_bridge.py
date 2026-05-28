# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""XDR → SOAR closed loop — execute recommended actions from correlated findings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..soar.engine import SoarEngine
    from ..storage import Database


class XdrSoarBridge:
    def __init__(self, database: "Database", soar: "SoarEngine") -> None:
        self.db = database
        self.soar = soar

    def execute_for_findings(self, *, limit: int = 10) -> dict[str, Any]:
        executed = 0
        skipped = 0
        runs: list[dict[str, Any]] = []
        for finding in self.db.list_xdr_findings(limit=limit):
            action = str(finding.get("recommended_action", "investigate"))
            endpoint_id = str(finding.get("endpoint_id", ""))
            if action == "isolate_endpoint" and endpoint_id not in {"", "network", "unknown"}:
                run = self.soar._run(  # noqa: SLF001 — orchestration bridge
                    "SOAR-HIGH-RISK-ISOLATE",
                    endpoint_id,
                    finding,
                    risk_score=int(finding.get("severity", 90)),
                    source="xdr",
                )
                if run:
                    runs.append(run)
                    executed += 1
                else:
                    skipped += 1
            else:
                skipped += 1
        return {"executed": executed, "skipped": skipped, "runs": runs}
