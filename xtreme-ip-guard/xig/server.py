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
        self._access_ctx = None
        super().__init__(*args, **kwargs)

    def end_headers(self) -> None:
        from .security.http_hardening import apply_security_headers

        apply_security_headers(self.send_header, path=urlparse(self.path).path)
        super().end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if not self._gate_request():
            return
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
        if path == "/api/system/enterprise":
            from .config import is_enterprise

            return self._send_json(
                {
                    "enterprise_mode": is_enterprise(),
                    "version": self._version(),
                }
            )
        if path == "/api/platform/status" and self._authorized():
            from .platform_ops.health import PlatformHealth

            return self._send_json(PlatformHealth(self.database).full_status())
        if path == "/api/platform/integrations" and self._authorized():
            from .integrations.integration_hub import IntegrationHub

            return self._send_json(IntegrationHub(self.database).full_matrix())
        if path == "/api/platform/backups" and self._authorized():
            from .platform_ops.backup import BackupManager

            return self._send_json(BackupManager(self.database).list_backups())
        if path == "/api/integrations/suricata/status" and self._authorized() and self.fabric:
            from .integrations.suricata_manager import SuricataManager

            return self._send_json(SuricataManager(self.database, self.fabric).status())
        if path == "/api/integrations/siem/forwarders" and self._authorized():
            return self._send_json(self.database.list_siem_forwarders())
        if path == "/api/auth/oidc/login":
            from .integrations.oidc import OidcProvider

            return self._send_json(OidcProvider(self.database).authorization_url())
        if path.startswith("/api/auth/oidc/callback"):
            return self._handle_oidc_callback()
        if path == "/api/auth/saml/login":
            from .integrations.saml import SamlProvider

            return self._send_json(SamlProvider(self.database).login_redirect())
        if path.startswith("/api/scim/v2/Users"):
            return self._handle_scim_get()
        if path.startswith("/api/scim/v2/Users/"):
            return self._handle_scim_get_user()
        if path.startswith("/api/updates/latest"):
            from urllib.parse import parse_qs

            component = parse_qs(urlparse(self.path).query).get("component", ["agent"])[0]
            from .platform_ops.updates import UpdateChannel

            manifest = UpdateChannel(self.database).latest_for(component)
            if manifest and UpdateChannel(self.database).verify_manifest(manifest):
                return self._send_json(manifest)
            return self._send_json(manifest or {}, status=HTTPStatus.NOT_FOUND)
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
            return self._send_json(self.database.list_endpoints(tenant_id=self._tenant_scope()))
        if path == "/api/events":
            return self._send_json(self.database.list_events(tenant_id=self._tenant_scope()))
        if path == "/api/policies":
            return self._send_json(self.database.list_policies(tenant_id=self._tenant_scope()))
        if path == "/api/agents":
            return self._send_json(self.database.list_agents(tenant_id=self._tenant_scope()))
        if path == "/api/audit":
            return self._send_json(self.database.list_audit(tenant_id=self._tenant_scope()))
        if path == "/api/audit/verify":
            return self._send_json(self.database.verify_audit_chain())
        if path == "/api/security/events":
            return self._send_json(self.database.list_security_events(tenant_id=self._tenant_scope()))
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
            return self._send_json(self.database.list_siem_alerts(tenant_id=self._tenant_scope()))
        if path == "/api/incidents":
            return self._send_json(self.database.list_incidents(tenant_id=self._tenant_scope()))
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
        if path == "/api/global/dashboard" and self.fabric:
            return self._send_json(self.fabric.global_platform.dashboard())
        if path == "/api/global/matrix" and self.fabric:
            return self._send_json(self.fabric.global_platform.comparison_matrix())
        if path == "/api/tenants":
            return self._send_json(self.database.list_tenants())
        if path == "/api/users":
            return self._send_json(self.database.list_rbac_users())
        if path == "/api/webhooks":
            tenant = self.headers.get("X-Mersal-Tenant", "default")
            return self._send_json(self.database.list_webhooks(tenant_id=tenant))
        if path.startswith("/api/reports/export"):
            from urllib.parse import parse_qs

            report_type = parse_qs(urlparse(self.path).query).get("type", ["executive"])[0]
            from .reporting import ReportExporter

            csv_body = ReportExporter(self.database).export_csv(report_type)
            body = csv_body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="mersal-{report_type}.csv"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/alerts/stream":
            return self._handle_alert_stream()
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def do_PUT(self) -> None:  # noqa: N802
        if not self._gate_request():
            return
        if urlparse(self.path).path.startswith("/api/scim/v2/Users/"):
            return self._handle_scim_patch()

    def do_DELETE(self) -> None:  # noqa: N802
        if not self._gate_request():
            return
        if urlparse(self.path).path.startswith("/api/scim/v2/Users/"):
            return self._handle_scim_delete()

    def do_POST(self) -> None:  # noqa: N802
        if not self._gate_request():
            return
        path = urlparse(self.path).path
        if path == "/api/auth/login":
            return self._handle_login()
        if path == "/api/auth/saml/acs":
            return self._handle_saml_acs()
        if path.startswith("/api/scim/v2/Users") and not path.rstrip("/").endswith("/Users"):
            return self._handle_scim_patch()
        if path.startswith("/api/scim/v2/Users"):
            return self._handle_scim_post()
        if path == "/api/updates/publish":
            if not self._authorized():
                return
            payload = self._read_json()
            from .platform_ops.updates import UpdateChannel

            try:
                meta = UpdateChannel(self.database).publish_manifest(
                    component=str(payload["component"]),
                    version=str(payload["version"]),
                    artifact_url=str(payload["artifact_url"]),
                    checksum_sha256=str(payload["checksum_sha256"]),
                )
            except ValueError as exc:
                return self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            self.database.record_audit(self._actor(), "update.publish", target=meta.get("manifest_id", ""))
            return self._send_json(meta, status=HTTPStatus.CREATED)
        if path == "/api/platform/autonomous-cycle":
            if not self.fabric:
                return self._send_json({"error": "fabric unavailable"}, status=HTTPStatus.SERVICE_UNAVAILABLE)
            if not self._authorized():
                return
            from .platform_ops.standalone import StandaloneController

            result = StandaloneController(self.database, self.fabric).run_autonomous_cycle()
            self.database.record_audit(
                self._actor(), "platform.autonomous_cycle", details={"keys": list(result.keys())}
            )
            return self._send_json(result)
        if path == "/api/platform/backup":
            if not self._authorized():
                return
            from .platform_ops.backup import BackupManager

            meta = BackupManager(self.database).create_backup()
            self.database.record_audit(self._actor(), "platform.backup", target=meta.get("backup_id", ""))
            return self._send_json(meta, status=HTTPStatus.CREATED)
        if path == "/api/integrations/siem/forward":
            if not self._authorized():
                return
            from .integrations.siem_forwarder import SiemForwarder

            return self._send_json(SiemForwarder(self.database).forward_batch())
        if path in {"/api/agents/heartbeat", "/api/events"}:
            if not self._authorize_agent(path):
                return
        elif not self._authorized():
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

            if path == "/api/global/cycle":
                if not self.fabric:
                    return self._send_json({"error": "fabric not initialized"}, status=HTTPStatus.SERVICE_UNAVAILABLE)
                result = self.fabric.global_platform.run_global_cycle()
                self.database.record_audit(actor, "global.cycle", details={"keys": list(result.keys())})
                return self._send_json(result)

            if path == "/api/tenants":
                from .tenant import TenantManager

                payload = self._read_json()
                created = TenantManager(self.database).create(
                    str(payload["name"]),
                    slug=str(payload.get("slug", "")),
                    plan=str(payload.get("plan", "enterprise")),
                    region=str(payload.get("region", "global")),
                )
                self.database.record_audit(actor, "tenant.create", target=created.get("tenant_id"))
                return self._send_json(created, status=HTTPStatus.CREATED)

            if path == "/api/webhooks":
                payload = self._read_json()
                import secrets

                hook = self.database.create_webhook(
                    webhook_id=f"wh-{secrets.token_hex(6)}",
                    tenant_id=str(payload.get("tenant_id", "default")),
                    name=str(payload["name"]),
                    url=str(payload["url"]),
                    events=list(payload.get("events", ["soar.playbook"])),
                    secret=str(payload.get("secret", "")),
                )
                self.database.record_audit(actor, "webhook.create", target=hook["webhook_id"])
                return self._send_json(hook, status=HTTPStatus.CREATED)

            if path == "/api/threat/taxii/sync":
                if not self.fabric:
                    return self._send_json({"error": "fabric not initialized"}, status=HTTPStatus.SERVICE_UNAVAILABLE)
                result = self.fabric.global_platform.taxii.sync()
                self.database.record_audit(actor, "taxii.sync", details=result)
                return self._send_json(result)

            if path == "/api/integrations/siem/forwarders":
                payload = self._read_json()
                import secrets

                fw = self.database.create_siem_forwarder(
                    forwarder_id=f"fw-{secrets.token_hex(6)}",
                    name=str(payload["name"]),
                    host=str(payload["host"]),
                    port=int(payload.get("port", 514)),
                    protocol=str(payload.get("protocol", "syslog_udp")),
                    tenant_id=str(payload.get("tenant_id", self._audit_tenant())),
                )
                self.database.record_audit(actor, "siem.forwarder.create", target=fw["forwarder_id"])
                return self._send_json(fw, status=HTTPStatus.CREATED)

            if path == "/api/agents/register-key":
                payload = self._read_json()
                agent_id = str(payload["agent_id"])
                from .security.agent_auth import generate_agent_key, hash_agent_key

                plain = generate_agent_key()
                self.database.set_agent_key_hash(
                    agent_id,
                    hash_agent_key(plain),
                    tenant_id=str(payload.get("tenant_id", self._audit_tenant())),
                )
                self.database.record_audit(
                    actor, "agent.key.register", target=agent_id, tenant_id=self._audit_tenant()
                )
                return self._send_json(
                    {"agent_id": agent_id, "api_key": plain, "note": "Store key once; it is not shown again."},
                    status=HTTPStatus.CREATED,
                )

            if path == "/api/users" and self._access_ctx and self._access_ctx.role in {"super_admin", "soc_admin"}:
                payload = self._read_json()
                from .rbac import RbacEngine
                from .security.password_policy import validate_password

                rbac = RbacEngine(self.database)
                ok, msg = validate_password(str(payload.get("password", "")), username=str(payload.get("username", "")))
                if not ok:
                    return self._send_json({"error": msg}, status=HTTPStatus.BAD_REQUEST)
                user = self.database.create_rbac_user(
                    username=str(payload["username"]),
                    password_hash=rbac.hash_password(str(payload["password"])),
                    role=str(payload.get("role", "analyst")),
                    tenant_id=str(payload.get("tenant_id", self._audit_tenant())),
                    display_name=str(payload.get("display_name", "")),
                )
                self.database.record_audit(actor, "user.create", target=user.get("user_id", ""), tenant_id=self._audit_tenant())
                return self._send_json(user, status=HTTPStatus.CREATED)

            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _gate_request(self) -> bool:
        from .security.http_hardening import admin_ip_allowed, check_rate_limit, client_ip

        path = urlparse(self.path).path
        ip = client_ip({k: v for k, v in self.headers.items()}, self.client_address)
        if not check_rate_limit(path=path, client_key=ip):
            self.database.record_security_event(
                category="rate_limit",
                message=f"Rate limit exceeded for {path}",
                severity="high",
                source_ip=ip,
            )
            self._send_json({"error": "rate limit exceeded"}, status=HTTPStatus.TOO_MANY_REQUESTS)
            return False
        if path == "/api/auth/login" and not admin_ip_allowed(ip):
            self.database.record_security_event(
                category="auth",
                message="Login blocked by IP allowlist",
                severity="high",
                source_ip=ip,
            )
            self._send_json({"error": "forbidden"}, status=HTTPStatus.FORBIDDEN)
            return False
        return True

    def _authorize_agent(self, path: str) -> bool:
        from .security.agent_auth import authorize_agent_request

        token = self.headers.get("X-Mersal-Token") or self.headers.get("Authorization", "")
        if token.startswith("Bearer "):
            token = token.removeprefix("Bearer ").strip()
        agent_id = self.headers.get("X-Mersal-Agent-Id", "").strip()
        agent_key = self.headers.get("X-Mersal-Agent-Key", "").strip()
        if authorize_agent_request(
            self.database,
            agent_id=agent_id,
            agent_key_header=agent_key or None,
            bearer_token=token or None,
        ):
            self._access_ctx = None
            return True
        self._send_json({"error": "agent unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
        return False

    def _handle_saml_acs(self) -> None:
        from .integrations.saml import SamlProvider

        try:
            payload = self._read_json()
            saml_response = str(payload.get("SAMLResponse", ""))
            if not saml_response:
                return self._send_json({"error": "SAMLResponse required"}, status=HTTPStatus.BAD_REQUEST)
            result = SamlProvider(self.database).consume_response(saml_response)
            if "error" in result:
                return self._send_json(result, status=HTTPStatus.BAD_REQUEST)
            self.database.record_audit(result.get("username", "saml"), "saml.login", target="sso")
            return self._send_json(result)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def _scim_bearer_ok(self) -> bool:
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return False
        from .integrations.scim import ScimProvisioner

        return ScimProvisioner(self.database).verify_bearer(auth.removeprefix("Bearer ").strip())

    def _scim_user_id(self) -> str | None:
        parts = urlparse(self.path).path.rstrip("/").split("/")
        if len(parts) >= 5 and parts[-2] == "Users":
            return parts[-1]
        return None

    def _handle_scim_get(self) -> None:
        if not self._scim_bearer_ok():
            return self._send_json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
        from .integrations.scim import ScimProvisioner

        return self._send_json(ScimProvisioner(self.database).list_users())

    def _handle_scim_get_user(self) -> None:
        if not self._scim_bearer_ok():
            return self._send_json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
        user_id = self._scim_user_id()
        if not user_id:
            return self._send_json({"error": "user id required"}, status=HTTPStatus.BAD_REQUEST)
        from .integrations.scim import ScimProvisioner

        user = ScimProvisioner(self.database).get_user(user_id)
        if not user:
            return self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
        return self._send_json(user)

    def _handle_scim_patch(self) -> None:
        if not self._scim_bearer_ok():
            return self._send_json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
        user_id = self._scim_user_id()
        if not user_id:
            return self._send_json({"error": "user id required"}, status=HTTPStatus.BAD_REQUEST)
        from .integrations.scim import ScimProvisioner

        try:
            payload = self._read_json()
            updated = ScimProvisioner(self.database).patch_user(user_id, payload)
            if not updated:
                return self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
            return self._send_json(updated)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def _handle_scim_delete(self) -> None:
        if not self._scim_bearer_ok():
            return self._send_json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
        user_id = self._scim_user_id()
        if not user_id:
            return self._send_json({"error": "user id required"}, status=HTTPStatus.BAD_REQUEST)
        from .integrations.scim import ScimProvisioner

        if ScimProvisioner(self.database).delete_user(user_id):
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        return self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

    def _handle_scim_post(self) -> None:
        if not self._scim_bearer_ok():
            return self._send_json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
        from .integrations.scim import ScimProvisioner

        try:
            payload = self._read_json()
            created = ScimProvisioner(self.database).create_user(payload)
            return self._send_json(created, status=HTTPStatus.CREATED)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def _handle_oidc_callback(self) -> None:
        from urllib.parse import parse_qs

        from .integrations.oidc import OidcProvider

        query = parse_qs(urlparse(self.path).query)
        code = query.get("code", [""])[0]
        state = query.get("state", [""])[0]
        if not code:
            return self._send_json({"error": "missing code"}, status=HTTPStatus.BAD_REQUEST)
        result = OidcProvider(self.database).exchange_code(code, state=state)
        if "error" in result:
            return self._send_json(result, status=HTTPStatus.BAD_REQUEST)
        self.database.record_audit(result.get("username", "oidc"), "oidc.login", target="sso")
        return self._send_json(result)

    def _handle_login(self) -> None:
        try:
            payload = self._read_json()
            username = str(payload.get("username", ""))
            password = str(payload.get("password", ""))
            tenant_id = str(payload.get("tenant_id", "default"))
            role = "admin"
            permissions: list[str] = []
            from .rbac import RbacEngine

            rbac = RbacEngine(self.database)
            user = rbac.authenticate(username, password, tenant_id=tenant_id)
            if user:
                role = str(user["role"])
                permissions = rbac.permissions_for_role(role)
            elif verify_admin(username, password):
                role = "super_admin"
                permissions = rbac.permissions_for_role(role)
            else:
                from .ldap_auth import authenticate_ldap

                ldap_user = authenticate_ldap(username, password)
                if not ldap_user:
                    return self._send_json({"error": "invalid credentials"}, status=HTTPStatus.UNAUTHORIZED)
                role = str(ldap_user.get("role", "analyst"))
                tenant_id = str(ldap_user.get("tenant_id", tenant_id))
                permissions = rbac.permissions_for_role(role)
            token = create_session_token(username, role=role, tenant_id=tenant_id)
            self.database.record_audit(
                username, "admin.login", target="command-center", tenant_id=tenant_id
            )
            return self._send_json(
                {
                    "token": token,
                    "username": username,
                    "role": role,
                    "tenant_id": tenant_id,
                    "permissions": permissions,
                }
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def _handle_alert_stream(self) -> None:
        import time

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        last_id = 0
        for _ in range(15):
            alerts = self.database.recent_alerts_for_stream(since_id=last_id, limit=10)
            for alert in alerts:
                last_id = max(last_id, int(alert.get("alert_id", 0)))
                chunk = f"data: {json.dumps(alert, ensure_ascii=False)}\n\n".encode("utf-8")
                self.wfile.write(chunk)
                self.wfile.flush()
            time.sleep(2)

    def _authorized(self) -> bool:
        from .security.access import permission_for_route, resolve_access

        path = urlparse(self.path).path
        token = self.headers.get("X-Mersal-Token") or self.headers.get("Authorization", "")
        ctx = resolve_access(
            self.database,
            token_header=token,
            tenant_header=self.headers.get("X-Mersal-Tenant"),
            actor_header=self.headers.get("X-Mersal-Actor"),
        )
        if not ctx.authenticated:
            self._send_json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
            return False
        perm = permission_for_route(self.command, path)
        if not ctx.allows(perm):
            self._send_json(
                {"error": "forbidden", "required_permission": perm, "role": ctx.role},
                status=HTTPStatus.FORBIDDEN,
            )
            return False
        self._access_ctx = ctx
        return True

    def _tenant_scope(self) -> str | None:
        ctx = self._access_ctx
        if not ctx:
            return None
        if ctx.role == "super_admin":
            header = (self.headers.get("X-Mersal-Tenant") or "").strip()
            return header or None
        return ctx.tenant_id

    def _actor(self) -> str:
        if self._access_ctx:
            return self._access_ctx.principal
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return "api-token"
        return self.headers.get("X-Mersal-Actor", "admin")

    def _audit_tenant(self) -> str:
        if self._access_ctx:
            return self._access_ctx.tenant_id
        return (self.headers.get("X-Mersal-Tenant") or "default").strip() or "default"

    def _read_json(self) -> dict:
        cached = getattr(self, "_cached_json_body", None)
        if cached is not None:
            self._cached_json_body = None
            return cached
        from .security.http_hardening import max_body_bytes

        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        if length > max_body_bytes():
            raise ValueError("request body too large")
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
        ebpf = metadata.get("ebpf_edr") or {}
        detections = list(metadata.get("edr_detections") or [])
        if isinstance(ebpf, dict):
            detections.extend(ebpf.get("edr_detections") or [])
        for det in detections:
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
    from .security.access import organization_startup_errors

    startup_errors = organization_startup_errors()
    if startup_errors:
        for err in startup_errors:
            print(f"[mersal] FATAL: {err}")
        raise SystemExit(1)

    bind_host = host or os.environ.get("MERSAL_HOST", "0.0.0.0")
    bind_port = port or int(os.environ.get("MERSAL_PORT", "8090"))
    database = Database(os.environ.get("MERSAL_DB", os.environ.get("XIG_DB", DEFAULT_DB)))
    database.init_schema()
    database.ensure_rbac_seed()
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

    from .config import is_enterprise, is_production

    print(f"{BRAND['full_name']} v{RequestHandler._version()} running at {scheme}://{bind_host}:{bind_port}")
    if is_enterprise():
        print("Enterprise mode (MERSAL_ENTERPRISE=1): RBAC enforced, audit chain, tenant isolation.")
    print(f"Command Center: {scheme}://{bind_host}:{bind_port}/console/")
    print(f"Mersal Global Security Fabric v{RequestHandler._version()}: vuln + CISA KEV + EDR-lite + SOAR + AI + posture.")
    if is_production():
        print("Production mode (MERSAL_PRODUCTION=1). Readiness: /api/system/readiness")
    if auth_required():
        print("Authentication enabled (API token and/or admin password).")
    if scheme == "https":
        print("TLS enabled via MERSAL_TLS_CERT / MERSAL_TLS_KEY.")
    server.serve_forever()
