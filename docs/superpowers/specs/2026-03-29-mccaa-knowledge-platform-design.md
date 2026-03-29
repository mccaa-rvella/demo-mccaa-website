# MCCAA Knowledge Platform — Design Specification

**Date**: 2026-03-29
**Status**: Draft
**Phases**: Phase 1 (Backend: CMS + AI Pipeline), Phase 2 (Frontend: Knowledge Base)

---

## 1. Overview

Redesign the MCCAA website from a wizard-based compliance lookup into an AI-powered knowledge platform. Admins seed data through multiple channels; an AI pipeline (Claude Sonnet) classifies, consolidates, and generates tagged articles for both business users and consumers. The frontend replaces the wizard with a knowledge base featuring sector browsing, conversational search, and a full-page Source Viewer with tag-based navigation.

### Architecture: Modular Monolith

- Single FastAPI service, split into modules: ingestion, classification, article generation, skills, CMS API, public API
- Background task queue (DB-backed `task_queue` table) for long-running AI operations
- PostgreSQL + pgvector as the single data store
- Docker Compose deployment (FastAPI + PostgreSQL + Redis if needed later)
- Extends the existing codebase rather than rewriting

---

## 2. Data Model

### 2.1 New Tables

#### `raw_sources`
Stores crawled/scraped/imported data before AI processing.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | |
| `source_type` | VARCHAR | `crawl`, `scrape`, `manual`, `json_import` |
| `source_url` | TEXT | Origin URL (nullable for manual/JSON) |
| `raw_content` | TEXT | Extracted content |
| `raw_metadata` | JSONB | Source-specific metadata |
| `batch_id` | UUID | Groups pages from one crawl operation |
| `status` | VARCHAR | `pending`, `processing`, `consolidated`, `failed` |
| `created_at` | TIMESTAMP | |

#### `knowledge_units`
AI-consolidated, classified knowledge entries.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | |
| `title` | TEXT | |
| `content` | TEXT | Consolidated content |
| `source_ids` | INT[] | References to `raw_sources` |
| `classification` | JSONB | `{types[], sectors[], actors[], scope}` |
| `ai_confidence` | FLOAT | Classification confidence score |
| `admin_overrides` | JSONB | Manual corrections to classification |
| `consumer_essential` | BOOLEAN | `true` = admin marked for consumer articles, `false` = admin excluded, `null` = AI decides |
| `embedding` | VECTOR(1536) | For similarity search |
| `created_at` | TIMESTAMP | |
| `updated_at` | TIMESTAMP | |

#### `articles`
Sonnet-generated articles with approval workflow.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | |
| `title` | TEXT | |
| `slug` | VARCHAR(80) UNIQUE | |
| `sector` | VARCHAR | FK to `sectors`. NULL for cross-cutting/universal articles (these are linked to sectors through their source knowledge units' classification data) |
| `scope` | VARCHAR | `sector-specific`, `cross-cutting`, `universal` |
| `audience` | VARCHAR | `business`, `consumer` |
| `html_content` | TEXT | Generated HTML with tagged sections |
| `tag_map` | JSONB | Maps section DOM IDs to topic/actor tags |
| `status` | VARCHAR | `draft`, `pending_approval`, `published`, `update_pending` |
| `published_version_id` | INT | Self-reference to live version while new draft is pending |
| `skills_used` | TEXT[] | Skill names used in generation |
| `source_knowledge_unit_ids` | INT[] | Knowledge units this article draws from |
| `cross_cutting_summaries` | JSONB | Contextual summaries for hybrid article layout |
| `admin_edits` | JSONB | Section-level overrides made by admin. Stored as `[{section_id, original_html, edited_html}]`. On re-generation, Sonnet is instructed to incorporate these overrides into the new version, preserving admin intent while integrating new data. |
| `created_at` | TIMESTAMP | |
| `updated_at` | TIMESTAMP | |
| `approved_at` | TIMESTAMP | |
| `approved_by` | VARCHAR | |

#### `skills`
Claude Agent Skills uploaded by admin.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | |
| `name` | VARCHAR(64) | Lowercase letters, numbers, hyphens |
| `description` | VARCHAR(1024) | What the skill does and when to use it |
| `skill_content` | TEXT | SKILL.md body |
| `resources` | JSONB | Additional files as `{filename: content}` |
| `is_active` | BOOLEAN | |
| `auto_select` | BOOLEAN | Whether AI can auto-discover this skill |
| `pinned_sectors` | TEXT[] | Always include for these sectors |
| `pinned_types` | TEXT[] | Always include for these article types |
| `excluded_sectors` | TEXT[] | Never include for these sectors |
| `created_at` | TIMESTAMP | |
| `updated_at` | TIMESTAMP | |

#### `exclusions`
Topics explicitly outside MCCAA's remit.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | |
| `type` | VARCHAR | `keyword`, `rule` |
| `value` | TEXT | Keyword or detailed rule with reasoning for AI |
| `created_at` | TIMESTAMP | |

#### `topic_analytics`
Tracks visits and trends.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | |
| `topic` | TEXT | |
| `sector` | VARCHAR | Nullable |
| `visit_count` | INT | |
| `last_visited_at` | TIMESTAMP | |

#### `inquiries`
Contact form submissions with search context.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | |
| `user_name` | VARCHAR | |
| `user_email` | VARCHAR | |
| `message` | TEXT | |
| `search_context` | JSONB | What they searched for, match result |
| `match_type` | VARCHAR | `not_related`, `partially_related`, `not_covered` |
| `created_at` | TIMESTAMP | |
| `status` | VARCHAR | `new`, `reviewed`, `resolved` |

#### `task_queue`
Lightweight DB-backed background task queue.

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL PK | |
| `task_type` | VARCHAR | `crawl`, `scrape`, `consolidate`, `classify`, `json_normalize`, `generate_article`, `update_article` |
| `payload` | JSONB | Task-specific parameters |
| `status` | VARCHAR | `queued`, `running`, `completed`, `failed` |
| `result` | JSONB | Task output |
| `error` | TEXT | Error message if failed |
| `created_at` | TIMESTAMP | |
| `started_at` | TIMESTAMP | |
| `completed_at` | TIMESTAMP | |

### 2.2 Evolved Tables

#### `sectors`
Existing table, enhanced:

| New Column | Type | Description |
|------------|------|-------------|
| `article_id` | INT | FK to main published business article |
| `consumer_article_id` | INT | FK to main published consumer article |
| `visit_count` | INT | For top-3 ranking on landing page |

---

## 3. CMS Ingestion Pipeline

### 3.1 Crawl Ingestion

1. Admin enters a URL (domain, subdomain, or specific route) in the CMS
2. System dispatches a `crawl` task to the background queue
3. Task uses Firecrawl crawl API to discover and extract all pages under that URL
4. Each page stored as a `raw_source` with `source_type=crawl`, linked by shared `batch_id`
5. On crawl completion, system auto-dispatches a `consolidate` task for that batch
6. **Consolidation**: Sonnet reviews all pages in the batch, identifies thematic clusters, merges them into coherent `knowledge_unit` records with attribution to `source_ids`
7. After consolidation, a `classify` task runs automatically

### 3.2 Scrape Ingestion (Single URL)

1. Admin enters a specific URL
2. Firecrawl scrapes that single page
3. Stored as one `raw_source`, then consolidated (may remain as single unit or merge with existing related units)
4. Classification follows automatically

### 3.3 Manual Entry

1. Admin fills CMS form: title, content (rich text), optionally pre-selects classification
2. Stored directly as a `knowledge_unit` (skips `raw_sources`)
3. If admin provided classification → stored with `admin_overrides`, no AI classification needed
4. If classification left blank → `classify` task runs

### 3.4 JSON Import

1. Admin uploads a JSON file
2. System validates against strict schema first
3. If valid → records created directly as `knowledge_units`
4. If invalid → AI normalisation task dispatched. Sonnet interprets the JSON, maps to internal schema, returns a preview
5. Admin reviews preview and confirms or adjusts before saving
6. Classification runs on any units that don't already have it

### 3.5 Pipeline Automation

After classification completes for any ingestion path, the system checks:
- Does this knowledge unit relate to an existing published article?
  - **Yes** → dispatch `update_article` task
  - **No** → dispatch `generate_article` task

### 3.6 Cascade Update Rules

When any knowledge unit is created or updated (regardless of ingestion path):

1. **Conflict resolution**: New information always overrides old. When Sonnet consolidates new data with existing knowledge units, factual conflicts are resolved in favour of the newer source. Sonnet flags what changed so the admin can see what was overridden.

2. **Article impact detection**: System queries all articles whose:
   - `source_knowledge_unit_ids` include the affected knowledge unit
   - Sector/scope means they should incorporate the new data
   - `cross_cutting_summaries` reference the affected knowledge unit

3. **Re-generation cascade**:
   - Each affected article gets an `update_article` task queued
   - Sonnet re-generates incorporating new/updated knowledge, using the same skills as originally (plus any newly relevant ones)
   - **Published articles** → status becomes `update_pending`, old version stays live with "This article is being updated" indicator
   - **Draft/pending_approval articles** → draft is replaced with new version
   - Admin approval queue shows a diff: old published vs new draft

4. **Cross-cutting summary refresh**: When a cross-cutting or universal article is re-generated, all sector-specific articles referencing it via `cross_cutting_summaries` get their summaries re-generated too. Summary updates are queued for approval.

---

## 4. AI Article Generation & Skills

### 4.1 Article Generation Flow

When a `generate_article` or `update_article` task runs:

1. **Gather inputs**: Collect relevant knowledge units based on target sector + scope:
   - All knowledge units classified for that sector
   - Cross-cutting knowledge units where AI determines applicability to the sector
   - Universal knowledge units (always included)

2. **Skill selection**:
   - Load all skills where `is_active = true`
   - AI reads each skill's `name` + `description`, determines relevance (same discovery pattern as Claude Agent Skills)
   - Admin-pinned skills (matching sector or type) always included
   - Admin-excluded skills always removed
   - Selected skills recorded in `articles.skills_used`

3. **Generation prompt**: Sonnet receives:
   - Knowledge units as source material
   - Selected skills (instructions, resources)
   - System instruction to produce structured HTML with:
     - Sections tagged by topic (technical regulations, consumer affairs, competition, standardisation)
     - Sections tagged by actor (manufacturer, importer, distributor/retailer, fulfilment service provider, authorised representative, conformity assessment body/notified body)
     - A `tag_map` mapping each section's DOM ID to its topic/actor tags
   - For sector-specific articles: instruction to generate `cross_cutting_summaries`

4. **Output**: Structured JSON containing `title`, `html_content`, `tag_map`, `cross_cutting_summaries`, `metadata`. Stored as article in `draft` status.

### 4.2 Audience-Specific Generation

**Business articles**:
- Comprehensive, detailed, covers all actors and regulatory obligations
- Tagged by topic and actor for navigation
- Includes cross-cutting summaries with links
- Technical/professional tone (modulated by skills)

**Consumer articles**:
- Simple, plain language — no jargon, no legal references unless essential
- Focused only on essential topics that directly affect consumers
- Essential topics determined by:
  - AI analysis: Sonnet identifies consumer-relevant knowledge units during classification
  - Admin curation: admin can mark `consumer_essential` on any knowledge unit
- Consolidates aggressively — fewer, broader articles
- Tagged by topic only (no actor tags)
- Cross-cutting/universal content woven directly into article (self-contained)

### 4.3 Consumer Article Trigger Logic

During the `classify` task, Sonnet also assesses consumer relevance:
- Does this information directly affect consumers? (rights, safety, warranties, pricing, complaints, recalls)
- Would a consumer need to know this to protect their interests?

If yes → `consumer_essential = true` (AI suggestion). If clearly not → `consumer_essential = false`. Admin can override at any time.

After classification:
1. Are there any `consumer_essential = true` knowledge units for this sector?
2. **Yes, no consumer article exists** → dispatch `generate_article` with `audience=consumer`
3. **Yes, consumer article exists** → dispatch `update_article` (same cascade as business articles)
4. **No consumer-essential units** → no consumer article generated

If admin changes `consumer_essential` to `false` after a consumer article exists: system re-evaluates. If units remain → re-generate without excluded unit. If none remain → flag for admin decision.

### 4.4 Skills Management

Admin capabilities in CMS:
- **Upload**: Provide SKILL.md content + optional resource files (scripts, reference docs, templates)
- **Edit/delete**: Full CRUD
- **Pin**: Assign to specific sectors or article types
- **Exclude**: Block from specific sectors
- **Toggle active/inactive**: Deactivated skills never selected
- **Preview**: Test generation on a single article to see skill effect before global activation

### 4.5 Approval Workflow

- **New articles**: `draft` → admin reviews → approves to `published` or sends back with notes
- **Updated articles**: `update_pending` → admin sees diff (old published vs new draft) → approves (new version published, old archived) or rejects (old stays, flag cleared)
- **Manual edits**: Admin can edit any article directly. Manual edits stored as `admin_edits` metadata, preserved across re-generations
- **Manual creation**: Admin can create articles entirely without AI involvement

---

## 5. Knowledge Base Frontend (Phase 2)

### 5.1 Landing Page

- **Top 3 sectors**: Highlight cards ranked by `sectors.visit_count`
- **Free-text search**: Field with placeholder, e.g., "What do you need help with?"
- **Full sector list**: All sectors with published articles, auto-populated from CMS
- Each sector card indicates availability of business content, consumer content, or both

### 5.2 Sector Selection Flow

User clicks a sector:
- If both business and consumer articles exist → simple two-button choice: "Are you a business or a consumer?"
- Then the appropriate article opens in the Source Viewer

### 5.3 Free-Text Search & Conversational Follow-up

When user types in the free-text field:

1. **Intent matching**: Sonnet analyses the query against:
   - Published article titles, tags, content (vector similarity search)
   - Exclusion list (keywords + rules)
   - "Not yet covered" topics (admin-created but no content seeded)

2. **Resolution outcomes**:

   | Match type | Action |
   |---|---|
   | Strong match to published article | Open Source Viewer directly |
   | Ambiguous — multiple matches or needs refinement | Clarifying question (up to 3 exchanges) |
   | Matches "not yet covered" topic | Message: "MCCAA covers this area but information is being prepared. Contact us for assistance." → contact form |
   | Partially related to MCCAA's remit | Message: "This may fall under MCCAA's remit. Contact us for guidance." → contact form |
   | Not related (matches exclusion rules) | Message: "This area most probably does not fall under the MCCAA's remit, however you may contact us for further information." → contact form |

3. **Conversation state**: Maintained in frontend, no login required. Full search context available for contact form pre-fill.

### 5.4 Source Viewer

Full-page article view:

- **Left sidebar** (sticky):
  - Topic tags (colour-coded: teal for technical regulations, burgundy for consumer affairs, orange for standardisation, yellow for competition)
  - Actor tags (neutral colour)
  - Clicking a tag scrolls to the first section with that tag
  - For sector-specific articles: cards for related cross-cutting/universal articles under "Related Topics"

- **Main content area**:
  - Article HTML with section headers tagged by topic/actor
  - Cross-cutting content appears as contextual summaries (teal left border) with "Read full details →" links
  - Universal content appears as contextual summaries (green left border) with "Read full details →" links
  - Clicking a tag on a section header highlights all sections with that tag

- **Header**: Article title, last updated date, approval status, sector badge

- **Update indicator**: For articles with `update_pending` status, a subtle banner: "This article is being updated"

### 5.5 Contact Form (Built-in)

Appears inline on the same page when triggered by topic routing:
- Pre-filled: `search_context` (what user searched, match result, match type)
- User fills: name, email, message
- On submit: stored in `inquiries` table with full context
- Admin sees in CMS with trend analytics

### 5.6 Analytics

- Every sector click and article view increments counters
- Drives top-3 sector highlights on landing page
- Admin dashboard shows trending topics
- Correlation with inquiry data (many visits + many inquiries = content gap signal)

---

## 6. Module Structure

The FastAPI backend splits into these modules:

```
api/
├── main.py                    # App startup, middleware, router mounting
├── config.py                  # Settings, env vars
├── db.py                      # Database connection, migrations
├── queue.py                   # Task queue runner (polls task_queue table)
├── modules/
│   ├── ingestion/
│   │   ├── router.py          # Admin endpoints: crawl, scrape, import, manual entry
│   │   ├── crawl.py           # Firecrawl integration
│   │   ├── consolidation.py   # AI consolidation logic
│   │   └── json_schema.py     # Strict schema + AI normalisation
│   ├── classification/
│   │   ├── router.py          # Admin endpoints: override classification
│   │   └── classifier.py      # AI classification + consumer relevance
│   ├── articles/
│   │   ├── router.py          # Admin CRUD + approval endpoints
│   │   ├── generator.py       # AI article generation (business + consumer)
│   │   ├── cascade.py         # Update cascade logic
│   │   └── diff.py            # Diff generation for approval review
│   ├── skills/
│   │   ├── router.py          # Admin CRUD for skills
│   │   └── selector.py        # AI skill selection logic
│   ├── cms/
│   │   ├── router.py          # Admin panel, exclusions, analytics dashboard
│   │   └── admin.html         # Admin panel UI
│   └── public/
│       ├── router.py          # Public API: sectors, articles, search, contact
│       ├── search.py          # Vector search + intent matching
│       └── conversation.py    # Conversational follow-up logic
├── Dockerfile
└── requirements.txt
```

---

## 7. External Dependencies

| Service | Purpose | Existing? |
|---------|---------|-----------|
| PostgreSQL + pgvector | Data store + vector search | Yes |
| Firecrawl | Web crawling and scraping | Yes |
| Claude Sonnet (via Anthropic API) | Classification, consolidation, article generation, search intent | Switching from OpenRouter to direct Anthropic API |
| OpenAI Embeddings | text-embedding-3-small for vector search | Yes |

---

## 8. Migration Strategy

### From existing schema:
- `documents` table → migrate relevant records to `knowledge_units` (re-classify via AI)
- `syntheses` table → deprecated (replaced by `articles`)
- `sectors` table → kept, enhanced with new columns
- Existing admin panel → replaced by new modular CMS

### From existing frontend:
- Wizard component → removed, replaced by Knowledge Base landing page
- AI Chat → evolved into conversational search
- News section → kept as-is
- Hero section → updated to link to Knowledge Base instead of wizard
