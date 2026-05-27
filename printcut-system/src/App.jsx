import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Notification from './components/Notification';
import Dashboard from './pages/Dashboard';
import Jobs from './pages/Jobs';
import NewJob from './pages/NewJob';
import Queue from './pages/Queue';
import History from './pages/History';
import Clients from './pages/Clients';
import Settings from './pages/Settings';

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <Notification />
      <main className="mr-[260px] transition-all duration-300">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/new-job" element={<NewJob />} />
          <Route path="/queue" element={<Queue />} />
          <Route path="/history" element={<History />} />
          <Route path="/clients" element={<Clients />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}
