import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Flame, Users, LogOut, Menu } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useState } from 'react';
import { clsx } from 'clsx';

export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { icon: LayoutDashboard, label: 'Дашборд', path: '/' },
    { icon: Flame, label: 'Прогноз', path: '/predict' },
  ];

  if (user?.role === 'admin') {
    navItems.push({ icon: Users, label: 'Пользователи', path: '/admin' });
  }

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans overflow-hidden">
      <aside className={clsx(
        "bg-slate-900 text-white transition-all duration-300 flex flex-col flex-shrink-0",
        sidebarOpen ? "w-64" : "w-20"
      )}>
        <div className="p-6 flex items-center gap-3 font-bold text-xl border-b border-slate-800 h-20">
          <Flame className="text-orange-500 w-8 h-8 flex-shrink-0" />
          {sidebarOpen && <span className="text-orange-500 tracking-wider truncate">VIBETON</span>}
        </div>

        <nav className="flex-1 py-6 space-y-2 px-3 overflow-y-auto">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={clsx(
                "flex items-center gap-4 px-4 py-3 rounded-xl transition-colors",
                location.pathname === item.path
                  ? "bg-orange-600 text-white shadow-lg shadow-orange-900/20"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
              )}
            >
              <item.icon size={24} className="flex-shrink-0" />
              {sidebarOpen && <span className="truncate">{item.label}</span>}
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-800">
          <button
            onClick={handleLogout}
            className="flex items-center gap-4 px-4 py-3 w-full text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-xl transition-colors"
          >
            <LogOut size={24} className="flex-shrink-0" />
            {sidebarOpen && <span>Выход</span>}
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="bg-white shadow-sm h-20 flex items-center justify-between px-8 flex-shrink-0 z-10">
          <button onClick={() => setSidebarOpen(!sidebarOpen)} className="p-2 hover:bg-slate-100 rounded-lg">
            <Menu size={24} className="text-slate-600" />
          </button>
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-bold text-slate-900">{user?.full_name}</p>
              <p className="text-xs text-slate-500 uppercase">{user?.role}</p>
            </div>
            <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center text-orange-700 font-bold">
              {user?.full_name?.[0] || 'U'}
            </div>
          </div>
        </header>
        
        <main className="flex-1 overflow-y-auto p-4 md:p-8 bg-slate-50">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}