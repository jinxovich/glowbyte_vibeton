import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  full_name: string;
  role: 'admin' | 'user';
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, role: string, full_name: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

  useEffect(() => {
    const storedRole = localStorage.getItem('role');
    const storedName = localStorage.getItem('full_name');
    if (token && storedRole && storedName) {
      setUser({ role: storedRole as 'admin' | 'user', full_name: storedName });
    }
  }, [token]);

  const login = (newToken: string, role: string, full_name: string) => {
    localStorage.setItem('token', newToken);
    localStorage.setItem('role', role);
    localStorage.setItem('full_name', full_name);
    setToken(newToken);
    setUser({ role: role as 'admin' | 'user', full_name });
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('full_name');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};