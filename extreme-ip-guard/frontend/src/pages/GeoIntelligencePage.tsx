import React, { useEffect, useState } from 'react';
import { Globe, MapPin, TrendingUp } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts';
import { CyberCard } from '../components/ui/CyberCard';
import { ThreatBadge } from '../components/ui/ThreatBadge';
import { analyticsApi } from '../utils/api';
import { getCountryFlag } from '../utils/helpers';
import type { GeoThreat } from '../types';

const LEVEL_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
  info: '#6b7280',
};

export function GeoIntelligencePage() {
  const [geoData, setGeoData] = useState<GeoThreat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await analyticsApi.getGeoDistribution();
        setGeoData(res.data.distribution || []);
      } catch {}
      setLoading(false);
    };
    fetch();
    const interval = setInterval(fetch, 30000);
    return () => clearInterval(interval);
  }, []);

  const chartData = geoData.slice(0, 10).map((g) => ({
    name: g.code,
    fullName: g.country,
    threats: g.threats,
    color: LEVEL_COLORS[g.level] || '#6b7280',
  }));

  return (
    <div className="p-4 md:p-6 space-y-6 overflow-auto">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Globe className="w-6 h-6 text-cyber-accent" />
          Geo Intelligence
        </h1>
        <p className="text-gray-500 text-sm mt-1">Geographic threat distribution and country-level analysis</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Bar chart */}
        <CyberCard className="p-4" glow>
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-cyber-accent" />
            Threats by Country (Top 10)
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1a2d4d" horizontal={false} />
              <XAxis type="number" stroke="#4b5563" tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="name" stroke="#4b5563" tick={{ fontSize: 10 }} width={30} />
              <Tooltip
                contentStyle={{ background: '#0d1628', border: '1px solid #1a2d4d', borderRadius: '8px', fontSize: 11 }}
                formatter={(value, name, props) => [value, props.payload.fullName]}
              />
              <Bar dataKey="threats" radius={[0, 4, 4, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CyberCard>

        {/* Threat Map Visual */}
        <CyberCard className="p-4" glow glowColor="#7c3aed">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
            <MapPin className="w-4 h-4 text-purple-400" />
            Threat Origin Points
          </h3>
          {/* Simplified world map representation */}
          <div className="relative bg-black/30 rounded-lg overflow-hidden" style={{ height: 280 }}>
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-gray-700 text-xs font-mono">GLOBAL THREAT MAP</div>
            </div>
            {/* Threat dots */}
            {geoData.map((threat, idx) => {
              // Convert lat/lng to relative position
              const x = ((threat.lng + 180) / 360) * 100;
              const y = ((90 - threat.lat) / 180) * 100;
              const size = Math.max(6, Math.min(20, threat.threats / 30));
              const color = LEVEL_COLORS[threat.level] || '#6b7280';
              
              return (
                <div
                  key={idx}
                  className="absolute transform -translate-x-1/2 -translate-y-1/2"
                  style={{ left: `${x}%`, top: `${y}%` }}
                  title={`${threat.country}: ${threat.threats} threats`}
                >
                  <div
                    className="rounded-full animate-ping absolute opacity-30"
                    style={{ width: size * 2, height: size * 2, background: color, top: -size/2, left: -size/2 }}
                  />
                  <div
                    className="rounded-full relative z-10 cursor-pointer hover:scale-150 transition-transform"
                    style={{ width: size, height: size, background: color }}
                  />
                </div>
              );
            })}
            
            {/* Grid lines */}
            <svg className="absolute inset-0 w-full h-full opacity-10" xmlns="http://www.w3.org/2000/svg">
              <defs>
                <pattern id="grid" width="40" height="30" patternUnits="userSpaceOnUse">
                  <path d="M 40 0 L 0 0 0 30" fill="none" stroke="#00d4ff" strokeWidth="0.5"/>
                </pattern>
              </defs>
              <rect width="100%" height="100%" fill="url(#grid)" />
            </svg>
          </div>
          <div className="flex flex-wrap gap-2 mt-3">
            {Object.entries(LEVEL_COLORS).map(([level, color]) => (
              <div key={level} className="flex items-center gap-1 text-[10px] text-gray-400">
                <div className="w-2 h-2 rounded-full" style={{ background: color }} />
                {level}
              </div>
            ))}
          </div>
        </CyberCard>
      </div>

      {/* Country table */}
      <CyberCard className="p-4" glow>
        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-4">
          <Globe className="w-4 h-4 text-cyber-accent" />
          Country Threat Analysis
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-cyber-border">
                <th className="text-left pb-3 font-mono text-gray-600 uppercase text-[10px]">#</th>
                <th className="text-left pb-3 font-mono text-gray-600 uppercase text-[10px]">Country</th>
                <th className="text-left pb-3 font-mono text-gray-600 uppercase text-[10px]">Threats</th>
                <th className="text-left pb-3 font-mono text-gray-600 uppercase text-[10px]">Risk Level</th>
                <th className="text-left pb-3 font-mono text-gray-600 uppercase text-[10px]">Coordinates</th>
              </tr>
            </thead>
            <tbody>
              {geoData.map((geo, idx) => (
                <tr key={geo.code} className="border-b border-cyber-border/30 hover:bg-white/[0.01]">
                  <td className="py-2.5 text-gray-600 font-mono text-[10px]">{idx + 1}</td>
                  <td className="py-2.5">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{getCountryFlag(geo.code)}</span>
                      <div>
                        <div className="text-white font-medium">{geo.country}</div>
                        <div className="text-[10px] text-gray-500 font-mono">{geo.code}</div>
                      </div>
                    </div>
                  </td>
                  <td className="py-2.5">
                    <div className="flex items-center gap-2">
                      <div
                        className="h-1.5 rounded-full"
                        style={{
                          width: `${Math.min((geo.threats / (geoData[0]?.threats || 1)) * 80, 80)}px`,
                          background: LEVEL_COLORS[geo.level]
                        }}
                      />
                      <span className="font-mono text-white">{geo.threats.toLocaleString()}</span>
                    </div>
                  </td>
                  <td className="py-2.5">
                    <ThreatBadge level={geo.level} />
                  </td>
                  <td className="py-2.5 text-gray-500 font-mono text-[10px]">
                    {geo.lat.toFixed(1)}°, {geo.lng.toFixed(1)}°
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
