import { useState, useEffect } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  Rss,
  FileText,
  Key,
  Settings,
  Menu,
  X,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { statsApi } from '@/api';
import type { Stats } from '@/api';

const navItems = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/sources', label: 'RSS Sources', icon: Rss },
  { path: '/articles', label: 'Articles', icon: FileText },
  { path: '/keys', label: 'API Keys', icon: Key },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [stats, setStats] = useState<Stats | null>(null);
  const location = useLocation();

  useEffect(() => {
    statsApi.get().then(setStats).catch(console.error);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Mobile sidebar toggle */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 rounded-md bg-white shadow-md"
        >
          {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 w-64 bg-white border-r border-slate-200 transform transition-transform lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-2 px-6 py-4 border-b border-slate-200">
            <RefreshCw className="h-6 w-6 text-slate-900" />
            <span className="font-bold text-lg">RSS MCP</span>
          </div>

          {/* Stats */}
          {stats && (
            <div className="px-4 py-3 border-b border-slate-200">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="bg-slate-50 rounded p-2">
                  <div className="text-slate-500">Sources</div>
                  <div className="font-semibold">{stats.total_sources}</div>
                </div>
                <div className="bg-slate-50 rounded p-2">
                  <div className="text-slate-500">Articles</div>
                  <div className="font-semibold">{stats.total_articles}</div>
                </div>
              </div>
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={cn(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-slate-900 text-white'
                      : 'text-slate-600 hover:bg-slate-100'
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          {/* Footer */}
          <div className="px-4 py-3 border-t border-slate-200 text-xs text-slate-500">
            {stats?.mcp_name} v{stats?.mcp_version}
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="lg:pl-64 min-h-screen">
        <div className="container py-6"><Outlet /></div>
      </main>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}
