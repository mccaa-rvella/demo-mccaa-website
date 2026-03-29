# Phase 2: Knowledge Base Frontend — Design Specification

**Date**: 2026-03-29
**Status**: Approved
**Depends on**: Phase 1 Backend (complete)

---

## 1. Overview

Replace the wizard-based compliance lookup with an AI-powered knowledge base frontend. Users browse sectors or search free-text; the system matches intent, handles conversational follow-up, and presents articles in a full-page Source Viewer with tag-based navigation. An admin panel provides article approval workflow and inquiry trend analytics.

### Tech Stack

- React 19 + TypeScript + Vite (existing)
- Tailwind CSS 4 (existing)
- React Router v7 — new, for `/kb/*` and `/admin/*` routes only
- TanStack Query (React Query) v5 — new, for API data fetching with caching
- Motion (Framer Motion) — existing, for animations
- Lucide React — existing, for icons

### Architecture Decision

React Router is added **only for the new knowledge base and admin routes**. The existing site pages (home, about, consumer rights, etc.) continue using the current state-based routing in `App.tsx`. This avoids disrupting existing pages while giving the new features proper URL-based routing (shareable article links, browser back/forward).

---

## 2. Routing Structure

```
/                          → Existing App.tsx (state-based routing)
/kb                        → Knowledge Base Landing
/kb/:slug                  → Source Viewer (article by slug)
/kb/search?q=...           → (not a separate page — search is inline on /kb)
/admin                     → Admin login gate
/admin/articles            → Article management (list, preview, approve/reject)
/admin/trends              → Inquiry trends dashboard
```

### Router Setup

In `main.tsx`, wrap the app with `BrowserRouter`. Routes:
- `/kb/*` renders `KnowledgeBase` layout
- `/admin/*` renders `AdminPanel` layout
- `/*` renders existing `App` component (catches all legacy routes)

---

## 3. Knowledge Base Landing (`/kb`)

### 3.1 Layout: Search Hero

```
┌─────────────────────────────────────────────────┐
│  MCCAA Navbar (existing, shared)                │
├─────────────────────────────────────────────────┤
│                                                 │
│   ┌─── Teal Hero Banner ───────────────────┐    │
│   │  "What do you need help with?"         │    │
│   │  [ Search input field              🔍 ]│    │
│   │  Try: "toy safety", "CE marking"       │    │
│   └────────────────────────────────────────┘    │
│                                                 │
│   ┌── Top 3 Sectors ──────────────────────┐     │
│   │  [ Toys ]    [ Electronics ]  [ Cosmetics ] │
│   │  Biz+Con     Biz+Con         Biz+Con       │
│   └────────────────────────────────────────┘    │
│                                                 │
│   All Sectors                                   │
│   ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐   │
│   │Batt│ │Chem│ │Cons│ │Food│ │Lift│ │Mach│   │
│   └────┘ └────┘ └────┘ └────┘ └────┘ └────┘   │
│   ... (all 26 sectors in a responsive grid)     │
│                                                 │
│   Footer                                        │
└─────────────────────────────────────────────────┘
```

### 3.2 Data

- **Top 3 sectors**: `GET /sectors/top` — returns sectors ordered by `visit_count DESC`, limit 3
- **All sectors**: `GET /sectors` — returns all sectors with published articles
- Each sector card shows: name, availability badges (Business / Consumer / both)

### 3.3 Sector Click Flow

1. User clicks a sector card
2. If sector has both business and consumer articles → show inline audience picker: "Are you a business or a consumer?"
3. If sector has only one audience → navigate directly to `/kb/:slug`
4. Track visit: `POST /track/visit` with `{sector, topic}`

### 3.4 Search & Conversational Follow-up (Inline)

When user types in the search field and submits:

1. Call `POST /search` with `{query, conversation_id}`
2. Display result **inline below the search bar** (the hero expands):

| Match Type | UI Behaviour |
|---|---|
| `strong_match` | Navigate to `/kb/:article_slug` |
| `ambiguous` | Show follow-up question inline, user can reply (max 3 exchanges) |
| `not_covered` | Show message + inline contact form |
| `partially_related` | Show message + inline contact form |
| `not_related` | Show message + inline contact form |

3. Conversation state: `conversation_id` generated client-side (UUID), passed on each follow-up
4. After 3 exchanges without resolution → show "Contact MCCAA for assistance" + contact form

### 3.5 Inline Contact Form

Appears below the search conversation when triggered:
- Pre-filled: search query, match type, conversation history (as `search_context`)
- User fills: name, email, message
- Submit: `POST /contact`
- Success: "Thank you. We'll get back to you shortly."

---

## 4. Source Viewer (`/kb/:slug`)

### 4.1 Layout: Fixed Sidebar

```
┌─────────────────────────────────────────────────┐
│  Navbar                                         │
├─────────────────────────────────────────────────┤
│  [Toys]  Toy Safety Compliance Guide   29 Mar   │
│  ← Back to Knowledge Base                       │
├────────────┬────────────────────────────────────┤
│ TOPICS     │                                    │
│ [Technical]│  ┌─ Safety Requirements ────────┐  │
│ [Standards]│  │ Technical | Manufacturer     │  │
│ [Consumer] │  │ Content text here...         │  │
│            │  └──────────────────────────────┘  │
│ ACTORS     │                                    │
│ [Manufact.]│  ┌─ Importer Obligations ───────┐  │
│ [Importer] │  │ Technical | Importer         │  │
│ [Distribut]│  │ Content text here...         │  │
│            │  └──────────────────────────────┘  │
│ RELATED    │                                    │
│ ┌────────┐ │  ┌─ CE Marking (cross-cutting) ─┐ │
│ │CE Mark │ │  │ Teal bg | "Read full →"      │ │
│ │Market  │ │  └──────────────────────────────┘  │
│ │Surveill│ │                                    │
│ └────────┘ │                                    │
├────────────┴────────────────────────────────────┤
│  Footer                                         │
└─────────────────────────────────────────────────┘
```

### 4.2 Header

- **Back link**: "← Back to Knowledge Base" → `/kb`
- **Sector badge**: coloured pill with sector name
- **Article title**: prominent heading
- **Last updated**: date from `updated_at`
- **Update indicator**: if `status === 'update_pending'`, show subtle banner: "This article is being updated with new information"

### 4.3 Sidebar (Sticky)

Fixed position, scrolls independently from content.

**Topics section:**
- Colour-coded tag pills extracted from `tag_map`
- Colours: teal (technical), burgundy (consumer), orange (standardisation), yellow (competition)
- Click → smooth scroll to first section with that topic, highlight all matching sections

**Actors section:**
- Slate-coloured tag pills extracted from `tag_map`
- Click → smooth scroll and highlight (same as topics)

**Related Topics section:**
- Cards for cross-cutting/universal articles from `cross_cutting_summaries`
- Each card shows: topic name, scope label
- Click → navigate to `/kb/:related_slug`

### 4.4 Main Content Area

Renders `html_content` from the article. Each section (`<div>` with `data-topics` and `data-actors` attributes) is displayed with:

- **Left border**: coloured by primary topic (teal for technical, etc.)
- **Tag pills**: inline topic and actor tags above content
- **Click behaviour**: clicking a tag pill on a section highlights all sections sharing that tag

**Cross-cutting summaries** (from `cross_cutting_summaries` array):
- Rendered inline at relevant positions
- Teal left border + light teal background for cross-cutting scope
- Green left border + light green background for universal scope
- Content: topic name, 2-3 sentence summary, "Read full details →" link to the full article

### 4.5 Analytics

On page load: `POST /track/visit` with `{sector: article.sector, topic: first_topic_from_tag_map}`

### 4.6 Consumer Articles

Consumer articles use the same Source Viewer but with:
- No actor tags (consumers don't think in supply chain terms)
- Simpler sidebar (topics only + related articles)
- Same tag-click-to-scroll behaviour for topics

---

## 5. Admin Panel (`/admin`)

### 5.1 Login Gate

Simple form: enter admin key → stored in sessionStorage → sent as `X-Admin-Key` header on all admin API calls. No user/password — just the shared admin key.

### 5.2 Articles Tab (`/admin/articles`)

**List view:**
- Table: title, sector, audience, status, updated_at
- Status filter dropdown: all / draft / published / update_pending / rejected
- Audience filter: all / business / consumer
- Click row → article detail

**Detail view (expands inline below the selected row):**
- Article preview: rendered HTML content
- Metadata: sector, audience, skills used, source knowledge unit IDs
- Actions:
  - **Approve** → `POST /admin/articles/:id/approve` → status becomes `published`
  - **Reject** → `POST /admin/articles/:id/reject` → status becomes `rejected`
  - **Edit** → `PUT /admin/articles/:id` with updated fields
- For `update_pending` articles: show diff between current published version and new draft (using `generate_html_diff` from backend)

### 5.3 Trends Tab (`/admin/trends`)

- **Inquiry trends**: `GET /admin/inquiries/trends` → bar chart or table showing top queries
- **Recent inquiries**: `GET /admin/inquiries` → list with user, message, match_type, search_context
- **Content gap signals**: queries with `not_covered` match_type → these indicate topics MCCAA covers but has no article for
- Update inquiry status: `PUT /admin/inquiries/:id` with `{status: "reviewed"}`

---

## 6. File Structure

```
src/
├── App.tsx                              # Existing (unchanged)
├── main.tsx                             # Add BrowserRouter + route setup
├── index.css                            # Add new utility classes
├── api/
│   └── client.ts                        # API client with base URL + auth helpers
├── components/
│   ├── Wizard/Wizard.tsx                # Existing (unchanged)
│   └── ui/                              # Shared UI components
│       ├── TagPill.tsx                   # Colour-coded tag pill
│       ├── SectorCard.tsx               # Sector card (landing page)
│       └── ContactForm.tsx              # Reusable contact form
├── kb/
│   ├── KBLayout.tsx                     # Layout wrapper (navbar + outlet)
│   ├── KBLanding.tsx                    # Landing page (/kb)
│   ├── SearchBar.tsx                    # Search + inline conversation
│   ├── SourceViewer.tsx                 # Article viewer (/kb/:slug)
│   ├── Sidebar.tsx                      # Fixed sidebar (tags + related)
│   └── AudiencePicker.tsx              # Business/Consumer choice modal
├── admin/
│   ├── AdminLayout.tsx                  # Layout with login gate + tabs
│   ├── AdminLogin.tsx                   # Admin key input
│   ├── ArticleList.tsx                  # Article management table
│   ├── ArticleDetail.tsx                # Preview + approve/reject
│   └── TrendsDashboard.tsx              # Inquiry trends
└── hooks/
    ├── useSearch.ts                     # Search + conversation state
    ├── useSectors.ts                    # Sectors data (React Query)
    └── useAdminAuth.ts                  # Admin key in sessionStorage
```

---

## 7. API Integration

All API calls go through a shared client (`api/client.ts`):

```typescript
const API_BASE = 'http://localhost:8000'

// Public endpoints (no auth)
GET  /sectors/top           → top 3 sectors
GET  /sectors               → all sectors
GET  /articles/:slug        → published article by slug
POST /search                → intent matching
POST /track/visit           → analytics
POST /contact               → submit inquiry

// Admin endpoints (X-Admin-Key header)
GET  /admin/articles        → list articles (with status/audience filters)
GET  /admin/articles/:id    → article detail
POST /admin/articles/:id/approve  → approve
POST /admin/articles/:id/reject   → reject
PUT  /admin/articles/:id    → edit
GET  /admin/inquiries       → list inquiries
GET  /admin/inquiries/trends → trend data
PUT  /admin/inquiries/:id   → update inquiry status
```

### React Query Configuration

- **Stale time**: 5 minutes for sectors/articles (content changes infrequently)
- **Stale time**: 30 seconds for admin data (needs to be fresh)
- **Retry**: 1 retry on failure
- **Refetch on window focus**: enabled for admin, disabled for public

---

## 8. Colour System

| Purpose | Colour | Hex | Usage |
|---------|--------|-----|-------|
| Technical Regulations | Teal | `#2da0a4` | Topic tags, section borders, cross-cutting summaries |
| Consumer Affairs | Burgundy | `#7a4a5f` | Topic tags, section borders |
| Standardisation | Orange | `#d68f49` | Topic tags, section borders |
| Competition | Yellow | `#e5ca6d` | Topic tags, section borders |
| Actor tags | Slate | `#64748b` | Actor tag pills |
| Universal summaries | Green | `#b8e38d` | Section borders, summary backgrounds |
| Cross-cutting bg | Light teal | `#f0fafa` | Summary card background |
| Universal bg | Light green | `#f0faf0` | Summary card background |

---

## 9. Responsive Behaviour

- **Desktop (>1024px)**: Full sidebar + content layout
- **Tablet (768-1024px)**: Sidebar collapses to a horizontal tag bar above content
- **Mobile (<768px)**: Tags become a horizontally scrollable row, full-width content below

The landing page sector grid adapts:
- Desktop: 4 columns
- Tablet: 3 columns
- Mobile: 2 columns

---

## 10. Migration Strategy

1. Add React Router and React Query as dependencies
2. Wrap existing `App` in router — existing pages continue working at `/`
3. Build `/kb` and `/admin` routes as new components
4. Add "Knowledge Base" link to existing navbar
5. Old wizard remains accessible during transition
6. Once validated, wizard can be removed or kept as a legacy option
