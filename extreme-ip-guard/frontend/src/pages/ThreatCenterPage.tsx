import React, { useEffect, useState } from 'react';
import { AlertTriangle, Shield, Target, Cpu, Info } from 'lucide-react';
import { CyberCard } from '../components/ui/CyberCard';
import { ThreatBadge, RiskScoreBar } from '../components/ui/ThreatBadge';
import { useMonitoringStore } from '../store';
import { analyticsApi } from '../utils/api';
import {
  getCountryFlag, getCategoryIcon, formatTimestamp, timeAgo
} from '../utils/helpers';
import type { TopThreat } from '../types';
import { cn } from '../utils/helpers';

const MITRE_TACTICS: Record<string, { color: string; label: string }> = {
  'T1046': { color: '#a855f7', label: 'Discovery' },
  'T1110': { color: '#ef4444', label: 'Credential Access' },
  'T1498': { color: '#f97316', label: 'Impact' },
  'T1595': { color: '#3b82f6', label: 'Reconnaissance' },
  'T1021': { color: '#eab308', label: 'Lateral Movement' },
  'T1041': { color: '#ec4899', label: 'Exfiltration' },
};

export function ThreatCenterPage() {
  const { recentThreats } = useMonitoringStore();
  const [topThreats, setTopThreats] = useState<TopThreat[]>([]);
  const [selectedThreat, setSelectedThreat] = useState<any>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await analyticsApi.getTopThreats(10);
        setTopThreats(res.data.threats || []);
      } catch {}
    };
    fetch();
    const interval = setInterval(fetch, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-4 md:p-6 space-y-6 overflow-auto">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 text-red-400" />
          Threat Intelligence Center
        </h1>
        <p className="text-gray-500 text-sm mt-1">MITRE ATT&CK mapped threat analysis and intelligence</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {/* Active Threats List */}
        <div className="xl:col-span-1 space-y-3">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <Target className="w-4 h-4 text-red-400" />
            Active Threat Sources
          </h3>

          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {topThreats.map((threat) => (
              <CyberCard
                key={threat.ip}
                className={cn(
                  'p-3 cursor-pointer transition-all',
                  selectedThreat?.ip === threat.ip && 'border-cyber-accent/40 bg-cyber-accent/5'
                )}
                onClick={() => setSelectedThreat(threat)}
                glow={selectedThreat?.ip === threat.ip}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{getCountryFlag(threat.country_code)}</span>
                    <div>
                      <div className="font-mono text-white text-sm">{threat.ip}</div>
                      <div className="text-xs text-gray-500">{threat.country}</div>
                    </div>
                  </div>
                  {threat.is_blocked && (
                    <span className="text-[10px] font-mono text-red-400 bg-red-500/10 border border-red-500/20 px-2 py-0.5 rounded">
                      BLOCKED
                    </span>
                  )}
                </div>
                <RiskScoreBar score={threat.risk_score} />
                <div className="flex flex-wrap gap-1 mt-2">
                  {threat.threat_types.map((type) => (
                    <span key={type} className="text-[9px] font-mono px-1.5 py-0.5 bg-cyber-border rounded text-gray-400">
                      {getCategoryIcon(type)} {type}
                    </span>
                  ))}
                </div>
              </CyberCard>
            ))}
          </div>
        </div>

        {/* Threat Detail Panel */}
        <div className="xl:col-span-2 space-y-4">
          {selectedThreat ? (
            <>
              <CyberCard className="p-5" glow>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center justify-center">
                      <span className="text-2xl">{getCountryFlag(selectedThreat.country_code)}</span>
                    </div>
                    <div>
                      <div className="text-xl font-mono text-white font-bold">{selectedThreat.ip}</div>
                      <div className="text-sm text-gray-400">{selectedThreat.country}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold font-mono text-red-400">{selectedThreat.risk_score}</div>
                    <div className="text-[10px] text-gray-500 uppercase">Risk Score</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-black/20 rounded-lg p-3 border border-cyber-border">
                    <div className="text-[10px] text-gray-500 uppercase mb-1">Threat Events</div>
                    <div className="text-2xl font-mono text-white font-bold">{selectedThreat.threat_count}</div>
                  </div>
                  <div className="bg-black/20 rounded-lg p-3 border border-cyber-border">
                    <div className="text-[10px] text-gray-500 uppercase mb-1">Last Seen</div>
                    <div className="text-sm font-mono text-white">{timeAgo(selectedThreat.last_seen)}</div>
                  </div>
                </div>

                <RiskScoreBar score={selectedThreat.risk_score} />
              </CyberCard>

              {/* MITRE ATT&CK Mapping */}
              <CyberCard className="p-4" glow glowColor="#7c3aed">
                <h4 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                  <Shield className="w-4 h-4 text-purple-400" />
                  MITRE ATT&CK Techniques
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  {Object.entries(MITRE_TACTICS).map(([technique, info]) => (
                    <div
                      key={technique}
                      className="flex items-center gap-2 p-2 rounded-lg border"
                      style={{ borderColor: `${info.color}30`, background: `${info.color}10` }}
                    >
                      <div className="w-1 h-8 rounded-full" style={{ background: info.color }} />
                      <div>
                        <div className="text-xs font-mono font-semibold text-white">{technique}</div>
                        <div className="text-[10px] text-gray-400">{info.label}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CyberCard>

              {/* Attack Types */}
              <CyberCard className="p-4" glow glowColor="#f97316">
                <h4 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                  <Cpu className="w-4 h-4 text-orange-400" />
                  Attack Techniques Observed
                </h4>
                <div className="space-y-2">
                  {selectedThreat.threat_types.map((type: string) => (
                    <div key={type} className="flex items-center gap-3 p-2 rounded-lg bg-black/20 border border-cyber-border">
                      <span className="text-xl">{getCategoryIcon(type)}</span>
                      <div className="flex-1">
                        <div className="text-sm text-white capitalize">{type.replace(/_/g, ' ')}</div>
                        <div className="text-[10px] text-gray-500">Detected pattern</div>
                      </div>
                      <ThreatBadge level="high" />
                    </div>
                  ))}
                </div>
              </CyberCard>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center h-64">
              <div className="text-center text-gray-600">
                <Info className="w-12 h-12 mx-auto mb-3 opacity-20" />
                <p className="text-sm">Select a threat source to view details</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recent threat events */}
      <CyberCard className="p-4" glow glowColor="#ef4444">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
          <AlertTriangle className="w-4 h-4 text-red-400" />
          Recent Threat Events
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-cyber-border">
                <th className="text-left pb-2 font-mono text-gray-600 uppercase text-[10px]">Time</th>
                <th className="text-left pb-2 font-mono text-gray-600 uppercase text-[10px]">Source</th>
                <th className="text-left pb-2 font-mono text-gray-600 uppercase text-[10px]">Country</th>
                <th className="text-left pb-2 font-mono text-gray-600 uppercase text-[10px]">Category</th>
                <th className="text-left pb-2 font-mono text-gray-600 uppercase text-[10px]">Level</th>
                <th className="text-left pb-2 font-mono text-gray-600 uppercase text-[10px]">Confidence</th>
                <th className="text-left pb-2 font-mono text-gray-600 uppercase text-[10px]">Explanation</th>
              </tr>
            </thead>
            <tbody>
              {recentThreats.slice(0, 20).map((threat, idx) => (
                <tr key={idx} className="border-b border-cyber-border/30 hover:bg-white/[0.01]">
                  <td className="py-2 text-gray-600 font-mono text-[10px]">
                    {formatTimestamp(threat.timestamp)}
                  </td>
                  <td className="py-2 font-mono text-white">{threat.source_ip}</td>
                  <td className="py-2">
                    <span title={threat.country}>{getCountryFlag(threat.country_code)}</span>
                  </td>
                  <td className="py-2 text-gray-400">
                    {getCategoryIcon(threat.threat_categories?.[0] || 'anomaly')}{' '}
                    {threat.threat_categories?.[0] || 'anomaly'}
                  </td>
                  <td className="py-2">
                    <ThreatBadge level={threat.threat_level || 'low'} />
                  </td>
                  <td className="py-2">
                    <div className="flex items-center gap-1">
                      <div className="w-16 bg-gray-700 rounded-full h-1">
                        <div
                          className="h-1 rounded-full bg-cyber-accent"
                          style={{ width: `${(threat.confidence || 0) * 100}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-gray-500">
                        {((threat.confidence || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </td>
                  <td className="py-2 text-gray-500 max-w-[200px] truncate text-[10px]">
                    {threat.explanation?.[0] || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CyberCard>
    </div>
  );
}
