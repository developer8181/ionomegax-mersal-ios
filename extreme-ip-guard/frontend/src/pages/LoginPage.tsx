import React, { useState } from 'react';
import { Shield, Eye, EyeOff, Lock, User, Zap } from 'lucide-react';
import { useAuthStore } from '../store';
import { authApi } from '../utils/api';
import toast from 'react-hot-toast';

export function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { setAuth } = useAuthStore();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      toast.error('Please enter credentials');
      return;
    }

    setIsLoading(true);
    try {
      const res = await authApi.login(username, password);
      const { access_token, user } = res.data;
      setAuth(user, access_token);
      toast.success(`Welcome, ${user.full_name}`);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Login failed';
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = (user: string, pass: string) => {
    setUsername(user);
    setPassword(pass);
  };

  return (
    <div className="min-h-screen bg-cyber-bg flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background grid */}
      <div
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage: `
            linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />

      {/* Ambient glow effects */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyber-accent/5 rounded-full blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-cyber-panel border border-cyber-border mb-4 relative">
            <Shield className="w-10 h-10 text-cyber-accent" />
            <div className="absolute inset-0 rounded-2xl shadow-[0_0_30px_rgba(0,212,255,0.2)]" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">
            EXTREME <span className="text-cyber-accent">IP GUARD</span>
          </h1>
          <p className="text-gray-500 text-sm mt-1 font-mono">AI-Powered Network Security Platform v2.0</p>
        </div>

        {/* Login Card */}
        <div className="bg-cyber-panel border border-cyber-border rounded-2xl p-8 shadow-[0_0_40px_rgba(0,212,255,0.1)]">
          <div className="relative top-0 left-0 right-0 h-[1px] mb-6 -mt-[1px] rounded-t-2xl overflow-hidden">
            <div className="h-full bg-gradient-to-r from-transparent via-cyber-accent to-transparent opacity-60" />
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="text-xs font-mono text-gray-400 uppercase tracking-wider block mb-2">
                Username
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter username"
                  className="w-full bg-black/30 border border-cyber-border rounded-lg pl-10 pr-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-cyber-accent/60 focus:shadow-[0_0_0_2px_rgba(0,212,255,0.1)] transition-all"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-mono text-gray-400 uppercase tracking-wider block mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  className="w-full bg-black/30 border border-cyber-border rounded-lg pl-10 pr-10 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-cyber-accent/60 focus:shadow-[0_0_0_2px_rgba(0,212,255,0.1)] transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-600 hover:text-gray-400"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 bg-cyber-accent text-cyber-bg font-bold rounded-lg transition-all hover:bg-cyber-accent/90 hover:shadow-[0_0_20px_rgba(0,212,255,0.3)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-cyber-bg/30 border-t-cyber-bg rounded-full animate-spin" />
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  AUTHENTICATE
                </>
              )}
            </button>
          </form>

          {/* Demo accounts */}
          <div className="mt-6 pt-6 border-t border-cyber-border">
            <p className="text-xs text-gray-600 text-center mb-3 font-mono">DEMO ACCOUNTS</p>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => handleDemoLogin('admin', 'Admin@2026!')}
                className="flex items-center justify-center gap-2 py-2 text-xs bg-cyber-accent/5 hover:bg-cyber-accent/10 border border-cyber-accent/20 text-cyber-accent rounded-lg transition-all font-mono"
              >
                <Shield className="w-3 h-3" />
                Admin
              </button>
              <button
                onClick={() => handleDemoLogin('analyst', 'Analyst@2026!')}
                className="flex items-center justify-center gap-2 py-2 text-xs bg-purple-500/5 hover:bg-purple-500/10 border border-purple-500/20 text-purple-400 rounded-lg transition-all font-mono"
              >
                <User className="w-3 h-3" />
                Analyst
              </button>
            </div>
          </div>
        </div>

        <p className="text-center text-gray-700 text-xs mt-6 font-mono">
          EXTREME IP GUARD © 2026 | All Rights Reserved
        </p>
      </div>
    </div>
  );
}
