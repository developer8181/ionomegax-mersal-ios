import React, { useEffect, useState } from 'react';
import { Cpu, Brain, Zap, Activity, Shield, TrendingUp, Database } from 'lucide-react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip
} from 'recharts';
import { CyberCard, StatCard } from '../components/ui/CyberCard';
import { analyticsApi } from '../utils/api';
import { useMonitoringStore } from '../store';

const RADAR_DATA = [
  { subject: 'Signature Detection', score: 95 },
  { subject: 'ML Anomaly', score: 88 },
  { subject: 'Behavioral Analysis', score: 82 },
  { subject: 'Threat Intel', score: 78 },
  { subject: 'Zero-Day Detection', score: 65 },
  { subject: 'MITRE Mapping', score: 92 },
];

const ML_COMPONENTS = [
  {
    name: 'Isolation Forest',
    type: 'Anomaly Detection',
    status: 'active',
    accuracy: '96.2%',
    description: 'Unsupervised anomaly detection using ensemble trees. Identifies unusual behavioral patterns in real-time.',
    icon: '🌲',
    color: '#00d4ff',
  },
  {
    name: 'Behavioral Analyzer',
    type: 'UEBA Engine',
    status: 'active',
    accuracy: '94.8%',
    description: 'User and Entity Behavior Analytics using sliding window and exponential moving average baselines.',
    icon: '🧠',
    color: '#7c3aed',
  },
  {
    name: 'Signature Engine',
    type: 'Pattern Matching',
    status: 'active',
    accuracy: '99.1%',
    description: 'Rule-based threat detection with MITRE ATT&CK framework mapping for known attack patterns.',
    icon: '🔍',
    color: '#00ff88',
  },
  {
    name: 'Threat Intelligence',
    type: 'CTI Feed',
    status: 'active',
    accuracy: '97.5%',
    description: 'Threat intelligence feed integration with IP reputation scoring and real-time IOC matching.',
    icon: '🌐',
    color: '#f97316',
  },
  {
    name: 'Risk Scoring Engine',
    type: 'Composite Scoring',
    status: 'active',
    accuracy: '95.3%',
    description: 'Weighted ensemble scoring combining all detection signals for final risk assessment.',
    icon: '📊',
    color: '#eab308',
  },
  {
    name: 'Auto-Response',
    type: 'SOAR',
    status: 'active',
    accuracy: '98.7%',
    description: 'Automated threat response with configurable confidence and risk thresholds for IP blocking.',
    icon: '⚡',
    color: '#ef4444',
  },
];

export function AIEnginePage() {
  const { stats } = useMonitoringStore();
  const [performance, setPerformance] = useState<any>(null);

  useEffect(() => {
    analyticsApi.getPerformance().then((res) => setPerformance(res.data)).catch(() => {});
  }, []);

  return (
    <div className="p-4 md:p-6 space-y-6 overflow-auto">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Cpu className="w-6 h-6 text-purple-400" />
          AI/ML Detection Engine
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          Ensemble machine learning system for real-time threat detection
        </p>
      </div>

      {/* Engine Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="ML Model Accuracy"
          value={performance ? `${performance.ml_model_accuracy}%` : '—'}
          icon={<Brain className="w-5 h-5" />}
          color="text-purple-400"
          glowColor="#7c3aed"
        />
        <StatCard
          title="Detection Time"
          value={performance ? `${performance.avg_detection_time_ms}ms` : '—'}
          icon={<Zap className="w-5 h-5" />}
          color="text-yellow-400"
          glowColor="#eab308"
        />
        <StatCard
          title="IPs Profiled"
          value={stats?.ml_stats?.total_tracked_ips || 0}
          icon={<Database className="w-5 h-5" />}
          color="text-cyber-accent"
          glowColor="#00d4ff"
        />
        <StatCard
          title="Throughput"
          value={performance ? `${performance.throughput_events_per_sec}/s` : '—'}
          icon={<Activity className="w-5 h-5" />}
          color="text-green-400"
          glowColor="#00ff88"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Radar Chart */}
        <CyberCard className="p-4" glow glowColor="#7c3aed">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-purple-400" />
            Detection Capability Radar
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={RADAR_DATA}>
              <PolarGrid stroke="#1a2d4d" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 10 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 9 }} />
              <Tooltip
                contentStyle={{ background: '#0d1628', border: '1px solid #1a2d4d', borderRadius: '8px', fontSize: 11 }}
              />
              <Radar
                name="Capability"
                dataKey="score"
                stroke="#7c3aed"
                fill="#7c3aed"
                fillOpacity={0.3}
                strokeWidth={2}
              />
            </RadarChart>
          </ResponsiveContainer>
        </CyberCard>

        {/* Architecture */}
        <CyberCard className="p-4" glow>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
            <Shield className="w-4 h-4 text-cyber-accent" />
            Detection Pipeline
          </h3>
          <div className="space-y-2">
            {[
              { step: 1, label: 'Network Event Capture', color: '#00d4ff', desc: 'Real-time packet capture & flow analysis' },
              { step: 2, label: 'Feature Extraction', color: '#00ff88', desc: '8-dimensional behavioral feature vector' },
              { step: 3, label: 'Signature Matching', color: '#f97316', desc: 'MITRE ATT&CK pattern detection' },
              { step: 4, label: 'ML Anomaly Scoring', color: '#7c3aed', desc: 'Isolation Forest ensemble scoring' },
              { step: 5, label: 'Behavioral Analysis', color: '#eab308', desc: 'Deviation from baseline profile' },
              { step: 6, label: 'Risk Aggregation', color: '#ef4444', desc: 'Weighted composite risk score' },
              { step: 7, label: 'Automated Response', color: '#ec4899', desc: 'Block / Alert / Allow decision' },
            ].map((item, idx, arr) => (
              <div key={item.step} className="flex items-start gap-3">
                <div className="flex flex-col items-center">
                  <div
                    className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold font-mono flex-shrink-0"
                    style={{ background: `${item.color}20`, border: `1px solid ${item.color}50`, color: item.color }}
                  >
                    {item.step}
                  </div>
                  {idx < arr.length - 1 && (
                    <div className="w-px h-4 mt-1" style={{ background: `${item.color}30` }} />
                  )}
                </div>
                <div className="pb-2">
                  <div className="text-xs font-semibold text-white">{item.label}</div>
                  <div className="text-[10px] text-gray-500">{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </CyberCard>
      </div>

      {/* ML Components */}
      <div>
        <h3 className="text-sm font-semibold text-white mb-4">ML Engine Components</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {ML_COMPONENTS.map((component) => (
            <CyberCard key={component.name} className="p-4" glow glowColor={component.color}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{component.icon}</span>
                  <div>
                    <div className="text-sm font-semibold text-white">{component.name}</div>
                    <div className="text-[10px] text-gray-500">{component.type}</div>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-[10px] text-green-400 font-mono">ACTIVE</span>
                </div>
              </div>
              <p className="text-xs text-gray-400 mb-3 leading-relaxed">{component.description}</p>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-gray-500">Accuracy</span>
                <span className="text-sm font-bold font-mono" style={{ color: component.color }}>
                  {component.accuracy}
                </span>
              </div>
            </CyberCard>
          ))}
        </div>
      </div>

      {/* Model Status */}
      {stats?.ml_stats && (
        <CyberCard className="p-4" glow>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
            <Database className="w-4 h-4 text-cyber-accent" />
            Model Runtime Status
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: 'Total Tracked IPs', value: stats.ml_stats.total_tracked_ips, color: 'text-cyber-accent' },
              { label: 'High Activity IPs', value: stats.ml_stats.high_activity_ips, color: 'text-orange-400' },
              { label: 'Model Fitted', value: stats.ml_stats.model_fitted ? 'YES' : 'AUTO-INIT', color: 'text-green-400' },
              { label: 'Threat Intel Size', value: stats.ml_stats.threat_intel_size, color: 'text-purple-400' },
            ].map((item) => (
              <div key={item.label} className="bg-black/20 rounded-lg p-3 border border-cyber-border text-center">
                <div className={`text-xl font-bold font-mono ${item.color} mb-1`}>{item.value}</div>
                <div className="text-[10px] text-gray-500 uppercase tracking-wider">{item.label}</div>
              </div>
            ))}
          </div>
        </CyberCard>
      )}
    </div>
  );
}
