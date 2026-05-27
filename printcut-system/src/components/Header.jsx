import { Bell, Search, User } from 'lucide-react';
import { useState } from 'react';
import { useApp } from '../context/AppContext';

export default function Header({ title, subtitle }) {
  const { state } = useApp();
  const [searchOpen, setSearchOpen] = useState(false);

  const activeJobs = state.jobs.filter(j => j.status === 'in_progress').length;

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between sticky top-0 z-30">
      <div>
        <h2 className="text-xl font-bold text-gray-900">{title}</h2>
        {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {searchOpen && (
          <div className="animate-fade-in">
            <input
              type="text"
              placeholder="بحث..."
              className="px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent w-64"
              autoFocus
              onBlur={() => setSearchOpen(false)}
            />
          </div>
        )}

        <button
          onClick={() => setSearchOpen(!searchOpen)}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <Search className="w-5 h-5" />
        </button>

        <button className="relative p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
          <Bell className="w-5 h-5" />
          {activeJobs > 0 && (
            <span className="absolute -top-0.5 -left-0.5 w-5 h-5 bg-danger-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
              {activeJobs}
            </span>
          )}
        </button>

        <div className="flex items-center gap-3 pr-4 border-r border-gray-200">
          <div className="text-left">
            <p className="text-sm font-semibold text-gray-900">المدير</p>
            <p className="text-xs text-gray-500">admin@printcut.com</p>
          </div>
          <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
            <User className="w-4 h-4 text-white" />
          </div>
        </div>
      </div>
    </header>
  );
}
