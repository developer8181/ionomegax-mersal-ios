"""
Real-time Network Monitoring Service
Manages active monitoring sessions and event processing
"""
import asyncio
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Callable
from collections import defaultdict
import ipaddress
from loguru import logger

from app.ml.threat_detector import get_ml_engine, ThreatPrediction
from app.core.config import settings


class ConnectionManager:
    """WebSocket connection manager for real-time updates"""
    
    def __init__(self):
        self.active_connections: List = []
        self.subscriptions: Dict[str, Set] = defaultdict(set)
    
    async def connect(self, websocket, client_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected: {client_id}")
    
    def disconnect(self, websocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        disconnected = []
        message_str = json.dumps(message)
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_personal(self, message: dict, websocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")


class NetworkEventSimulator:
    """
    Simulates realistic network traffic for demonstration
    Generates a mix of normal and malicious traffic
    """
    
    INTERNAL_IPS = [f"192.168.1.{i}" for i in range(1, 30)]
    EXTERNAL_IPS = [
        "203.0.113.10", "198.51.100.5", "185.220.101.45",
        "45.33.32.156", "104.16.133.229", "172.217.5.110",
        "91.108.4.227", "157.240.22.35", "52.94.236.248",
        "64.233.160.0", "8.8.8.8", "1.1.1.1", "208.67.222.222",
        "45.142.212.0", "194.165.16.0", "5.188.206.0",
        "192.0.2.100", "198.18.0.100", "192.0.2.200",
    ]
    
    COUNTRIES = {
        "203.0.113.10": ("China", "CN", 39.9, 116.4),
        "198.51.100.5": ("Russia", "RU", 55.7, 37.6),
        "185.220.101.45": ("Germany", "DE", 52.5, 13.4),
        "45.33.32.156": ("United States", "US", 37.8, -122.4),
        "104.16.133.229": ("United States", "US", 37.8, -122.4),
        "172.217.5.110": ("United States", "US", 37.4, -122.1),
        "91.108.4.227": ("Netherlands", "NL", 52.4, 4.9),
        "157.240.22.35": ("United States", "US", 37.5, -122.3),
        "52.94.236.248": ("United States", "US", 47.6, -122.3),
        "64.233.160.0": ("United States", "US", 37.4, -122.1),
        "45.142.212.0": ("Ukraine", "UA", 50.4, 30.5),
        "194.165.16.0": ("Iran", "IR", 35.7, 51.4),
        "5.188.206.0": ("Russia", "RU", 55.7, 37.6),
    }
    
    PROTOCOLS = ["TCP", "UDP", "HTTP", "HTTPS", "DNS", "SMTP", "SSH", "FTP", "RDP"]
    PORTS = [80, 443, 22, 3389, 3306, 5432, 8080, 8443, 25, 53, 21, 445, 139]
    
    ATTACK_SCENARIOS = [
        "port_scan",
        "brute_force",
        "ddos",
        "normal",
        "normal",
        "normal",
        "normal",
        "normal",
    ]
    
    def __init__(self):
        self.active_attacks: Dict[str, dict] = {}
        self.traffic_multiplier = 1.0
    
    def generate_event(self) -> dict:
        """Generate a realistic network event"""
        scenario = random.choice(self.ATTACK_SCENARIOS)
        
        if scenario == "port_scan":
            return self._generate_port_scan()
        elif scenario == "brute_force":
            return self._generate_brute_force()
        elif scenario == "ddos":
            return self._generate_ddos()
        else:
            return self._generate_normal_traffic()
    
    def _generate_normal_traffic(self) -> dict:
        src_ip = random.choice(self.EXTERNAL_IPS)
        country_info = self.COUNTRIES.get(src_ip, ("Unknown", "UN", 0, 0))
        
        return {
            "source_ip": src_ip,
            "destination_ip": random.choice(self.INTERNAL_IPS),
            "source_port": random.randint(1024, 65535),
            "destination_port": random.choice([80, 443, 8080]),
            "protocol": random.choice(["HTTP", "HTTPS"]),
            "bytes_sent": random.randint(200, 5000),
            "bytes_received": random.randint(1000, 50000),
            "status_code": random.choices([200, 301, 404, 500], weights=[80, 5, 10, 5])[0],
            "country": country_info[0],
            "country_code": country_info[1],
            "latitude": country_info[2],
            "longitude": country_info[3],
            "is_threat": False,
            "scenario": "normal",
        }
    
    def _generate_port_scan(self) -> dict:
        src_ip = random.choice(["203.0.113.10", "198.51.100.5", "45.142.212.0"])
        country_info = self.COUNTRIES.get(src_ip, ("Unknown", "UN", 0, 0))
        
        return {
            "source_ip": src_ip,
            "destination_ip": random.choice(self.INTERNAL_IPS),
            "source_port": random.randint(40000, 65000),
            "destination_port": random.randint(1, 65535),
            "protocol": "TCP",
            "bytes_sent": random.randint(40, 100),
            "bytes_received": random.randint(0, 60),
            "status_code": random.choice([0, 0, 0, 200]),
            "country": country_info[0],
            "country_code": country_info[1],
            "latitude": country_info[2],
            "longitude": country_info[3],
            "is_threat": True,
            "scenario": "port_scan",
        }
    
    def _generate_brute_force(self) -> dict:
        src_ip = random.choice(["194.165.16.0", "5.188.206.0"])
        country_info = self.COUNTRIES.get(src_ip, ("Unknown", "UN", 0, 0))
        
        return {
            "source_ip": src_ip,
            "destination_ip": random.choice(self.INTERNAL_IPS),
            "source_port": random.randint(30000, 60000),
            "destination_port": random.choice([22, 3389, 21, 3306]),
            "protocol": random.choice(["SSH", "RDP", "FTP"]),
            "bytes_sent": random.randint(200, 500),
            "bytes_received": random.randint(100, 300),
            "status_code": random.choices([401, 403, 200], weights=[85, 10, 5])[0],
            "country": country_info[0],
            "country_code": country_info[1],
            "latitude": country_info[2],
            "longitude": country_info[3],
            "is_threat": True,
            "scenario": "brute_force",
        }
    
    def _generate_ddos(self) -> dict:
        src_ip = random.choice(self.EXTERNAL_IPS)
        country_info = self.COUNTRIES.get(src_ip, ("Unknown", "UN", 0, 0))
        
        return {
            "source_ip": src_ip,
            "destination_ip": random.choice(self.INTERNAL_IPS[:3]),
            "source_port": random.randint(1024, 65535),
            "destination_port": random.choice([80, 443]),
            "protocol": "HTTP",
            "bytes_sent": random.randint(100, 500),
            "bytes_received": random.randint(0, 100),
            "status_code": random.choice([200, 503, 503, 503]),
            "country": country_info[0],
            "country_code": country_info[1],
            "latitude": country_info[2],
            "longitude": country_info[3],
            "is_threat": True,
            "scenario": "ddos",
        }


class MonitoringService:
    """
    Core monitoring service orchestrator
    Manages event pipeline: Capture -> Analyze -> Alert -> Respond
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        self.cm = connection_manager
        self.ml_engine = get_ml_engine()
        self.simulator = NetworkEventSimulator()
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            "total_events": 0,
            "threats_detected": 0,
            "blocked_ips": 0,
            "events_per_second": 0,
        }
        self.blocked_ips: Set[str] = set()
        self.alert_callbacks: List[Callable] = []
        
        # Recent events buffer for dashboard
        self.recent_events = []
        self.recent_threats = []
        self.max_buffer = 1000
        
        # Metrics history for charts
        self.metrics_history = {
            "events": [],
            "threats": [],
            "timestamps": [],
        }
    
    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info("Monitoring service started")
    
    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Monitoring service stopped")
    
    async def _monitoring_loop(self):
        """Main event processing loop"""
        event_count_window = []
        
        while self.is_running:
            try:
                # Generate and process batch of events
                batch_size = random.randint(3, 12)
                events_this_second = []
                
                for _ in range(batch_size):
                    event = self.simulator.generate_event()
                    processed = await self._process_event(event)
                    events_this_second.append(processed)
                
                # Update EPS
                now = time.time()
                event_count_window = [t for t in event_count_window if now - t < 1.0]
                event_count_window.extend([now] * batch_size)
                self.stats["events_per_second"] = len(event_count_window)
                
                # Broadcast dashboard update
                await self._broadcast_update(events_this_second)
                
                await asyncio.sleep(0.5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(1)
    
    async def _process_event(self, event: dict) -> dict:
        """Process a single network event through the analysis pipeline"""
        self.stats["total_events"] += 1
        
        ip = event["source_ip"]
        
        # Check if IP is already blocked
        if ip in self.blocked_ips:
            event["action"] = "blocked"
            event["blocked"] = True
            return event
        
        # ML/AI analysis
        prediction: ThreatPrediction = self.ml_engine.analyze(ip, event)
        
        event["risk_score"] = float(prediction.risk_score)
        event["anomaly_score"] = float(prediction.anomaly_score)
        event["confidence"] = float(prediction.confidence)
        event["threat_categories"] = list(prediction.threat_categories)
        event["mitre_techniques"] = list(prediction.mitre_techniques)
        event["explanation"] = list(prediction.explanation)
        event["is_ml_threat"] = bool(prediction.is_threat)
        event["timestamp"] = datetime.utcnow().isoformat()
        
        # Determine final threat status and action
        if prediction.is_threat:
            self.stats["threats_detected"] += 1
            
            # Auto-block high confidence threats
            if prediction.confidence > 0.8 and prediction.risk_score > 60:
                self.blocked_ips.add(ip)
                self.stats["blocked_ips"] = len(self.blocked_ips)
                event["action"] = "auto_blocked"
                event["auto_blocked"] = True
            else:
                event["action"] = "alert"
            
            # Determine threat level
            if prediction.risk_score >= 80:
                event["threat_level"] = "critical"
            elif prediction.risk_score >= 60:
                event["threat_level"] = "high"
            elif prediction.risk_score >= 40:
                event["threat_level"] = "medium"
            else:
                event["threat_level"] = "low"
            
            # Add to recent threats
            self.recent_threats.insert(0, event.copy())
            self.recent_threats = self.recent_threats[:100]
        else:
            event["action"] = "allow"
            event["threat_level"] = "info"
        
        # Add to recent events buffer
        self.recent_events.insert(0, event.copy())
        self.recent_events = self.recent_events[:self.max_buffer]
        
        return event
    
    async def _broadcast_update(self, events: List[dict]):
        """Broadcast real-time update to WebSocket clients"""
        threats = [e for e in events if e.get("is_ml_threat", False)]
        
        update = {
            "type": "monitoring_update",
            "timestamp": datetime.utcnow().isoformat(),
            "stats": {
                **self.stats,
                "active_connections": len(self.cm.active_connections),
            },
            "events": events[-5:],  # Last 5 events
            "threats": threats,
            "recent_threats": self.recent_threats[:10],
        }
        
        await self.cm.broadcast(update)
    
    def get_dashboard_stats(self) -> dict:
        total = self.stats["total_events"]
        threats = self.stats["threats_detected"]
        
        return {
            "total_events": total,
            "threats_detected": threats,
            "blocked_ips": self.stats["blocked_ips"],
            "events_per_second": self.stats["events_per_second"],
            "threat_rate": round((threats / max(total, 1)) * 100, 2),
            "monitored_ips": len(self.ml_engine.behavior_analyzer.profiles),
            "ml_stats": self.ml_engine.get_statistics(),
            "is_monitoring": self.is_running,
        }
    
    def get_recent_threats(self, limit: int = 50) -> List[dict]:
        return self.recent_threats[:limit]
    
    def get_recent_events(self, limit: int = 100) -> List[dict]:
        return self.recent_events[:limit]
    
    def block_ip(self, ip: str) -> bool:
        self.blocked_ips.add(ip)
        self.stats["blocked_ips"] = len(self.blocked_ips)
        return True
    
    def unblock_ip(self, ip: str) -> bool:
        self.blocked_ips.discard(ip)
        self.stats["blocked_ips"] = len(self.blocked_ips)
        return True
    
    def get_blocked_ips(self) -> List[str]:
        return list(self.blocked_ips)


# Global service instances
_connection_manager: Optional[ConnectionManager] = None
_monitoring_service: Optional[MonitoringService] = None


def get_connection_manager() -> ConnectionManager:
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


def get_monitoring_service() -> MonitoringService:
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService(get_connection_manager())
    return _monitoring_service
