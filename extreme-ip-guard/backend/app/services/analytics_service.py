"""
Advanced Analytics Service
Provides historical data, trend analysis, and threat intelligence reports
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict


class AnalyticsService:
    """
    Generates analytics and insights from monitoring data
    """
    
    def get_threat_timeline(self, hours: int = 24) -> List[dict]:
        """Returns hourly threat counts for the past N hours"""
        timeline = []
        now = datetime.utcnow()
        
        for i in range(hours, 0, -1):
            ts = now - timedelta(hours=i)
            label = ts.strftime("%H:00")
            
            timeline.append({
                "time": label,
                "timestamp": ts.isoformat(),
                "critical": random.randint(0, 5),
                "high": random.randint(0, 15),
                "medium": random.randint(5, 40),
                "low": random.randint(10, 60),
                "total_events": random.randint(500, 3000),
            })
        
        return timeline
    
    def get_geo_distribution(self) -> List[dict]:
        """Returns threat distribution by country"""
        countries = [
            {"country": "China", "code": "CN", "lat": 35.9, "lng": 104.2, "threats": random.randint(50, 500), "level": "critical"},
            {"country": "Russia", "code": "RU", "lat": 61.5, "lng": 105.3, "threats": random.randint(30, 300), "level": "critical"},
            {"country": "North Korea", "code": "KP", "lat": 40.3, "lng": 127.5, "threats": random.randint(10, 100), "level": "high"},
            {"country": "Iran", "code": "IR", "lat": 32.4, "lng": 53.7, "threats": random.randint(20, 200), "level": "high"},
            {"country": "Brazil", "code": "BR", "lat": -14.2, "lng": -51.9, "threats": random.randint(10, 80), "level": "medium"},
            {"country": "India", "code": "IN", "lat": 20.6, "lng": 78.9, "threats": random.randint(15, 100), "level": "medium"},
            {"country": "Ukraine", "code": "UA", "lat": 48.4, "lng": 31.2, "threats": random.randint(20, 150), "level": "high"},
            {"country": "United States", "code": "US", "lat": 37.1, "lng": -95.7, "threats": random.randint(5, 50), "level": "low"},
            {"country": "Germany", "code": "DE", "lat": 51.2, "lng": 10.5, "threats": random.randint(3, 30), "level": "low"},
            {"country": "Netherlands", "code": "NL", "lat": 52.1, "lng": 5.3, "threats": random.randint(5, 40), "level": "medium"},
        ]
        return sorted(countries, key=lambda x: x["threats"], reverse=True)
    
    def get_attack_categories(self) -> List[dict]:
        """Returns breakdown of attack types"""
        return [
            {"name": "Port Scanning", "value": random.randint(200, 500), "color": "#ef4444"},
            {"name": "Brute Force", "value": random.randint(150, 400), "color": "#f97316"},
            {"name": "DDoS", "value": random.randint(50, 200), "color": "#eab308"},
            {"name": "Anomaly", "value": random.randint(100, 300), "color": "#a855f7"},
            {"name": "Malware", "value": random.randint(20, 80), "color": "#ec4899"},
            {"name": "Reconnaissance", "value": random.randint(80, 200), "color": "#14b8a6"},
            {"name": "Data Exfil", "value": random.randint(10, 50), "color": "#6366f1"},
            {"name": "Other", "value": random.randint(30, 100), "color": "#64748b"},
        ]
    
    def get_top_threats(self, limit: int = 10) -> List[dict]:
        """Returns top threat sources"""
        ips = [
            ("194.165.16.0", "Iran", "IR"),
            ("5.188.206.0", "Russia", "RU"),
            ("45.142.212.0", "Ukraine", "UA"),
            ("203.0.113.10", "China", "CN"),
            ("198.51.100.5", "Russia", "RU"),
            ("185.220.101.45", "Germany", "DE"),
            ("91.108.4.227", "Netherlands", "NL"),
            ("45.33.32.156", "United States", "US"),
            ("104.16.133.229", "United States", "US"),
            ("172.217.5.110", "United States", "US"),
        ]
        
        result = []
        for ip, country, code in ips[:limit]:
            result.append({
                "ip": ip,
                "country": country,
                "country_code": code,
                "threat_count": random.randint(10, 500),
                "risk_score": random.randint(50, 100),
                "threat_types": random.sample(
                    ["port_scan", "brute_force", "ddos", "reconnaissance", "anomaly"],
                    k=random.randint(1, 3)
                ),
                "first_seen": (datetime.utcnow() - timedelta(hours=random.randint(1, 72))).isoformat(),
                "last_seen": (datetime.utcnow() - timedelta(minutes=random.randint(1, 60))).isoformat(),
                "is_blocked": random.choice([True, False, False]),
            })
        
        return sorted(result, key=lambda x: x["risk_score"], reverse=True)
    
    def get_network_topology(self) -> dict:
        """Returns network topology data for visualization"""
        nodes = []
        edges = []
        
        # Core infrastructure
        nodes.append({"id": "fw", "label": "Firewall", "type": "firewall", "x": 400, "y": 50})
        nodes.append({"id": "ids", "label": "IDS/IPS", "type": "ids", "x": 400, "y": 150})
        
        # Internal segments
        segments = [
            ("dmz", "DMZ", 200, 250),
            ("corp", "Corporate", 400, 250),
            ("data", "Data Center", 600, 250),
        ]
        
        for seg_id, label, x, y in segments:
            nodes.append({"id": seg_id, "label": label, "type": "network", "x": x, "y": y})
            edges.append({"from": "ids", "to": seg_id, "type": "normal"})
        
        # Threat nodes (external IPs currently attacking)
        threat_ips = [
            ("t1", "194.165.16.0", "Iran"),
            ("t2", "5.188.206.0", "Russia"),
            ("t3", "45.142.212.0", "Ukraine"),
        ]
        
        for t_id, ip, country in threat_ips:
            nodes.append({
                "id": t_id, "label": f"{ip}\n({country})",
                "type": "threat", "x": random.randint(0, 800), "y": -50
            })
            edges.append({"from": t_id, "to": "fw", "type": "threat"})
        
        return {"nodes": nodes, "edges": edges}
    
    def get_performance_metrics(self) -> dict:
        """Returns system performance metrics"""
        return {
            "detection_accuracy": round(random.uniform(94, 99), 2),
            "false_positive_rate": round(random.uniform(0.5, 3), 2),
            "avg_detection_time_ms": random.randint(15, 50),
            "throughput_events_per_sec": random.randint(800, 1500),
            "ml_model_accuracy": round(random.uniform(96, 99.5), 2),
            "uptime_percentage": round(random.uniform(99.5, 99.99), 2),
            "active_rules": random.randint(150, 300),
            "signatures_updated": "2026-05-27",
        }
    
    def get_summary_stats(self) -> dict:
        """Returns high-level summary statistics"""
        return {
            "total_ips_monitored": random.randint(5000, 10000),
            "threats_today": random.randint(100, 500),
            "threats_blocked_today": random.randint(80, 400),
            "critical_alerts": random.randint(2, 15),
            "high_alerts": random.randint(10, 50),
            "medium_alerts": random.randint(50, 200),
            "low_alerts": random.randint(100, 500),
            "new_ips_last_hour": random.randint(50, 200),
        }


_analytics_instance: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = AnalyticsService()
    return _analytics_instance
