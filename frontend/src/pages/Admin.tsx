import { useEffect, useState } from 'react';
import api from '../lib/api';
import { Check, X, User as UserIcon } from 'lucide-react';

export default function Admin() {
  const [users, setUsers] = useState<any[]>([]);

  const fetchUsers = () => api.get('/admin/users').then((res) => setUsers(res.data));
  useEffect(() => { fetchUsers(); }, []);

  const handleAction = async (id: number, action: 'approve' | 'reject') => {
    await api.patch(`/admin/users/${id}/${action}`);
    fetchUsers();
  };

  return (
    <div className="space-y-6 animate-in">
      <h1 className="text-3xl font-bold text-slate-900">Управление доступом</h1>
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden overflow-x-auto">
        <table className="w-full text-left min-w-[600px]">
          <thead className="bg-slate-50 border-b border-slate-100">
            <tr>
              <th className="p-6 text-xs font-bold text-slate-500 uppercase">Пользователь</th>
              <th className="p-6 text-xs font-bold text-slate-500 uppercase">Email</th>
              <th className="p-6 text-xs font-bold text-slate-500 uppercase">Роль</th>
              <th className="p-6 text-xs font-bold text-slate-500 uppercase">Статус</th>
              <th className="p-6 text-xs font-bold text-slate-500 uppercase text-right">Действия</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-slate-50/50 transition-colors">
                <td className="p-6 font-medium text-slate-900 flex items-center gap-3">
                  <div className="w-8 h-8 bg-slate-100 rounded-full flex items-center justify-center text-slate-500"><UserIcon size={16} /></div>
                  {u.full_name}
                </td>
                <td className="p-6 text-slate-500">{u.email}</td>
                <td className="p-6"><span className={`px-3 py-1 rounded-full text-xs font-bold ${u.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-700'}`}>{u.role.toUpperCase()}</span></td>
                <td className="p-6"><span className={`px-3 py-1 rounded-full text-xs font-bold ${u.status === 'approved' ? 'bg-green-100 text-green-700' : u.status === 'pending' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>{u.status.toUpperCase()}</span></td>
                <td className="p-6 text-right">
                  {u.status === 'pending' && (
                    <div className="flex justify-end gap-2">
                      <button onClick={() => handleAction(u.id, 'approve')} className="p-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-100"><Check size={18} /></button>
                      <button onClick={() => handleAction(u.id, 'reject')} className="p-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100"><X size={18} /></button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}