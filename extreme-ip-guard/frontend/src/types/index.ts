export type ThreatLevel = 'critical' | 'high' | 'medium' | 'low' | 'info';

export type ThreatCategory =
  | 'port_scan'
  | 'brute_force'
  | 'ddos'
  | 'malware'
  | 'intrusion'
  | 'data_exfiltration'
  | 'anomaly'
  | 'policy_violation'
  | 'reconnaissance'
  | 'lateral_movement'
  | 'zero_day';

export interface NetworkEvent {
  id?: string;
  source_ip: string;
  destination_ip: string;
  source_port: number;
  destination_port: number;
  protocol: string;
  bytes_sent: number;
  bytes_received: number;
  status_code: number;
  country: string;
  country_code: string;
  latitude: number;
  longitude: number;
  is_threat: boolean;
  is_ml_threat?: boolean;
  threat_level?: ThreatLevel;
  threat_categories?: string[];
  risk_score?: number;
  anomaly_score?: number;
  confidence?: number;
  mitre_techniques?: string[];
  explanation?: string[];
  action?: string;
  auto_blocked?: boolean;
  timestamp: string;
  scenario?: string;
}

export interface ThreatEvent extends NetworkEvent {
  threat_level: ThreatLevel;
  threat_categories: string[];
  risk_score: number;
}

export interface MonitoringStats {
  total_events: number;
  threats_detected: number;
  blocked_ips: number;
  events_per_second: number;
  threat_rate: number;
  monitored_ips: number;
  ml_stats: {
    total_tracked_ips: number;
    high_activity_ips: number;
    model_fitted: boolean;
    threat_intel_size: number;
  };
  is_monitoring: boolean;
  active_connections?: number;
}

export interface SecurityPolicy {
  id: string;
  name: string;
  description?: string;
  is_active: boolean;
  priority: number;
  action: 'allow' | 'block' | 'monitor' | 'alert' | 'quarantine' | 'rate_limit';
  source_ip_range?: string;
  destination_ports?: number[];
  protocols?: string[];
  countries?: string[];
  risk_score_min?: number;
  times_triggered: number;
  created_by: string;
  created_at: string;
}

export interface GeoThreat {
  country: string;
  code: string;
  lat: number;
  lng: number;
  threats: number;
  level: ThreatLevel;
}

export interface ThreatTimelineEntry {
  time: string;
  timestamp: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
  total_events: number;
}

export interface AttackCategory {
  name: string;
  value: number;
  color: string;
}

export interface TopThreat {
  ip: string;
  country: string;
  country_code: string;
  threat_count: number;
  risk_score: number;
  threat_types: string[];
  first_seen: string;
  last_seen: string;
  is_blocked: boolean;
}

export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'analyst' | 'viewer';
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

export interface WSMessage {
  type: string;
  timestamp?: string;
  stats?: Partial<MonitoringStats>;
  events?: NetworkEvent[];
  threats?: ThreatEvent[];
  recent_threats?: ThreatEvent[];
  message?: string;
}
