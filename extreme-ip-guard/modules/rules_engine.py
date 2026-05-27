"""
Extreme IP Guard - Security Rules Engine
Flexible rule evaluation engine that matches conditions against
incoming events and triggers automated responses.
"""

import fnmatch
import ipaddress
import operator
import time
from typing import Any, Callable, Dict, List, Optional

from core.models import ActionType


OPERATORS: Dict[str, Callable] = {
    "eq": operator.eq,
    "ne": operator.ne,
    "gt": operator.gt,
    "ge": operator.ge,
    "lt": operator.lt,
    "le": operator.le,
    "contains": lambda a, b: b in a if isinstance(a, (str, list)) else False,
    "not_contains": lambda a, b: b not in a if isinstance(a, (str, list)) else True,
    "in": lambda a, b: a in b if isinstance(b, (list, set)) else False,
    "not_in": lambda a, b: a not in b if isinstance(b, (list, set)) else True,
    "matches": lambda a, b: fnmatch.fnmatch(str(a), str(b)),
    "starts_with": lambda a, b: str(a).startswith(str(b)),
    "ends_with": lambda a, b: str(a).endswith(str(b)),
    "ip_in_range": lambda a, b: _ip_in_range(a, b),
    "ip_not_in_range": lambda a, b: not _ip_in_range(a, b),
}


def _ip_in_range(ip_str: str, network_str: str) -> bool:
    try:
        return ipaddress.ip_address(ip_str) in ipaddress.ip_network(
            network_str, strict=False
        )
    except ValueError:
        return False


class RuleCondition:
    def __init__(self, field: str, op: str, value: Any):
        self.field = field
        self.op = op
        self.value = value
        self._operator_fn = OPERATORS.get(op)

    def evaluate(self, context: dict) -> bool:
        actual_value = self._resolve_field(context, self.field)
        if actual_value is None and self.op not in ("eq", "ne"):
            return False
        if self._operator_fn is None:
            return False
        try:
            return self._operator_fn(actual_value, self.value)
        except (TypeError, ValueError):
            return False

    def _resolve_field(self, context: dict, field_path: str) -> Any:
        parts = field_path.split(".")
        current = context
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            if current is None:
                return None
        return current


class SecurityRule:
    def __init__(
        self,
        rule_id: int,
        name: str,
        conditions: List[dict],
        action: ActionType,
        action_params: dict = None,
        priority: int = 100,
        enabled: bool = True,
        logic: str = "and",
    ):
        self.rule_id = rule_id
        self.name = name
        self.action = action
        self.action_params = action_params or {}
        self.priority = priority
        self.enabled = enabled
        self.logic = logic
        self.hit_count = 0
        self.last_hit = 0.0

        self.conditions = [
            RuleCondition(c["field"], c["operator"], c["value"])
            for c in conditions
        ]

    def evaluate(self, context: dict) -> bool:
        if not self.enabled or not self.conditions:
            return False

        if self.logic == "and":
            result = all(c.evaluate(context) for c in self.conditions)
        elif self.logic == "or":
            result = any(c.evaluate(context) for c in self.conditions)
        else:
            result = all(c.evaluate(context) for c in self.conditions)

        if result:
            self.hit_count += 1
            self.last_hit = time.monotonic()

        return result


class RulesEngine:
    """
    Evaluates security rules against event contexts and returns
    the highest-priority matching action.
    """

    def __init__(self):
        self._rules: Dict[int, SecurityRule] = {}

    def add_rule(self, rule: SecurityRule):
        self._rules[rule.rule_id] = rule

    def remove_rule(self, rule_id: int) -> bool:
        return self._rules.pop(rule_id, None) is not None

    def load_rules(self, rules_data: List[dict]):
        for data in rules_data:
            conditions = data.get("conditions", [])
            if isinstance(conditions, dict):
                conditions_list = conditions.get("rules", [])
                logic = conditions.get("logic", "and")
            else:
                conditions_list = conditions
                logic = "and"

            rule = SecurityRule(
                rule_id=data["id"],
                name=data["name"],
                conditions=conditions_list,
                action=ActionType(data["action"]),
                action_params=data.get("action_params", {}),
                priority=data.get("priority", 100),
                enabled=data.get("enabled", True),
                logic=logic,
            )
            self.add_rule(rule)

    def evaluate(self, context: dict) -> Optional[dict]:
        matching_rules = []

        for rule in self._rules.values():
            if rule.evaluate(context):
                matching_rules.append(rule)

        if not matching_rules:
            return None

        matching_rules.sort(key=lambda r: r.priority)
        best = matching_rules[0]

        return {
            "rule_id": best.rule_id,
            "rule_name": best.name,
            "action": best.action.value,
            "action_params": best.action_params,
            "priority": best.priority,
            "all_matches": [
                {"rule_id": r.rule_id, "name": r.name, "action": r.action.value}
                for r in matching_rules
            ],
        }

    def get_all_rules(self) -> List[dict]:
        return [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "action": r.action.value,
                "priority": r.priority,
                "enabled": r.enabled,
                "hit_count": r.hit_count,
                "conditions_count": len(r.conditions),
            }
            for r in sorted(self._rules.values(), key=lambda r: r.priority)
        ]

    def get_stats(self) -> dict:
        rules = list(self._rules.values())
        return {
            "total_rules": len(rules),
            "enabled_rules": sum(1 for r in rules if r.enabled),
            "total_hits": sum(r.hit_count for r in rules),
            "top_rules": sorted(
                [
                    {"id": r.rule_id, "name": r.name, "hits": r.hit_count}
                    for r in rules
                ],
                key=lambda x: x["hits"],
                reverse=True,
            )[:10],
        }


rules_engine = RulesEngine()
