import React, { useState, useEffect, useRef } from 'react';
import { useChat } from 'ai/react';
import Markdown from 'react-markdown';
import WizardClient from './components/Wizard/Wizard';
import { 
  Search, 
  MessageSquare, 
  X, 
  Send, 
  ArrowRight, 
  ArrowLeft,
  Filter,
  Building2, 
  Scale, 
  Gavel, 
  ShieldCheck, 
  Phone, 
  Mail, 
  MapPin,
  FileText,
  Sparkles,
  ChevronRight,
  Menu,
  User,
  Briefcase,
  Facebook,
  Twitter,
  Instagram,
  Linkedin,
  ArrowUp,
  CheckCircle,
  Paperclip
} from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

// --- Types ---
type Page = 'home' | 'about' | 'login' | 'consumer-rights' | 'calls' | 'news' | 'wizard';

// --- Constants & Data ---

const ARTICLES = [
  { 
    id: '1',
    category: 'Reports', 
    title: 'Quarter 3 Price Monitoring Report Released', 
    desc: 'Our latest findings on essential grocery prices across major retail outlets in Malta.', 
    content: `The Malta Competition and Consumer Affairs Authority (MCCAA) has released its price monitoring report for the third quarter of 2025. The report highlights significant trends in the pricing of essential grocery items across various retail outlets in Malta and Gozo.

Key findings include:
- A stabilization in the prices of dairy products.
- Seasonal fluctuations in fresh produce, with a slight decrease in the price of local vegetables.
- Increased competition in the canned goods sector, leading to more promotional offers for consumers.

The MCCAA remains committed to ensuring market transparency and protecting consumer interests by providing regular updates on price movements. Consumers are encouraged to use this data to make informed purchasing decisions.`,
    color: 'text-mccaa-teal', 
    seed: 'grocery',
    date: 'Oct 15, 2025'
  },
  { 
    id: '2',
    category: 'Market Surveillance', 
    title: 'New Toy Safety Legislation for 2026', 
    desc: 'Guidance for importers and retailers regarding upcoming safety certification requirements.', 
    content: `Starting January 1, 2026, new toy safety regulations will come into effect across the European Union, including Malta. These regulations aim to enhance the safety of toys by introducing stricter requirements for chemical composition and mechanical properties.

Importers and retailers are advised to:
1. Verify that all products carry the CE marking.
2. Ensure that technical documentation is readily available for inspection.
3. Conduct additional safety tests for toys intended for children under 36 months.

The MCCAA will be conducting workshops throughout the coming months to assist businesses in complying with these new standards. Failure to comply may result in significant fines and the withdrawal of products from the market.`,
    color: 'text-mccaa-burgundy', 
    seed: 'toys',
    date: 'Nov 02, 2025'
  },
  { 
    id: '3',
    category: 'Consumer Rights', 
    title: 'Black Friday: Know Your Rights Before You Shop', 
    desc: 'A guide to returns, warranties, and deceptive pricing during the sales season.', 
    content: `As Black Friday approaches, the MCCAA is reminding consumers of their fundamental rights when shopping during sales events. While retailers often offer deep discounts, consumer protection laws still apply in full.

Important reminders for shoppers:
- **Right to Return**: For online purchases, you have a 14-day cooling-off period. For in-store purchases, check the shop's individual return policy.
- **Warranties**: All electronic goods come with a minimum two-year legal warranty, regardless of any "sale" status.
- **Price Transparency**: Retailers must show the lowest price charged for the item in the 30 days prior to the discount.

If you encounter deceptive pricing or issues with a purchase, do not hesitate to contact our consumer helpline or file a report through our website.`,
    color: 'text-mccaa-orange', 
    seed: 'shopping',
    date: 'Nov 20, 2025'
  },
];

// --- Components ---

const Navbar = ({ onPageChange, currentPage }: { onPageChange: (p: Page) => void, currentPage: Page }) => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className="fixed top-6 left-0 right-0 z-50 flex justify-center px-4">
      <motion.nav 
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className={`glass-nav flex items-center justify-between w-full h-16 transition-all duration-700 ease-in-out px-6 rounded-full shadow-lg ${
          isScrolled ? 'max-w-3xl border-mccaa-teal/30 bg-white/90' : 'max-w-5xl border-white/30 bg-white/70'
        }`}
      >
        <button onClick={() => onPageChange('home')} className="flex-shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-mccaa-teal rounded-lg flex items-center justify-center text-white font-bold text-xs">
              M
            </div>
            <span className="font-bold text-gray-800 tracking-tight hidden sm:block">MCCAA</span>
          </div>
        </button>

        <div className="hidden md:flex items-center space-x-8">
          <a href="/kb" className="text-sm font-semibold text-gray-700 hover:text-mccaa-teal transition-colors">
              Knowledge Base
            </a>
          {[
            { name: 'About', id: 'about' as Page },
            { name: 'News', id: 'news' as Page },
            { name: 'Calls', id: 'calls' as Page }
          ].map((item) => (
            <button
              key={item.id}
              onClick={() => onPageChange(item.id)}
              className={`text-sm font-semibold transition-colors ${
                currentPage === item.id ? 'text-mccaa-teal' : 'text-gray-700 hover:text-mccaa-teal'
              }`}
            >
              {item.name}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={() => onPageChange('login')}
            className={`px-6 py-2 rounded-full text-sm font-bold transition-all shadow-md ${
              currentPage === 'login' ? 'bg-mccaa-teal text-white' : 'bg-gray-900 text-white hover:bg-mccaa-teal'
            }`}
          >
            Login
          </button>
          <button className="md:hidden text-gray-800">
            <Menu size={24} />
          </button>
        </div>
      </motion.nav>
    </header>
  );
};

const Hero = ({ onOpenAI, onOpenReport, onPageChange }: { onOpenAI: () => void, onOpenReport: () => void, onPageChange: (p: Page) => void }) => {
  const [hoveredPane, setHoveredPane] = useState<'left' | 'right' | null>(null);

  return (
    <main className="relative flex flex-col md:flex-row h-screen w-full overflow-hidden bg-black">
      {/* LEFT: Consumers */}
      <motion.section 
        onMouseEnter={() => setHoveredPane('left')}
        onMouseLeave={() => setHoveredPane(null)}
        animate={{ 
          width: hoveredPane === 'left' ? '90%' : hoveredPane === 'right' ? '10%' : '50%' 
        }}
        transition={{ duration: 0.7, ease: [0.4, 0, 0.2, 1] }}
        className="relative h-1/2 md:h-full overflow-hidden border-b md:border-b-0 md:border-r border-white/10"
      >
        <div className="absolute inset-0 z-0">
          <img 
            src="https://picsum.photos/seed/consumer/1200/800" 
            alt="Consumer Scene" 
            className="w-full h-full object-cover opacity-40 grayscale-[0.2]"
            referrerPolicy="no-referrer"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-mccaa-teal/60 to-black/80 mix-blend-multiply"></div>
        </div>
        
        <motion.div 
          animate={{ opacity: hoveredPane === 'right' ? 0 : 1 }}
          transition={{ duration: 0.4 }}
          className="relative z-10 h-full w-full flex flex-col items-center justify-center p-4 md:p-8 text-center text-white"
        >
          <span className="inline-block px-3 py-1 mb-4 text-[10px] sm:text-xs font-bold tracking-widest uppercase bg-white/10 backdrop-blur-md rounded-full border border-white/20">
            Citizen Space
          </span>
          <h1 className="text-3xl sm:text-4xl md:text-6xl font-bold mb-4 tracking-tight">
            Consumers
          </h1>
          <p className="text-sm sm:text-lg md:text-xl text-white/80 max-w-md mx-auto px-4 mb-8">
            Protecting your rights, ensuring safety, and providing market clarity for every shopper in Malta.
          </p>

          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 w-full sm:w-auto px-6">
            <button 
              onClick={onOpenReport}
              className="bg-white text-mccaa-teal font-bold px-[clamp(0.75rem,2vw,2rem)] py-[clamp(0.5rem,1vw,1rem)] rounded-lg hover:scale-105 transition-transform shadow-xl flex items-center justify-center gap-2 whitespace-nowrap text-[clamp(10px,1.2vw,16px)]"
            >
              <User size={14} className="w-[clamp(12px,1.5vw,18px)]" />
              Submit a Formal Report
            </button>
            <button 
              onClick={() => onPageChange('consumer-rights')}
              className="bg-transparent border-2 border-white/40 hover:border-white text-white font-bold px-[clamp(0.75rem,2vw,2rem)] py-[clamp(0.5rem,1vw,1rem)] rounded-lg transition-all whitespace-nowrap text-[clamp(10px,1.2vw,16px)]"
            >
              Consumer Rights
            </button>
          </div>
        </motion.div>
      </motion.section>

      {/* RIGHT: Businesses */}
      <motion.section 
        onMouseEnter={() => setHoveredPane('right')}
        onMouseLeave={() => setHoveredPane(null)}
        animate={{ 
          width: hoveredPane === 'right' ? '90%' : hoveredPane === 'left' ? '10%' : '50%' 
        }}
        transition={{ duration: 0.7, ease: [0.4, 0, 0.2, 1] }}
        className="relative h-1/2 md:h-full overflow-hidden"
      >
        <div className="absolute inset-0 z-0">
          <img 
            src="https://picsum.photos/seed/business/1200/800" 
            alt="Business Scene" 
            className="w-full h-full object-cover opacity-40 grayscale-[0.2]"
            referrerPolicy="no-referrer"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-mccaa-burgundy/60 to-black/80 mix-blend-multiply"></div>
        </div>
        
        <motion.div 
          animate={{ opacity: hoveredPane === 'left' ? 0 : 1 }}
          transition={{ duration: 0.4 }}
          className="relative z-10 h-full w-full flex flex-col items-center justify-center p-4 md:p-8 text-center text-white"
        >
          <span className="inline-block px-3 py-1 mb-4 text-[10px] sm:text-xs font-bold tracking-widest uppercase bg-white/10 backdrop-blur-md rounded-full border border-white/20">
            Enterprise Hub
          </span>
          <h1 className="text-3xl sm:text-4xl md:text-6xl font-bold mb-4 tracking-tight">
            Businesses
          </h1>
          <p className="text-sm sm:text-lg md:text-xl text-white/80 max-w-md mx-auto px-4 mb-8">
            Upholding fair competition, technical standards, and providing essential compliance support.
          </p>

          <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 w-full sm:w-auto px-6">
            <button className="bg-white text-mccaa-burgundy font-bold px-[clamp(0.75rem,2vw,2rem)] py-[clamp(0.5rem,1vw,1rem)] rounded-lg hover:scale-105 transition-transform shadow-xl flex items-center justify-center gap-2 whitespace-nowrap text-[clamp(10px,1.2vw,16px)]">
              <Briefcase size={14} className="w-[clamp(12px,1.5vw,18px)]" />
              Business Services
            </button>
            <button onClick={() => onPageChange('wizard')} className="bg-transparent border-2 border-white/40 hover:border-white text-white font-bold px-[clamp(0.75rem,2vw,2rem)] py-[clamp(0.5rem,1vw,1rem)] rounded-lg transition-all whitespace-nowrap text-[clamp(10px,1.2vw,16px)]">
              Technical Standards
            </button>
          </div>
        </motion.div>
      </motion.section>

      {/* Prominent AI Button - Morphism Style */}
      <div className="absolute left-1/2 bottom-[5vh] -translate-x-1/2 z-30 pointer-events-none">
        <motion.button 
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onOpenAI}
          className="glass-morphism pointer-events-auto px-[clamp(1rem,3vw,2.5rem)] py-[clamp(0.5rem,1.5vw,1.25rem)] rounded-full flex items-center gap-3 text-white font-semibold text-[clamp(12px,1.5vw,18px)] hover:bg-white/20 transition-all border border-white/30 shadow-2xl backdrop-blur-xl group whitespace-nowrap"
        >
          <div className="bg-mccaa-yellow/20 p-[clamp(4px,1vw,10px)] rounded-full group-hover:bg-mccaa-yellow/40 transition-colors">
            <Sparkles className="text-mccaa-yellow animate-pulse w-[clamp(16px,2vw,24px)] h-[clamp(16px,2vw,24px)]" />
          </div>
          <span>Ask l-Uffiċjal, our AI Assistant</span>
        </motion.button>
      </div>
    </main>
  );
};

const BrandingStrip = () => (
  <div className="h-3 w-full flex">
    <div className="h-full flex-grow bg-mccaa-teal"></div>
    <div className="h-full flex-grow bg-mccaa-burgundy"></div>
    <div className="h-full flex-grow bg-mccaa-orange"></div>
    <div className="h-full flex-grow bg-mccaa-yellow"></div>
    <div className="h-full flex-grow bg-mccaa-green"></div>
  </div>
);

const Portals = () => {
  const portals = [
    { title: 'Resolve Issue', desc: 'Lodge and track consumer protection tribunal claims.', icon: Gavel, color: 'text-mccaa-teal', bg: 'bg-mccaa-teal/10' },
    { title: 'Lift Compliance', desc: 'Register and manage lift safety certifications online.', icon: ArrowUp, color: 'text-mccaa-burgundy', bg: 'bg-mccaa-burgundy/10' },
    { title: 'Product Safety', desc: 'Report and view unsafe product alerts across the EU.', icon: ShieldCheck, color: 'text-mccaa-orange', bg: 'bg-mccaa-orange/10' },
    { title: 'Standard Sales', desc: 'Purchase and download technical standards documentation.', icon: Scale, color: 'text-mccaa-green', bg: 'bg-mccaa-green/10' },
  ];

  return (
    <section className="py-24 bg-white" id="portals">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">Take Action</h2>
          <p className="text-gray-600 max-w-2xl mx-auto">Direct access to our most requested digital services and compliance tools.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {portals.map((portal, idx) => (
            <motion.a 
              key={portal.title}
              href="#"
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              viewport={{ once: true }}
              className="group p-8 rounded-2xl bg-gray-50 border border-gray-100 hover:border-gray-300 hover:shadow-xl transition-all flex flex-col items-center text-center"
            >
              <div className={`w-16 h-16 ${portal.bg} rounded-2xl flex items-center justify-center mb-6 ${portal.color} group-hover:scale-110 transition-transform`}>
                <portal.icon size={32} />
              </div>
              <h3 className="font-bold text-lg mb-2">{portal.title}</h3>
              <p className="text-sm text-gray-500">{portal.desc}</p>
              <div className="mt-6 flex items-center text-sm font-bold text-gray-900 group-hover:text-mccaa-teal transition-colors">
                Get Started <ChevronRight size={16} className="ml-1" />
              </div>
            </motion.a>
          ))}
        </div>
      </div>
    </section>
  );
};

const News = ({ onArticleClick }: { onArticleClick: (article: any) => void }) => {
  return (
    <section className="py-24 bg-gray-50" id="news">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex justify-between items-end mb-12">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">News & Updates</h2>
            <p className="text-gray-600">Stay informed with the latest regulatory changes and reports.</p>
          </div>
          <button className="hidden md:flex items-center text-mccaa-teal font-bold hover:underline">
            View all news <ArrowRight className="ml-1" size={18} />
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {ARTICLES.map((article, idx) => (
            <motion.article 
              key={article.title}
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
              viewport={{ once: true }}
              onClick={() => onArticleClick(article)}
              className="bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-shadow border border-gray-100 group flex flex-col h-full cursor-pointer"
            >
              <div className="h-48 overflow-hidden flex-shrink-0">
                <img 
                  src={`https://picsum.photos/seed/${article.seed}/600/400`} 
                  alt={article.title} 
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                  referrerPolicy="no-referrer"
                />
              </div>
              <div className="p-6 flex flex-col flex-grow">
                <span className={`text-xs font-bold ${article.color} uppercase tracking-widest`}>{article.category}</span>
                <h3 className="text-xl font-bold mt-2 mb-3 leading-tight group-hover:text-mccaa-teal transition-colors">{article.title}</h3>
                <p className="text-sm text-gray-600 line-clamp-2 mb-4">{article.desc}</p>
                <div className="mt-auto">
                  <span className="inline-block text-sm font-bold text-gray-900 group-hover:text-mccaa-teal">Read More →</span>
                </div>
              </div>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
};

const Contact = ({ onOpenReport }: { onOpenReport: () => void }) => (
  <section className="py-24 bg-white" id="contact">
    <div className="max-w-7xl mx-auto px-6 space-y-12">
      {/* Report an Issue Section */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="bg-mccaa-teal/5 p-8 md:p-12 rounded-3xl border border-mccaa-teal/10 flex flex-col items-start gap-8"
      >
        <div className="max-w-3xl">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Report an Issue</h2>
          <p className="text-gray-700 text-lg leading-relaxed">
            Protect your rights and help us maintain market safety. Lodge a formal complaint or report issues such as product safety concerns, incorrect weights and measures, or unfair commercial practices.
          </p>
        </div>
        <button 
          onClick={onOpenReport}
          className="bg-mccaa-teal text-white font-bold px-10 py-4 rounded-xl hover:bg-mccaa-teal/90 transition-all shadow-lg hover:shadow-teal-200/50 flex items-center gap-2 whitespace-nowrap shrink-0"
        >
          Submit a Formal Report <FileText size={20} />
        </button>
      </motion.div>

      {/* Professional Assistance Section */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.1 }}
        className="bg-gray-900 p-8 md:p-16 rounded-3xl text-white flex flex-col"
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-24 items-stretch">
          <div className="flex flex-col h-full">
            <div className="mb-12">
              <h2 className="text-4xl font-bold text-white mb-6">Professional Assistance</h2>
              <p className="text-white/70 text-lg leading-relaxed max-w-xl">
                Our technical experts provide specialized guidance for both enterprise compliance and citizen inquiries. Reach out to our headquarters for direct support.
              </p>
            </div>
            
            <div className="flex-1 flex flex-col gap-4">
              <div className="flex-1 flex items-center gap-4 p-5 rounded-xl bg-white/5 border border-white/10">
                <div className="w-12 h-12 bg-mccaa-teal/20 rounded-lg flex items-center justify-center text-mccaa-teal flex-shrink-0">
                  <Phone size={24} />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-widest text-white/40 font-bold">Telephone</p>
                  <span className="text-lg font-medium block">+356 2395 2000</span>
                </div>
              </div>
              <div className="flex-1 flex items-center gap-4 p-5 rounded-xl bg-white/5 border border-white/10">
                <div className="w-12 h-12 bg-mccaa-teal/20 rounded-lg flex items-center justify-center text-mccaa-teal flex-shrink-0">
                  <Mail size={24} />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-widest text-white/40 font-bold">Email</p>
                  <span className="text-lg font-medium block whitespace-nowrap">info@mccaa.org.mt</span>
                </div>
              </div>
              <a 
                href="https://www.google.com/maps/search/?api=1&query=MCCAA+Mizzi+House+Blata+l-Bajda" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex-1 flex items-center gap-4 p-5 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors group"
              >
                <div className="w-12 h-12 bg-mccaa-teal/20 rounded-lg flex items-center justify-center text-mccaa-teal flex-shrink-0 group-hover:scale-110 transition-transform">
                  <MapPin size={24} />
                </div>
                <div>
                  <p className="text-xs uppercase tracking-widest text-white/40 font-bold">Location</p>
                  <span className="text-lg font-medium block">Mizzi House, Blata l-Bajda</span>
                </div>
              </a>
            </div>
          </div>

          <form className="space-y-6 flex flex-col h-full" onSubmit={(e) => e.preventDefault()}>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-widest text-white/40 font-bold">Full Name</label>
                <input 
                  type="text" 
                  placeholder="John Doe"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-5 py-4 text-white placeholder-white/20 focus:border-mccaa-teal focus:ring-0 outline-none transition-all"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs uppercase tracking-widest text-white/40 font-bold">Email Address</label>
                <input 
                  type="email" 
                  placeholder="john@example.com"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-5 py-4 text-white placeholder-white/20 focus:border-mccaa-teal focus:ring-0 outline-none transition-all"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs uppercase tracking-widest text-white/40 font-bold">Subject</label>
              <select 
                className="w-full bg-white/5 border border-white/10 rounded-xl px-5 py-4 text-white outline-none focus:border-mccaa-teal focus:ring-0 transition-all appearance-none cursor-pointer"
                defaultValue=""
              >
                <option value="" disabled className="bg-gray-900">Select a subject...</option>
                <option value="general" className="bg-gray-900">General Inquiry</option>
                <option value="media" className="bg-gray-900">Media & Press</option>
                <option value="standards" className="bg-gray-900">Standards & Certification</option>
                <option value="compliance" className="bg-gray-900">Business Compliance Guidance</option>
                <option value="feedback" className="bg-gray-900">Feedback & Suggestions</option>
                <option value="careers" className="bg-gray-900">Career Opportunities</option>
              </select>
            </div>
            <div className="space-y-2 flex-1 flex flex-col">
              <label className="text-xs uppercase tracking-widest text-white/40 font-bold">Your Message</label>
              <textarea 
                rows={4}
                placeholder="How can we help you?"
                className="w-full flex-1 bg-white/5 border border-white/10 rounded-xl px-5 py-4 text-white placeholder-white/20 focus:border-mccaa-teal focus:ring-0 outline-none transition-all resize-none"
              ></textarea>
            </div>
            <button className="w-full bg-mccaa-teal text-white font-bold py-5 rounded-xl hover:bg-mccaa-teal/90 transition-all shadow-lg flex items-center justify-center gap-2 text-lg">
              Send Message <Send size={20} />
            </button>
          </form>
        </div>
      </motion.div>
    </div>
  </section>
);

const Footer = () => (
  <footer className="bg-gray-900 text-white/60 py-16 border-t border-white/5">
    <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-12">
      {/* Brand Column */}
      <div className="flex flex-col items-center md:items-start gap-6">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center text-gray-900 font-bold">
            M
          </div>
          <span className="font-bold text-white text-xl tracking-tight">MCCAA</span>
        </div>
        <p className="text-xs text-center md:text-left">© 2026 MCCAA. All rights reserved.</p>
      </div>

      {/* Links Column */}
      <div className="flex flex-col items-center md:items-start gap-4 text-sm">
        <h4 className="text-white font-bold uppercase tracking-widest text-xs mb-2">Legal & Info</h4>
        {['Privacy Policy', 'Accessibility Statement', 'Contact Us', 'Freedom of Information'].map(link => (
          <a key={link} href="#" className="hover:text-white transition-colors">{link}</a>
        ))}
      </div>

      {/* Social Column */}
      <div className="flex flex-col items-center md:items-start gap-4 text-sm">
        <h4 className="text-white font-bold uppercase tracking-widest text-xs mb-2">Follow Us</h4>
        <div className="flex flex-col gap-4">
          <a href="#" className="flex items-center gap-3 hover:text-white transition-colors group">
            <Facebook size={18} className="group-hover:scale-110 transition-transform" />
            <span>Facebook</span>
          </a>
          <a href="#" className="flex items-center gap-3 hover:text-white transition-colors group">
            <Twitter size={18} className="group-hover:scale-110 transition-transform" />
            <span>Twitter</span>
          </a>
          <a href="#" className="flex items-center gap-3 hover:text-white transition-colors group">
            <Instagram size={18} className="group-hover:scale-110 transition-transform" />
            <span>Instagram</span>
          </a>
          <a href="#" className="flex items-center gap-3 hover:text-white transition-colors group">
            <Linkedin size={18} className="group-hover:scale-110 transition-transform" />
            <span>LinkedIn</span>
          </a>
        </div>
      </div>

      {/* Right side left empty to avoid overlap with Ask l-Uffiċjal button */}
      <div className="hidden md:block"></div>
    </div>
  </footer>
);

const AIChat = ({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  const { messages, input, handleInputChange, handleSubmit, isLoading, append } = useChat({
    api: 'http://localhost:8000/chat',
    initialMessages: [
      { id: 'welcome', role: 'assistant', content: "Hello! I'm l-Uffiċjal, your MCCAA digital assistant. How can I help you with consumer rights or business regulations today?" }
    ],
  });

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleChipClick = (text: string) => {
    append({ role: 'user', content: text });
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
        >
          <motion.div 
            initial={{ scale: 0.9, y: 20, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.9, y: 20, opacity: 0 }}
            className="w-full max-w-lg h-[600px] bg-white/10 backdrop-blur-[30px] rounded-[32px] border border-white/30 shadow-2xl flex flex-col overflow-hidden relative"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-5 border-b border-white/10 bg-white/5">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center p-1 shadow-inner">
                  <div className="w-full h-full bg-mccaa-teal rounded-full flex items-center justify-center text-white font-bold text-xs">M</div>
                </div>
                <div>
                  <h3 className="text-white font-bold text-lg">l-Uffiċjal Assistant</h3>
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full animate-pulse ${isLoading ? 'bg-mccaa-orange' : 'bg-mccaa-green'}`}></span>
                    <span className="text-white/60 text-xs font-medium">{isLoading ? 'Thinking...' : 'Online now'}</span>
                  </div>
                </div>
              </div>
              <button 
                onClick={onClose}
                className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-white/10 text-white/70 transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Messages */}
            <div 
              ref={scrollRef}
              className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide"
            >
              {messages.map((msg) => (
                <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'} max-w-[85%] ${msg.role === 'user' ? 'ml-auto' : ''}`}>
                  <div className={`px-5 py-4 rounded-2xl text-sm leading-relaxed shadow-sm ${
                    msg.role === 'user' 
                      ? 'bg-mccaa-teal text-white rounded-tr-none' 
                      : 'bg-white/20 backdrop-blur-md border border-white/20 text-white rounded-tl-none'
                  }`}>
                    <div className="markdown-content">
                      <Markdown>{msg.content}</Markdown>
                    </div>
                  </div>
                  <span className="text-[10px] text-white/40 mt-2 mx-1">
                    {msg.role === 'assistant' ? 'l-Uffiċjal' : 'You'} • {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))}
              {isLoading && (
                <div className="flex flex-col items-start max-w-[85%]">
                  <div className="px-5 py-4 rounded-2xl bg-white/20 backdrop-blur-md border border-white/20 text-white rounded-tl-none flex gap-1">
                    <span className="w-1.5 h-1.5 bg-white/50 rounded-full animate-bounce"></span>
                    <span className="w-1.5 h-1.5 bg-white/50 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                    <span className="w-1.5 h-1.5 bg-white/50 rounded-full animate-bounce [animation-delay:0.4s]"></span>
                  </div>
                </div>
              )}
            </div>

            {/* Suggestions */}
            <div className="px-6 pb-2 flex flex-wrap gap-2">
              {['Consumer Rights', 'Business Compliance', 'File a Complaint'].map(chip => (
                <button 
                  key={chip}
                  disabled={isLoading}
                  onClick={() => handleChipClick(chip)}
                  className="px-4 py-2 rounded-full bg-white/5 border border-white/10 text-white/80 text-xs font-semibold hover:bg-white/10 transition-all disabled:opacity-50"
                >
                  {chip}
                </button>
              ))}
            </div>

            {/* Input */}
            <div className="p-6">
              <form onSubmit={handleSubmit}>
                <div className="relative flex items-center">
                  <input 
                    type="text"
                    value={input}
                    disabled={isLoading}
                    onChange={handleInputChange}
                    placeholder={isLoading ? "l-Uffiċjal is thinking..." : "Ask about regulations..."}
                    className="w-full bg-white/10 border border-white/20 focus:border-mccaa-teal focus:ring-0 rounded-2xl py-4 pl-5 pr-14 text-white placeholder-white/40 backdrop-blur-md outline-none transition-all disabled:opacity-50"
                  />
                  <button 
                    type="submit"
                    disabled={isLoading || !input.trim()}
                    className="absolute right-2 w-10 h-10 flex items-center justify-center rounded-xl bg-mccaa-teal text-white shadow-lg hover:bg-mccaa-teal/80 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send size={18} />
                  </button>
                </div>
              </form>
              <div className="mt-4 flex justify-center gap-4 opacity-50">
                <div className="h-1 w-8 rounded-full bg-mccaa-teal"></div>
                <div className="h-1 w-8 rounded-full bg-mccaa-burgundy"></div>
                <div className="h-1 w-8 rounded-full bg-mccaa-orange"></div>
                <div className="h-1 w-8 rounded-full bg-mccaa-yellow"></div>
                <div className="h-1 w-8 rounded-full bg-mccaa-green"></div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

const ComplaintForm = ({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) => {
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitted(true);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
        >
          <motion.div 
            initial={{ scale: 0.9, y: 20, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.9, y: 20, opacity: 0 }}
            className="w-full max-w-2xl h-[85vh] bg-white/10 backdrop-blur-[30px] rounded-[32px] border border-white/30 shadow-2xl flex flex-col overflow-hidden relative"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-8 py-6 border-b border-white/10 bg-white/5">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center p-1 shadow-inner">
                  <FileText className="text-mccaa-teal" size={24} />
                </div>
                <div>
                  <h3 className="text-white font-bold text-xl">Report an Issue</h3>
                  <p className="text-white/60 text-xs">Official Consumer Protection Report</p>
                </div>
              </div>
              <button 
                onClick={onClose}
                className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-white/10 text-white/70 transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Form Content */}
            <div className="flex-1 overflow-y-auto p-8 scrollbar-hide">
              {isSubmitted ? (
                <div className="h-full flex flex-col items-center justify-center text-center space-y-6 py-12">
                   <motion.div 
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="w-20 h-20 bg-mccaa-green/20 rounded-full flex items-center justify-center text-mccaa-green"
                   >
                      <CheckCircle size={48} />
                   </motion.div>
                   <h2 className="text-2xl font-bold text-white">Report Submitted</h2>
                   <p className="text-white/70 max-w-md">Your formal complaint has been received and assigned reference #MCC-2026-8842. Our team will review the details and contact you within 5 working days.</p>
                   <button 
                    onClick={onClose}
                    className="bg-white text-mccaa-teal font-bold px-8 py-3 rounded-xl hover:scale-105 transition-transform"
                   >
                    Close Window
                   </button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-8">
                  {/* Personal Info Section */}
                  <div className="space-y-4">
                    <h4 className="text-mccaa-teal font-bold text-xs uppercase tracking-widest">Personal Details</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-white/60 text-xs font-semibold ml-1">Full Name</label>
                        <input required type="text" placeholder="John Doe" className="w-full bg-white/5 border border-white/10 focus:border-mccaa-teal focus:ring-0 rounded-xl py-3 px-4 text-white placeholder-white/20 outline-none transition-all" />
                      </div>
                      <div className="space-y-2">
                        <label className="text-white/60 text-xs font-semibold ml-1">ID Card / Passport</label>
                        <input required type="text" placeholder="123456M" className="w-full bg-white/5 border border-white/10 focus:border-mccaa-teal focus:ring-0 rounded-xl py-3 px-4 text-white placeholder-white/20 outline-none transition-all" />
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-white/60 text-xs font-semibold ml-1">Email Address</label>
                        <input required type="email" placeholder="john@example.com" className="w-full bg-white/5 border border-white/10 focus:border-mccaa-teal focus:ring-0 rounded-xl py-3 px-4 text-white placeholder-white/20 outline-none transition-all" />
                      </div>
                      <div className="space-y-2">
                        <label className="text-white/60 text-xs font-semibold ml-1">Phone Number</label>
                        <input required type="tel" placeholder="+356 21XX XXXX" className="w-full bg-white/5 border border-white/10 focus:border-mccaa-teal focus:ring-0 rounded-xl py-3 px-4 text-white placeholder-white/20 outline-none transition-all" />
                      </div>
                    </div>
                  </div>

                  {/* Trader Details */}
                  <div className="space-y-4">
                    <h4 className="text-mccaa-burgundy font-bold text-xs uppercase tracking-widest">Trader Details</h4>
                    <div className="space-y-2">
                      <label className="text-white/60 text-xs font-semibold ml-1">Business Name</label>
                      <input required type="text" placeholder="Company Name Ltd." className="w-full bg-white/5 border border-white/10 focus:border-mccaa-burgundy focus:ring-0 rounded-xl py-3 px-4 text-white placeholder-white/20 outline-none transition-all" />
                    </div>
                  </div>

                  {/* Complaint Details */}
                  <div className="space-y-4">
                    <h4 className="text-mccaa-orange font-bold text-xs uppercase tracking-widest">Complaint Details</h4>
                    <div className="space-y-2">
                      <label className="text-white/60 text-xs font-semibold ml-1">Type of Issue</label>
                      <select required className="w-full bg-white/5 border border-white/10 focus:border-mccaa-orange focus:ring-0 rounded-xl py-3 px-4 text-white outline-none transition-all appearance-none">
                        <option value="" className="bg-gray-900">Select Issue Type...</option>
                        <option value="product-safety" className="bg-gray-900">Product Safety Concern</option>
                        <option value="weights-measures" className="bg-gray-900">Incorrect Weights / Measures</option>
                        <option value="unfair-practice" className="bg-gray-900">Unfair Commercial Practice</option>
                        <option value="commercial-dispute" className="bg-gray-900">Commercial Dispute</option>
                        <option value="other" className="bg-gray-900">Other</option>
                      </select>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="text-white/60 text-xs font-semibold ml-1">Date of Purchase</label>
                        <input required type="date" className="w-full bg-white/5 border border-white/10 focus:border-mccaa-orange focus:ring-0 rounded-xl py-3 px-4 text-white placeholder-white/20 outline-none transition-all" />
                      </div>
                      <div className="space-y-2">
                        <label className="text-white/60 text-xs font-semibold ml-1">Transaction Ref (Optional)</label>
                        <input type="text" placeholder="Receipt # / Invoice #" className="w-full bg-white/5 border border-white/10 focus:border-mccaa-orange focus:ring-0 rounded-xl py-3 px-4 text-white placeholder-white/20 outline-none transition-all" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <label className="text-white/60 text-xs font-semibold ml-1">Description of Issue</label>
                      <textarea required rows={4} placeholder="Please provide a detailed description of the problem..." className="w-full bg-white/5 border border-white/10 focus:border-mccaa-orange focus:ring-0 rounded-xl py-3 px-4 text-white placeholder-white/20 outline-none transition-all resize-none"></textarea>
                    </div>
                  </div>

                  {/* Submit */}
                  <div className="pt-4">
                    <button type="submit" className="w-full bg-mccaa-teal text-white font-bold py-4 rounded-2xl shadow-lg hover:bg-mccaa-teal/80 transition-all flex items-center justify-center gap-2 group">
                      Submit Formal Report
                      <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                    </button>
                    <p className="text-white/30 text-[10px] text-center mt-4 uppercase tracking-widest">Secure submission to MCCAA Enforcement Division</p>
                  </div>
                </form>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

const NewsDetail = ({ article, onBack, onArticleClick }: { article: any, onBack: () => void, onArticleClick: (a: any) => void }) => {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [article]);

  const otherArticles = ARTICLES.filter(a => a.id !== article.id);

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="pt-32 pb-24 bg-white min-h-screen"
    >
      <div className="max-w-7xl mx-auto px-6">
        <button 
          onClick={onBack}
          className="flex items-center text-mccaa-teal font-bold mb-8 hover:gap-2 transition-all"
        >
          <ArrowUp className="-rotate-90 mr-2" size={18} /> Back to News
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            <div className="space-y-4">
              <span className={`text-xs font-bold ${article.color} uppercase tracking-widest`}>{article.category}</span>
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 leading-tight">{article.title}</h1>
              <div className="flex items-center text-gray-500 text-sm gap-4">
                <span>Published on {article.date}</span>
                <span>•</span>
                <span>5 min read</span>
              </div>
            </div>

            <div className="aspect-video rounded-3xl overflow-hidden shadow-2xl">
              <img 
                src={`https://picsum.photos/seed/${article.seed}/1200/800`} 
                alt={article.title} 
                className="w-full h-full object-cover"
                referrerPolicy="no-referrer"
              />
            </div>

            <div className="prose prose-lg max-w-none text-gray-700 leading-relaxed whitespace-pre-line">
              {article.content}
            </div>

            <div className="pt-12 border-t border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="text-sm font-bold text-gray-900">Share this article:</span>
                <div className="flex gap-2">
                  {[Facebook, Twitter, Linkedin].map((Icon, i) => (
                    <button key={i} className="p-2 rounded-full bg-gray-50 hover:bg-mccaa-teal hover:text-white transition-colors">
                      <Icon size={18} />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-8">
            <h3 className="text-xl font-bold text-gray-900 pb-4 border-b border-gray-100">Other News</h3>
            <div className="space-y-6">
              {otherArticles.map((a) => (
                <button 
                  key={a.id}
                  onClick={() => onArticleClick(a)}
                  className="group flex gap-4 text-left items-start"
                >
                  <div className="w-24 h-24 rounded-xl overflow-hidden shrink-0">
                    <img 
                      src={`https://picsum.photos/seed/${a.seed}/200/200`} 
                      alt={a.title} 
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform"
                      referrerPolicy="no-referrer"
                    />
                  </div>
                  <div className="space-y-1">
                    <span className={`text-[10px] font-bold ${a.color} uppercase tracking-widest`}>{a.category}</span>
                    <h4 className="text-sm font-bold text-gray-900 line-clamp-2 group-hover:text-mccaa-teal transition-colors">{a.title}</h4>
                    <span className="text-[10px] text-gray-400">{a.date}</span>
                  </div>
                </button>
              ))}
            </div>

            <div className="p-8 bg-mccaa-teal rounded-3xl text-white space-y-4">
              <h4 className="font-bold text-lg">Stay Updated</h4>
              <p className="text-sm text-white/80">Subscribe to our newsletter for the latest regulatory updates.</p>
              <div className="space-y-2">
                <input type="email" placeholder="Your email" className="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-2 text-sm placeholder-white/40 outline-none focus:bg-white/20 transition-all" />
                <button className="w-full bg-white text-mccaa-teal font-bold py-2 rounded-xl text-sm hover:scale-105 transition-transform">Subscribe</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const AboutPage = () => {
  return (
    <div className="pt-32 pb-20 px-4 max-w-7xl mx-auto">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-16"
      >
        <div className="text-center space-y-4">
          <h1 className="text-5xl font-bold tracking-tight text-gray-900">About MCCAA</h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            The Malta Competition and Consumer Affairs Authority is dedicated to ensuring fair competition and consumer protection.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            { title: 'Our Mission', text: 'To promote and enhance competition and consumer welfare in Malta through effective regulation and advocacy.' },
            { title: 'Our Vision', text: 'To be a leading regulatory authority that fosters a competitive market and empowers consumers.' },
            { title: 'Our Values', text: 'Integrity, Transparency, Excellence, and Accountability in everything we do.' }
          ].map((item, i) => (
            <div key={i} className="p-8 bg-white rounded-3xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <h3 className="text-xl font-bold mb-4 text-mccaa-teal">{item.title}</h3>
              <p className="text-gray-600 leading-relaxed">{item.text}</p>
            </div>
          ))}
        </div>

        <div className="bg-gray-900 rounded-[40px] p-8 md:p-16 text-white overflow-hidden relative">
          <div className="relative z-10 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <h2 className="text-3xl font-bold">Our Leadership</h2>
              <p className="text-white/70 leading-relaxed">
                Led by a board of dedicated professionals, the MCCAA operates across several directorates, each focused on specific areas of competition and consumer protection.
              </p>
              <div className="space-y-4">
                {['Office for Competition', 'Office for Consumer Affairs', 'Technical Regulations Division', 'Standards and Metrology Institute'].map((dept, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-1.5 h-1.5 rounded-full bg-mccaa-teal"></div>
                    <span className="text-white/80 font-medium">{dept}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <img src="https://picsum.photos/seed/office1/400/300" alt="Office" className="rounded-2xl opacity-60" referrerPolicy="no-referrer" />
              <img src="https://picsum.photos/seed/office2/400/300" alt="Team" className="rounded-2xl opacity-60 mt-8" referrerPolicy="no-referrer" />
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

const LoginPage = ({ onBack }: { onBack: () => void }) => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md bg-white rounded-[32px] shadow-2xl p-8 md:p-12 border border-gray-100"
      >
        <div className="text-center mb-10">
          <button onClick={onBack} className="mb-6 text-gray-400 hover:text-mccaa-teal transition-colors flex items-center gap-2 mx-auto text-sm font-medium">
            <ArrowLeft size={16} /> Back to Home
          </button>
          <div className="w-16 h-16 bg-mccaa-teal rounded-2xl flex items-center justify-center text-white font-bold text-2xl mx-auto mb-4 shadow-lg">
            M
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Welcome Back</h2>
          <p className="text-gray-500 mt-2">Sign in to your MCCAA portal</p>
        </div>

        <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
          <div className="space-y-2">
            <label className="text-xs font-bold uppercase tracking-widest text-gray-400">Email Address</label>
            <input 
              type="email" 
              placeholder="name@company.com"
              className="w-full bg-gray-50 border border-gray-200 rounded-xl px-5 py-4 focus:border-mccaa-teal focus:ring-0 outline-none transition-all"
            />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-xs font-bold uppercase tracking-widest text-gray-400">Password</label>
              <button className="text-xs font-bold text-mccaa-teal hover:underline">Forgot?</button>
            </div>
            <input 
              type="password" 
              placeholder="••••••••"
              className="w-full bg-gray-50 border border-gray-200 rounded-xl px-5 py-4 focus:border-mccaa-teal focus:ring-0 outline-none transition-all"
            />
          </div>
          <button className="w-full bg-mccaa-teal text-white font-bold py-4 rounded-xl hover:bg-mccaa-teal/90 transition-all shadow-lg">
            Sign In
          </button>
        </form>

        <div className="mt-8 pt-8 border-t border-gray-100 text-center">
          <p className="text-sm text-gray-500">
            Don't have an account? <button className="text-mccaa-teal font-bold hover:underline">Register here</button>
          </p>
        </div>
      </motion.div>
    </div>
  );
};

const ConsumerRightsPage = ({ onOpenReport }: { onOpenReport: () => void }) => {
  const rights = [
    { title: 'Legal Guarantee', desc: 'All goods bought in Malta come with a 2-year legal guarantee against defects.', icon: <ShieldCheck size={24} /> },
    { title: 'Right to Return', desc: '14-day cooling-off period for online purchases with full refund rights.', icon: <ArrowRight size={24} /> },
    { title: 'Product Safety', desc: 'Right to expect that all products on the market meet strict safety standards.', icon: <CheckCircle size={24} /> },
    { title: 'Clear Pricing', desc: 'Prices must be clearly displayed, including VAT and any additional charges.', icon: <Scale size={24} /> },
  ];

  return (
    <div className="pt-32 pb-20">
      <div className="max-w-7xl mx-auto px-4">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-16"
        >
          <div className="text-center space-y-4">
            <h1 className="text-5xl font-bold tracking-tight text-gray-900">Your Consumer Rights</h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Empowering citizens with knowledge and protection in the Maltese marketplace.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {rights.map((right, i) => (
              <div key={i} className="p-10 bg-white rounded-[32px] shadow-sm border border-gray-100 flex gap-6 items-start hover:shadow-md transition-shadow">
                <div className="w-14 h-14 bg-mccaa-teal/10 rounded-2xl flex items-center justify-center text-mccaa-teal shrink-0">
                  {right.icon}
                </div>
                <div>
                  <h3 className="text-xl font-bold mb-2">{right.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{right.desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-mccaa-teal rounded-[40px] p-12 text-white text-center space-y-8">
            <h2 className="text-3xl font-bold">Have your rights been breached?</h2>
            <p className="text-white/80 max-w-xl mx-auto text-lg">
              If you believe a business has failed to honor your legal rights, you can file a formal complaint with our Office for Consumer Affairs.
            </p>
            <button 
              onClick={onOpenReport}
              className="bg-white text-mccaa-teal font-bold px-10 py-4 rounded-xl hover:scale-105 transition-transform shadow-xl inline-flex items-center gap-2"
            >
              Start a Formal Complaint <Send size={20} />
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

const CallsPage = () => {
  const [activeTab, setActiveTab] = useState<'procurement' | 'vacancies'>('procurement');
  const [searchQuery, setSearchQuery] = useState('');
  const [isApplyModalOpen, setIsApplyModalOpen] = useState(false);
  const [selectedCall, setSelectedCall] = useState<any>(null);
  const [viewingCall, setViewingCall] = useState<any>(null);

  const procurementCalls = [
    { 
      id: 'p1', 
      title: 'Provision of IT Support Services', 
      category: 'IT Services', 
      deadline: '2026-04-15', 
      ref: 'MCCAA/T/001/2026',
      description: 'The MCCAA is seeking a qualified service provider to deliver comprehensive IT support services across all its offices. This includes hardware maintenance, software troubleshooting, network management, and cybersecurity monitoring.',
      requirements: ['Minimum 5 years experience in IT support', 'ISO 27001 certification preferred', 'Local presence in Malta', '24/7 emergency support capability'],
      budget: 'Competitive Tendering'
    },
    { 
      id: 'p2', 
      title: 'Consultancy for Market Surveillance', 
      category: 'Consultancy', 
      deadline: '2026-05-01', 
      ref: 'MCCAA/T/002/2026',
      description: 'Consultancy services required to enhance our market surveillance strategies in line with new EU regulations. The consultant will review current processes and recommend improvements for better consumer protection.',
      requirements: ['Expertise in EU Market Surveillance Regulation', 'Proven track record in regulatory consultancy', 'Fluency in English and Maltese'],
      budget: 'Fixed Fee'
    },
    { 
      id: 'p3', 
      title: 'Supply of Laboratory Equipment', 
      category: 'Equipment', 
      deadline: '2026-04-20', 
      ref: 'MCCAA/T/003/2026',
      description: 'Tender for the supply, delivery, and installation of specialized laboratory equipment for our Standards and Metrology Institute. Equipment must meet international calibration standards.',
      requirements: ['Authorized distributor status', 'Full warranty and maintenance package', 'On-site training for staff'],
      budget: 'Public Tender'
    },
  ];

  const vacancies = [
    { 
      id: 'v1', 
      title: 'Senior Legal Officer', 
      category: 'Legal', 
      deadline: '2026-03-30', 
      ref: 'VAC/2026/01',
      description: 'We are looking for an experienced Legal Officer to join our Office for Competition. You will be responsible for legal analysis, drafting regulations, and representing the authority in legal proceedings.',
      requirements: ['Law degree (LL.D or equivalent)', 'Warrant to practice in Malta', 'Specialization in Competition Law is an asset'],
      salary: 'Scale 5'
    },
    { 
      id: 'v2', 
      title: 'Market Surveillance Inspector', 
      category: 'Technical', 
      deadline: '2026-04-10', 
      ref: 'VAC/2026/02',
      description: 'Inspectors are responsible for conducting site visits, checking product compliance, and ensuring that goods on the market meet safety standards.',
      requirements: ['Technical diploma or degree', 'Valid driving license', 'Strong attention to detail'],
      salary: 'Scale 9'
    },
    { 
      id: 'v3', 
      title: 'Administrative Assistant', 
      category: 'Admin', 
      deadline: '2026-03-25', 
      ref: 'VAC/2026/03',
      description: 'Providing essential administrative support to the Technical Regulations Division, including document management, meeting coordination, and public inquiries.',
      requirements: ['O-level standard of education', 'Proficiency in MS Office', 'Excellent communication skills'],
      salary: 'Scale 14'
    },
  ];

  const filteredItems = (activeTab === 'procurement' ? procurementCalls : vacancies).filter(item => 
    item.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
    item.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.ref.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleApply = (call: any) => {
    setSelectedCall(call);
    setIsApplyModalOpen(true);
  };

  return (
    <div className="pt-32 pb-20 px-4 max-w-7xl mx-auto min-h-screen">
      <AnimatePresence mode="wait">
        {!viewingCall ? (
          <motion.div 
            key="list"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="space-y-12"
          >
            <div className="text-center space-y-4">
              <h1 className="text-5xl font-bold tracking-tight text-gray-900">Calls & Vacancies</h1>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Explore active procurement opportunities and career openings at MCCAA.
              </p>
            </div>

            {/* Tabs */}
            <div className="flex justify-center">
              <div className="bg-gray-100 p-1.5 rounded-2xl flex gap-1">
                <button 
                  onClick={() => setActiveTab('procurement')}
                  className={`px-8 py-3 rounded-xl font-bold text-sm transition-all ${
                    activeTab === 'procurement' ? 'bg-white text-mccaa-teal shadow-sm' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Procurement
                </button>
                <button 
                  onClick={() => setActiveTab('vacancies')}
                  className={`px-8 py-3 rounded-xl font-bold text-sm transition-all ${
                    activeTab === 'vacancies' ? 'bg-white text-mccaa-teal shadow-sm' : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Vacancies
                </button>
              </div>
            </div>

            {/* Search & Filter */}
            <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-white p-6 rounded-3xl shadow-sm border border-gray-100">
              <div className="relative w-full md:max-w-md">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                <input 
                  type="text" 
                  placeholder={`Search ${activeTab}...`}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:border-mccaa-teal focus:ring-0 outline-none transition-all"
                />
              </div>
              <button className="flex items-center gap-2 px-6 py-3 bg-gray-50 border border-gray-200 rounded-xl text-sm font-bold text-gray-600 hover:bg-gray-100 transition-all">
                <Filter size={18} /> Filters
              </button>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredItems.map((item) => (
                <motion.div 
                  key={item.id}
                  layoutId={`card-${item.id}`}
                  onClick={() => setViewingCall(item)}
                  className="bg-white p-8 rounded-[32px] shadow-sm border border-gray-100 flex flex-col justify-between hover:shadow-md transition-all cursor-pointer group"
                >
                  <div className="space-y-4">
                    <div className="flex justify-between items-start">
                      <span className="px-3 py-1 bg-mccaa-teal/10 text-mccaa-teal rounded-full text-[10px] font-bold uppercase tracking-widest">
                        {item.category}
                      </span>
                      <span className="text-[10px] text-gray-400 font-mono">{item.ref}</span>
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 leading-tight group-hover:text-mccaa-teal transition-colors">{item.title}</h3>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <FileText size={16} />
                      <span>Deadline: {item.deadline}</span>
                    </div>
                  </div>
                  <div className="mt-8 flex items-center text-mccaa-teal font-bold text-sm gap-2">
                    View Details <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
                  </div>
                </motion.div>
              ))}
            </div>

            {filteredItems.length === 0 && (
              <div className="text-center py-20">
                <p className="text-gray-400 text-lg italic">No active {activeTab} found matching your search.</p>
              </div>
            )}
          </motion.div>
        ) : (
          <motion.div 
            key="detail"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="max-w-4xl mx-auto"
          >
            <button 
              onClick={() => setViewingCall(null)}
              className="flex items-center gap-2 text-mccaa-teal font-bold mb-8 hover:gap-3 transition-all"
            >
              <ArrowLeft size={20} /> Back to all calls
            </button>

            <motion.div 
              layoutId={`card-${viewingCall.id}`}
              className="bg-white rounded-[40px] shadow-2xl border border-gray-100 overflow-hidden"
            >
              <div className="p-8 md:p-12 space-y-8">
                <div className="space-y-4">
                  <div className="flex flex-wrap gap-3 items-center justify-between">
                    <span className="px-4 py-1.5 bg-mccaa-teal/10 text-mccaa-teal rounded-full text-xs font-bold uppercase tracking-widest">
                      {viewingCall.category}
                    </span>
                    <span className="text-xs text-gray-400 font-mono bg-gray-50 px-3 py-1 rounded-lg border border-gray-100">
                      Ref: {viewingCall.ref}
                    </span>
                  </div>
                  <h2 className="text-3xl md:text-5xl font-bold text-gray-900 leading-tight">
                    {viewingCall.title}
                  </h2>
                  <div className="flex flex-wrap gap-6 text-sm text-gray-500 pt-2">
                    <div className="flex items-center gap-2">
                      <FileText size={18} className="text-mccaa-teal" />
                      <span className="font-medium">Deadline: {viewingCall.deadline}</span>
                    </div>
                    {viewingCall.salary && (
                      <div className="flex items-center gap-2">
                        <Building2 size={18} className="text-mccaa-teal" />
                        <span className="font-medium">Salary: {viewingCall.salary}</span>
                      </div>
                    )}
                    {viewingCall.budget && (
                      <div className="flex items-center gap-2">
                        <Scale size={18} className="text-mccaa-teal" />
                        <span className="font-medium">Budget: {viewingCall.budget}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="h-px bg-gray-100 w-full"></div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                  <div className="lg:col-span-2 space-y-8">
                    <section className="space-y-4">
                      <h3 className="text-xl font-bold text-gray-900">Description</h3>
                      <p className="text-gray-600 leading-relaxed text-lg">
                        {viewingCall.description}
                      </p>
                    </section>

                    <section className="space-y-4">
                      <h3 className="text-xl font-bold text-gray-900">Requirements</h3>
                      <ul className="space-y-3">
                        {viewingCall.requirements.map((req: string, i: number) => (
                          <li key={i} className="flex items-start gap-3 text-gray-600">
                            <div className="w-1.5 h-1.5 rounded-full bg-mccaa-teal mt-2.5 shrink-0"></div>
                            <span>{req}</span>
                          </li>
                        ))}
                      </ul>
                    </section>
                  </div>

                  <div className="space-y-6">
                    <div className="p-8 bg-gray-50 rounded-3xl border border-gray-100 space-y-6">
                      <h4 className="font-bold text-gray-900">Ready to apply?</h4>
                      <p className="text-sm text-gray-500">
                        Ensure you have all required documents ready before starting your application.
                      </p>
                      <button 
                        onClick={() => handleApply(viewingCall)}
                        className="w-full bg-mccaa-teal text-white font-bold py-4 rounded-xl hover:bg-mccaa-teal/90 transition-all shadow-lg flex items-center justify-center gap-2"
                      >
                        Start Application <Send size={18} />
                      </button>
                    </div>

                    <div className="p-8 bg-mccaa-burgundy/5 rounded-3xl border border-mccaa-burgundy/10 space-y-4">
                      <h4 className="font-bold text-mccaa-burgundy">Need Help?</h4>
                      <p className="text-xs text-mccaa-burgundy/70">
                        Contact our {activeTab === 'procurement' ? 'Procurement Team' : 'HR department'} for any inquiries regarding this {activeTab === 'procurement' ? 'call' : 'vacancy'}.
                      </p>
                      <button className="text-sm font-bold text-mccaa-burgundy hover:underline">
                        Contact Support
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Application Modal */}
      <AnimatePresence>
        {isApplyModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              className="w-full max-w-2xl bg-white rounded-[40px] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
            >
              <div className="p-8 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                <div>
                  <h3 className="text-2xl font-bold text-gray-900">Application Form</h3>
                  <p className="text-sm text-gray-500 mt-1">Applying for: {selectedCall?.title}</p>
                </div>
                <button onClick={() => setIsApplyModalOpen(false)} className="w-10 h-10 rounded-full bg-white shadow-sm flex items-center justify-center text-gray-400 hover:text-gray-600 transition-colors">
                  <X size={20} />
                </button>
              </div>
              
              <div className="flex-1 overflow-y-auto p-8">
                <form className="space-y-6" onSubmit={(e) => { e.preventDefault(); setIsApplyModalOpen(false); alert('Application submitted successfully!'); }}>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-xs font-bold uppercase tracking-widest text-gray-400">First Name</label>
                      <input type="text" required className="w-full bg-gray-50 border border-gray-200 rounded-xl px-5 py-4 outline-none focus:border-mccaa-teal transition-all" />
                    </div>
                    <div className="space-y-2">
                      <label className="text-xs font-bold uppercase tracking-widest text-gray-400">Last Name</label>
                      <input type="text" required className="w-full bg-gray-50 border border-gray-200 rounded-xl px-5 py-4 outline-none focus:border-mccaa-teal transition-all" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-widest text-gray-400">Email Address</label>
                    <input type="email" required className="w-full bg-gray-50 border border-gray-200 rounded-xl px-5 py-4 outline-none focus:border-mccaa-teal transition-all" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-widest text-gray-400">Phone Number</label>
                    <input type="tel" required className="w-full bg-gray-50 border border-gray-200 rounded-xl px-5 py-4 outline-none focus:border-mccaa-teal transition-all" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-widest text-gray-400">
                      {activeTab === 'procurement' ? 'Upload Proposal / Quote' : 'Upload CV / Documents'}
                    </label>
                    <div className="border-2 border-dashed border-gray-200 rounded-2xl p-8 text-center hover:border-mccaa-teal transition-all cursor-pointer group">
                      <Paperclip className="mx-auto text-gray-300 group-hover:text-mccaa-teal mb-2" size={32} />
                      <p className="text-sm text-gray-500">Click to upload or drag and drop</p>
                      <p className="text-[10px] text-gray-400 mt-1">PDF, DOCX up to 10MB</p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-xs font-bold uppercase tracking-widest text-gray-400">
                      {activeTab === 'procurement' ? 'Additional Remarks' : 'Cover Letter / Additional Info'}
                    </label>
                    <textarea rows={4} className="w-full bg-gray-50 border border-gray-200 rounded-xl px-5 py-4 outline-none focus:border-mccaa-teal transition-all resize-none"></textarea>
                  </div>
                  <button type="submit" className="w-full bg-mccaa-teal text-white font-bold py-5 rounded-xl hover:bg-mccaa-teal/90 transition-all shadow-lg flex items-center justify-center gap-2">
                    Submit Application <Send size={20} />
                  </button>
                </form>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>(() => {
    const params = new URLSearchParams(window.location.search);
    const page = params.get('page');
    if (page && ['home', 'about', 'login', 'consumer-rights', 'calls', 'news', 'wizard'].includes(page)) {
      return page as Page;
    }
    return 'home';
  });
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [showStickyAI, setShowStickyAI] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState<any>(null);

  useEffect(() => {
    const handleScroll = () => {
      setShowStickyAI(window.scrollY > window.innerHeight * 0.8);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const handlePageChange = (page: Page) => {
    if (page === 'news') {
      if (currentPage !== 'home') {
        setCurrentPage('home');
      }
      setTimeout(() => {
        const newsSection = document.getElementById('news');
        if (newsSection) newsSection.scrollIntoView({ behavior: 'smooth' });
      }, 100);
      return;
    }
    setCurrentPage(page);
    setSelectedArticle(null);
    window.scrollTo(0, 0);
  };

  return (
    <div className="min-h-screen bg-gray-50 font-sans selection:bg-mccaa-teal/30">
      <Navbar onPageChange={handlePageChange} currentPage={currentPage} />
      
      <AnimatePresence mode="wait">
        {currentPage === 'home' && !selectedArticle && (
          <motion.div
            key="home"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <Hero onOpenAI={() => setIsChatOpen(true)} onOpenReport={() => setIsReportOpen(true)} onPageChange={handlePageChange} />
            <BrandingStrip />
            <Portals />
            <News onArticleClick={setSelectedArticle} />
            <Contact onOpenReport={() => setIsReportOpen(true)} />
          </motion.div>
        )}

        {selectedArticle && (
          <motion.div
            key="detail"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <NewsDetail 
              article={selectedArticle} 
              onBack={() => setSelectedArticle(null)} 
              onArticleClick={setSelectedArticle}
            />
          </motion.div>
        )}

        {currentPage === 'about' && (
          <motion.div key="about" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <AboutPage />
          </motion.div>
        )}

        {currentPage === 'login' && (
          <motion.div key="login" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <LoginPage onBack={() => setCurrentPage('home')} />
          </motion.div>
        )}

        {currentPage === 'consumer-rights' && (
          <motion.div key="consumer-rights" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <ConsumerRightsPage onOpenReport={() => setIsReportOpen(true)} />
          </motion.div>
        )}

        {currentPage === 'calls' && (
          <motion.div key="calls" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <CallsPage />
          </motion.div>
        )}

        {currentPage === 'wizard' && (
          <motion.div key="wizard" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
            <WizardClient />
          </motion.div>
        )}
      </AnimatePresence>

      <Footer />
      
      {/* Sticky AI Button */}
      <AnimatePresence>
        {showStickyAI && (
          <motion.div 
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 100, opacity: 0 }}
            className="fixed bottom-8 right-8 z-[60]"
          >
            <motion.button 
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => setIsChatOpen(true)}
              className="bg-mccaa-teal text-white p-4 rounded-full shadow-2xl flex items-center gap-2 border border-white/20 group"
            >
              <Sparkles className="text-mccaa-yellow group-hover:rotate-12 transition-transform" size={24} />
              <span className="font-bold pr-2 hidden sm:inline">Ask l-Uffiċjal</span>
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>

      <AIChat isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
      <ComplaintForm isOpen={isReportOpen} onClose={() => setIsReportOpen(false)} />
    </div>
  );
}
