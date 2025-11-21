import { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Flame, Activity, Calendar, History, BarChart3, Settings } from 'lucide-react';
import { healthCheck } from '../lib/api';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const [modelLoaded, setModelLoaded] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await healthCheck();
        setModelLoaded(health.model_loaded);
      } catch (error) {
        console.error('Health check failed:', error);
      } finally {
        setChecking(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Activity },
    { name: 'Календарь', href: '/calendar', icon: Calendar },
    { name: 'История', href: '/history', icon: History },
    { name: 'Метрики', href: '/metrics', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-red-600 to-red-700 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <Flame className="h-8 w-8 text-white animate-pulse" />
              <h1 className="text-2xl font-bold text-white">
                Coal Fire Prediction
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <Link
                to="/train"
                className="flex items-center space-x-2 px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors"
              >
                <Settings className="h-4 w-4" />
                <span className="hidden sm:inline">Обучить модель</span>
              </Link>
              
              <div className="flex items-center space-x-2 px-4 py-2 bg-white/10 rounded-lg">
                <div className={`h-2 w-2 rounded-full ${
                  checking ? 'bg-yellow-400' : 
                  modelLoaded ? 'bg-green-400 animate-pulse' : 'bg-red-400'
                }`} />
                <span className="text-white text-sm hidden sm:inline">
                  {checking ? 'Проверка...' : modelLoaded ? 'Модель загружена' : 'Модель не найдена'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`
                    flex items-center space-x-2 px-3 py-4 text-sm font-medium border-b-2 transition-colors
                    ${isActive
                      ? 'border-red-600 text-red-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            🔥 Coal Fire Prediction System v1.0 | Сделано с ❤️ для безопасности угольных терминалов
          </p>
        </div>
      </footer>
    </div>
  );
}

