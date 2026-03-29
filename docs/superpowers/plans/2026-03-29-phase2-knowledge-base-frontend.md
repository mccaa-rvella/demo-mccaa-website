# Phase 2: Knowledge Base Frontend — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the wizard with a knowledge base frontend featuring sector browsing, conversational search, Source Viewer with tag navigation, and an admin panel for article approval and inquiry trends.

**Architecture:** React Router added for `/kb/*` and `/admin/*` routes alongside the existing state-based routing. TanStack Query for API data fetching. Existing `App.tsx` and pages remain untouched.

**Tech Stack:** React 19, TypeScript, Vite, Tailwind CSS 4, React Router v7, TanStack Query v5, Motion (Framer Motion), Lucide React

**Spec:** `docs/superpowers/specs/2026-03-29-phase2-knowledge-base-frontend.md`

---

## File Structure

```
src/
├── main.tsx                             # Modified: add BrowserRouter + routes
├── App.tsx                              # Unchanged (legacy pages)
├── index.css                            # Modified: add KB-specific utility classes
├── api/
│   └── client.ts                        # API client: base URL, fetch helpers, auth
├── components/
│   ├── Wizard/Wizard.tsx                # Unchanged
│   └── ui/
│       ├── TagPill.tsx                  # Colour-coded topic/actor tag pill
│       ├── SectorCard.tsx               # Sector card for landing page
│       └── ContactForm.tsx              # Reusable inline contact form
├── kb/
│   ├── KBLayout.tsx                     # Layout: shared navbar + Outlet
│   ├── KBLanding.tsx                    # Landing page: search hero + sectors
│   ├── SearchBar.tsx                    # Search input + inline conversation
│   ├── SourceViewer.tsx                 # Full article view with sidebar
│   ├── Sidebar.tsx                      # Sticky sidebar: tags + related articles
│   └── AudiencePicker.tsx              # Business/Consumer choice modal
├── admin/
│   ├── AdminLayout.tsx                  # Layout: login gate + tab navigation
│   ├── AdminLogin.tsx                   # Admin key input form
│   ├── ArticleList.tsx                  # Article table with filters
│   ├── ArticleDetail.tsx                # Preview + approve/reject actions
│   └── TrendsDashboard.tsx              # Inquiry trends + recent inquiries
└── hooks/
    ├── useSearch.ts                     # Search state + conversation management
    ├── useSectors.ts                    # React Query hooks for sectors
    └── useAdminAuth.ts                  # Admin key in sessionStorage
```

---

### Task 1: Install Dependencies & Router Setup

**Files:**
- Modify: `package.json`
- Modify: `src/main.tsx`
- Create: `src/api/client.ts`

- [ ] **Step 1: Install new dependencies**

Run:
```bash
cd /Users/rudie/mccaa-website/demo-mccaa-website
npm install react-router-dom @tanstack/react-query
```

- [ ] **Step 2: Create API client**

```typescript
// src/api/client.ts
const API_BASE = 'http://localhost:8000';

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export function adminFetch<T>(path: string, adminKey: string, options?: RequestInit): Promise<T> {
  return apiFetch<T>(path, {
    ...options,
    headers: {
      'X-Admin-Key': adminKey,
      ...options?.headers,
    },
  });
}
```

- [ ] **Step 3: Update main.tsx with router**

```typescript
// src/main.tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App.tsx';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

// Lazy-load KB and Admin to avoid bloating the initial bundle
const KBLayout = React.lazy(() => import('./kb/KBLayout.tsx'));
const KBLanding = React.lazy(() => import('./kb/KBLanding.tsx'));
const SourceViewer = React.lazy(() => import('./kb/SourceViewer.tsx'));
const AdminLayout = React.lazy(() => import('./admin/AdminLayout.tsx'));
const ArticleList = React.lazy(() => import('./admin/ArticleList.tsx'));
const TrendsDashboard = React.lazy(() => import('./admin/TrendsDashboard.tsx'));

import React, { Suspense } from 'react';

function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-pulse text-mccaa-teal text-lg">Loading...</div>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/kb" element={<KBLayout />}>
              <Route index element={<KBLanding />} />
              <Route path=":slug" element={<SourceViewer />} />
            </Route>
            <Route path="/admin" element={<AdminLayout />}>
              <Route index element={<ArticleList />} />
              <Route path="articles" element={<ArticleList />} />
              <Route path="trends" element={<TrendsDashboard />} />
            </Route>
            <Route path="/*" element={<App />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
```

- [ ] **Step 4: Create placeholder components so the app compiles**

Create minimal placeholder files so the router doesn't break:

```typescript
// src/kb/KBLayout.tsx
import { Outlet } from 'react-router-dom';
export default function KBLayout() {
  return <div className="min-h-screen bg-gray-50"><Outlet /></div>;
}
```

```typescript
// src/kb/KBLanding.tsx
export default function KBLanding() {
  return <div className="pt-24 text-center">Knowledge Base Landing (placeholder)</div>;
}
```

```typescript
// src/kb/SourceViewer.tsx
export default function SourceViewer() {
  return <div className="pt-24 text-center">Source Viewer (placeholder)</div>;
}
```

```typescript
// src/admin/AdminLayout.tsx
import { Outlet } from 'react-router-dom';
export default function AdminLayout() {
  return <div className="min-h-screen bg-gray-50"><Outlet /></div>;
}
```

```typescript
// src/admin/ArticleList.tsx
export default function ArticleList() {
  return <div className="pt-24 text-center">Articles (placeholder)</div>;
}
```

```typescript
// src/admin/TrendsDashboard.tsx
export default function TrendsDashboard() {
  return <div className="pt-24 text-center">Trends (placeholder)</div>;
}
```

- [ ] **Step 5: Verify the app compiles and all routes work**

Run:
```bash
npm run dev
```

Test in browser:
- `http://localhost:3000/` → existing home page
- `http://localhost:3000/kb` → "Knowledge Base Landing (placeholder)"
- `http://localhost:3000/kb/some-slug` → "Source Viewer (placeholder)"
- `http://localhost:3000/admin` → "Articles (placeholder)"
- `http://localhost:3000/admin/trends` → "Trends (placeholder)"

- [ ] **Step 6: Commit**

```bash
git add package.json package-lock.json src/main.tsx src/api/client.ts src/kb/ src/admin/
git commit -m "feat: add React Router + TanStack Query, wire up KB and admin routes"
```

---

### Task 2: Shared UI Components

**Files:**
- Create: `src/components/ui/TagPill.tsx`
- Create: `src/components/ui/SectorCard.tsx`
- Create: `src/components/ui/ContactForm.tsx`

- [ ] **Step 1: Create TagPill component**

```typescript
// src/components/ui/TagPill.tsx
const TOPIC_COLOURS: Record<string, { bg: string; text: string }> = {
  technical: { bg: 'bg-[#2da0a4]', text: 'text-white' },
  consumer: { bg: 'bg-[#7a4a5f]', text: 'text-white' },
  standardisation: { bg: 'bg-[#d68f49]', text: 'text-white' },
  competition: { bg: 'bg-[#e5ca6d]', text: 'text-gray-800' },
};

const ACTOR_STYLE = { bg: 'bg-[#64748b]', text: 'text-white' };

interface TagPillProps {
  label: string;
  type: 'topic' | 'actor';
  active?: boolean;
  onClick?: () => void;
}

export default function TagPill({ label, type, active = false, onClick }: TagPillProps) {
  const style = type === 'topic'
    ? TOPIC_COLOURS[label.toLowerCase()] ?? TOPIC_COLOURS.technical
    : ACTOR_STYLE;

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium transition-all cursor-pointer
        ${style.bg} ${style.text} ${active ? 'ring-2 ring-offset-1 ring-gray-900' : 'opacity-80 hover:opacity-100'}`}
    >
      {label}
    </button>
  );
}
```

- [ ] **Step 2: Create SectorCard component**

```typescript
// src/components/ui/SectorCard.tsx
interface SectorCardProps {
  name: string;
  slug: string;
  hasBusiness: boolean;
  hasConsumer: boolean;
  visitCount?: number;
  featured?: boolean;
  onClick: (slug: string) => void;
}

export default function SectorCard({ name, slug, hasBusiness, hasConsumer, visitCount, featured, onClick }: SectorCardProps) {
  return (
    <button
      onClick={() => onClick(slug)}
      className={`text-left rounded-xl border transition-all hover:shadow-md hover:border-[#2da0a4]/50 ${
        featured
          ? 'bg-white border-[#2da0a4]/30 p-5 shadow-sm'
          : 'bg-white border-gray-200 p-4'
      }`}
    >
      <div className={`font-bold text-gray-900 ${featured ? 'text-lg' : 'text-sm'}`}>{name}</div>
      <div className="flex gap-2 mt-2">
        {hasBusiness && (
          <span className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">Business</span>
        )}
        {hasConsumer && (
          <span className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">Consumer</span>
        )}
      </div>
      {featured && visitCount != null && (
        <div className="text-xs text-gray-400 mt-2">{visitCount} visits</div>
      )}
    </button>
  );
}
```

- [ ] **Step 3: Create ContactForm component**

```typescript
// src/components/ui/ContactForm.tsx
import { useState } from 'react';
import { apiFetch } from '../../api/client';

interface ContactFormProps {
  searchContext?: Record<string, unknown>;
  matchType?: string;
}

export default function ContactForm({ searchContext, matchType }: ContactFormProps) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiFetch('/contact', {
        method: 'POST',
        body: JSON.stringify({
          user_name: name,
          user_email: email,
          message,
          search_context: searchContext ?? {},
          match_type: matchType ?? 'general',
        }),
      });
      setSubmitted(true);
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-800 text-sm">
        Thank you. We'll get back to you shortly.
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
      <div className="text-sm font-semibold text-gray-700">Contact the MCCAA</div>
      <input
        type="text" placeholder="Your name" value={name} onChange={e => setName(e.target.value)}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#2da0a4]"
      />
      <input
        type="email" placeholder="Your email" value={email} onChange={e => setEmail(e.target.value)}
        required
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#2da0a4]"
      />
      <textarea
        placeholder="How can we help?" value={message} onChange={e => setMessage(e.target.value)}
        rows={3}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#2da0a4]"
      />
      <button
        type="submit" disabled={submitting || !email}
        className="bg-[#2da0a4] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#258487] disabled:opacity-50 transition-colors"
      >
        {submitting ? 'Sending...' : 'Send Message'}
      </button>
    </form>
  );
}
```

- [ ] **Step 4: Verify the app compiles**

Run: `npm run dev` — no errors in terminal.

- [ ] **Step 5: Commit**

```bash
git add src/components/ui/
git commit -m "feat: add shared UI components — TagPill, SectorCard, ContactForm"
```

---

### Task 3: Hooks & Data Layer

**Files:**
- Create: `src/hooks/useSectors.ts`
- Create: `src/hooks/useSearch.ts`
- Create: `src/hooks/useAdminAuth.ts`

- [ ] **Step 1: Create useSectors hook**

```typescript
// src/hooks/useSectors.ts
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '../api/client';

interface Sector {
  id: number;
  name: string;
  slug: string;
  showcase: boolean;
  visit_count: number;
  article_id: number | null;
  consumer_article_id: number | null;
  has_business: boolean;
  has_consumer: boolean;
}

export function useTopSectors() {
  return useQuery<Sector[]>({
    queryKey: ['sectors', 'top'],
    queryFn: () => apiFetch('/sectors/top'),
  });
}

export function useAllSectors() {
  return useQuery<Sector[]>({
    queryKey: ['sectors', 'all'],
    queryFn: () => apiFetch('/sectors'),
  });
}
```

- [ ] **Step 2: Create useSearch hook**

```typescript
// src/hooks/useSearch.ts
import { useState, useCallback } from 'react';
import { apiFetch } from '../api/client';

interface SearchResult {
  match_type: 'strong_match' | 'ambiguous' | 'not_covered' | 'partially_related' | 'not_related';
  article_slug: string | null;
  message: string | null;
  follow_up_question: string | null;
  show_contact_form: boolean;
}

interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
}

export function useSearch() {
  const [conversationId] = useState(() => crypto.randomUUID());
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  const search = useCallback(async (query: string) => {
    setIsSearching(true);
    setMessages(prev => [...prev, { role: 'user', content: query }]);

    try {
      const res = await apiFetch<SearchResult>('/search', {
        method: 'POST',
        body: JSON.stringify({ query, conversation_id: conversationId }),
      });
      setResult(res);

      if (res.follow_up_question) {
        setMessages(prev => [...prev, { role: 'assistant', content: res.follow_up_question! }]);
      } else if (res.message) {
        setMessages(prev => [...prev, { role: 'assistant', content: res.message! }]);
      }

      return res;
    } finally {
      setIsSearching(false);
    }
  }, [conversationId]);

  const reset = useCallback(() => {
    setMessages([]);
    setResult(null);
  }, []);

  return { search, messages, result, isSearching, reset, conversationId };
}
```

- [ ] **Step 3: Create useAdminAuth hook**

```typescript
// src/hooks/useAdminAuth.ts
import { useState, useCallback } from 'react';
import { adminFetch } from '../api/client';

export function useAdminAuth() {
  const [adminKey, setAdminKeyState] = useState<string | null>(
    () => sessionStorage.getItem('mccaa_admin_key')
  );

  const login = useCallback(async (key: string) => {
    // Validate by trying to list articles
    await adminFetch('/admin/articles?status=draft', key);
    sessionStorage.setItem('mccaa_admin_key', key);
    setAdminKeyState(key);
  }, []);

  const logout = useCallback(() => {
    sessionStorage.removeItem('mccaa_admin_key');
    setAdminKeyState(null);
  }, []);

  return { adminKey, isAuthenticated: adminKey !== null, login, logout };
}
```

- [ ] **Step 4: Verify the app compiles**

Run: `npm run dev` — no errors.

- [ ] **Step 5: Commit**

```bash
git add src/hooks/
git commit -m "feat: add data hooks — useSectors, useSearch, useAdminAuth"
```

---

### Task 4: Knowledge Base Landing Page

**Files:**
- Modify: `src/kb/KBLayout.tsx`
- Modify: `src/kb/KBLanding.tsx`
- Create: `src/kb/SearchBar.tsx`
- Create: `src/kb/AudiencePicker.tsx`

- [ ] **Step 1: Implement KBLayout with shared navbar**

```typescript
// src/kb/KBLayout.tsx
import { Outlet, Link, useLocation } from 'react-router-dom';

export default function KBLayout() {
  const location = useLocation();
  const isLanding = location.pathname === '/kb';

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      {/* Navbar */}
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

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-8 text-center text-sm">
        <p>© {new Date().getFullYear()} Malta Competition and Consumer Affairs Authority</p>
      </footer>
    </div>
  );
}
```

- [ ] **Step 2: Implement SearchBar with inline conversation**

```typescript
// src/kb/SearchBar.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Send } from 'lucide-react';
import { useSearch } from '../hooks/useSearch';
import ContactForm from '../components/ui/ContactForm';

export default function SearchBar() {
  const [input, setInput] = useState('');
  const { search, messages, result, isSearching, reset, conversationId } = useSearch();
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || isSearching) return;

    const query = input.trim();
    setInput('');
    const res = await search(query);

    if (res?.match_type === 'strong_match' && res.article_slug) {
      navigate(`/kb/${res.article_slug}`);
    }
  }

  const hasConversation = messages.length > 0;
  const showContactForm = result?.show_contact_form ?? false;

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="What do you need help with?"
          className="w-full bg-white/90 backdrop-blur rounded-full px-6 py-4 pr-14 text-gray-800 placeholder-gray-400 shadow-lg border border-white/50 focus:outline-none focus:ring-2 focus:ring-white/50 text-base"
        />
        <button
          type="submit"
          disabled={isSearching || !input.trim()}
          className="absolute right-3 top-1/2 -translate-y-1/2 bg-white/30 hover:bg-white/50 p-2.5 rounded-full transition-colors disabled:opacity-30"
        >
          {isSearching ? (
            <div className="w-5 h-5 border-2 border-white/50 border-t-white rounded-full animate-spin" />
          ) : (
            <Search size={18} className="text-white" />
          )}
        </button>
      </form>

      {hasConversation && (
        <div className="mt-4 bg-white/10 backdrop-blur rounded-2xl p-4 space-y-3 border border-white/20">
          {messages.map((msg, i) => (
            <div key={i} className={`text-sm ${msg.role === 'user' ? 'text-white/80' : 'text-white font-medium'}`}>
              <span className="text-white/50 text-xs">{msg.role === 'user' ? 'You' : 'MCCAA'}:</span>{' '}
              {msg.content}
            </div>
          ))}

          {result?.match_type === 'ambiguous' && (
            <form onSubmit={handleSubmit} className="flex gap-2 mt-2">
              <input
                type="text" value={input} onChange={e => setInput(e.target.value)}
                placeholder="Type your reply..."
                className="flex-1 bg-white/20 rounded-full px-4 py-2 text-sm text-white placeholder-white/40 border border-white/20 focus:outline-none"
              />
              <button type="submit" disabled={isSearching} className="bg-white/20 hover:bg-white/30 p-2 rounded-full transition-colors">
                <Send size={14} className="text-white" />
              </button>
            </form>
          )}

          {showContactForm && (
            <div className="mt-3">
              <ContactForm
                searchContext={{ query: messages.filter(m => m.role === 'user').map(m => m.content).join(' → '), conversation_id: conversationId }}
                matchType={result?.match_type}
              />
            </div>
          )}

          <button onClick={reset} className="text-xs text-white/40 hover:text-white/60 transition-colors">
            Clear search
          </button>
        </div>
      )}

      <p className="text-center text-white/50 text-xs mt-3">
        Try: "toy safety", "CE marking", "consumer rights"
      </p>
    </div>
  );
}
```

- [ ] **Step 3: Implement AudiencePicker**

```typescript
// src/kb/AudiencePicker.tsx
import { motion, AnimatePresence } from 'motion/react';
import { Briefcase, User, X } from 'lucide-react';

interface AudiencePickerProps {
  sectorName: string;
  businessSlug: string;
  consumerSlug: string;
  onSelect: (slug: string) => void;
  onClose: () => void;
}

export default function AudiencePicker({ sectorName, businessSlug, consumerSlug, onSelect, onClose }: AudiencePickerProps) {
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}
          className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full"
          onClick={e => e.stopPropagation()}
        >
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-gray-900">{sectorName}</h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
          </div>
          <p className="text-gray-600 text-sm mb-6">Are you looking for information as a business or as a consumer?</p>
          <div className="flex gap-4">
            <button
              onClick={() => onSelect(businessSlug)}
              className="flex-1 flex flex-col items-center gap-3 p-6 rounded-xl border-2 border-gray-200 hover:border-[#2da0a4] hover:bg-[#2da0a4]/5 transition-all"
            >
              <Briefcase size={32} className="text-[#2da0a4]" />
              <span className="font-semibold text-gray-900">Business</span>
              <span className="text-xs text-gray-500">Compliance & regulations</span>
            </button>
            <button
              onClick={() => onSelect(consumerSlug)}
              className="flex-1 flex flex-col items-center gap-3 p-6 rounded-xl border-2 border-gray-200 hover:border-[#7a4a5f] hover:bg-[#7a4a5f]/5 transition-all"
            >
              <User size={32} className="text-[#7a4a5f]" />
              <span className="font-semibold text-gray-900">Consumer</span>
              <span className="text-xs text-gray-500">Your rights & safety</span>
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
```

- [ ] **Step 4: Implement KBLanding page**

```typescript
// src/kb/KBLanding.tsx
import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTopSectors, useAllSectors } from '../hooks/useSectors';
import SectorCard from '../components/ui/SectorCard';
import SearchBar from './SearchBar';
import AudiencePicker from './AudiencePicker';
import { apiFetch } from '../api/client';

interface PickerState {
  sectorName: string;
  businessSlug: string;
  consumerSlug: string;
}

export default function KBLanding() {
  const { data: topSectors } = useTopSectors();
  const { data: allSectors } = useAllSectors();
  const navigate = useNavigate();
  const [picker, setPicker] = useState<PickerState | null>(null);

  const handleSectorClick = useCallback(async (slug: string) => {
    const sector = allSectors?.find(s => s.slug === slug) ?? topSectors?.find(s => s.slug === slug);
    if (!sector) return;

    // Track visit
    apiFetch('/track/visit', { method: 'POST', body: JSON.stringify({ sector: slug }) }).catch(() => {});

    if (sector.has_business && sector.has_consumer) {
      // Both audiences exist — show picker. Use by-sector endpoint to get article slugs.
      const [bizArticle, conArticle] = await Promise.all([
        apiFetch<{ slug: string }>(`/articles/by-sector/${slug}?audience=business`).catch(() => null),
        apiFetch<{ slug: string }>(`/articles/by-sector/${slug}?audience=consumer`).catch(() => null),
      ]);
      setPicker({
        sectorName: sector.name,
        businessSlug: bizArticle?.slug ?? slug,
        consumerSlug: conArticle?.slug ?? slug,
      });
    } else {
      // Only one audience — fetch the article slug and navigate directly
      const audience = sector.has_consumer ? 'consumer' : 'business';
      try {
        const article = await apiFetch<{ slug: string }>(`/articles/by-sector/${slug}?audience=${audience}`);
        navigate(`/kb/${article.slug}`);
      } catch {
        navigate(`/kb/${slug}`);
      }
    }
  }, [allSectors, topSectors, navigate]);

  const handleAudienceSelect = (slug: string) => {
    setPicker(null);
    navigate(`/kb/${slug}`);
  };

  // Filter out top sectors from the "all" grid to avoid duplication
  const topSlugs = new Set(topSectors?.map(s => s.slug) ?? []);
  const remainingSectors = allSectors?.filter(s => !topSlugs.has(s.slug)) ?? [];

  return (
    <div className="pt-24">
      {/* Search Hero */}
      <section className="bg-gradient-to-br from-[#2da0a4] to-[#258487] py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl md:text-4xl font-bold text-white mb-2">MCCAA Knowledge Base</h1>
          <p className="text-white/70 mb-8">Find regulations, standards, and consumer rights information</p>
          <SearchBar />
        </div>
      </section>

      {/* Top 3 Sectors */}
      {topSectors && topSectors.length > 0 && (
        <section className="max-w-5xl mx-auto px-4 -mt-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {topSectors.map(s => (
              <SectorCard
                key={s.slug}
                name={s.name}
                slug={s.slug}
                hasBusiness={s.has_business}
                hasConsumer={s.has_consumer}
                visitCount={s.visit_count}
                featured
                onClick={handleSectorClick}
              />
            ))}
          </div>
        </section>
      )}

      {/* All Sectors */}
      <section className="max-w-5xl mx-auto px-4 py-12">
        <h2 className="text-lg font-bold text-gray-900 mb-4">All Sectors</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {remainingSectors.map(s => (
            <SectorCard
              key={s.slug}
              name={s.name}
              slug={s.slug}
              hasBusiness={s.has_business}
              hasConsumer={s.has_consumer}
              onClick={handleSectorClick}
            />
          ))}
        </div>
      </section>

      {/* Audience Picker Modal */}
      {picker && (
        <AudiencePicker
          sectorName={picker.sectorName}
          businessSlug={picker.businessSlug}
          consumerSlug={picker.consumerSlug}
          onSelect={handleAudienceSelect}
          onClose={() => setPicker(null)}
        />
      )}
    </div>
  );
}


```


- [ ] **Step 5: Verify the landing page renders with live data**

Run: `npm run dev`
Ensure the API server is running: `DB_PORT=5434 python -m uvicorn api.main:app --port 8000`

Test: `http://localhost:3000/kb` → should show the teal hero, top 3 sectors, and full grid.

- [ ] **Step 6: Commit**

```bash
git add src/kb/KBLayout.tsx src/kb/KBLanding.tsx src/kb/SearchBar.tsx src/kb/AudiencePicker.tsx
git commit -m "feat: implement KB landing page — search hero, sector grid, audience picker"
```

---

### Task 5: Backend — Public Article-by-Sector Endpoint

**Files:**
- Modify: `api/modules/public/router.py`

The frontend needs to navigate from a sector slug to an article. Currently the public API only has `GET /articles/:slug` (by article slug). We need a way to find articles by sector + audience.

- [ ] **Step 1: Add endpoint to find articles by sector**

Append to `api/modules/public/router.py` before the search endpoint:

```python
@router.get("/articles/by-sector/{sector_slug}")
def get_articles_by_sector(sector_slug: str, audience: str = "business"):
    """Return a published article for a given sector and audience."""
    with get_cursor(commit=False) as cur:
        cur.execute(
            "SELECT * FROM articles WHERE sector = %s AND audience = %s AND status IN ('published', 'update_pending') ORDER BY updated_at DESC LIMIT 1",
            (sector_slug, audience),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        return dict(row)
```

- [ ] **Step 2: Verify it works**

Run:
```bash
curl -s "http://localhost:8000/articles/by-sector/toys?audience=business" | python3 -m json.tool | head -5
curl -s "http://localhost:8000/articles/by-sector/toys?audience=consumer" | python3 -m json.tool | head -5
```

Expected: returns the published toy safety articles.

- [ ] **Step 3: Run backend tests to verify no regressions**

Run: `cd /Users/rudie/mccaa-website/demo-mccaa-website && python -m pytest api/tests/ -q`
Expected: 56 passed

- [ ] **Step 4: Commit**

```bash
git add api/modules/public/router.py
git commit -m "feat: add GET /articles/by-sector/:slug endpoint for frontend sector navigation"
```

---

### Task 6: Source Viewer

**Files:**
- Modify: `src/kb/SourceViewer.tsx`
- Create: `src/kb/Sidebar.tsx`

- [ ] **Step 1: Implement Sidebar component**

```typescript
// src/kb/Sidebar.tsx
import { Link } from 'react-router-dom';
import TagPill from '../components/ui/TagPill';

interface SidebarProps {
  topics: string[];
  actors: string[];
  crossCuttingSummaries: Array<{ topic: string; scope: string; article_slug: string }>;
  activeTag: string | null;
  audience: string;
  onTagClick: (tag: string) => void;
}

export default function Sidebar({ topics, actors, crossCuttingSummaries, activeTag, audience, onTagClick }: SidebarProps) {
  return (
    <aside className="w-56 flex-shrink-0 hidden lg:block">
      <div className="sticky top-28 space-y-6">
        {/* Topics */}
        <div>
          <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Topics</div>
          <div className="flex flex-wrap gap-2">
            {topics.map(t => (
              <TagPill key={t} label={t} type="topic" active={activeTag === t} onClick={() => onTagClick(t)} />
            ))}
          </div>
        </div>

        {/* Actors — only for business articles */}
        {audience === 'business' && actors.length > 0 && (
          <div>
            <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Actors</div>
            <div className="flex flex-wrap gap-2">
              {actors.map(a => (
                <TagPill key={a} label={a} type="actor" active={activeTag === a} onClick={() => onTagClick(a)} />
              ))}
            </div>
          </div>
        )}

        {/* Related Topics */}
        {crossCuttingSummaries.length > 0 && (
          <div>
            <div className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Related Topics</div>
            <div className="space-y-2">
              {crossCuttingSummaries.map(s => (
                <Link
                  key={s.article_slug}
                  to={`/kb/${s.article_slug}`}
                  className="block bg-gray-50 hover:bg-gray-100 rounded-lg p-3 transition-colors"
                >
                  <div className="font-semibold text-sm text-gray-900">{s.topic}</div>
                  <div className="text-xs text-gray-500">{s.scope}</div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
```

- [ ] **Step 2: Implement SourceViewer**

```typescript
// src/kb/SourceViewer.tsx
import { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft } from 'lucide-react';
import { apiFetch } from '../api/client';
import Sidebar from './Sidebar';

const TOPIC_BORDER_COLOURS: Record<string, string> = {
  technical: 'border-l-[#2da0a4]',
  consumer: 'border-l-[#7a4a5f]',
  standardisation: 'border-l-[#d68f49]',
  competition: 'border-l-[#e5ca6d]',
};

interface Article {
  id: number;
  title: string;
  slug: string;
  sector: string;
  scope: string;
  audience: string;
  html_content: string;
  tag_map: Record<string, { topics?: string[]; actors?: string[] }>;
  cross_cutting_summaries: Array<{ topic: string; scope: string; summary: string; article_slug: string }>;
  status: string;
  updated_at: string;
}

export default function SourceViewer() {
  const { slug } = useParams<{ slug: string }>();
  const [activeTag, setActiveTag] = useState<string | null>(null);

  // Try fetching by article slug first, fallback to sector slug
  const { data: article, isLoading, error } = useQuery<Article>({
    queryKey: ['article', slug],
    queryFn: async () => {
      try {
        return await apiFetch<Article>(`/articles/${slug}`);
      } catch {
        // Fallback: try as a sector slug with audience suffix
        const parts = slug?.split('-') ?? [];
        const audience = parts[parts.length - 1];
        const sectorSlug = audience === 'business' || audience === 'consumer'
          ? parts.slice(0, -1).join('-')
          : slug;
        const aud = audience === 'consumer' ? 'consumer' : 'business';
        return await apiFetch<Article>(`/articles/by-sector/${sectorSlug}?audience=${aud}`);
      }
    },
    enabled: !!slug,
  });

  // Track visit
  useEffect(() => {
    if (article) {
      apiFetch('/track/visit', {
        method: 'POST',
        body: JSON.stringify({ sector: article.sector }),
      }).catch(() => {});
    }
  }, [article]);

  // Extract unique topics and actors from tag_map
  const { topics, actors } = useMemo(() => {
    if (!article?.tag_map) return { topics: [], actors: [] };
    const topicSet = new Set<string>();
    const actorSet = new Set<string>();
    for (const section of Object.values(article.tag_map)) {
      section.topics?.forEach(t => topicSet.add(t));
      section.actors?.forEach(a => actorSet.add(a));
    }
    return { topics: Array.from(topicSet), actors: Array.from(actorSet) };
  }, [article]);

  function handleTagClick(tag: string) {
    setActiveTag(prev => prev === tag ? null : tag);
    // Scroll to first matching section
    const sections = document.querySelectorAll('[data-topics], [data-actors]');
    for (const section of sections) {
      const sectionTopics = section.getAttribute('data-topics')?.split(',') ?? [];
      const sectionActors = section.getAttribute('data-actors')?.split(',') ?? [];
      if (sectionTopics.includes(tag) || sectionActors.includes(tag)) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        break;
      }
    }
  }

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center pt-24"><div className="animate-pulse text-[#2da0a4]">Loading article...</div></div>;
  }

  if (error || !article) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center pt-24 gap-4">
        <p className="text-gray-500">Article not found</p>
        <Link to="/kb" className="text-[#2da0a4] hover:underline">← Back to Knowledge Base</Link>
      </div>
    );
  }

  // Determine border colour for the primary topic
  const primaryTopic = topics[0]?.toLowerCase() ?? 'technical';

  return (
    <div className="pt-24 max-w-6xl mx-auto px-4">
      {/* Header */}
      <div className="mb-6">
        <Link to="/kb" className="text-sm text-[#2da0a4] hover:underline flex items-center gap-1 mb-3">
          <ArrowLeft size={14} /> Back to Knowledge Base
        </Link>
        <div className="flex items-center gap-3 mb-2">
          <span className="bg-[#2da0a4] text-white text-xs font-bold px-3 py-1 rounded-full">{article.sector}</span>
          {article.audience === 'consumer' && (
            <span className="bg-[#7a4a5f] text-white text-xs font-bold px-3 py-1 rounded-full">Consumer</span>
          )}
          <span className="text-xs text-gray-400">Updated {new Date(article.updated_at).toLocaleDateString()}</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">{article.title}</h1>
        {article.status === 'update_pending' && (
          <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-2 text-sm text-yellow-800">
            This article is being updated with new information.
          </div>
        )}
      </div>

      {/* Content + Sidebar */}
      <div className="flex gap-8 pb-16">
        <Sidebar
          topics={topics}
          actors={actors}
          crossCuttingSummaries={article.cross_cutting_summaries ?? []}
          activeTag={activeTag}
          audience={article.audience}
          onTagClick={handleTagClick}
        />

        {/* Main content */}
        <main className="flex-1 min-w-0">
          <div
            className="prose prose-gray max-w-none article-content"
            dangerouslySetInnerHTML={{ __html: article.html_content }}
          />

          {/* Cross-cutting summaries */}
          {article.cross_cutting_summaries?.map((summary, i) => (
            <div
              key={i}
              className={`border-l-4 rounded-r-lg p-4 my-4 ${
                summary.scope === 'universal'
                  ? 'border-l-[#b8e38d] bg-[#f0faf0]'
                  : 'border-l-[#2da0a4] bg-[#f0fafa]'
              }`}
            >
              <div className={`text-xs font-bold uppercase mb-1 ${
                summary.scope === 'universal' ? 'text-green-700' : 'text-[#2da0a4]'
              }`}>
                {summary.scope}
              </div>
              <div className="font-semibold text-sm text-gray-900 mb-1">{summary.topic}</div>
              <p className="text-sm text-gray-700">{summary.summary}</p>
              {summary.article_slug && (
                <Link to={`/kb/${summary.article_slug}`} className="text-sm text-[#2da0a4] hover:underline mt-2 inline-block">
                  Read full details →
                </Link>
              )}
            </div>
          ))}
        </main>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Add article content styles to index.css**

Append to `src/index.css`:

```css
/* Source Viewer article sections */
.article-content > div[data-topics] {
  border-left: 3px solid #2da0a4;
  padding-left: 1rem;
  margin-bottom: 1.5rem;
}

.article-content > div[data-topics] h2 {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.article-content > div[data-topics] p {
  color: #374151;
  line-height: 1.7;
}
```

- [ ] **Step 4: Verify the Source Viewer works**

Run: `npm run dev`
Test: `http://localhost:3000/kb/toy-safety-compliance-guide-for-business-operators-in-malta`

Should show the full article with sidebar tags and cross-cutting summaries.

- [ ] **Step 5: Commit**

```bash
git add src/kb/SourceViewer.tsx src/kb/Sidebar.tsx src/index.css
git commit -m "feat: implement Source Viewer — article display with sticky sidebar and tag navigation"
```

---

### Task 7: Admin Login & Layout

**Files:**
- Modify: `src/admin/AdminLayout.tsx`
- Create: `src/admin/AdminLogin.tsx`

- [ ] **Step 1: Implement AdminLogin**

```typescript
// src/admin/AdminLogin.tsx
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
        <input
          type="password" value={key} onChange={e => setKey(e.target.value)}
          placeholder="Admin key"
          className="w-full border border-gray-300 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#2da0a4] mb-4"
        />
        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
        <button
          type="submit" disabled={loading || !key}
          className="w-full bg-[#2da0a4] text-white py-3 rounded-lg font-medium hover:bg-[#258487] disabled:opacity-50 transition-colors"
        >
          {loading ? 'Verifying...' : 'Login'}
        </button>
      </form>
    </div>
  );
}
```

- [ ] **Step 2: Implement AdminLayout with tabs**

```typescript
// src/admin/AdminLayout.tsx
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
      {/* Admin header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/admin" className="font-bold text-gray-900 text-lg">MCCAA Admin</Link>
            <nav className="flex gap-1">
              <Link
                to="/admin/articles"
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isArticles ? 'bg-[#2da0a4]/10 text-[#2da0a4]' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <FileText size={16} /> Articles
              </Link>
              <Link
                to="/admin/trends"
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isTrends ? 'bg-[#2da0a4]/10 text-[#2da0a4]' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
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
```

- [ ] **Step 3: Verify admin login works**

Run: `npm run dev`
Test: `http://localhost:3000/admin` → login form → enter `mccaa-admin-2026` → should see admin layout with tabs.

- [ ] **Step 4: Commit**

```bash
git add src/admin/AdminLayout.tsx src/admin/AdminLogin.tsx
git commit -m "feat: implement admin layout — login gate with tab navigation"
```

---

### Task 8: Article Management (Admin)

**Files:**
- Modify: `src/admin/ArticleList.tsx`
- Create: `src/admin/ArticleDetail.tsx`

- [ ] **Step 1: Implement ArticleList**

```typescript
// src/admin/ArticleList.tsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useOutletContext } from 'react-router-dom';
import { adminFetch } from '../api/client';
import ArticleDetail from './ArticleDetail';

interface Article {
  id: number;
  title: string;
  slug: string;
  sector: string;
  audience: string;
  status: string;
  updated_at: string;
  html_content: string;
  tag_map: Record<string, unknown>;
  skills_used: string[];
  source_knowledge_unit_ids: number[];
}

const STATUS_COLOURS: Record<string, string> = {
  draft: 'bg-yellow-100 text-yellow-800',
  published: 'bg-green-100 text-green-800',
  update_pending: 'bg-blue-100 text-blue-800',
  rejected: 'bg-red-100 text-red-800',
  archived: 'bg-gray-100 text-gray-500',
};

export default function ArticleList() {
  const { adminKey } = useOutletContext<{ adminKey: string }>();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState('');
  const [audienceFilter, setAudienceFilter] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const { data: articles, isLoading } = useQuery<Article[]>({
    queryKey: ['admin', 'articles', statusFilter, audienceFilter],
    queryFn: () => {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      if (audienceFilter) params.set('audience', audienceFilter);
      const qs = params.toString();
      return adminFetch(`/admin/articles${qs ? `?${qs}` : ''}`, adminKey);
    },
    staleTime: 30 * 1000,
    refetchOnWindowFocus: true,
  });

  const approveMutation = useMutation({
    mutationFn: (id: number) => adminFetch(`/admin/articles/${id}/approve`, adminKey, {
      method: 'POST',
      body: JSON.stringify({ approved_by: 'admin@mccaa.org.mt' }),
    }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'articles'] }),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: number) => adminFetch(`/admin/articles/${id}/reject`, adminKey, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'articles'] }),
  });

  const selectedArticle = articles?.find(a => a.id === selectedId);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Articles</h1>
        <div className="flex gap-3">
          <select
            value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="update_pending">Update Pending</option>
            <option value="rejected">Rejected</option>
          </select>
          <select
            value={audienceFilter} onChange={e => setAudienceFilter(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value="">All audiences</option>
            <option value="business">Business</option>
            <option value="consumer">Consumer</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Loading articles...</div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Title</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Sector</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Audience</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-500">Updated</th>
              </tr>
            </thead>
            <tbody>
              {articles?.map(article => (
                <tr
                  key={article.id}
                  onClick={() => setSelectedId(selectedId === article.id ? null : article.id)}
                  className={`border-b border-gray-100 cursor-pointer transition-colors ${
                    selectedId === article.id ? 'bg-[#2da0a4]/5' : 'hover:bg-gray-50'
                  }`}
                >
                  <td className="px-4 py-3 font-medium text-gray-900">{article.title}</td>
                  <td className="px-4 py-3 text-gray-600">{article.sector}</td>
                  <td className="px-4 py-3 text-gray-600 capitalize">{article.audience}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLOURS[article.status] ?? ''}`}>
                      {article.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">{new Date(article.updated_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Inline detail panel */}
          {selectedArticle && (
            <ArticleDetail
              article={selectedArticle}
              onApprove={() => approveMutation.mutate(selectedArticle.id)}
              onReject={() => rejectMutation.mutate(selectedArticle.id)}
              isApproving={approveMutation.isPending}
              isRejecting={rejectMutation.isPending}
            />
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Implement ArticleDetail**

```typescript
// src/admin/ArticleDetail.tsx
import { CheckCircle, XCircle } from 'lucide-react';

interface ArticleDetailProps {
  article: {
    id: number;
    title: string;
    sector: string;
    audience: string;
    status: string;
    html_content: string;
    skills_used: string[];
    source_knowledge_unit_ids: number[];
  };
  onApprove: () => void;
  onReject: () => void;
  isApproving: boolean;
  isRejecting: boolean;
}

export default function ArticleDetail({ article, onApprove, onReject, isApproving, isRejecting }: ArticleDetailProps) {
  const canApprove = article.status === 'draft' || article.status === 'update_pending';
  const canReject = article.status === 'draft' || article.status === 'update_pending';

  return (
    <div className="border-t-2 border-[#2da0a4] bg-gray-50 p-6">
      {/* Actions */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm text-gray-500">
          Skills: {article.skills_used.length > 0 ? article.skills_used.join(', ') : 'none'} |
          Sources: {article.source_knowledge_unit_ids.length} knowledge units
        </div>
        <div className="flex gap-3">
          {canApprove && (
            <button
              onClick={onApprove} disabled={isApproving}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              <CheckCircle size={16} /> {isApproving ? 'Approving...' : 'Approve'}
            </button>
          )}
          {canReject && (
            <button
              onClick={onReject} disabled={isRejecting}
              className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              <XCircle size={16} /> {isRejecting ? 'Rejecting...' : 'Reject'}
            </button>
          )}
        </div>
      </div>

      {/* Article preview */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 max-h-96 overflow-y-auto">
        <div dangerouslySetInnerHTML={{ __html: article.html_content }} className="prose prose-sm max-w-none" />
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verify articles admin works**

Run: `npm run dev`
Test: `http://localhost:3000/admin` → login → see article table → click a row → see preview → approve/reject buttons work.

- [ ] **Step 4: Commit**

```bash
git add src/admin/ArticleList.tsx src/admin/ArticleDetail.tsx
git commit -m "feat: implement article management — list, filter, preview, approve/reject"
```

---

### Task 9: Trends Dashboard (Admin)

**Files:**
- Modify: `src/admin/TrendsDashboard.tsx`

- [ ] **Step 1: Implement TrendsDashboard**

```typescript
// src/admin/TrendsDashboard.tsx
import { useQuery } from '@tanstack/react-query';
import { useOutletContext } from 'react-router-dom';
import { adminFetch } from '../api/client';
import { AlertCircle } from 'lucide-react';

interface Trend {
  query: string;
  match_type: string;
  count: number;
  last_seen: string;
}

interface Inquiry {
  id: number;
  user_name: string;
  user_email: string;
  message: string;
  match_type: string;
  search_context: Record<string, unknown>;
  status: string;
  created_at: string;
}

const MATCH_TYPE_LABELS: Record<string, { label: string; colour: string }> = {
  strong_match: { label: 'Strong Match', colour: 'bg-green-100 text-green-800' },
  ambiguous: { label: 'Ambiguous', colour: 'bg-yellow-100 text-yellow-800' },
  not_covered: { label: 'Not Covered', colour: 'bg-red-100 text-red-800' },
  partially_related: { label: 'Partial', colour: 'bg-orange-100 text-orange-800' },
  not_related: { label: 'Not Related', colour: 'bg-gray-100 text-gray-600' },
};

export default function TrendsDashboard() {
  const { adminKey } = useOutletContext<{ adminKey: string }>();

  const { data: trends } = useQuery<Trend[]>({
    queryKey: ['admin', 'trends'],
    queryFn: () => adminFetch('/admin/inquiries/trends', adminKey),
    staleTime: 30 * 1000,
  });

  const { data: inquiries } = useQuery<Inquiry[]>({
    queryKey: ['admin', 'inquiries'],
    queryFn: () => adminFetch('/admin/inquiries', adminKey),
    staleTime: 30 * 1000,
  });

  const contentGaps = trends?.filter(t => t.match_type === 'not_covered') ?? [];

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Inquiry Trends</h1>

      {/* Content Gaps Alert */}
      {contentGaps.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertCircle size={18} className="text-red-600" />
            <h3 className="font-semibold text-red-800">Content Gaps Detected</h3>
          </div>
          <p className="text-sm text-red-700 mb-3">These topics are within MCCAA's remit but have no published article:</p>
          <div className="flex flex-wrap gap-2">
            {contentGaps.map(g => (
              <span key={g.query} className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm">
                {g.query} ({g.count}x)
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Trends Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h2 className="font-semibold text-gray-700">Top Search Queries</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left px-4 py-2 text-gray-500 font-medium">Query</th>
              <th className="text-left px-4 py-2 text-gray-500 font-medium">Match Type</th>
              <th className="text-left px-4 py-2 text-gray-500 font-medium">Count</th>
              <th className="text-left px-4 py-2 text-gray-500 font-medium">Last Seen</th>
            </tr>
          </thead>
          <tbody>
            {trends?.map((t, i) => {
              const mt = MATCH_TYPE_LABELS[t.match_type] ?? { label: t.match_type, colour: 'bg-gray-100 text-gray-600' };
              return (
                <tr key={i} className="border-b border-gray-50">
                  <td className="px-4 py-2 font-medium text-gray-900">{t.query}</td>
                  <td className="px-4 py-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${mt.colour}`}>{mt.label}</span>
                  </td>
                  <td className="px-4 py-2 text-gray-600">{t.count}</td>
                  <td className="px-4 py-2 text-gray-400">{new Date(t.last_seen).toLocaleDateString()}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {(!trends || trends.length === 0) && (
          <div className="text-center py-8 text-gray-400">No inquiry data yet</div>
        )}
      </div>

      {/* Recent Inquiries */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h2 className="font-semibold text-gray-700">Recent Inquiries</h2>
        </div>
        <div className="divide-y divide-gray-100">
          {inquiries?.slice(0, 20).map(inq => (
            <div key={inq.id} className="px-4 py-3">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-900 text-sm">{inq.user_name || 'Anonymous'}</span>
                <span className="text-xs text-gray-400">{new Date(inq.created_at).toLocaleDateString()}</span>
              </div>
              <p className="text-sm text-gray-600">{inq.message}</p>
              {inq.match_type && (
                <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                  MATCH_TYPE_LABELS[inq.match_type]?.colour ?? 'bg-gray-100 text-gray-600'
                }`}>
                  {MATCH_TYPE_LABELS[inq.match_type]?.label ?? inq.match_type}
                </span>
              )}
            </div>
          ))}
          {(!inquiries || inquiries.length === 0) && (
            <div className="text-center py-8 text-gray-400">No inquiries yet</div>
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify trends dashboard works**

Run: `npm run dev`
Test: `http://localhost:3000/admin/trends` → should show trends table and recent inquiries (populated from earlier smoke testing).

- [ ] **Step 3: Commit**

```bash
git add src/admin/TrendsDashboard.tsx
git commit -m "feat: implement trends dashboard — inquiry trends, content gaps, recent inquiries"
```

---

### Task 10: Add Knowledge Base Link to Existing Navbar + Final Polish

**Files:**
- Modify: `src/App.tsx` (add KB link to existing navbar)
- Modify: `src/index.css` (add any final styles)

- [ ] **Step 1: Add Knowledge Base link to existing navbar**

In `src/App.tsx`, find the Navbar component (around line 124-130) where the nav items are defined:

```typescript
{[
  { name: 'About', id: 'about' as Page },
  { name: 'News', id: 'news' as Page },
  { name: 'Calls', id: 'calls' as Page }
].map((item) => (
```

Add a Knowledge Base link before the existing items. Since the existing nav uses `onClick` with state-based routing but we need a real URL, add a direct link:

Find the closing `</div>` of the nav items loop (around line 139) and add after it:

```tsx
<a href="/kb" className="text-sm font-semibold text-gray-700 hover:text-mccaa-teal transition-colors">
  Knowledge Base
</a>
```

- [ ] **Step 2: Verify the link appears and works**

Run: `npm run dev`
Test: `http://localhost:3000/` → navbar should show "Knowledge Base" link → clicking it goes to `/kb`.

- [ ] **Step 3: Commit**

```bash
git add src/App.tsx
git commit -m "feat: add Knowledge Base link to existing navbar"
```

---

### Task 11: End-to-End Verification

- [ ] **Step 1: Verify all routes work**

Start both servers:
```bash
# Terminal 1: Backend
DB_PORT=5434 python -m uvicorn api.main:app --port 8000

# Terminal 2: Frontend
npm run dev
```

Test each route:
1. `http://localhost:3000/` → existing home page with KB link in nav
2. `http://localhost:3000/kb` → knowledge base landing with search hero, 3 featured sectors, full grid
3. Click "Toys" sector → audience picker (if both exist) → Source Viewer
4. `http://localhost:3000/kb/toy-safety-compliance-guide-for-business-operators-in-malta` → Source Viewer with sidebar
5. Search "toy safety" in the search bar → should navigate to article
6. Search "taxation" → should show "not related" message + contact form
7. `http://localhost:3000/admin` → login → article list with filters → approve/reject
8. `http://localhost:3000/admin/trends` → inquiry trends + recent inquiries
9. Browser back/forward works for KB routes

- [ ] **Step 2: Final commit**

```bash
git add -A
git commit -m "chore: Phase 2 knowledge base frontend complete — KB landing, Source Viewer, admin panel"
```

- [ ] **Step 3: Push**

```bash
git push origin main
```
