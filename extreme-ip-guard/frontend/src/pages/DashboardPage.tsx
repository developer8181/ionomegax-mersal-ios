import React, { useEffect, useState } from 'react';
import {
  Shield, AlertTriangle, Activity, Ban, Cpu, Globe,
  TrendingUp, Eye, Zap, CheckCircle
} from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { StatCard, CyberCard } from '../components/ui/CyberCard';
import { ThreatBadge, RiskScoreBar } from '../components/ui/ThreatBadge';
import { useMonitoringStore } from '../store';
import { analyticsApi } from '../utils/api';
import {
  formatNumber, formatTimestamp, getCountryFlag,
  getThreatLevelColor, getCategoryIcon
} from '../utils/helpers';
import type { ThreatTimelineEntry, AttackCategory, TopThreat } from '../types';

const CHART_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
};

export function DashboardPage() {
  const { stats, recentThreats } = useMonitoringStore();
  const [timeline, setTimeline] = useState<ThreatTimelineEntry[]>([]);
  const [categories, setCategories] = useState<AttackCategory[]>([]);
  const [topThreats, setTopThreats] = useState<TopThreat[]>([]);
  const [performance, setPerformance] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [timelineRes, catRes, topRes, perfRes] = await Promise.all([
          analyticsApi.getThreatTimeline(12),
          analyticsApi.getAttackCategories(),
          analyticsApi.getTopThreats(5),
          analyticsApi.getPerformance(),
        ]);
        setTimeline(timelineRes.data.timeline || []);
        setCategories(catRes.data.categories || []);
        setTopThreats(topRes.data.threats || []);
        setPerformance(perfRes.data);
      } catch (err) {
        console.error('Failed to fetch analytics:', err);
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-4 md:p-6 space-y-6 overflow-auto">
      {/* Page title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Shield className="text-cyber-accent w-6 h-6" />
            Security Dashboard
          </h1>
          <p className="text-gray-500 text-sm mt-1">Real-time threat monitoring and analytics</p>
        </div>
        <div className="text-xs font-mono text-gray-500 bg-cyber-panel border border-cyber-border px-3 py-1.5 rounded-full">
          {new Date().toLocaleString()}
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Events"
          value={formatNumber(stats?.total_events || 0)}
          icon={<Activity className="w-5 h-5" />}
          subtitle="Since monitoring started"
          color="text-cyber-accent"
          glowColor="#00d4ff"
        />
        <StatCard
          title="Threats Detected"
          value={formatNumber(stats?.threats_detected || 0)}
          icon={<AlertTriangle className="w-5 h-5" />}
          subtitle={`${stats?.threat_rate?.toFixed(1) || 0}% threat rate`}
          color="text-red-400"
          glowColor="#ef4444"
          trend={12}
        />
        <StatCard
          title="IPs Blocked"
          value={stats?.blocked_ips || 0}
          icon={<Ban className="w-5 h-5" />}
          subtitle="Auto-blocked by AI"
          color="text-orange-400"
          glowColor="#f97316"
        />
        <StatCard
          title="Events/Second"
          value={stats?.events_per_second || 0}
          icon={<Zap className="w-5 h-5" />}
          subtitle="Current throughput"
          color="text-yellow-400"
          glowColor="#eab308"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Threat Timeline */}
        <CyberCard className="lg:col-span-2 p-4" glow>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-cyber-accent" />
              Threat Timeline (12 Hours)
            </h3>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={timeline}>
              <defs>
                <linearGradient id="critGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="highGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="medGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#eab308" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#eab308" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a2d4d" />
              <XAxis dataKey="time" stroke="#4b5563" tick={{ fontSize: 10 }} />
              <YAxis stroke="#4b5563" tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: '#0d1628', border: '1px solid #1a2d4d', borderRadius: '8px' }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Legend wrapperStyle={{ fontSize: '11px' }} />
              <Area type="monotone" dataKey="critical" stroke="#ef4444" fill="url(#critGrad)" strokeWidth={2} />
              <Area type="monotone" dataKey="high" stroke="#f97316" fill="url(#highGrad)" strokeWidth={2} />
              <Area type="monotone" dataKey="medium" stroke="#eab308" fill="url(#medGrad)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </CyberCard>

        {/* Attack Categories Pie */}
        <CyberCard className="p-4" glow glowColor="#7c3aed">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
            <Eye className="w-4 h-4 text-purple-400" />
            Attack Categories
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={categories}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
              >
                {categories.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#0d1628', border: '1px solid #1a2d4d', borderRadius: '8px', fontSize: 11 }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="grid grid-cols-2 gap-1 mt-2">
            {categories.slice(0, 6).map((cat) => (
              <div key={cat.name} className="flex items-center gap-1.5 text-[10px] text-gray-400">
                <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: cat.color }} />
                <span className="truncate">{cat.name}</span>
              </div>
            ))}
          </div>
        </CyberCard>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Top Threats */}
        <CyberCard className="p-4" glow glowColor="#ef4444">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
            <AlertTriangle className="w-4 h-4 text-red-400" />
            Top Threat Sources
          </h3>
          <div className="space-y-3">
            {topThreats.map((threat, idx) => (
              <div key={threat.ip} className="flex items-center gap-3">
                <div className="text-[10px] font-mono text-gray-600 w-4">{idx + 1}</div>
                <div className="text-lg leading-none" title={threat.country}>
                  {getCountryFlag(threat.country_code)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono text-white">{threat.ip}</span>
                    <span className="text-[10px] text-gray-500">{threat.threat_count} events</span>
                  </div>
                  <RiskScoreBar score={threat.risk_score} />
                </div>
                {threat.is_blocked && (
                  <Ban className="w-3 h-3 text-red-400 flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
        </CyberCard>

        {/* Recent Threat Events */}
        <CyberCard className="p-4" glow glowColor="#f97316">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
            <Activity className="w-4 h-4 text-orange-400" />
            Recent Threat Events
          </h3>
          <div className="space-y-2 max-h-[220px] overflow-y-auto custom-scroll">
            {recentThreats.slice(0, 8).map((threat, idx) => (
              <div
                key={idx}
                className="flex items-start gap-2 p-2 rounded-lg bg-black/20 border border-cyber-border/50 text-xs"
              >
                <span className="text-lg leading-none flex-shrink-0">
                  {getCategoryIcon(threat.threat_categories?.[0] || 'anomaly')}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="font-mono text-white">{threat.source_ip}</span>
                    <ThreatBadge level={threat.threat_level || 'low'} />
                  </div>
                  <div className="text-gray-500 truncate">
                    {threat.threat_categories?.join(', ') || 'anomaly'} →{' '}
                    {threat.destination_ip}:{threat.destination_port}
                  </div>
                </div>
                <span className="text-[10px] text-gray-600 flex-shrink-0">
                  {formatTimestamp(threat.timestamp)}
                </span>
              </div>
            ))}
            {recentThreats.length === 0 && (
              <div className="text-center text-gray-600 py-8 text-xs">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 opacity-30" />
                No threats detected yet
              </div>
            )}
          </div>
        </CyberCard>
      </div>

      {/* Performance Metrics */}
      {performance && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Detection Accuracy', value: `${performance.detection_accuracy}%`, color: 'text-green-400' },
            { label: 'False Positive Rate', value: `${performance.false_positive_rate}%`, color: 'text-yellow-400' },
            { label: 'Avg Detection Time', value: `${performance.avg_detection_time_ms}ms`, color: 'text-cyber-accent' },
            { label: 'ML Model Accuracy', value: `${performance.ml_model_accuracy}%`, color: 'text-purple-400' },
          ].map((metric) => (
            <CyberCard key={metric.label} className="p-4 text-center">
              <div className={`text-2xl font-bold font-mono ${metric.color} mb-1`}>
                {metric.value}
              </div>
              <div className="text-[11px] text-gray-500 uppercase tracking-wider">{metric.label}</div>
            </CyberCard>
          ))}
        </div>
      )}
    </div>
  );
}
