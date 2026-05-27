import React, { useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { useAuthStore, useUIStore } from './store';
import { useWebSocket } from './hooks/useWebSocket';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { LiveMonitorPage } from './pages/LiveMonitorPage';
import { ThreatCenterPage } from './pages/ThreatCenterPage';
import { GeoIntelligencePage } from './pages/GeoIntelligencePage';
import { PoliciesPage } from './pages/PoliciesPage';
import { AIEnginePage } from './pages/AIEnginePage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { PlaceholderPage } from './pages/PlaceholderPage';
import { Sidebar } from './components/dashboard/Sidebar';
import { Header } from './components/dashboard/Header';
import { FileText, Users, Settings } from 'lucide-react';

function AppLayout() {
  const { activeTab } = useUIStore();
  useWebSocket();

  const renderPage = () => {
    switch (activeTab) {
      case 'dashboard': return <DashboardPage />;
      case 'monitor': return <LiveMonitorPage />;
      case 'threats': return <ThreatCenterPage />;
      case 'geo': return <GeoIntelligencePage />;
      case 'analytics': return <AnalyticsPage />;
      case 'policies': return <PoliciesPage />;
      case 'ai-engine': return <AIEnginePage />;
      case 'reports': return <PlaceholderPage title="Reports & Exports" icon={<FileText className="w-8 h-8 text-cyber-accent" />} />;
      case 'users': return <PlaceholderPage title="User Management" icon={<Users className="w-8 h-8 text-cyber-accent" />} />;
      case 'settings': return <PlaceholderPage title="System Settings" icon={<Settings className="w-8 h-8 text-cyber-accent" />} />;
      default: return <DashboardPage />;
    }
  };

  return (
    <div className="flex h-screen bg-cyber-bg overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}

function App() {
  const { isAuthenticated } = useAuthStore();

  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#0d1628',
            color: '#e5e7eb',
            border: '1px solid #1a2d4d',
            fontSize: '13px',
          },
          success: {
            iconTheme: { primary: '#00ff88', secondary: '#0d1628' },
          },
          error: {
            iconTheme: { primary: '#ef4444', secondary: '#0d1628' },
          },
        }}
      />
      {isAuthenticated ? <AppLayout /> : <LoginPage />}
    </>
  );
}

export default App;
