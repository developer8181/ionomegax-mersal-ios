import React from 'react';
import { Shield, Wifi, WifiOff, Bell, Activity } from 'lucide-react';
import { cn, formatNumber } from '../../utils/helpers';
import { useMonitoringStore, useAuthStore } from '../../store';
import { monitoringApi } from '../../utils/api';
import toast from 'react-hot-toast';

export function Header() {
  const { isConnected, isMonitoring, stats } = useMonitoringStore();
  const { user } = useAuthStore();

  const handleToggleMonitoring = async () => {
    try {
      if (isMonitoring) {
        await monitoringApi.stop();
        toast.success('Monitoring paused');
      } else {
        await monitoringApi.start();
        toast.success('Monitoring activated');
      }
    } catch (err) {
      toast.error('Failed to toggle monitoring');
    }
  };

  return (
    <header className="h-14 bg-cyber-panel border-b border-cyber-border flex items-center px-4 gap-4 flex-shrink-0 z-10">
      {/* Status indicators */}
      <div className="flex items-center gap-3">
        <div className={cn(
          'flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-full border',
          isConnected
            ? 'text-green-400 border-green-500/30 bg-green-500/10'
            : 'text-gray-500 border-gray-600/30 bg-gray-500/10'
        )}>
          {isConnected ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
          {isConnected ? 'LIVE' : 'OFFLINE'}
        </div>

        <button
          onClick={handleToggleMonitoring}
          className={cn(
            'flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-full border transition-all',
            isMonitoring
              ? 'text-cyber-accent border-cyber-accent/30 bg-cyber-accent/10 hover:bg-cyber-accent/20'
              : 'text-gray-500 border-gray-600/30 bg-gray-500/10 hover:bg-gray-500/20'
          )}
        >
          <Activity className={cn('w-3 h-3', isMonitoring && 'animate-pulse')} />
          {isMonitoring ? 'MONITORING' : 'PAUSED'}
        </button>
      </div>

      {/* Live metrics */}
      {stats && (
        <div className="flex items-center gap-4 ml-4">
          <div className="hidden md:flex items-center gap-1.5 text-xs">
            <span className="text-gray-500">Events/s:</span>
            <span className="text-cyber-accent font-mono font-semibold">
              {stats.events_per_second || 0}
            </span>
          </div>
          <div className="hidden md:flex items-center gap-1.5 text-xs">
            <span className="text-gray-500">Threats:</span>
            <span className="text-red-400 font-mono font-semibold">
              {formatNumber(stats.threats_detected || 0)}
            </span>
          </div>
          <div className="hidden lg:flex items-center gap-1.5 text-xs">
            <span className="text-gray-500">Blocked:</span>
            <span className="text-orange-400 font-mono font-semibold">
              {stats.blocked_ips || 0}
            </span>
          </div>
        </div>
      )}

      <div className="ml-auto flex items-center gap-3">
        {/* Threat rate indicator */}
        {stats && (
          <div className={cn(
            'hidden sm:flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-full border',
            (stats.threat_rate || 0) > 10
              ? 'text-red-400 border-red-500/30 bg-red-500/5'
              : 'text-green-400 border-green-500/30 bg-green-500/5'
          )}>
            <Shield className="w-3 h-3" />
            {stats.threat_rate?.toFixed(1)}% THREAT RATE
          </div>
        )}

        {/* Notifications */}
        <button className="relative p-2 text-gray-400 hover:text-white transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
        </button>

        {/* User badge */}
        {user && (
          <div className="flex items-center gap-2 pl-3 border-l border-cyber-border">
            <div className="w-7 h-7 rounded-full bg-cyber-accent/20 border border-cyber-accent/40 flex items-center justify-center">
              <span className="text-cyber-accent text-xs font-bold">
                {user.full_name.charAt(0)}
              </span>
            </div>
            <span className="text-xs text-gray-300 hidden sm:block">{user.full_name}</span>
          </div>
        )}
      </div>
    </header>
  );
}
