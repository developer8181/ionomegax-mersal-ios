import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { ThreatLevel } from '../types';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function getThreatLevelColor(level: ThreatLevel): string {
  const colors = {
    critical: 'text-red-400',
    high: 'text-orange-400',
    medium: 'text-yellow-400',
    low: 'text-blue-400',
    info: 'text-gray-400',
  };
  return colors[level] || colors.info;
}

export function getThreatLevelBg(level: ThreatLevel): string {
  const colors = {
    critical: 'bg-red-500/20 border-red-500/40',
    high: 'bg-orange-500/20 border-orange-500/40',
    medium: 'bg-yellow-500/20 border-yellow-500/40',
    low: 'bg-blue-500/20 border-blue-500/40',
    info: 'bg-gray-500/20 border-gray-500/40',
  };
  return colors[level] || colors.info;
}

export function getThreatLevelGlow(level: ThreatLevel): string {
  const colors = {
    critical: 'shadow-red-500/30',
    high: 'shadow-orange-500/30',
    medium: 'shadow-yellow-500/30',
    low: 'shadow-blue-500/30',
    info: 'shadow-gray-500/30',
  };
  return colors[level] || colors.info;
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

export function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

export function formatTimestamp(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return ts;
  }
}

export function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    port_scan: '🔍',
    brute_force: '🔨',
    ddos: '💥',
    malware: '🦠',
    intrusion: '🚨',
    data_exfiltration: '📤',
    anomaly: '⚠️',
    policy_violation: '📋',
    reconnaissance: '👁️',
    lateral_movement: '↔️',
    zero_day: '💀',
  };
  return icons[category] || '❓';
}

export function getMITRETactic(technique: string): string {
  const tactics: Record<string, string> = {
    'T1046': 'Discovery',
    'T1110': 'Credential Access',
    'T1498': 'Impact',
    'T1595': 'Reconnaissance',
    'T1021': 'Lateral Movement',
    'T1041': 'Exfiltration',
  };
  return tactics[technique] || 'Unknown';
}

export function getCountryFlag(code: string): string {
  if (!code || code.length !== 2) return '🌐';
  const codePoints = code
    .toUpperCase()
    .split('')
    .map((char) => 127397 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
}

export function getRiskScoreColor(score: number): string {
  if (score >= 80) return 'text-red-400';
  if (score >= 60) return 'text-orange-400';
  if (score >= 40) return 'text-yellow-400';
  if (score >= 20) return 'text-blue-400';
  return 'text-green-400';
}

export function truncateIP(ip: string): string {
  return ip;
}

export function timeAgo(timestamp: string): string {
  const now = Date.now();
  const ts = new Date(timestamp).getTime();
  const diff = Math.floor((now - ts) / 1000);

  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}
