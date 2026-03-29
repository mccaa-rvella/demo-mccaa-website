import { useState, useEffect } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { motion } from 'motion/react';
import { Menu } from 'lucide-react';

export default function KBLayout() {
  const location = useLocation();
  const isLanding = location.pathname === '/kb';
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 font-sans selection:bg-mccaa-teal/30">
      <header className="fixed top-6 left-0 right-0 z-50 flex justify-center px-4">
        <motion.nav
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className={`glass-nav flex items-center justify-between w-full h-16 transition-all duration-700 ease-in-out px-6 rounded-full shadow-lg ${
            isScrolled ? 'max-w-3xl border-mccaa-teal/30 bg-white/90' : 'max-w-5xl border-white/30 bg-white/70'
          }`}
        >
          <a href="/" className="flex-shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-mccaa-teal rounded-lg flex items-center justify-center text-white font-bold text-xs">
                M
              </div>
              <span className="font-bold text-gray-800 tracking-tight hidden sm:block">MCCAA</span>
            </div>
          </a>

          <div className="hidden md:flex items-center space-x-8">
            <Link to="/kb" className={`text-sm font-semibold transition-colors ${
              isLanding ? 'text-mccaa-teal' : 'text-gray-700 hover:text-mccaa-teal'
            }`}>
              Knowledge Base
            </Link>
            <a href="/?page=about" className="text-sm font-semibold text-gray-700 hover:text-mccaa-teal transition-colors">
              About
            </a>
            <a href="/?page=news" className="text-sm font-semibold text-gray-700 hover:text-mccaa-teal transition-colors">
              News
            </a>
            <a href="/?page=calls" className="text-sm font-semibold text-gray-700 hover:text-mccaa-teal transition-colors">
              Calls
            </a>
          </div>

          <div className="flex items-center gap-3">
            <a
              href="/?page=login"
              className="px-6 py-2 rounded-full text-sm font-bold transition-all shadow-md bg-gray-900 text-white hover:bg-mccaa-teal"
            >
              Login
            </a>
            <button className="md:hidden text-gray-800">
              <Menu size={24} />
            </button>
          </div>
        </motion.nav>
      </header>

      <div className="pt-28">
        <Outlet />
      </div>

      <footer className="bg-gray-900 text-gray-400 py-8 text-center text-sm">
        <p>© {new Date().getFullYear()} Malta Competition and Consumer Affairs Authority</p>
      </footer>
    </div>
  );
}
