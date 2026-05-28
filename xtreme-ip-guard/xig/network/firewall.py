# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Network security — firewall policy generation (nftables)."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class FirewallManager:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def build_policy(self) -> dict[str, Any]:
        isolated = [ep["endpoint_id"] for ep in self.db.list_endpoints() if ep.get("isolated")]
        high_risk_ports = {21, 23, 445, 3389, 5900}
        rules = [
            "flush table inet mersal",
            "table inet mersal {",
            "  chain input { type filter hook input priority 0; policy accept; }",
            "  chain forward { type filter hook forward priority 0; policy drop; }",
            "  chain output { type filter hook output priority 0; policy accept; }",
        ]
        for port in sorted(high_risk_ports):
            rules.append(f"    # block inbound high-risk port {port} from WAN")
            rules.append(f"    ip saddr != @lan tcp dport {port} drop")
        rules.append("  }")
        rules.append("}")
        return {
            "backend": "nftables" if shutil.which("nft") else "policy-only",
            "isolated_endpoints": isolated,
            "blocked_inbound_ports": sorted(high_risk_ports),
            "config": "\n".join(rules),
        }

    def dashboard(self) -> dict[str, Any]:
        policy = self.build_policy()
        flows = self.db.list_network_flows(limit=20)
        risky = [f for f in flows if int(f.get("risk", 0)) >= 50]
        return {
            "module": "Mersal Network Security",
            "policy": policy,
            "recent_flows": len(flows),
            "risky_flows": len(risky),
        }
