import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard, ShoppingBag, Users, Package, Printer,
  Scissors, BarChart2, Palette, ChevronLeft, Menu
} from 'lucide-react';
import { useState } from 'react';

const navItems = [
  { path: '/', label: 'لوحة التحكم', icon: LayoutDashboard, exact: true },
  { path: '/orders', label: 'الطلبات', icon: ShoppingBag },
  { path: '/design', label: 'التصميم', icon: Palette },
  { path: '/print-queue', label: 'طابور الطباعة', icon: Printer },
  { path: '/cut-queue', label: 'طابور القص', icon: Scissors },
  { path: '/customers', label: 'العملاء', icon: Users },
  { path: '/materials', label: 'المواد', icon: Package },
  { path: '/reports', label: 'التقارير', icon: BarChart2 },
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-16'} bg-slate-900 text-white flex flex-col transition-all duration-300 shrink-0`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          {sidebarOpen && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center">
                <Scissors size={16} />
              </div>
              <div>
                <h1 className="font-bold text-sm">PrintCut Pro</h1>
                <p className="text-xs text-slate-400">نظام الطباعة والقص</p>
              </div>
            </div>
          )}
          {!sidebarOpen && (
            <div className="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center mx-auto">
              <Scissors size={16} />
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-slate-400 hover:text-white p-1 rounded"
          >
            {sidebarOpen ? <ChevronLeft size={18} /> : <Menu size={18} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 space-y-1 px-2 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.exact}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-sm font-medium ${
                  isActive
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              <item.icon size={18} className="shrink-0" />
              {sidebarOpen && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        {sidebarOpen && (
          <div className="p-4 border-t border-slate-700">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-slate-600 rounded-full flex items-center justify-center text-xs font-bold">
                م
              </div>
              <div className="text-xs">
                <div className="text-white font-medium">مدير النظام</div>
                <div className="text-slate-400">admin@printcut.sa</div>
              </div>
            </div>
          </div>
        )}
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
