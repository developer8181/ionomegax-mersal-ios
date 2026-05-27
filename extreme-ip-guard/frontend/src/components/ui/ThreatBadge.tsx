import React from 'react';
import { cn, getThreatLevelBg, getThreatLevelColor } from '../../utils/helpers';
import type { ThreatLevel } from '../../types';

interface ThreatBadgeProps {
  level: ThreatLevel;
  pulse?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function ThreatBadge({ level, pulse, size = 'sm' }: ThreatBadgeProps) {
  const sizeClasses = {
    sm: 'text-[10px] px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3 py-1.5',
  };

  return (
    <span className={cn(
      'inline-flex items-center gap-1 font-mono font-semibold uppercase tracking-widest rounded border',
      getThreatLevelBg(level),
      getThreatLevelColor(level),
      sizeClasses[size],
    )}>
      {pulse && level === 'critical' && (
        <span className="relative flex h-1.5 w-1.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-red-500" />
        </span>
      )}
      {level}
    </span>
  );
}

interface RiskScoreBarProps {
  score: number;
  showLabel?: boolean;
}

export function RiskScoreBar({ score, showLabel = true }: RiskScoreBarProps) {
  const color = score >= 80 ? '#ef4444' : score >= 60 ? '#f97316' : score >= 40 ? '#eab308' : '#3b82f6';
  
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-700/50 rounded-full h-1.5 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${score}%`, backgroundColor: color }}
        />
      </div>
      {showLabel && (
        <span className="text-xs font-mono min-w-[32px] text-right" style={{ color }}>
          {score}
        </span>
      )}
    </div>
  );
}
