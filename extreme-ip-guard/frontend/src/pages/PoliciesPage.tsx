import React, { useEffect, useState } from 'react';
import { Lock, Plus, Trash2, CheckCircle, XCircle } from 'lucide-react';
import { CyberCard } from '../components/ui/CyberCard';
import { policiesApi } from '../utils/api';
import type { SecurityPolicy } from '../types';
import { cn } from '../utils/helpers';
import toast from 'react-hot-toast';

const ACTION_COLORS: Record<string, string> = {
  allow: 'text-green-400 bg-green-500/10 border-green-500/20',
  block: 'text-red-400 bg-red-500/10 border-red-500/20',
  monitor: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  alert: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  quarantine: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  rate_limit: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
};

export function PoliciesPage() {
  const [policies, setPolicies] = useState<SecurityPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newPolicy, setNewPolicy] = useState({
    name: '',
    description: '',
    action: 'monitor',
    priority: 100,
    countries: '',
    destination_ports: '',
    protocols: '',
  });

  useEffect(() => {
    fetchPolicies();
  }, []);

  const fetchPolicies = async () => {
    try {
      const res = await policiesApi.list();
      setPolicies(res.data.policies || []);
    } catch {
      toast.error('Failed to load policies');
    }
    setLoading(false);
  };

  const handleToggle = async (id: string) => {
    try {
      const res = await policiesApi.toggle(id);
      setPolicies((prev) =>
        prev.map((p) => (p.id === id ? res.data.policy : p))
      );
      toast.success(res.data.message);
    } catch {
      toast.error('Failed to toggle policy');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await policiesApi.delete(id);
      setPolicies((prev) => prev.filter((p) => p.id !== id));
      toast.success('Policy deleted');
    } catch {
      toast.error('Failed to delete policy');
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = {
        ...newPolicy,
        countries: newPolicy.countries ? newPolicy.countries.split(',').map((s) => s.trim()) : [],
        destination_ports: newPolicy.destination_ports
          ? newPolicy.destination_ports.split(',').map((s) => parseInt(s.trim())).filter(Boolean)
          : [],
        protocols: newPolicy.protocols ? newPolicy.protocols.split(',').map((s) => s.trim()) : [],
        priority: parseInt(newPolicy.priority as any) || 100,
      };
      const res = await policiesApi.create(data);
      setPolicies((prev) => [...prev, res.data.policy]);
      setShowCreateForm(false);
      setNewPolicy({ name: '', description: '', action: 'monitor', priority: 100, countries: '', destination_ports: '', protocols: '' });
      toast.success('Policy created successfully');
    } catch {
      toast.error('Failed to create policy');
    }
  };

  return (
    <div className="p-4 md:p-6 space-y-6 overflow-auto">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Lock className="w-6 h-6 text-cyber-accent" />
            Security Policies
          </h1>
          <p className="text-gray-500 text-sm mt-1">Manage traffic rules and enforcement policies</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center gap-2 px-4 py-2 bg-cyber-accent/10 hover:bg-cyber-accent/20 text-cyber-accent border border-cyber-accent/30 rounded-lg text-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          New Policy
        </button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <CyberCard className="p-5" glow>
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Plus className="w-4 h-4 text-cyber-accent" />
            Create New Policy
          </h3>
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="text-xs text-gray-400 block mb-1">Policy Name *</label>
              <input
                required
                value={newPolicy.name}
                onChange={(e) => setNewPolicy({ ...newPolicy, name: e.target.value })}
                placeholder="e.g. Block SSH from external"
                className="w-full bg-black/30 border border-cyber-border rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-cyber-accent/50"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Action *</label>
              <select
                value={newPolicy.action}
                onChange={(e) => setNewPolicy({ ...newPolicy, action: e.target.value })}
                className="w-full bg-black/30 border border-cyber-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyber-accent/50"
              >
                {['allow', 'block', 'monitor', 'alert', 'quarantine', 'rate_limit'].map((a) => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Priority (lower = higher)</label>
              <input
                type="number"
                value={newPolicy.priority}
                onChange={(e) => setNewPolicy({ ...newPolicy, priority: parseInt(e.target.value) })}
                min={1} max={1000}
                className="w-full bg-black/30 border border-cyber-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyber-accent/50"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Countries (comma-separated codes)</label>
              <input
                value={newPolicy.countries}
                onChange={(e) => setNewPolicy({ ...newPolicy, countries: e.target.value })}
                placeholder="CN, RU, KP"
                className="w-full bg-black/30 border border-cyber-border rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-cyber-accent/50"
              />
            </div>
            <div>
              <label className="text-xs text-gray-400 block mb-1">Ports (comma-separated)</label>
              <input
                value={newPolicy.destination_ports}
                onChange={(e) => setNewPolicy({ ...newPolicy, destination_ports: e.target.value })}
                placeholder="22, 3389, 3306"
                className="w-full bg-black/30 border border-cyber-border rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-cyber-accent/50"
              />
            </div>
            <div className="md:col-span-2">
              <label className="text-xs text-gray-400 block mb-1">Description</label>
              <textarea
                value={newPolicy.description}
                onChange={(e) => setNewPolicy({ ...newPolicy, description: e.target.value })}
                rows={2}
                className="w-full bg-black/30 border border-cyber-border rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-cyber-accent/50 resize-none"
                placeholder="Policy description..."
              />
            </div>
            <div className="md:col-span-2 flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-cyber-accent text-cyber-bg font-semibold text-sm rounded-lg hover:bg-cyber-accent/90 transition-all"
              >
                Create Policy
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 bg-gray-700 text-gray-300 text-sm rounded-lg hover:bg-gray-600 transition-all"
              >
                Cancel
              </button>
            </div>
          </form>
        </CyberCard>
      )}

      {/* Policies List */}
      <div className="space-y-3">
        {loading ? (
          <div className="text-center text-gray-600 py-12">Loading policies...</div>
        ) : policies.length === 0 ? (
          <div className="text-center text-gray-600 py-12">No policies configured</div>
        ) : (
          policies.map((policy) => (
            <CyberCard
              key={policy.id}
              className={cn('p-4', !policy.is_active && 'opacity-50')}
              glow={policy.is_active}
              glowColor={policy.action === 'block' ? '#ef4444' : policy.action === 'allow' ? '#00ff88' : '#00d4ff'}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1 min-w-0">
                  {/* Priority badge */}
                  <div className="text-[10px] font-mono text-gray-600 bg-black/30 px-2 py-1 rounded border border-cyber-border flex-shrink-0">
                    P{policy.priority}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <span className="text-sm font-semibold text-white">{policy.name}</span>
                      <span className={cn(
                        'text-[10px] font-mono px-2 py-0.5 rounded border uppercase tracking-wider',
                        ACTION_COLORS[policy.action] || 'text-gray-400 bg-gray-500/10 border-gray-500/20'
                      )}>
                        {policy.action}
                      </span>
                      {!policy.is_active && (
                        <span className="text-[10px] text-gray-500 bg-gray-500/10 border border-gray-500/20 px-2 py-0.5 rounded">
                          DISABLED
                        </span>
                      )}
                    </div>

                    {policy.description && (
                      <p className="text-xs text-gray-500 mb-2">{policy.description}</p>
                    )}

                    <div className="flex flex-wrap gap-3 text-[10px] text-gray-600">
                      {policy.countries && policy.countries.length > 0 && (
                        <span>Countries: {policy.countries.join(', ')}</span>
                      )}
                      {policy.destination_ports && policy.destination_ports.length > 0 && (
                        <span>Ports: {policy.destination_ports.join(', ')}</span>
                      )}
                      {policy.protocols && policy.protocols.length > 0 && (
                        <span>Protocols: {policy.protocols.join(', ')}</span>
                      )}
                      <span className="text-gray-700">
                        Triggered: {policy.times_triggered.toLocaleString()}x
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => handleToggle(policy.id)}
                    className={cn(
                      'p-1.5 rounded-lg transition-all',
                      policy.is_active
                        ? 'text-green-400 hover:bg-green-500/10'
                        : 'text-gray-500 hover:bg-gray-500/10'
                    )}
                    title={policy.is_active ? 'Disable' : 'Enable'}
                  >
                    {policy.is_active ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      <XCircle className="w-4 h-4" />
                    )}
                  </button>
                  <button
                    onClick={() => handleDelete(policy.id)}
                    className="p-1.5 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-500/10 transition-all"
                    title="Delete policy"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </CyberCard>
          ))
        )}
      </div>
    </div>
  );
}
