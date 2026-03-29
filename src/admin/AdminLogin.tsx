import { useState } from 'react';
import { ShieldCheck } from 'lucide-react';

interface AdminLoginProps {
  onLogin: (key: string) => Promise<void>;
}

export default function AdminLogin({ onLogin }: AdminLoginProps) {
  const [key, setKey] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await onLogin(key);
    } catch {
      setError('Invalid admin key');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-sm">
        <div className="flex items-center gap-3 mb-6">
          <ShieldCheck size={28} className="text-[#2da0a4]" />
          <h1 className="text-xl font-bold text-gray-900">MCCAA Admin</h1>
        </div>
        <input type="password" value={key} onChange={e => setKey(e.target.value)} placeholder="Admin key"
          className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#2da0a4] mb-4" />
        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
        <button type="submit" disabled={loading || !key}
          className="w-full bg-[#2da0a4] text-white py-3 rounded-lg font-medium hover:bg-[#258487] disabled:opacity-50 transition-colors">
          {loading ? 'Verifying...' : 'Login'}
        </button>
      </form>
    </div>
  );
}
