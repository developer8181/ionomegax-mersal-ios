import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Printer,
  Scissors,
  ListOrdered,
  Clock,
  Users,
  Settings,
  Plus,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { useState } from 'react';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'لوحة التحكم' },
  { path: '/jobs', icon: Printer, label: 'إدارة المهام' },
  { path: '/new-job', icon: Plus, label: 'مهمة جديدة' },
  { path: '/queue', icon: ListOrdered, label: 'قائمة الانتظار' },
  { path: '/history', icon: Clock, label: 'السجل' },
  { path: '/clients', icon: Users, label: 'العملاء' },
  { path: '/settings', icon: Settings, label: 'الإعدادات' },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`fixed top-0 right-0 h-full bg-sidebar text-white z-40 transition-all duration-300 flex flex-col ${
        collapsed ? 'w-[70px]' : 'w-[260px]'
      }`}
    >
      <div className="flex items-center gap-3 p-5 border-b border-white/10">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shrink-0">
          <Scissors className="w-5 h-5 text-white" />
        </div>
        {!collapsed && (
          <div className="animate-fade-in">
            <h1 className="text-lg font-bold leading-tight">PrintCut Pro</h1>
            <p className="text-xs text-gray-400">نظام الطباعة والقص</p>
          </div>
        )}
      </div>

      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group ${
                isActive
                  ? 'bg-sidebar-active text-white shadow-lg shadow-primary-900/30'
                  : 'text-gray-400 hover:bg-sidebar-hover hover:text-white'
              } ${collapsed ? 'justify-center' : ''}`
            }
          >
            <item.icon className="w-5 h-5 shrink-0" />
            {!collapsed && <span className="text-sm font-medium">{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      <button
        onClick={() => setCollapsed(!collapsed)}
        className="m-3 p-2 rounded-lg bg-sidebar-hover text-gray-400 hover:text-white transition-colors flex items-center justify-center"
      >
        {collapsed ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
      </button>

      {!collapsed && (
        <div className="p-4 border-t border-white/10">
          <div className="bg-gradient-to-r from-primary-600/20 to-accent-600/20 rounded-lg p-3">
            <p className="text-xs text-gray-400">الإصدار</p>
            <p className="text-sm font-semibold">PrintCut Pro v1.0</p>
          </div>
        </div>
      )}
    </aside>
  );
}
