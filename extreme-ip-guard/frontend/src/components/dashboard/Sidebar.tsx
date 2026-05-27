import React from 'react';
import {
  Shield, Activity, AlertTriangle, Globe, FileText,
  Settings, LogOut, ChevronLeft, ChevronRight,
  Cpu, Lock, Radio, BarChart3, Users
} from 'lucide-react';
import { cn } from '../../utils/helpers';
import { useUIStore, useAuthStore, useMonitoringStore } from '../../store';
import { authApi } from '../../utils/api';
import toast from 'react-hot-toast';

const MENU_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: Activity, group: 'main' },
  { id: 'threats', label: 'Threat Center', icon: AlertTriangle, group: 'main' },
  { id: 'monitor', label: 'Live Monitor', icon: Radio, group: 'main' },
  { id: 'analytics', label: 'Analytics', icon: BarChart3, group: 'analytics' },
  { id: 'geo', label: 'Geo Intelligence', icon: Globe, group: 'analytics' },
  { id: 'policies', label: 'Security Policies', icon: Lock, group: 'security' },
  { id: 'ai-engine', label: 'AI Engine', icon: Cpu, group: 'security' },
  { id: 'reports', label: 'Reports', icon: FileText, group: 'reports' },
  { id: 'users', label: 'Users', icon: Users, group: 'reports' },
  { id: 'settings', label: 'Settings', icon: Settings, group: 'system' },
];

const GROUPS = {
  main: 'OPERATIONS',
  analytics: 'INTELLIGENCE',
  security: 'SECURITY',
  reports: 'MANAGEMENT',
  system: 'SYSTEM',
};

export function Sidebar() {
  const { sidebarOpen, setSidebarOpen, activeTab, setActiveTab } = useUIStore();
  const { user, logout } = useAuthStore();
  const { isConnected, isMonitoring } = useMonitoringStore();

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {}
    logout();
    toast.success('Logged out successfully');
  };

  const groups = Object.entries(GROUPS);

  return (
    <aside
      className={cn(
        'flex flex-col bg-cyber-panel border-r border-cyber-border transition-all duration-300 relative z-20 flex-shrink-0',
        sidebarOpen ? 'w-64' : 'w-16'
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-cyber-border flex-shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="relative flex-shrink-0">
            <div className="w-8 h-8 bg-cyber-accent/10 border border-cyber-accent/40 rounded-lg flex items-center justify-center">
              <Shield className="w-4 h-4 text-cyber-accent" />
            </div>
            <div className={cn(
              'absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border border-cyber-bg',
              isConnected && isMonitoring ? 'bg-green-500 animate-pulse' : 'bg-gray-500'
            )} />
          </div>
          {sidebarOpen && (
            <div className="min-w-0 overflow-hidden">
              <div className="text-white font-bold text-sm leading-tight truncate">EXTREME</div>
              <div className="text-cyber-accent font-mono text-xs leading-tight">IP GUARD v2.0</div>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
        {groups.map(([groupId, groupLabel]) => {
          const items = MENU_ITEMS.filter((item) => item.group === groupId);
          return (
            <div key={groupId} className="mb-3">
              {sidebarOpen && (
                <div className="text-[10px] font-mono text-gray-600 uppercase tracking-widest px-2 mb-1">
                  {groupLabel}
                </div>
              )}
              {items.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={cn(
                      'w-full flex items-center gap-3 px-2 py-2 rounded-lg transition-all duration-150 group',
                      isActive
                        ? 'bg-cyber-accent/10 text-cyber-accent border border-cyber-accent/20'
                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                    )}
                    title={!sidebarOpen ? item.label : undefined}
                  >
                    <Icon className={cn('w-4 h-4 flex-shrink-0', isActive && 'drop-shadow-[0_0_6px_rgba(0,212,255,0.8)]')} />
                    {sidebarOpen && (
                      <span className="text-sm font-medium truncate">{item.label}</span>
                    )}
                    {isActive && sidebarOpen && (
                      <div className="ml-auto w-1 h-4 rounded-full bg-cyber-accent" />
                    )}
                  </button>
                );
              })}
            </div>
          );
        })}
      </nav>

      {/* User section */}
      <div className="border-t border-cyber-border p-3 space-y-2 flex-shrink-0">
        {sidebarOpen && user && (
          <div className="flex items-center gap-2 px-2 py-1">
            <div className="w-7 h-7 rounded-full bg-cyber-accent/20 border border-cyber-accent/40 flex items-center justify-center flex-shrink-0">
              <span className="text-cyber-accent text-xs font-bold">
                {user.full_name.charAt(0)}
              </span>
            </div>
            <div className="min-w-0">
              <div className="text-white text-xs font-medium truncate">{user.full_name}</div>
              <div className="text-gray-500 text-[10px] uppercase tracking-wider">{user.role}</div>
            </div>
          </div>
        )}

        <button
          onClick={handleLogout}
          className={cn(
            'w-full flex items-center gap-3 px-2 py-2 rounded-lg text-gray-400',
            'hover:text-red-400 hover:bg-red-500/10 transition-all duration-150'
          )}
          title={!sidebarOpen ? 'Logout' : undefined}
        >
          <LogOut className="w-4 h-4 flex-shrink-0" />
          {sidebarOpen && <span className="text-sm">Logout</span>}
        </button>
      </div>

      {/* Collapse button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-cyber-panel border border-cyber-border rounded-full flex items-center justify-center text-gray-400 hover:text-cyber-accent hover:border-cyber-accent/50 transition-all z-30"
      >
        {sidebarOpen ? (
          <ChevronLeft className="w-3 h-3" />
        ) : (
          <ChevronRight className="w-3 h-3" />
        )}
      </button>
    </aside>
  );
}
