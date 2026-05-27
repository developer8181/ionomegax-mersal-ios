import React from 'react';
import { FileText, Users, Settings, Construction } from 'lucide-react';
import { CyberCard } from '../components/ui/CyberCard';

interface PlaceholderPageProps {
  title: string;
  icon?: React.ReactNode;
}

export function PlaceholderPage({ title, icon }: PlaceholderPageProps) {
  return (
    <div className="p-4 md:p-6 flex items-center justify-center min-h-[60vh]">
      <CyberCard className="p-12 text-center max-w-md" glow>
        <div className="w-16 h-16 rounded-2xl bg-cyber-accent/10 border border-cyber-accent/20 flex items-center justify-center mx-auto mb-4">
          {icon || <Construction className="w-8 h-8 text-cyber-accent" />}
        </div>
        <h2 className="text-xl font-bold text-white mb-2">{title}</h2>
        <p className="text-gray-500 text-sm">
          This module is under development and will be available in the next release.
        </p>
        <div className="mt-6 flex items-center justify-center gap-2 text-xs font-mono text-cyber-accent">
          <div className="w-1.5 h-1.5 rounded-full bg-cyber-accent animate-pulse" />
          Coming Soon
        </div>
      </CyberCard>
    </div>
  );
}
