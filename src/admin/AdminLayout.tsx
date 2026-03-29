import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { FileText, TrendingUp, LogOut } from 'lucide-react';
import { useAdminAuth } from '../hooks/useAdminAuth';
import AdminLogin from './AdminLogin';

export default function AdminLayout() {
  const { adminKey, isAuthenticated, login, logout } = useAdminAuth();
  const location = useLocation();
  const navigate = useNavigate();

  if (!isAuthenticated) {
    return <AdminLogin onLogin={login} />;
  }

  const isArticles = location.pathname === '/admin' || location.pathname === '/admin/articles';
  const isTrends = location.pathname === '/admin/trends';

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/admin" className="font-bold text-gray-900 text-lg">MCCAA Admin</Link>
            <nav className="flex gap-1">
              <Link to="/admin/articles"
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isArticles ? 'bg-[#2da0a4]/10 text-[#2da0a4]' : 'text-gray-600 hover:bg-gray-100'
                }`}>
                <FileText size={16} /> Articles
              </Link>
              <Link to="/admin/trends"
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isTrends ? 'bg-[#2da0a4]/10 text-[#2da0a4]' : 'text-gray-600 hover:bg-gray-100'
                }`}>
                <TrendingUp size={16} /> Trends
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/kb" className="text-sm text-gray-500 hover:text-[#2da0a4]">View KB</Link>
            <button onClick={() => { logout(); navigate('/admin'); }} className="flex items-center gap-1 text-sm text-gray-500 hover:text-red-500">
              <LogOut size={14} /> Logout
            </button>
          </div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-6 py-8">
        <Outlet context={{ adminKey }} />
      </main>
    </div>
  );
}
