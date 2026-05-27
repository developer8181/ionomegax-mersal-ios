import React from 'react';
import { Shield } from 'lucide-react';

export function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center gap-4">
      <div className="relative">
        <div className="w-16 h-16 border-2 border-cyber-accent/30 rounded-full animate-spin border-t-cyber-accent" />
        <div className="absolute inset-0 flex items-center justify-center">
          <Shield className="w-6 h-6 text-cyber-accent" />
        </div>
      </div>
      <p className="text-cyber-accent font-mono text-sm animate-pulse">INITIALIZING SECURITY SYSTEMS...</p>
    </div>
  );
}

export function PageLoader() {
  return (
    <div className="flex-1 flex items-center justify-center min-h-screen bg-cyber-bg">
      <LoadingSpinner />
    </div>
  );
}
