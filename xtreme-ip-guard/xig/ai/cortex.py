"""Mersal Neural Cortex — learning, prediction, and autonomous defensive decisions."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..core import ACTION_RANK, EndpointEvent, PolicyDecision, calculate_risk_score
from .baseline import OnlineStats
from .predictor import predict_risk_trend
from .threat_intel import DEFAULT_IOCS, match_destination

if TYPE_CHECKING:
    from ..storage import Database


@dataclass(frozen=True)
class AIFusionResult:
    """AI-enhanced decision fused with policy engine output."""

    action: str
    risk_score: int
    reason: str
    anomaly_score: float
    predicted_risk: float
    breach_probability: float
    confidence: float
    ai_escalated: bool
    signals: dict[str, Any] = field(default_factory=dict)
    ioc_hits: tuple[dict[str, Any], ...] = field(default_factory=tuple)


class MersalAICortex:
    """Adaptive security brain: learns baselines, detects anomalies, predicts and decides."""

    def __init__(self, database: "Database") -> None:
        self.db = database

    def analyze_and_fuse(
        self,
        event: EndpointEvent,
        rule_decision: PolicyDecision,
        *,
        endpoint_trust: int,
    ) -> AIFusionResult:
        risk = calculate_risk_score(event, endpoint_trust=endpoint_trust)
        baseline_key = self._baseline_key(event)
        stats = self.db.get_baseline(baseline_key)
        stats.update(float(risk))
        self.db.save_baseline(baseline_key, event.endpoint_id, "risk", stats)

        z = abs(stats.z_score(float(risk)))
        anomaly_score = min(100.0, z * 18.0)
        recent = self.db.recent_risks_for_endpoint(event.endpoint_id, limit=12)
        prediction = predict_risk_trend(recent + [float(risk)])
        iocs = self.db.list_threat_intel()
        if not iocs:
            self.db.seed_threat_intel(DEFAULT_IOCS)
            iocs = self.db.list_threat_intel()
        ioc_hits = tuple(match_destination(event.destination, iocs))

        confidence = self._confidence(anomaly_score, len(ioc_hits), stats.count)
        fused_action = rule_decision.action
        fused_risk = max(rule_decision.risk_score, int(risk), int(prediction["predicted_risk"]))
        reason = rule_decision.reason
        ai_escalated = False

        if ioc_hits:
            fused_action = self._escalate(fused_action, "block")
            fused_risk = max(fused_risk, 80)
            reason = f"AI threat-intel match: {ioc_hits[0].get('indicator')}"
            ai_escalated = True
        elif anomaly_score >= 55 and confidence >= 0.65:
            fused_action = self._escalate(fused_action, "quarantine")
            fused_risk = max(fused_risk, 70)
            reason = f"AI behavioral anomaly (z={z:.1f}, score={anomaly_score:.0f})"
            ai_escalated = True
        elif prediction["breach_probability"] >= 0.82 and confidence >= 0.7:
            fused_action = self._escalate(fused_action, "isolate_endpoint")
            fused_risk = max(fused_risk, 88)
            reason = "AI predicts high breach probability within forecast horizon"
            ai_escalated = True
        elif prediction["predicted_risk"] >= 75:
            fused_action = self._escalate(fused_action, "warn")
            reason = f"AI risk forecast elevated ({prediction['predicted_risk']})"

        signals = {
            "baseline": stats.to_dict(),
            "anomaly_score": round(anomaly_score, 2),
            "z_score": round(z, 3),
            "prediction": prediction,
            "confidence": round(confidence, 3),
        }
        return AIFusionResult(
            action=fused_action,
            risk_score=min(100, fused_risk),
            reason=reason,
            anomaly_score=anomaly_score,
            predicted_risk=float(prediction["predicted_risk"]),
            breach_probability=float(prediction["breach_probability"]),
            confidence=confidence,
            ai_escalated=ai_escalated,
            signals=signals,
            ioc_hits=ioc_hits,
        )

    def dashboard(self) -> dict[str, Any]:
        insights = self.db.list_ai_insights(limit=15)
        predictions = self.db.list_ai_predictions(limit=10)
        baselines = self.db.count_baselines()
        return {
            "engine": "Mersal Neural Cortex",
            "version": "1.0",
            "capabilities": [
                "behavioral_learning",
                "anomaly_detection",
                "risk_prediction",
                "threat_intel_fusion",
                "autonomous_escalation",
            ],
            "baseline_signals": baselines,
            "recent_insights": insights,
            "predictions": predictions,
            "recommended_policies": self.recommend_policies(),
        }

    def recommend_policies(self) -> list[dict[str, str]]:
        """Suggest policies from repeated high-risk patterns."""
        patterns = self.db.high_risk_patterns(limit=5)
        suggestions: list[dict[str, str]] = []
        for row in patterns:
            suggestions.append(
                {
                    "rule_id": f"AI-SUGGEST-{row['channel'].upper()}-{row['classification'].upper()}",
                    "name": f"AI: Block repeated {row['classification']} via {row['channel']}",
                    "action": "block",
                    "classification": row["classification"],
                    "channel": row["channel"],
                    "reason": f"Observed {row['hits']} high-risk events — Cortex recommendation",
                }
            )
        return suggestions

    @staticmethod
    def _baseline_key(event: EndpointEvent) -> str:
        return f"{event.endpoint_id}:{event.channel}:{event.classification}"

    @staticmethod
    def _confidence(anomaly_score: float, ioc_count: int, sample_count: int) -> float:
        base = min(0.95, 0.35 + sample_count * 0.04)
        if ioc_count:
            base = min(0.98, base + 0.25)
        if anomaly_score > 40:
            base = min(0.99, base + anomaly_score / 200.0)
        return base

    @staticmethod
    def _escalate(current: str, proposed: str) -> str:
        if ACTION_RANK.get(proposed, 0) > ACTION_RANK.get(current, 0):
            return proposed
        return current
