"""Operator CLI for Extreme IP Guard.

Used by SOC engineers and administrators against an already-running control
plane. Mirrors the most useful console actions: issuing enrolment tokens,
listing alerts, adding IOCs, verifying the audit chain.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any


DEFAULT_SERVER = "http://127.0.0.1:8090"


def http(method: str, url: str, payload: dict[str, Any] | None = None) -> Any:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"server returned {exc.code}: {detail}", file=sys.stderr)
        raise SystemExit(1)
    except urllib.error.URLError as exc:
        print(f"could not reach server: {exc.reason}", file=sys.stderr)
        raise SystemExit(1)
    if not raw:
        return {}
    return json.loads(raw)


def cmd_dashboard(args: argparse.Namespace) -> int:
    print(json.dumps(http("GET", f"{args.server}/api/dashboard"), indent=2, ensure_ascii=False))
    return 0


def cmd_alerts(args: argparse.Namespace) -> int:
    alerts = http("GET", f"{args.server}/api/alerts")
    for alert in alerts:
        print(f"[{alert['severity'].upper():8}] {alert['ts']} {alert['title']} (rule={alert['rule_id']}, mitre={alert['mitre']})")
    return 0


def cmd_issue_token(args: argparse.Namespace) -> int:
    response = http(
        "POST",
        f"{args.server}/api/agents/enrol-tokens",
        {"hostname": args.hostname, "criticality": args.criticality, "actor": "console-cli"},
    )
    print(json.dumps(response, indent=2))
    return 0


def cmd_add_ioc(args: argparse.Namespace) -> int:
    response = http(
        "POST",
        f"{args.server}/api/iocs",
        {"kind": args.kind, "value": args.value, "source": "console-cli"},
    )
    print(json.dumps(response, indent=2))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    events = http("GET", f"{args.server}/api/events/verify")
    audit = http("GET", f"{args.server}/api/audit/verify")
    print("Event chain :", "OK" if events["intact"] else f"BROKEN @ {events['broken_at']}", f"({events['count']} entries)")
    print("Audit chain :", "OK" if audit["intact"] else f"BROKEN @ {audit['broken_at']}", f"({audit['count']} entries)")
    return 0 if events["intact"] and audit["intact"] else 1


def cmd_acknowledge(args: argparse.Namespace) -> int:
    response = http(
        "POST",
        f"{args.server}/api/alerts/{args.alert_uid}/status",
        {"status": args.status, "actor": "console-cli"},
    )
    print(json.dumps(response, indent=2))
    return 0


def cmd_login(args: argparse.Namespace) -> int:
    response = http("POST", f"{args.server}/api/auth/login", {"username": args.username, "password": args.password})
    print(json.dumps(response, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extreme IP Guard operator CLI")
    parser.add_argument("--server", default=DEFAULT_SERVER)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("dashboard").set_defaults(func=cmd_dashboard)
    sub.add_parser("alerts").set_defaults(func=cmd_alerts)

    token = sub.add_parser("issue-token", help="Issue a one-time enrolment token for a host")
    token.add_argument("--hostname", required=True)
    token.add_argument("--criticality", default="normal", choices=["low", "normal", "high", "crown"])
    token.set_defaults(func=cmd_issue_token)

    ioc = sub.add_parser("add-ioc", help="Add a threat-intel indicator")
    ioc.add_argument("--kind", required=True, choices=["sha256", "domain", "ipv4", "ipv6", "ja3"])
    ioc.add_argument("--value", required=True)
    ioc.set_defaults(func=cmd_add_ioc)

    verify = sub.add_parser("verify-chains", help="Replay event and audit hash chains")
    verify.set_defaults(func=cmd_verify)

    ack = sub.add_parser("alert", help="Change the status of an alert")
    ack.add_argument("alert_uid")
    ack.add_argument("--status", required=True, choices=["new", "acknowledged", "resolved", "false_positive"])
    ack.set_defaults(func=cmd_acknowledge)

    login = sub.add_parser("login", help="Verify console credentials")
    login.add_argument("--username", required=True)
    login.add_argument("--password", required=True)
    login.set_defaults(func=cmd_login)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
