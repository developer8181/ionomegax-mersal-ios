import React from 'react';
import { cn } from '../../utils/helpers';

interface CyberCardProps {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
  glowColor?: string;
  onClick?: () => void;
}

export function CyberCard({ children, className, glow, glowColor = '#00d4ff', onClick }: CyberCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'relative bg-cyber-panel border border-cyber-border rounded-lg overflow-hidden',
        glow && 'shadow-lg',
        onClick && 'cursor-pointer hover:border-cyber-accent/50 transition-colors',
        className
      )}
      style={glow ? { boxShadow: `0 0 20px ${glowColor}20` } : undefined}
    >
      {/* Top edge glow */}
      {glow && (
        <div
          className="absolute top-0 left-0 right-0 h-[1px] opacity-60"
          style={{ background: `linear-gradient(90deg, transparent, ${glowColor}, transparent)` }}
        />
      )}
      {children}
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: number;
  color?: string;
  glowColor?: string;
}

export function StatCard({ title, value, subtitle, icon, trend, color = 'text-cyber-accent', glowColor = '#00d4ff' }: StatCardProps) {
  return (
    <CyberCard glow glowColor={glowColor} className="p-4 md:p-5">
      <div className="flex items-start justify-between mb-3">
        <div className={cn('p-2 rounded-lg', color.replace('text-', 'bg-').replace('400', '500/10'))}>
          <div className={color}>{icon}</div>
        </div>
        {trend !== undefined && (
          <span className={cn(
            'text-xs font-mono px-2 py-1 rounded-full',
            trend > 0 ? 'text-red-400 bg-red-500/10' : 'text-green-400 bg-green-500/10'
          )}>
            {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </span>
        )}
      </div>
      <div className="space-y-1">
        <div className={cn('text-2xl md:text-3xl font-bold font-mono', color)}>{value}</div>
        <div className="text-xs text-gray-400 font-medium uppercase tracking-wider">{title}</div>
        {subtitle && <div className="text-xs text-gray-500">{subtitle}</div>}
      </div>
    </CyberCard>
  );
}
