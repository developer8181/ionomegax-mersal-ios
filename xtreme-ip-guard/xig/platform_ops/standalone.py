# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Autonomous operations — daily cycle without external SOC tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..fabric import MersalSecurityFabric
    from ..integrations import SiemForwarder
    from ..storage import Database


class StandaloneController:
    """Runs the full security loop: intel → scan → correlate → SOAR → export → posture."""

    def __init__(self, database: "Database", fabric: "MersalSecurityFabric") -> None:
        self.db = database
        self.fabric = fabric

    def run_autonomous_cycle(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        results["enterprise"] = self.fabric.enterprise.run_enterprise_cycle()
        results["global"] = self.fabric.global_platform.run_global_cycle()
        from ..xdr.engine import XdrEngine
        from ..xdr.soar_bridge import XdrSoarBridge

        results["xdr"] = XdrEngine(self.db).run_correlation()
        results["xdr_soar"] = XdrSoarBridge(self.db, self.fabric.soar).execute_for_findings()
        from ..integrations.siem_forwarder import SiemForwarder

        results["siem_export"] = SiemForwarder(self.db).forward_batch()
        from ..edr.linux_deep import LinuxDeepEdr

        results["edr_deep"] = LinuxDeepEdr(self.db).collect_and_persist()
        from ..integrations.suricata_manager import SuricataManager

        results["suricata"] = SuricataManager(self.db, self.fabric).sync_if_available()
        from ..edr.ebpf_probe import collect_ebpf_snapshot

        results["ebpf"] = collect_ebpf_snapshot()
        from ..platform_ops.updates import UpdateChannel

        agent_manifest = UpdateChannel(self.db).latest_for("agent")
        results["updates"] = {"agent": agent_manifest}
        results["posture"] = self.db.latest_security_posture()
        self.db.touch_platform_heartbeat("standalone_controller", status="ok", detail={"cycle": "complete"})
        return results
