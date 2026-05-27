"""
Advanced AI/ML Threat Detection Engine
Uses ensemble methods: Isolation Forest + Random Forest + Behavioral Analysis
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import joblib
import os
import asyncio
from loguru import logger
from collections import defaultdict, deque
import time
import math


@dataclass
class ThreatPrediction:
    is_threat: bool
    confidence: float
    anomaly_score: float
    threat_categories: List[str]
    risk_score: float
    mitre_techniques: List[str]
    explanation: List[str]


@dataclass
class BehaviorProfile:
    ip_address: str
    request_count: int = 0
    unique_ports: set = None
    unique_destinations: set = None
    request_rate: float = 0.0
    error_rate: float = 0.0
    avg_payload_size: float = 0.0
    protocol_distribution: Dict = None
    time_pattern: List[int] = None
    last_updated: float = 0.0

    def __post_init__(self):
        if self.unique_ports is None:
            self.unique_ports = set()
        if self.unique_destinations is None:
            self.unique_destinations = set()
        if self.protocol_distribution is None:
            self.protocol_distribution = defaultdict(int)
        if self.time_pattern is None:
            self.time_pattern = [0] * 24


class BehaviorAnalyzer:
    """
    Real-time behavioral analysis using sliding window approach
    Implements UEBA (User and Entity Behavior Analytics)
    """
    
    def __init__(self, window_size: int = 300):
        self.window_size = window_size  # seconds
        self.profiles: Dict[str, BehaviorProfile] = {}
        self.event_windows: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=10000)
        )
        self.baseline_stats: Dict[str, dict] = {}
        
    def update_profile(self, ip: str, event: dict) -> BehaviorProfile:
        now = time.time()
        
        if ip not in self.profiles:
            self.profiles[ip] = BehaviorProfile(ip_address=ip)
        
        profile = self.profiles[ip]
        window = self.event_windows[ip]
        
        # Add event to window
        window.append({"time": now, **event})
        
        # Clean old events
        cutoff = now - self.window_size
        while window and window[0]["time"] < cutoff:
            window.popleft()
        
        # Update profile stats
        recent_events = list(window)
        profile.request_count = len(recent_events)
        profile.request_rate = len(recent_events) / self.window_size
        
        if "port" in event and event["port"]:
            profile.unique_ports.add(event["port"])
        if "destination" in event and event["destination"]:
            profile.unique_destinations.add(event["destination"])
        if "protocol" in event and event["protocol"]:
            profile.protocol_distribution[event["protocol"]] += 1
            
        # Time-of-day pattern
        hour = datetime.fromtimestamp(now).hour
        profile.time_pattern[hour] += 1
        
        # Error rate
        errors = sum(1 for e in recent_events if e.get("status_code", 200) >= 400)
        profile.error_rate = errors / max(len(recent_events), 1)
        
        profile.last_updated = now
        return profile
    
    def compute_deviation_score(self, ip: str, profile: BehaviorProfile) -> float:
        """Compute how much current behavior deviates from baseline"""
        if ip not in self.baseline_stats:
            return 0.0
        
        baseline = self.baseline_stats[ip]
        deviations = []
        
        if "avg_rate" in baseline and baseline["std_rate"] > 0:
            z_score = abs(profile.request_rate - baseline["avg_rate"]) / baseline["std_rate"]
            deviations.append(min(z_score / 3.0, 1.0))
        
        if "avg_ports" in baseline and baseline["std_ports"] > 0:
            port_count = len(profile.unique_ports)
            z_score = abs(port_count - baseline["avg_ports"]) / baseline["std_ports"]
            deviations.append(min(z_score / 3.0, 1.0))
        
        return np.mean(deviations) if deviations else 0.0
    
    def update_baseline(self, ip: str, profile: BehaviorProfile):
        """Exponential moving average for baseline updates"""
        alpha = 0.1
        current = self.baseline_stats.get(ip, {})
        
        new_rate = profile.request_rate
        new_ports = len(profile.unique_ports)
        
        self.baseline_stats[ip] = {
            "avg_rate": alpha * new_rate + (1 - alpha) * current.get("avg_rate", new_rate),
            "std_rate": max(0.1, alpha * abs(new_rate - current.get("avg_rate", new_rate))),
            "avg_ports": alpha * new_ports + (1 - alpha) * current.get("avg_ports", new_ports),
            "std_ports": max(0.5, alpha * abs(new_ports - current.get("avg_ports", new_ports))),
        }


class ThreatSignatureEngine:
    """
    Rule-based threat detection using known attack signatures
    Combined with MITRE ATT&CK framework mapping
    """
    
    SIGNATURES = {
        "port_scan": {
            "description": "Systematic port scanning detected",
            "indicators": lambda p: len(p.unique_ports) > 20,
            "mitre": ["T1046"],
            "severity": "high",
        },
        "brute_force": {
            "description": "Brute force authentication attack",
            "indicators": lambda p: p.error_rate > 0.7 and p.request_rate > 5,
            "mitre": ["T1110"],
            "severity": "critical",
        },
        "ddos": {
            "description": "Distributed Denial of Service attack",
            "indicators": lambda p: p.request_rate > 100,
            "mitre": ["T1498"],
            "severity": "critical",
        },
        "reconnaissance": {
            "description": "Network reconnaissance activity",
            "indicators": lambda p: len(p.unique_destinations) > 50 and p.request_rate < 10,
            "mitre": ["T1595"],
            "severity": "medium",
        },
        "lateral_movement": {
            "description": "Lateral movement detected across internal network",
            "indicators": lambda p: len(p.unique_destinations) > 10 and len(p.unique_ports) > 5,
            "mitre": ["T1021"],
            "severity": "high",
        },
        "data_exfiltration": {
            "description": "Potential data exfiltration",
            "indicators": lambda p: p.avg_payload_size > 100000 and p.request_rate > 2,
            "mitre": ["T1041"],
            "severity": "critical",
        },
    }
    
    def detect(self, profile: BehaviorProfile) -> List[Tuple[str, dict]]:
        """Return list of (threat_type, signature_info) matches"""
        detections = []
        for threat_type, sig in self.SIGNATURES.items():
            try:
                if sig["indicators"](profile):
                    detections.append((threat_type, sig))
            except Exception:
                pass
        return detections


class MLAnomalyDetector:
    """
    Unsupervised anomaly detection using Isolation Forest
    Automatically adapts to normal traffic patterns
    """
    
    def __init__(self, contamination: float = 0.05):
        self.model = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            max_features=0.8,
            bootstrap=True,
            random_state=42,
            n_jobs=-1,
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names = [
            "request_rate", "unique_ports", "unique_destinations",
            "error_rate", "avg_payload_size", "protocol_diversity",
            "hour_entropy", "port_entropy"
        ]
    
    def extract_features(self, profile: BehaviorProfile) -> np.ndarray:
        protocol_diversity = len(profile.protocol_distribution) / 10.0
        
        # Shannon entropy of hour distribution
        time_total = sum(profile.time_pattern)
        if time_total > 0:
            probs = [h / time_total for h in profile.time_pattern if h > 0]
            hour_entropy = -sum(p * math.log2(p) for p in probs) / math.log2(24)
        else:
            hour_entropy = 0.0
        
        # Port entropy
        port_count = len(profile.unique_ports)
        port_entropy = min(port_count / 65535.0, 1.0)
        
        return np.array([
            profile.request_rate,
            len(profile.unique_ports),
            len(profile.unique_destinations),
            profile.error_rate,
            profile.avg_payload_size / 10000.0,
            protocol_diversity,
            hour_entropy,
            port_entropy,
        ])
    
    def fit(self, profiles: List[BehaviorProfile]):
        if not profiles:
            return
        X = np.array([self.extract_features(p) for p in profiles])
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
        logger.info(f"Anomaly detector fitted on {len(profiles)} profiles")
    
    def predict(self, profile: BehaviorProfile) -> Tuple[bool, float]:
        """Returns (is_anomaly, anomaly_score 0-1)"""
        if not self.is_fitted:
            # Auto-train with synthetic normal data if not fitted
            self._auto_initialize()
        
        features = self.extract_features(profile).reshape(1, -1)
        features_scaled = self.scaler.transform(features)
        
        prediction = self.model.predict(features_scaled)[0]
        score = self.model.decision_function(features_scaled)[0]
        
        # Normalize score to 0-1 (higher = more anomalous)
        normalized_score = max(0.0, min(1.0, (0.5 - score)))
        
        return prediction == -1, normalized_score
    
    def _auto_initialize(self):
        """Initialize with synthetic normal traffic data"""
        np.random.seed(42)
        n_samples = 1000
        
        # Simulate normal traffic patterns
        normal_data = np.column_stack([
            np.random.exponential(2, n_samples),   # request_rate
            np.random.randint(1, 5, n_samples),    # unique_ports
            np.random.randint(1, 10, n_samples),   # unique_destinations
            np.random.beta(1, 10, n_samples),      # error_rate
            np.random.exponential(0.1, n_samples), # avg_payload_size
            np.random.uniform(0, 0.3, n_samples),  # protocol_diversity
            np.random.uniform(0.5, 1.0, n_samples),# hour_entropy
            np.random.uniform(0, 0.01, n_samples), # port_entropy
        ])
        
        self.scaler.fit(normal_data)
        normal_scaled = self.scaler.transform(normal_data)
        self.model.fit(normal_scaled)
        self.is_fitted = True
        logger.info("Anomaly detector auto-initialized with synthetic data")


class ThreatIntelligenceEngine:
    """
    Threat Intelligence feeds integration
    Maintains known malicious IPs, domains, and patterns
    """
    
    def __init__(self):
        # Known malicious IP ranges (examples - in production, load from threat feeds)
        self.malicious_ip_prefixes = set([
            "10.0.0.",  # For demo - internal
        ])
        
        self.tor_exit_nodes: set = set()
        self.known_scanners: set = set()
        self.botnet_c2: set = set()
        
        # Reputation scores (0-100, higher = worse)
        self.ip_reputation: Dict[str, int] = {}
        
    def check_ip_reputation(self, ip: str) -> Tuple[int, List[str]]:
        """Returns (reputation_score, threat_categories)"""
        score = 0
        categories = []
        
        # Check known threats
        if ip in self.tor_exit_nodes:
            score += 50
            categories.append("tor_exit_node")
        
        if ip in self.known_scanners:
            score += 60
            categories.append("known_scanner")
            
        if ip in self.botnet_c2:
            score += 90
            categories.append("botnet_c2")
        
        if ip in self.ip_reputation:
            score = max(score, self.ip_reputation[ip])
        
        return score, categories
    
    def is_known_threat(self, ip: str) -> bool:
        return ip in self.tor_exit_nodes or ip in self.known_scanners or ip in self.botnet_c2


class ExtremeIPGuardMLEngine:
    """
    Master threat detection orchestrator
    Combines: Signature Detection + ML Anomaly Detection + Behavioral Analysis + Threat Intelligence
    """
    
    def __init__(self):
        self.behavior_analyzer = BehaviorAnalyzer(window_size=300)
        self.signature_engine = ThreatSignatureEngine()
        self.anomaly_detector = MLAnomalyDetector()
        self.threat_intel = ThreatIntelligenceEngine()
        
        # Risk scoring weights
        self.weights = {
            "signature": 0.35,
            "anomaly": 0.30,
            "behavior_deviation": 0.20,
            "threat_intel": 0.15,
        }
        
        logger.info("Extreme IP Guard ML Engine initialized")
    
    def analyze(self, ip: str, event: dict) -> ThreatPrediction:
        """
        Full threat analysis pipeline
        Returns comprehensive ThreatPrediction
        """
        # 1. Update behavioral profile
        profile = self.behavior_analyzer.update_profile(ip, event)
        
        # 2. Signature-based detection
        signature_detections = self.signature_engine.detect(profile)
        
        # 3. ML anomaly detection
        is_anomaly, anomaly_score = self.anomaly_detector.predict(profile)
        
        # 4. Behavioral deviation score
        deviation_score = self.behavior_analyzer.compute_deviation_score(ip, profile)
        
        # 5. Threat intelligence check
        ti_score, ti_categories = self.threat_intel.check_ip_reputation(ip)
        ti_normalized = ti_score / 100.0
        
        # Composite risk score
        signature_score = min(len(signature_detections) * 0.3, 1.0)
        
        risk_score = (
            signature_score * self.weights["signature"] +
            anomaly_score * self.weights["anomaly"] +
            deviation_score * self.weights["behavior_deviation"] +
            ti_normalized * self.weights["threat_intel"]
        )
        
        # Determine threat categories and MITRE techniques
        threat_categories = [d[0] for d in signature_detections] + ti_categories
        if is_anomaly and not threat_categories:
            threat_categories.append("anomaly")
        
        mitre_techniques = []
        for _, sig in signature_detections:
            mitre_techniques.extend(sig.get("mitre", []))
        
        # Generate human-readable explanation
        explanation = self._generate_explanation(
            profile, signature_detections, is_anomaly, anomaly_score, ti_categories
        )
        
        # Confidence based on multiple signals agreeing
        signal_count = sum([
            len(signature_detections) > 0,
            is_anomaly,
            deviation_score > 0.5,
            ti_normalized > 0.3,
        ])
        confidence = min(0.5 + signal_count * 0.15, 0.99)
        
        is_threat = risk_score >= 0.25 or len(signature_detections) > 0 or is_anomaly
        
        # Update baseline for normal traffic
        if not is_threat:
            self.behavior_analyzer.update_baseline(ip, profile)
        
        return ThreatPrediction(
            is_threat=is_threat,
            confidence=confidence,
            anomaly_score=anomaly_score,
            threat_categories=threat_categories,
            risk_score=round(risk_score * 100, 2),
            mitre_techniques=mitre_techniques,
            explanation=explanation,
        )
    
    def _generate_explanation(
        self,
        profile: BehaviorProfile,
        signature_detections: list,
        is_anomaly: bool,
        anomaly_score: float,
        ti_categories: list,
    ) -> List[str]:
        explanations = []
        
        for threat_type, sig in signature_detections:
            explanations.append(
                f"[SIGNATURE] {sig['description']} - Severity: {sig['severity'].upper()}"
            )
        
        if is_anomaly:
            explanations.append(
                f"[ML-ANOMALY] Behavioral anomaly detected (score: {anomaly_score:.2f})"
            )
        
        if profile.request_rate > 50:
            explanations.append(
                f"[RATE] High request rate: {profile.request_rate:.1f} req/s"
            )
        
        if len(profile.unique_ports) > 15:
            explanations.append(
                f"[SCAN] {len(profile.unique_ports)} unique ports accessed"
            )
        
        for cat in ti_categories:
            explanations.append(f"[THREAT-INTEL] IP classified as: {cat.replace('_', ' ').upper()}")
        
        return explanations
    
    def get_statistics(self) -> dict:
        total_profiles = len(self.behavior_analyzer.profiles)
        high_risk = sum(
            1 for ip, w in self.behavior_analyzer.event_windows.items()
            if len(w) > 50
        )
        
        return {
            "total_tracked_ips": total_profiles,
            "high_activity_ips": high_risk,
            "model_fitted": self.anomaly_detector.is_fitted,
            "threat_intel_size": len(self.threat_intel.ip_reputation),
        }


# Singleton instance
_engine_instance: Optional[ExtremeIPGuardMLEngine] = None


def get_ml_engine() -> ExtremeIPGuardMLEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ExtremeIPGuardMLEngine()
    return _engine_instance
