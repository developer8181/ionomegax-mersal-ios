import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  User,
  MonitoringStats,
  NetworkEvent,
  ThreatEvent,
  SecurityPolicy,
} from '../types';

interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setAuth: (user, token) => set({ user, token, isAuthenticated: true }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
    }),
    { name: 'extreme-ipguard-auth' }
  )
);

interface MonitoringStore {
  stats: MonitoringStats | null;
  recentEvents: NetworkEvent[];
  recentThreats: ThreatEvent[];
  isConnected: boolean;
  isMonitoring: boolean;
  setStats: (stats: MonitoringStats) => void;
  addEvents: (events: NetworkEvent[]) => void;
  addThreats: (threats: ThreatEvent[]) => void;
  setConnected: (connected: boolean) => void;
  setMonitoring: (monitoring: boolean) => void;
}

export const useMonitoringStore = create<MonitoringStore>((set) => ({
  stats: null,
  recentEvents: [],
  recentThreats: [],
  isConnected: false,
  isMonitoring: false,
  setStats: (stats) => set({ stats, isMonitoring: stats.is_monitoring }),
  addEvents: (events) =>
    set((state) => ({
      recentEvents: [...events, ...state.recentEvents].slice(0, 500),
    })),
  addThreats: (threats) =>
    set((state) => ({
      recentThreats: [...threats, ...state.recentThreats].slice(0, 200),
    })),
  setConnected: (isConnected) => set({ isConnected }),
  setMonitoring: (isMonitoring) => set({ isMonitoring }),
}));

interface UIStore {
  sidebarOpen: boolean;
  activeTab: string;
  setSidebarOpen: (open: boolean) => void;
  setActiveTab: (tab: string) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  sidebarOpen: true,
  activeTab: 'dashboard',
  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  setActiveTab: (activeTab) => set({ activeTab }),
}));
