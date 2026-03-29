import { Outlet, Link, useLocation } from 'react-router-dom';

export default function KBLayout() {
  const location = useLocation();
  const isLanding = location.pathname === '/kb';

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <header className="fixed top-6 left-0 right-0 z-50 flex justify-center px-4">
        <nav className="glass-nav flex items-center justify-between w-full max-w-5xl h-16 px-6 rounded-full shadow-lg border-white/30 bg-white/70">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#2da0a4] rounded-lg flex items-center justify-center text-white font-bold text-xs">M</div>
            <span className="font-bold text-gray-800 tracking-tight hidden sm:block">MCCAA</span>
          </Link>
          <div className="flex items-center gap-6">
            <Link to="/kb" className={`text-sm font-semibold transition-colors ${isLanding ? 'text-[#2da0a4]' : 'text-gray-700 hover:text-[#2da0a4]'}`}>
              Knowledge Base
            </Link>
            <Link to="/" className="text-sm font-semibold text-gray-700 hover:text-[#2da0a4] transition-colors">Home</Link>
          </div>
        </nav>
      </header>
      <Outlet />
      <footer className="bg-gray-900 text-gray-400 py-8 text-center text-sm">
        <p>© {new Date().getFullYear()} Malta Competition and Consumer Affairs Authority</p>
      </footer>
    </div>
  );
}
