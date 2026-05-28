# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""Ionomegax Mersal Guard — HTTP API and Command Center."""

from __future__ import annotations

import json
import mimetypes
import os
import ssl
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .auth import (
    admin_password,
    admin_username,
    auth_required,
    authorize,
    create_session_token,
    verify_admin,
)
from .brand import BRAND
from .credits import system_about
from .core import EndpointEvent, PolicyRule
from .ai import MersalAICortex
from .fabric import MersalSecurityFabric
from .config import allow_demo_seed, should_bootstrap_on_start, tls_enabled
from .build_meta import build_info
from .readiness import production_readiness, tool_versions
from .storage import Database

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = PROJECT_ROOT / "data" / "mersal-guard.sqlite3"
WEB_ROOT = PROJECT_ROOT / "web"


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, database: Database, fabric: MersalSecurityFabric | None = None, **kwargs):
        self.database = database
        self.fabric = fabric
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/console", "/console/"}:
            return self._serve_file(WEB_ROOT / "index.html")
        if path.startswith("/console/"):
            return self._serve_file(WEB_ROOT / path.removeprefix("/console/"))
        if path == "/api/auth/status":
            return self._send_json(
                {
                    "auth_required": auth_required(),
                    "admin_configured": bool(admin_password()),
                    "admin_username": admin_username(),
                }
            )
        if path == "/api/system/about":
            return self._send_json(system_about(version=self._version()))
        if path == "/api/system/readiness":
            return self._send_json(production_readiness(self.database))
        if path == "/api/system/build":
            return self._send_json(build_info())
        if path == "/api/system/tools":
            return self._send_json(tool_versions())
        if path == "/api/threat/intel" and self._authorized():
            return self._send_json(self.database.threat_intel_summary())
        if not self._authorized():
            return
        if path == "/api/health":
            return self._send_json({"status": "ok", "product": BRAND["full_name"], "version": self._version()})
        if path == "/api/brand":
            return self._send_json(BRAND)
        if path == "/api/dashboard":
            return self._send_json(self.database.dashboard())
        if path == "/api/endpoints":
            return self._send_json(self.database.list_endpoints())
        if path == "/api/events":
            return self._send_json(self.database.list_events())
        if path == "/api/policies":
            return self._send_json(self.database.list_policies())
        if path == "/api/agents":
            return self._send_json(self.database.list_agents())
        if path == "/api/audit":
            return self._send_json(self.database.list_audit())
        if path.startswith("/api/endpoints/") and path.endswith("/directives"):
            endpoint_id = self._path_part(path, 2)
            return self._send_json(self.database.endpoint_directives(endpoint_id))
        if path == "/api/ai/dashboard":
            return self._send_json(MersalAICortex(self.database).dashboard())
        if path == "/api/ai/insights":
            return self._send_json(self.database.list_ai_insights())
        if path == "/api/ai/predictions":
            return self._send_json(self.database.list_ai_predictions())
        if path == "/api/fabric/dashboard" and self.fabric:
            return self._send_json(self.fabric.dashboard())
        if path == "/api/vuln/findings":
            return self._send_json(self.database.list_vuln_findings())
        if path == "/api/vuln/scans":
            return self._send_json(self.database.list_vuln_scans())
        if path == "/api/soar/runs":
            return self._send_json(self.database.list_soar_runs())
        if path == "/api/posture":
            return self._send_json(self.database.latest_security_posture())
        if path == "/api/enterprise/dashboard" and self.fabric:
            return self._send_json(self.fabric.enterprise.dashboard())
        if path == "/api/enterprise/matrix" and self.fabric:
            return self._send_json(self.fabric.enterprise.comparison_matrix())
        if path == "/api/siem/dashboard" and self.fabric:
            return self._send_json(self.fabric.enterprise.siem.dashboard())
        if path == "/api/siem/alerts":
            return self._send_json(self.database.list_siem_alerts())
        if path == "/api/incidents":
            return self._send_json(self.database.list_incidents())
        if path.startswith("/api/incidents/") and path.endswith("/timeline"):
            incident_id = self._path_part(path, 2)
            return self._send_json(self.database.get_incident_timeline(incident_id))
        if path == "/api/compliance":
            comp = self.database.latest_compliance_score()
            if not comp and self.fabric:
                comp = self.fabric.enterprise.compliance.assess()
            return self._send_json(comp or {})
        if path == "/api/edr/detections":
            return self._send_json(self.database.list_edr_detections())
        if path == "/api/network/flows":
            return self._send_json(self.database.list_network_flows())
        if path == "/api/network/policy" and self.fabric:
            return self._send_json(self.fabric.enterprise.firewall.build_policy())
        if path == "/api/xdr/dashboard" and self.fabric:
            return self._send_json(self.fabric.enterprise.xdr.dashboard())
        if path == "/api/xdr/findings":
            return self._send_json(self.database.list_xdr_findings())
        if path == "/api/logs/search":
            query = urlparse(self.path).query
            q = ""
            if "q=" in query:
                from urllib.parse import parse_qs

                q = parse_qs(query).get("q", [""])[0]
            if self.fabric:
                return self._send_json(self.fabric.enterprise.logvault.search(query=q))
            return self._send_json(self.database.search_logs(query=q))
        if path == "/api/logs/dashboard" and self.fabric:
            return self._send_json(self.fabric.enterprise.logvault.dashboard())
        if path == "/api/suricata/alerts":
            return self._send_json(self.database.list_suricata_alerts())
        if path == "/api/yara/rules":
            return self._send_json(self.database.list_yara_rules())
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/auth/login":
            return self._handle_login()
        if not self._authorized():
            return
        actor = self._actor()
        try:
            if path == "/api/agents/heartbeat":
                payload = self._read_json()
                metadata = dict(payload.get("metadata", {}))
                agent = self.database.record_agent_heartbeat(
                    agent_id=str(payload["agent_id"]),
                    agent_type=str(payload.get("agent_type", "endpoint")),
                    hostname=str(payload["hostname"]),
                    os_name=str(payload.get("os_name", "")),
                    version=str(payload.get("version", "")),
                    metadata=metadata,
                )
                self._ingest_agent_edr_telemetry(metadata)
                return self._send_json(agent)

            if path == "/api/events":
                payload = self._read_json()
                event = EndpointEvent(
                    endpoint_id=str(payload["endpoint_id"]),
                    actor=str(payload["actor"]),
                    event_type=str(payload["event_type"]),
                    channel=str(payload["channel"]),
                    resource=str(payload["resource"]),
                    classification=str(payload.get("classification", "internal")),
                    destination=str(payload.get("destination", "")),
                    process=str(payload.get("process", "")),
                    severity=int(payload.get("severity", 10)),
                    behavior_flags=tuple(payload.get("behavior_flags", [])),
                    metadata=dict(payload.get("metadata", {})),
                )
                return self._send_json(self.database.ingest_event(event), status=HTTPStatus.CREATED)

            if path == "/api/policies":
                payload = self._read_json()
                policy = PolicyRule(
                    rule_id=str(payload["rule_id"]),
                    name=str(payload["name"]),
                    action=str(payload["action"]),
                    event_type=str(payload.get("event_type", "*")),
                    classification=str(payload.get("classification", "*")),
                    channel=str(payload.get("channel", "*")),
                    destination_contains=str(payload.get("destination_contains", "")),
                    min_risk=int(payload.get("min_risk", 0)),
                    reason=str(payload.get("reason", "")),
                    enabled=bool(payload.get("enabled", True)),
                )
                created = self.database.create_policy(policy)
                self.database.record_audit(actor, "policy.create", target=policy.rule_id, details=created)
                return self._send_json(created, status=HTTPStatus.CREATED)

            if path.startswith("/api/endpoints/") and path.endswith("/isolate"):
                endpoint_id = self._path_part(path, 2)
                result = self.database.set_endpoint_isolation(endpoint_id, True)
                self.database.record_audit(actor, "endpoint.isolate", target=endpoint_id)
                return self._send_json(result)

            if path.startswith("/api/endpoints/") and path.endswith("/restore"):
                endpoint_id = self._path_part(path, 2)
                result = self.database.set_endpoint_isolation(endpoint_id, False)
                self.database.record_audit(actor, "endpoint.restore", target=endpoint_id)
                return self._send_json(result)

            if path == "/api/ai/train":
                payload = self._read_json()
                limit = int(payload.get("limit", 100))
                result = self.database.train_cortex_from_history(limit=limit)
                self.database.record_audit(actor, "ai.train", details=result)
                return self._send_json(result)

            if path == "/api/vuln/scan":
                if not self.fabric:
                    return self._send_json({"error": "fabric not initialized"}, status=HTTPStatus.SERVICE_UNAVAILABLE)
                scope = str(self._read_json().get("scope", "manual"))
                result = self.fabric.scanner.scan_all_endpoints(scope=scope)
                self.database.record_audit(actor, "vuln.scan", details={"scope": scope, "findings": result.get("findings_count")})
                return self._send_json(result)

            if path == "/api/fabric/daily":
                if not self.fabric:
                    return self._send_json({"error": "fabric not initialized"}, status=HTTPStatus.SERVICE_UNAVAILABLE)
                result = self.fabric.run_daily_now()
                self.database.record_audit(actor, "fabric.daily", details=result)
                return self._send_json(result)

            if path == "/api/threat/sync":
                if not self.fabric:
                    return self._send_json({"error": "fabric not initialized"}, status=HTTPStatus.SERVICE_UNAVAILABLE)
                result = self.fabric.feeds.sync_all(
                    remote_url=os.environ.get("MERSAL_STIX_FEED_URL", "").strip(),
                    kev_url=os.environ.get(
                        "MERSAL_KEV_FEED_URL",
                        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
                    ).strip(),
                )
                self.database.record_audit(actor, "threat.sync", details=result)
                return self._send_json(result)

            if path == "/api/enterprise/cycle":
                if not self.fabric:
                    return self._send_json({"error": "fabric not initialized"}, status=HTTPStatus.SERVICE_UNAVAILABLE)
                result = self.fabric.enterprise.run_enterprise_cycle()
                self.database.record_audit(actor, "enterprise.cycle", details={"keys": list(result.keys())})
                return self._send_json(result)

            if path.startswith("/api/incidents/") and path.endswith("/close"):
                incident_id = self._path_part(path, 2)
                from .incidents import IncidentManager

                result = IncidentManager(self.database).close_incident(incident_id, actor=actor)
                self.database.record_audit(actor, "incident.close", target=incident_id)
                return self._send_json(result)

            if path == "/api/logs/ingest":
                payload = self._read_json()
                records = payload if isinstance(payload, list) else payload.get("records", [])
                if self.fabric:
                    result = self.fabric.enterprise.logvault.ingest_batch(records)
                else:
                    from .logvault import LogVault

                    result = LogVault(self.database).ingest_batch(records)
                return self._send_json(result, status=HTTPStatus.CREATED)

            if path == "/api/suricata/ingest":
                payload = self._read_json()
                alerts = payload if isinstance(payload, list) else payload.get("alerts", [])
                if self.fabric:
                    result = self.fabric.enterprise.suricata.ingest_payload(alerts)
                else:
                    from .siem.suricata import SuricataIngester

                    result = SuricataIngester(self.database).ingest_payload(alerts)
                return self._send_json(result, status=HTTPStatus.CREATED)

            if path == "/api/xdr/correlate":
                if not self.fabric:
                    return self._send_json({"error": "fabric not initialized"}, status=HTTPStatus.SERVICE_UNAVAILABLE)
                result = self.fabric.enterprise.xdr.run_correlation()
                self.database.record_audit(actor, "xdr.correlate", details=result)
                return self._send_json(result)

            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _handle_login(self) -> None:
        try:
            payload = self._read_json()
            username = str(payload.get("username", ""))
            password = str(payload.get("password", ""))
            if not verify_admin(username, password):
                return self._send_json({"error": "invalid credentials"}, status=HTTPStatus.UNAUTHORIZED)
            token = create_session_token(username)
            self.database.record_audit(username, "admin.login", target="command-center")
            return self._send_json({"token": token, "username": username, "role": "admin"})
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def _authorized(self) -> bool:
        token = self.headers.get("X-Mersal-Token") or self.headers.get("Authorization", "")
        if authorize(token):
            return True
        self._send_json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
        return False

    def _actor(self) -> str:
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return "api-token"
        return self.headers.get("X-Mersal-Actor", "admin")

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send_json(self, data: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, relative: Path) -> None:
        target = relative
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            target = WEB_ROOT / "index.html"
        resolved = target.resolve()
        web_root = WEB_ROOT.resolve()
        if web_root not in resolved.parents and resolved != web_root / "index.html":
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        content_type, _ = mimetypes.guess_type(str(resolved))
        body = resolved.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _ingest_agent_edr_telemetry(self, metadata: dict) -> None:
        endpoint_id = str(metadata.get("endpoint_id", ""))
        if not endpoint_id:
            return
        flows = metadata.get("network_flows") or metadata.get("sensors", {}).get("network_flows")
        if isinstance(flows, list) and flows:
            self.database.record_network_flows(endpoint_id, flows)
        for det in metadata.get("edr_detections") or []:
            if isinstance(det, dict):
                self.database.record_edr_detection(
                    endpoint_id=endpoint_id,
                    detection_type=str(det.get("type", "agent")),
                    severity=int(det.get("severity", 50)),
                    title=str(det.get("title", "Agent detection")),
                    details=det,
                )

    @staticmethod
    def _path_part(path: str, index: int) -> str:
        parts = [part for part in path.split("/") if part]
        return parts[index]

    @staticmethod
    def _version() -> str:
        from . import __version__

        return __version__


def _initialize_database(database: Database) -> None:
    if allow_demo_seed():
        database.seed_demo()
        return
    if should_bootstrap_on_start() and len(database.list_policies()) == 0:

        def _run_bootstrap() -> None:
            from .bootstrap import bootstrap_organization

            try:
                summary = bootstrap_organization(database)
                print(
                    f"[mersal] production bootstrap complete: "
                    f"{summary.get('policies_installed', 0)} policies, "
                    f"feeds={summary.get('threat_feeds', {})}"
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[mersal] production bootstrap error: {exc}")

        threading.Thread(target=_run_bootstrap, name="mersal-bootstrap", daemon=True).start()
        print("[mersal] production bootstrap started in background")


def run(host: str | None = None, port: int | None = None) -> None:
    bind_host = host or os.environ.get("MERSAL_HOST", "0.0.0.0")
    bind_port = port or int(os.environ.get("MERSAL_PORT", "8090"))
    database = Database(os.environ.get("MERSAL_DB", os.environ.get("XIG_DB", DEFAULT_DB)))
    database.init_schema()
    _initialize_database(database)
    fabric = MersalSecurityFabric(database)
    if os.environ.get("MERSAL_NO_SCHEDULER", "").strip().lower() not in {"1", "true", "yes"}:
        fabric.scheduler.start()

    def handler(*args, **kwargs):
        RequestHandler(*args, database=database, fabric=fabric, **kwargs)

    server = ThreadingHTTPServer((bind_host, bind_port), handler)
    scheme = "http"
    if tls_enabled():
        cert = os.environ.get("MERSAL_TLS_CERT", "").strip()
        key = os.environ.get("MERSAL_TLS_KEY", "").strip()
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        from .config import agent_ca_path, agent_mtls_required

        ca = agent_ca_path()
        if agent_mtls_required() and ca:
            context.verify_mode = ssl.CERT_REQUIRED
            context.load_verify_locations(cafile=str(ca))
        server.socket = context.wrap_socket(server.socket, server_side=True)
        scheme = "https"

    from .config import is_production

    print(f"{BRAND['full_name']} v{RequestHandler._version()} running at {scheme}://{bind_host}:{bind_port}")
    print(f"Command Center: {scheme}://{bind_host}:{bind_port}/console/")
    print(f"Mersal Global Security Fabric v{RequestHandler._version()}: vuln + CISA KEV + EDR-lite + SOAR + AI + posture.")
    if is_production():
        print("Production mode (MERSAL_PRODUCTION=1). Readiness: /api/system/readiness")
    if auth_required():
        print("Authentication enabled (API token and/or admin password).")
    if scheme == "https":
        print("TLS enabled via MERSAL_TLS_CERT / MERSAL_TLS_KEY.")
    server.serve_forever()
