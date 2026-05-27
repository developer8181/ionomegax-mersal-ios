import React, { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, PieChart as PieIcon } from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, LineChart, Line
} from 'recharts';
import { CyberCard } from '../components/ui/CyberCard';
import { analyticsApi } from '../utils/api';
import type { ThreatTimelineEntry, AttackCategory } from '../types';

export function AnalyticsPage() {
  const [timeline, setTimeline] = useState<ThreatTimelineEntry[]>([]);
  const [categories, setCategories] = useState<AttackCategory[]>([]);
  const [hourly, setHourly] = useState(24);

  useEffect(() => {
    const fetch = async () => {
      try {
        const [tl, cat] = await Promise.all([
          analyticsApi.getThreatTimeline(hourly),
          analyticsApi.getAttackCategories(),
        ]);
        setTimeline(tl.data.timeline || []);
        setCategories(cat.data.categories || []);
      } catch {}
    };
    fetch();
    const interval = setInterval(fetch, 30000);
    return () => clearInterval(interval);
  }, [hourly]);

  const totalThreats = timeline.reduce((sum, t) => sum + t.critical + t.high + t.medium + t.low, 0);
  const totalEvents = timeline.reduce((sum, t) => sum + t.total_events, 0);

  return (
    <div className="p-4 md:p-6 space-y-6 overflow-auto">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-cyber-accent" />
            Security Analytics
          </h1>
          <p className="text-gray-500 text-sm mt-1">Historical data analysis and trend visualization</p>
        </div>
        <div className="flex gap-2">
          {[12, 24, 48, 168].map((h) => (
            <button
              key={h}
              onClick={() => setHourly(h)}
              className={`px-3 py-1.5 text-xs font-mono rounded-lg border transition-all ${
                hourly === h
                  ? 'bg-cyber-accent/10 text-cyber-accent border-cyber-accent/30'
                  : 'text-gray-500 border-cyber-border hover:text-white'
              }`}
            >
              {h >= 168 ? '7D' : `${h}H`}
            </button>
          ))}
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Events', value: totalEvents.toLocaleString(), color: 'text-cyber-accent' },
          { label: 'Total Threats', value: totalThreats.toLocaleString(), color: 'text-red-400' },
          { label: 'Threat Rate', value: `${totalEvents > 0 ? ((totalThreats / totalEvents) * 100).toFixed(2) : 0}%`, color: 'text-yellow-400' },
          { label: 'Peak Hour', value: timeline.reduce((max, t) => t.critical + t.high > max.val ? { val: t.critical + t.high, time: t.time } : max, { val: 0, time: '—' }).time, color: 'text-orange-400' },
        ].map((item) => (
          <CyberCard key={item.label} className="p-4 text-center">
            <div className={`text-2xl font-bold font-mono ${item.color} mb-1`}>{item.value}</div>
            <div className="text-[11px] text-gray-500 uppercase tracking-wider">{item.label}</div>
          </CyberCard>
        ))}
      </div>

      {/* Area chart - full timeline */}
      <CyberCard className="p-4" glow>
        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
          <TrendingUp className="w-4 h-4 text-cyber-accent" />
          Threat Distribution Over Time
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={timeline}>
            <defs>
              {['critical', 'high', 'medium', 'low'].map((level, idx) => {
                const colors = ['#ef4444', '#f97316', '#eab308', '#3b82f6'];
                return (
                  <linearGradient key={level} id={`grad_${level}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={colors[idx]} stopOpacity={0.4} />
                    <stop offset="95%" stopColor={colors[idx]} stopOpacity={0.0} />
                  </linearGradient>
                );
              })}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a2d4d" />
            <XAxis dataKey="time" stroke="#4b5563" tick={{ fontSize: 9 }} />
            <YAxis stroke="#4b5563" tick={{ fontSize: 9 }} />
            <Tooltip
              contentStyle={{ background: '#0d1628', border: '1px solid #1a2d4d', borderRadius: '8px', fontSize: 11 }}
            />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
            <Area type="monotone" dataKey="critical" stroke="#ef4444" fill="url(#grad_critical)" strokeWidth={1.5} />
            <Area type="monotone" dataKey="high" stroke="#f97316" fill="url(#grad_high)" strokeWidth={1.5} />
            <Area type="monotone" dataKey="medium" stroke="#eab308" fill="url(#grad_medium)" strokeWidth={1.5} />
            <Area type="monotone" dataKey="low" stroke="#3b82f6" fill="url(#grad_low)" strokeWidth={1.5} />
          </AreaChart>
        </ResponsiveContainer>
      </CyberCard>

      {/* Events vs Threats Bar */}
      <CyberCard className="p-4" glow glowColor="#00ff88">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
          <BarChart3 className="w-4 h-4 text-green-400" />
          Events vs Threats
        </h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={timeline.slice(-12)}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1a2d4d" />
            <XAxis dataKey="time" stroke="#4b5563" tick={{ fontSize: 9 }} />
            <YAxis stroke="#4b5563" tick={{ fontSize: 9 }} />
            <Tooltip
              contentStyle={{ background: '#0d1628', border: '1px solid #1a2d4d', borderRadius: '8px', fontSize: 11 }}
            />
            <Legend wrapperStyle={{ fontSize: '11px' }} />
            <Bar dataKey="total_events" fill="#00d4ff" fillOpacity={0.6} radius={[2, 2, 0, 0]} name="Total Events" />
            <Bar
              dataKey={(entry) => entry.critical + entry.high + entry.medium + entry.low}
              fill="#ef4444"
              fillOpacity={0.7}
              radius={[2, 2, 0, 0]}
              name="Threats"
            />
          </BarChart>
        </ResponsiveContainer>
      </CyberCard>

      {/* Attack Categories Donut */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <CyberCard className="p-4" glow glowColor="#7c3aed">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
            <PieIcon className="w-4 h-4 text-purple-400" />
            Attack Type Distribution
          </h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={categories}
                cx="50%"
                cy="50%"
                innerRadius={70}
                outerRadius={110}
                paddingAngle={2}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {categories.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#0d1628', border: '1px solid #1a2d4d', borderRadius: '8px', fontSize: 11 }}
              />
            </PieChart>
          </ResponsiveContainer>
        </CyberCard>

        {/* Category breakdown */}
        <CyberCard className="p-4" glow>
          <h3 className="text-sm font-semibold text-white mb-4">Attack Category Breakdown</h3>
          <div className="space-y-3">
            {categories.map((cat) => {
              const total = categories.reduce((sum, c) => sum + c.value, 0);
              const pct = total > 0 ? (cat.value / total) * 100 : 0;
              return (
                <div key={cat.name}>
                  <div className="flex items-center justify-between mb-1 text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: cat.color }} />
                      <span className="text-gray-300">{cat.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-500">{cat.value}</span>
                      <span className="text-gray-600 w-10 text-right">{pct.toFixed(1)}%</span>
                    </div>
                  </div>
                  <div className="h-1 bg-gray-700/50 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${pct}%`, background: cat.color }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </CyberCard>
      </div>
    </div>
  );
}
