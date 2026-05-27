import React, { useState } from 'react';
import { Radio, AlertTriangle, Shield, Ban, CheckCircle, Activity } from 'lucide-react';
import { CyberCard } from '../components/ui/CyberCard';
import { ThreatBadge } from '../components/ui/ThreatBadge';
import { useMonitoringStore } from '../store';
import { monitoringApi } from '../utils/api';
import {
  formatTimestamp, formatBytes, getCountryFlag,
  getCategoryIcon, getThreatLevelColor
} from '../utils/helpers';
import type { NetworkEvent } from '../types';
import toast from 'react-hot-toast';
import { cn } from '../utils/helpers';

export function LiveMonitorPage() {
  const { recentEvents, recentThreats, stats, isMonitoring } = useMonitoringStore();
  const [filter, setFilter] = useState<'all' | 'threats' | 'blocked'>('all');
  const [blockingIP, setBlockingIP] = useState<string | null>(null);

  const handleBlockIP = async (ip: string) => {
    setBlockingIP(ip);
    try {
      await monitoringApi.blockIP(ip);
      toast.success(`IP ${ip} blocked successfully`);
    } catch {
      toast.error('Failed to block IP');
    } finally {
      setBlockingIP(null);
    }
  };

  const filteredEvents: NetworkEvent[] = filter === 'threats'
    ? recentThreats
    : filter === 'blocked'
    ? recentEvents.filter((e) => e.action === 'blocked' || e.auto_blocked)
    : recentEvents;

  return (
    <div className="p-4 md:p-6 space-y-4 overflow-auto">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Radio className={cn('w-6 h-6', isMonitoring ? 'text-green-400 animate-pulse' : 'text-gray-500')} />
            Live Network Monitor
          </h1>
          <p className="text-gray-500 text-sm mt-1">Real-time traffic analysis and threat detection</p>
        </div>

        {/* Filter tabs */}
        <div className="flex gap-2">
          {(['all', 'threats', 'blocked'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                'px-3 py-1.5 text-xs font-mono uppercase tracking-wider rounded-lg border transition-all',
                filter === f
                  ? 'bg-cyber-accent/10 text-cyber-accent border-cyber-accent/30'
                  : 'text-gray-500 border-cyber-border hover:text-white'
              )}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Mini stats */}
      <div className="grid grid-cols-3 gap-3">
        <CyberCard className="p-3 flex items-center gap-3">
          <Activity className="w-4 h-4 text-cyber-accent flex-shrink-0" />
          <div>
            <div className="text-lg font-bold font-mono text-cyber-accent">{stats?.events_per_second || 0}</div>
            <div className="text-[10px] text-gray-500">Events/sec</div>
          </div>
        </CyberCard>
        <CyberCard className="p-3 flex items-center gap-3">
          <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
          <div>
            <div className="text-lg font-bold font-mono text-red-400">{recentThreats.length}</div>
            <div className="text-[10px] text-gray-500">Active Threats</div>
          </div>
        </CyberCard>
        <CyberCard className="p-3 flex items-center gap-3">
          <Ban className="w-4 h-4 text-orange-400 flex-shrink-0" />
          <div>
            <div className="text-lg font-bold font-mono text-orange-400">{stats?.blocked_ips || 0}</div>
            <div className="text-[10px] text-gray-500">Blocked IPs</div>
          </div>
        </CyberCard>
      </div>

      {/* Event Stream */}
      <CyberCard className="overflow-hidden" glow>
        <div className="flex items-center gap-2 px-4 py-3 border-b border-cyber-border">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs font-mono text-green-400">LIVE STREAM</span>
          <span className="text-xs text-gray-600 ml-auto">{filteredEvents.length} events</span>
        </div>

        {/* Table header */}
        <div className="grid grid-cols-12 gap-2 px-4 py-2 border-b border-cyber-border text-[10px] font-mono text-gray-600 uppercase tracking-wider">
          <div className="col-span-1">Time</div>
          <div className="col-span-2">Source IP</div>
          <div className="col-span-2">Destination</div>
          <div className="col-span-1">Proto</div>
          <div className="col-span-1">Country</div>
          <div className="col-span-1">Level</div>
          <div className="col-span-2">Category</div>
          <div className="col-span-1">Risk</div>
          <div className="col-span-1">Action</div>
        </div>

        <div className="overflow-y-auto max-h-[calc(100vh-420px)] min-h-[300px]">
          {filteredEvents.slice(0, 100).map((event, idx) => (
            <div
              key={idx}
              className={cn(
                'grid grid-cols-12 gap-2 px-4 py-2 border-b border-cyber-border/30 text-xs',
                'hover:bg-white/[0.02] transition-colors group',
                event.threat_level === 'critical' && 'bg-red-500/5',
                event.threat_level === 'high' && 'bg-orange-500/5',
                event.auto_blocked && 'bg-red-500/10',
              )}
            >
              <div className="col-span-1 text-gray-600 font-mono text-[10px] self-center">
                {formatTimestamp(event.timestamp)}
              </div>
              <div className="col-span-2 font-mono text-white self-center truncate">
                {event.source_ip}
              </div>
              <div className="col-span-2 font-mono text-gray-400 self-center truncate text-[10px]">
                {event.destination_ip}:{event.destination_port}
              </div>
              <div className="col-span-1 text-gray-500 self-center text-[10px] font-mono">
                {event.protocol}
              </div>
              <div className="col-span-1 self-center">
                <span title={event.country} className="text-base">
                  {getCountryFlag(event.country_code)}
                </span>
              </div>
              <div className="col-span-1 self-center">
                {event.threat_level && event.threat_level !== 'info' ? (
                  <ThreatBadge level={event.threat_level} pulse={event.threat_level === 'critical'} />
                ) : (
                  <span className="text-[10px] text-gray-600 font-mono">—</span>
                )}
              </div>
              <div className="col-span-2 self-center text-[10px] text-gray-400 truncate">
                {event.threat_categories?.length
                  ? `${getCategoryIcon(event.threat_categories[0])} ${event.threat_categories[0]}`
                  : <span className="text-gray-700">normal</span>
                }
              </div>
              <div className="col-span-1 self-center">
                <span className={cn('font-mono text-[10px]', getThreatLevelColor(event.threat_level || 'info'))}>
                  {event.risk_score?.toFixed(0) || '—'}
                </span>
              </div>
              <div className="col-span-1 self-center flex items-center gap-1">
                {event.action === 'blocked' || event.auto_blocked ? (
                  <span className="text-red-400 text-[10px] font-mono flex items-center gap-1">
                    <Ban className="w-2.5 h-2.5" /> BLOCKED
                  </span>
                ) : event.action === 'alert' ? (
                  <span className="text-yellow-400 text-[10px] font-mono flex items-center gap-1">
                    <AlertTriangle className="w-2.5 h-2.5" /> ALERT
                  </span>
                ) : (
                  <span className="text-green-500/50 text-[10px] font-mono flex items-center gap-1">
                    <CheckCircle className="w-2.5 h-2.5" /> ALLOW
                  </span>
                )}
                {event.is_ml_threat && !event.auto_blocked && (
                  <button
                    onClick={() => handleBlockIP(event.source_ip)}
                    disabled={blockingIP === event.source_ip}
                    className="opacity-0 group-hover:opacity-100 ml-1 p-0.5 rounded bg-red-500/20 text-red-400 hover:bg-red-500/40 transition-all"
                    title="Block IP"
                  >
                    <Ban className="w-2.5 h-2.5" />
                  </button>
                )}
              </div>
            </div>
          ))}

          {filteredEvents.length === 0 && (
            <div className="text-center text-gray-600 py-12 text-sm">
              <Shield className="w-8 h-8 mx-auto mb-3 opacity-20" />
              <p>No events to display</p>
            </div>
          )}
        </div>
      </CyberCard>
    </div>
  );
}
