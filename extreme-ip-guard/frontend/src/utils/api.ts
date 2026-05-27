import axios from 'axios';
import { useAuthStore } from '../store';

const API_BASE = '/api';

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  me: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
};

// Monitoring
export const monitoringApi = {
  getStats: () => api.get('/monitoring/stats'),
  getEvents: (limit = 100) => api.get(`/monitoring/events?limit=${limit}`),
  getThreats: (limit = 50) => api.get(`/monitoring/threats?limit=${limit}`),
  start: () => api.post('/monitoring/start'),
  stop: () => api.post('/monitoring/stop'),
  blockIP: (ip: string) => api.post(`/monitoring/block-ip/${ip}`),
  unblockIP: (ip: string) => api.delete(`/monitoring/block-ip/${ip}`),
  getBlockedIPs: () => api.get('/monitoring/blocked-ips'),
};

// Analytics
export const analyticsApi = {
  getThreatTimeline: (hours = 24) => api.get(`/analytics/threat-timeline?hours=${hours}`),
  getGeoDistribution: () => api.get('/analytics/geo-distribution'),
  getAttackCategories: () => api.get('/analytics/attack-categories'),
  getTopThreats: (limit = 10) => api.get(`/analytics/top-threats?limit=${limit}`),
  getNetworkTopology: () => api.get('/analytics/network-topology'),
  getPerformance: () => api.get('/analytics/performance'),
  getSummary: () => api.get('/analytics/summary'),
};

// Policies
export const policiesApi = {
  list: () => api.get('/policies'),
  create: (data: object) => api.post('/policies', data),
  get: (id: string) => api.get(`/policies/${id}`),
  update: (id: string, data: object) => api.put(`/policies/${id}`, data),
  delete: (id: string) => api.delete(`/policies/${id}`),
  toggle: (id: string) => api.post(`/policies/${id}/toggle`),
};

// WebSocket connection
export function createWebSocket(token?: string): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  const url = `${protocol}//${host}/api/monitoring/ws${token ? `?token=${token}` : ''}`;
  return new WebSocket(url);
}
