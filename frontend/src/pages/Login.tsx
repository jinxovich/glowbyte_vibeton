import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../lib/api';
import { Flame, Loader2 } from 'lucide-react';

export default function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const { register, handleSubmit, formState: { isSubmitting } } = useForm();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [msg, setMsg] = useState('');

  const onSubmit = async (data: any) => {
    setMsg('');
    try {
      if (isLogin) {
        const formData = new URLSearchParams();
        formData.append('username', data.email); 
        formData.append('password', data.password);
        
        // FastAPI OAuth2 ожидает username/password в form-data, но мы в API сделали json body
        // В коде бэкенда (main.py -> auth router) мы сделали schema UserLogin (json).
        // Поэтому шлем JSON:
        const res = await api.post('/auth/login', { 
           email: data.email, 
           password: data.password 
        });
        login(res.data.access_token, res.data.role, res.data.full_name);
        navigate('/');
      } else {
        await api.post('/auth/register', data);
        setIsLogin(true);
        setMsg('Регистрация успешна! Дождитесь одобрения.');
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Ошибка сервера';
      setMsg(errorMsg);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4">
      <div className="bg-white w-full max-w-md rounded-2xl shadow-2xl overflow-hidden">
        <div className="p-8 text-center bg-orange-600">
          <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4 backdrop-blur-sm">
            <Flame className="text-white w-10 h-10" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">VIBETON AI</h1>
          <p className="text-orange-100">Система предиктивной аналитики</p>
        </div>

        <div className="p-8">
          <div className="flex gap-4 mb-8 border-b">
            <button onClick={() => setIsLogin(true)} className={`flex-1 pb-2 font-medium text-sm transition-colors ${isLogin ? 'text-orange-600 border-b-2 border-orange-600' : 'text-slate-400'}`}>ВХОД</button>
            <button onClick={() => setIsLogin(false)} className={`flex-1 pb-2 font-medium text-sm transition-colors ${!isLogin ? 'text-orange-600 border-b-2 border-orange-600' : 'text-slate-400'}`}>РЕГИСТРАЦИЯ</button>
          </div>

          {msg && <div className={`mb-4 p-3 rounded-lg text-sm ${msg.includes('успешна') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{msg}</div>}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">ФИО</label>
                <input {...register('full_name')} className="w-full p-3 rounded-lg bg-slate-100 border-transparent focus:bg-white focus:ring-2 focus:ring-orange-500" placeholder="Иван Иванов" />
              </div>
            )}
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Email</label>
              <input {...register('email')} className="w-full p-3 rounded-lg bg-slate-100 border-transparent focus:bg-white focus:ring-2 focus:ring-orange-500" placeholder="email@company.com" />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Пароль</label>
              <input type="password" {...register('password')} className="w-full p-3 rounded-lg bg-slate-100 border-transparent focus:bg-white focus:ring-2 focus:ring-orange-500" placeholder="••••••••" />
            </div>
            <button disabled={isSubmitting} className="w-full bg-orange-600 text-white font-bold py-3 rounded-xl hover:bg-orange-700 flex items-center justify-center gap-2 shadow-lg">
              {isSubmitting && <Loader2 className="animate-spin" size={20} />}
              {isLogin ? 'ВОЙТИ' : 'СОЗДАТЬ АККАУНТ'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}