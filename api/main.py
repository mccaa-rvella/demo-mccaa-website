import os
import json
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import psycopg2
from openai import OpenAI

# Initialize Environment
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "mysecretpassword")
DB_NAME = os.getenv("DB_NAME", "mccaa_website")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "mccaa-admin-2026")

if not OPENROUTER_API_KEY:
    print("WARNING: OPENROUTER_API_KEY is not set.")

openai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
) if OPENROUTER_API_KEY else None

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        dbname=DB_NAME
    )

def expand_query(user_query: str) -> str:
    """
    LLM Query Expansion / HyDE technique.
    Translates a plain user query into a highly dense semantic string of related legal technical terms,
    EU directives, and MCCAA compliance areas to maximize Vector DB retrieval accuracy.
    """
    if not openai_client:
        return user_query

    system_prompt = (
        "You are an expert in European and Maltese commercial regulation. "
        "The user will provide a simple natural language query regarding compliance or import rules. "
        "Your task is to EXPAND this query into a highly technical, comma-separated list of EXACT regulatory "
        "keywords, EU Directives, and specific compliance areas that apply to the query. "
        "For example, if the query is 'importing white goods', you should respond with: "
        "'EPREL, Energy Labelling, EcoDesign Directive, Low Voltage Directive, Household appliances, CE marking, EMC Directive'."
        "\nRespond ONLY with the comma-separated keywords and directives (maximum 25 words). Do not include conversational text."
    )

    try:
        response = openai_client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.2
        )
        expanded_keywords = response.choices[0].message.content.strip()
        print(f"[Query Expansion] Original: '{user_query}' -> Expanded: '{expanded_keywords}'")
        return f"{user_query} {expanded_keywords}"
    except Exception as e:
        print(f"Query expansion failed: {e}")
        return user_query

def vector_search(query_text: str, limit: int = 8):
    """
    Semantic search over all KB documents (requires embeddings to be present).
    NOTE: Documents inserted via seed_kb.py skip embeddings — run POST /admin/embed-missing
    after seeding to make the full KB available to the chatbot.
    """
    if not openai_client:
        return []

    expanded_search_term = expand_query(query_text)

    try:
        res = openai_client.embeddings.create(input=expanded_search_term, model="openai/text-embedding-3-small")
        query_embedding = res.data[0].embedding

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT title, url, content
            FROM documents
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding, limit))

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return [{"title": r[0], "url": r[1], "content": r[2]} for r in results]
    except Exception as e:
        print(f"Search error: {e}")
        return []


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the syntheses cache table exists
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS syntheses (
                id SERIAL PRIMARY KEY,
                sector VARCHAR NOT NULL,
                role VARCHAR NOT NULL,
                topic VARCHAR NOT NULL,
                title TEXT NOT NULL,
                html_content TEXT NOT NULL,
                read_more JSONB DEFAULT '[]',
                meta JSONB DEFAULT '{}',
                generated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE (sector, role, topic)
            )
        """)
        conn.commit()
        cur.close(); conn.close()
        print("[Startup] Syntheses cache table ready.")
    except Exception as e:
        print(f"[Startup] Syntheses table init failed: {e}")
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- New modular routers ---
from api.modules.skills.router import router as skills_router
app.include_router(skills_router)

from api.modules.ingestion.router import router as ingestion_router
app.include_router(ingestion_router)

from api.modules.classification.router import router as classification_router
app.include_router(classification_router)

class ChatMessage(BaseModel):
    role: str
    text: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

class WizardRequest(BaseModel):
    query: str
    role: str

class WizardResultsRequest(BaseModel):
    sector: str
    role: str
    topic: str  # 'technical' | 'competition' | 'consumer' | 'standardisation' | 'all'

class WizardSynthesizeRequest(BaseModel):
    sector: str
    sector_label: str
    role: str
    role_label: str
    topic: str
    topic_label: str

PILLAR_NAMES = {
    'technical': 'Technical Regulations & Product Safety',
    'competition': 'Competition',
    'consumer': 'Consumer Protection',
    'standardisation': 'Standardisation & Metrology',
}

ROLE_LABELS = {
    'manufacturer': 'Manufacturer',
    'importer': 'Importer',
    'distributor': 'Distributor / Retailer',
    'authorised-rep': 'Authorised Representative',
    'cab': 'Conformity Assessment Body',
    'fsp': 'Fulfilment Service Provider',
}


def fetch_all_docs_for_synthesis(sector: str, role: str, topic: str) -> dict:
    """
    Fetch relevant KB docs for synthesis.

    Task 2 fix: When a specific topic is selected, cross-cutting and universal docs
    are only included if their pillar matches the selected topic. Only 'topic=all'
    includes all scopes without a pillar filter.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    if topic == 'all':
        # All scopes, all pillars — no pillar filter
        cur.execute("""
            SELECT title, content, legal_basis, scope, pillar, slug
            FROM documents
            WHERE slug IS NOT NULL AND (
                (scope = 'sector-specific' AND sector = %s AND (%s = ANY(roles) OR 'all' = ANY(roles)))
                OR (scope = 'cross-cutting' AND (%s = ANY(roles) OR 'all' = ANY(roles)))
                OR scope = 'universal'
            )
            ORDER BY CASE scope WHEN 'sector-specific' THEN 1 WHEN 'cross-cutting' THEN 2 ELSE 3 END
        """, (sector, role, role))
        primary_docs = [
            {'title': r[0], 'content': (r[1] or '')[:2000], 'legal_basis': r[2], 'scope': r[3], 'pillar': r[4], 'slug': r[5]}
            for r in cur.fetchall()
        ]
        supporting_docs = []  # When 'all', everything is primary — no "Also Relevant" cards
    else:
        # Specific pillar: only include cross-cutting and universal docs that match this pillar
        cur.execute("""
            SELECT title, content, legal_basis, scope, pillar, slug
            FROM documents
            WHERE slug IS NOT NULL AND (
                (scope = 'sector-specific' AND sector = %s AND (%s = ANY(roles) OR 'all' = ANY(roles)) AND pillar = %s)
                OR (scope = 'cross-cutting' AND (%s = ANY(roles) OR 'all' = ANY(roles)) AND pillar = %s)
                OR (scope = 'universal' AND pillar = %s)
            )
            ORDER BY CASE scope WHEN 'sector-specific' THEN 1 WHEN 'cross-cutting' THEN 2 ELSE 3 END
        """, (sector, role, topic, role, topic, topic))
        primary_docs = [
            {'title': r[0], 'content': (r[1] or '')[:2000], 'legal_basis': r[2], 'scope': r[3], 'pillar': r[4], 'slug': r[5]}
            for r in cur.fetchall()
        ]

        # Supporting: sector-specific docs from OTHER pillars (brief context for "Also Relevant" cards)
        other_pillars = [p for p in ['technical', 'competition', 'consumer', 'standardisation'] if p != topic]
        supporting_docs = []
        for p in other_pillars:
            cur.execute("""
                SELECT title, content, legal_basis, scope, pillar, slug
                FROM documents
                WHERE slug IS NOT NULL AND (
                    (scope = 'sector-specific' AND sector = %s AND (%s = ANY(roles) OR 'all' = ANY(roles)) AND pillar = %s)
                    OR (scope = 'cross-cutting' AND pillar = %s AND (%s = ANY(roles) OR 'all' = ANY(roles)))
                )
                ORDER BY scope LIMIT 3
            """, (sector, role, p, p, role))
            rows = cur.fetchall()
            if rows:
                supporting_docs.append({
                    'pillar': p,
                    'pillar_label': PILLAR_NAMES.get(p, p),
                    'docs': [{'title': r[0], 'content': (r[1] or '')[:800], 'legal_basis': r[2], 'slug': r[5]} for r in rows]
                })

    cur.close(); conn.close()
    return {'primary': primary_docs, 'supporting': supporting_docs}


# ─── Synthesis Cache Helpers ─────────────────────────────────────────────────

def _get_cached_synthesis(sector: str, role: str, topic: str) -> Optional[dict]:
    """Return pre-generated synthesis if available."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT title, html_content, read_more, meta FROM syntheses WHERE sector = %s AND role = %s AND topic = %s",
            (sector, role, topic)
        )
        row = cur.fetchone()
        cur.close(); conn.close()
        if row:
            return {"title": row[0], "html": row[1], "read_more": row[2] or [], "meta": row[3] or {}}
    except Exception as e:
        print(f"[Synthesis cache read] {e}")
    return None


def _cache_synthesis(sector: str, role: str, topic: str, result: dict):
    """Upsert a synthesis result into the cache table."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO syntheses (sector, role, topic, title, html_content, read_more, meta)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (sector, role, topic) DO UPDATE SET
                title = EXCLUDED.title,
                html_content = EXCLUDED.html_content,
                read_more = EXCLUDED.read_more,
                meta = EXCLUDED.meta,
                generated_at = NOW()
        """, (sector, role, topic, result['title'], result['html'],
              json.dumps(result['read_more']), json.dumps(result['meta'])))
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        print(f"[Synthesis cache write] {e}")


def _invalidate_syntheses(sector: Optional[str], scope: str, roles: list, pillar: str):
    """
    Delete cached syntheses that are affected by a document change.
    - universal: invalidate everything
    - cross-cutting: invalidate all combinations for matching roles + pillar (+ 'all')
    - sector-specific: invalidate all combinations for that sector
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        if scope == 'universal':
            cur.execute("DELETE FROM syntheses")
            print("[Synthesis invalidate] Cleared all (universal doc change)")
        elif scope == 'sector-specific' and sector:
            cur.execute("DELETE FROM syntheses WHERE sector = %s", (sector,))
            print(f"[Synthesis invalidate] Cleared sector={sector}")
        elif scope == 'cross-cutting':
            if roles and 'all' not in roles:
                cur.execute(
                    "DELETE FROM syntheses WHERE role = ANY(%s) AND topic IN %s",
                    (roles, (pillar, 'all'))
                )
            else:
                cur.execute("DELETE FROM syntheses WHERE topic IN %s", ((pillar, 'all'),))
            print(f"[Synthesis invalidate] Cleared cross-cutting pillar={pillar}")
        conn.commit(); cur.close(); conn.close()
    except Exception as e:
        print(f"[Synthesis invalidate] {e}")


# ─── Core Synthesis Logic ─────────────────────────────────────────────────────

def _run_synthesis(sector: str, sector_label: str, role: str, role_label: str, topic: str, topic_label: str) -> dict:
    """
    Generate a synthesis article from KB docs using Claude via OpenRouter.
    Returns the synthesis result dict (title, html, read_more, meta).
    """
    data = fetch_all_docs_for_synthesis(sector, role, topic)
    primary_docs = data['primary']
    supporting_docs = data['supporting']

    if not primary_docs:
        read_more = [
            {"pillar": s['pillar'], "pillar_label": s['pillar_label'],
             "summary": s['docs'][0]['content'][:200] if s['docs'] else "",
             "doc_count": len(s['docs'])}
            for s in supporting_docs
        ]
        return {
            "title": f"{topic_label} — {sector_label}",
            "html": "<p>No specific content found yet for this combination. More content is being added regularly.</p>",
            "meta": {"sector": sector_label, "role": role_label, "topic": topic_label, "topic_id": topic, "doc_count": 0},
            "read_more": read_more,
        }

    primary_context = "\n\n---\n\n".join([
        f"## {d['title']} [{d['scope'].upper()}]\n{'Legal basis: ' + d['legal_basis'] if d['legal_basis'] else ''}\n{d['content']}"
        for d in primary_docs
    ])

    supporting_context = ""
    for s in supporting_docs:
        supporting_context += f"\n\n### {s['pillar_label']} (brief context)\n"
        for d in s['docs']:
            supporting_context += f"**{d['title']}**: {d['content'][:400]}...\n\n"

    system_prompt = f"""You are an expert regulatory advisor for the Malta Competition and Consumer Affairs Authority (MCCAA).

You must write a comprehensive, professional compliance briefing for the following profile:
- Sector: {sector_label}
- Role: {role_label}
- Primary Topic: {topic_label}

STRICT RULES:
1. Base your response ONLY on the provided knowledge base content. Never invent regulations.
2. Write in a formal, authoritative tone — this is official regulatory guidance.
3. Prioritise {topic_label} content first. Then briefly note other relevant areas.
4. Structure using clear HTML headings (h2, h3), paragraphs, and bullet lists.
5. Include a one-paragraph executive summary at the top.
6. Where specific legal instruments are mentioned, bold them (e.g. <strong>Directive 2009/48/EC</strong>).
7. Do NOT use markdown. Output ONLY valid semantic HTML (no html/body/head tags).
8. Maximum length: 1200 words equivalent."""

    user_prompt = f"""PRIMARY KNOWLEDGE BASE — {topic_label.upper()}:

{primary_context}

---

SUPPORTING CONTEXT (other relevant areas — reference briefly):

{supporting_context}

Write the professional compliance briefing now."""

    try:
        response = openai_client.chat.completions.create(
            model="anthropic/claude-sonnet-4-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=3000,
        )
        html_content = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Synthesis LLM error: {e}")
        html_content = "\n".join([f"<h3>{d['title']}</h3>{d['content']}" for d in primary_docs])

    read_more = [
        {
            "pillar": s["pillar"],
            "pillar_label": s["pillar_label"],
            "summary": s["docs"][0]["content"][:200].replace("<h3>", "").replace("</h3>", ": ") if s["docs"] else "",
            "doc_count": len(s["docs"]),
        }
        for s in supporting_docs
    ]

    return {
        "title": f"{topic_label} Compliance Guide — {sector_label} ({role_label})",
        "html": html_content,
        "meta": {
            "sector": sector_label, "role": role_label, "topic": topic_label,
            "topic_id": topic, "doc_count": len(primary_docs),
        },
        "read_more": read_more,
    }


# ─── Background Tasks ─────────────────────────────────────────────────────────

def _proactive_regen_sector_specific(sector_slug: str, roles: list, pillar: str):
    """
    After saving a sector-specific doc, regenerate the affected synthesis combinations.
    Bounded: at most len(roles) × 2 LLM calls (pillar + 'all').
    Cross-cutting/universal changes require admin to run /admin/regenerate-syntheses.
    """
    if not openai_client:
        return
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM sectors WHERE slug = %s", (sector_slug,))
        row = cur.fetchone()
        sector_name = row[0] if row else sector_slug
        cur.close(); conn.close()
    except Exception:
        sector_name = sector_slug

    all_topic_labels = {**PILLAR_NAMES, 'all': 'All Topics'}
    roles_to_regen = roles if roles and 'all' not in roles else list(ROLE_LABELS.keys())
    topics_to_regen = [pillar, 'all'] if pillar else list(PILLAR_NAMES.keys()) + ['all']

    print(f"[Synthesis BG] Regenerating {len(roles_to_regen)}r × {len(topics_to_regen)}t for sector={sector_slug}")
    for role_id in roles_to_regen:
        for topic_id in topics_to_regen:
            try:
                result = _run_synthesis(
                    sector_slug, sector_name,
                    role_id, ROLE_LABELS.get(role_id, role_id),
                    topic_id, all_topic_labels.get(topic_id, topic_id)
                )
                if result['meta'].get('doc_count', 0) > 0:
                    _cache_synthesis(sector_slug, role_id, topic_id, result)
                    print(f"  ✓ {sector_slug}/{role_id}/{topic_id}")
            except Exception as e:
                print(f"  ✗ {sector_slug}/{role_id}/{topic_id}: {e}")


def _regenerate_all_syntheses():
    """
    Regenerate ALL synthesis combinations that have at least one relevant doc.
    Called by /admin/regenerate-syntheses. Runs in background.
    """
    if not openai_client:
        print("[Regenerate All] OpenRouter not configured, skipping.")
        return
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name, slug FROM sectors ORDER BY sort_order")
        all_sectors = [{'name': r[0], 'slug': r[1]} for r in cur.fetchall()]
        cur.close(); conn.close()
    except Exception as e:
        print(f"[Regenerate All] Failed to fetch sectors: {e}")
        return

    all_roles = list(ROLE_LABELS.items())
    all_topics = list(PILLAR_NAMES.items()) + [('all', 'All Topics')]
    total = 0; cached = 0

    for s in all_sectors:
        for role_id, role_label in all_roles:
            for topic_id, topic_label in all_topics:
                try:
                    result = _run_synthesis(s['slug'], s['name'], role_id, role_label, topic_id, topic_label)
                    if result['meta'].get('doc_count', 0) > 0:
                        _cache_synthesis(s['slug'], role_id, topic_id, result)
                        cached += 1
                    total += 1
                except Exception as e:
                    print(f"  ✗ {s['slug']}/{role_id}/{topic_id}: {e}")

    print(f"[Regenerate All] Complete. {cached}/{total} combinations with content cached.")


# ─── Wizard Endpoints ─────────────────────────────────────────────────────────

@app.get("/wizard/sectors")
async def get_sectors():
    """Return sectors from the sectors reference table."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, slug, showcase FROM sectors ORDER BY sort_order")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {"sectors": [{"name": r[0], "slug": r[1], "showcase": r[2]} for r in rows]}


@app.post("/wizard/synthesize")
async def wizard_synthesize(req: WizardSynthesizeRequest):
    """
    Return a compliance briefing for the given sector/role/topic.
    Checks the synthesis cache first; generates and caches on miss.
    Pre-generation via /admin/regenerate-syntheses ensures consistent output.
    """
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenRouter API key missing")

    # 1. Return cached synthesis if available (consistent, pre-generated)
    cached = _get_cached_synthesis(req.sector, req.role, req.topic)
    if cached:
        print(f"[Synthesis] Cache hit: {req.sector}/{req.role}/{req.topic}")
        return cached

    # 2. Generate on-demand and cache for next time
    print(f"[Synthesis] Cache miss, generating: {req.sector}/{req.role}/{req.topic}")
    result = _run_synthesis(req.sector, req.sector_label, req.role, req.role_label, req.topic, req.topic_label)
    _cache_synthesis(req.sector, req.role, req.topic, result)
    return result


@app.post("/wizard/results")
async def get_wizard_results(req: WizardResultsRequest):
    """
    Return KB documents filtered by sector + role + topic, grouped by scope.

    Task 2 fix: When a specific topic is selected, universal docs are only included
    if their pillar matches the selected topic.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    if req.topic == 'all':
        query = """
        SELECT d.id, d.title, d.slug, d.content, d.pillar, d.roles, d.scope, d.legal_basis, d.sector, d.topic_tags
        FROM documents d
        WHERE (
            (d.scope = 'sector-specific' AND d.sector = %s AND (%s = ANY(d.roles) OR 'all' = ANY(d.roles)))
            OR (d.scope = 'cross-cutting' AND (%s = ANY(d.roles) OR 'all' = ANY(d.roles)))
            OR (d.scope = 'universal')
        )
        ORDER BY
            CASE d.scope
                WHEN 'sector-specific' THEN 1
                WHEN 'cross-cutting' THEN 2
                WHEN 'universal' THEN 3
            END,
            d.title
        """
        params = [req.sector, req.role, req.role]
    else:
        # Task 2: universal docs only included when their pillar matches the selected topic
        query = """
        SELECT d.id, d.title, d.slug, d.content, d.pillar, d.roles, d.scope, d.legal_basis, d.sector, d.topic_tags
        FROM documents d
        WHERE (
            (d.scope = 'sector-specific' AND d.sector = %s AND (%s = ANY(d.roles) OR 'all' = ANY(d.roles)) AND d.pillar = %s)
            OR (d.scope = 'cross-cutting' AND (%s = ANY(d.roles) OR 'all' = ANY(d.roles)) AND d.pillar = %s)
            OR (d.scope = 'universal' AND d.pillar = %s)
        )
        ORDER BY
            CASE
                WHEN d.pillar = %s AND d.scope = 'cross-cutting' THEN 0
                WHEN d.scope = 'sector-specific' THEN 1
                WHEN d.scope = 'cross-cutting' THEN 2
                WHEN d.scope = 'universal' THEN 3
            END,
            d.title
        """
        params = [req.sector, req.role, req.topic, req.role, req.topic, req.topic, req.topic]

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close(); conn.close()

    groups = {'sector_specific': [], 'cross_cutting': [], 'universal': []}
    for r in rows:
        doc = {
            'id': r[0], 'title': r[1], 'slug': r[2],
            'content_preview': (r[3] or '')[:300],
            'pillar': r[4], 'roles': r[5] or [],
            'scope': r[6], 'legal_basis': r[7],
            'sector': r[8], 'topic_tags': r[9] or []
        }
        if r[6] == 'universal':
            groups['universal'].append(doc)
        elif r[6] == 'cross-cutting' and req.topic != 'all' and r[4] == req.topic:
            groups['sector_specific'].insert(0, doc)
        elif r[6] == 'sector-specific':
            groups['sector_specific'].append(doc)
        else:
            groups['cross_cutting'].append(doc)

    sector_specific = groups['sector_specific']
    if len(sector_specific) > 1:
        by_sector: dict[str, list] = {}
        for doc in sector_specific:
            key = doc.get('sector') or '_none'
            by_sector.setdefault(key, []).append(doc)

        merged = []
        for sector_key, docs in by_sector.items():
            role_specific = [d for d in docs if 'all' not in (d.get('roles') or [])]
            overviews     = [d for d in docs if 'all' in (d.get('roles') or [])]
            if role_specific and overviews:
                overview_preview = ' | '.join(o['title'] for o in overviews)
                for d in role_specific:
                    d['includes_overview'] = True
                    d['overview_slugs'] = [o['slug'] for o in overviews]
                merged.extend(role_specific)
            else:
                merged.extend(docs)
        groups['sector_specific'] = merged

    return groups


@app.get("/kb/{slug}")
async def get_kb_page(slug: str):
    """Return a single KB document plus universal content for the Source Viewer."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, title, content, pillar, roles, scope, legal_basis, sector, topic_tags, url
        FROM documents WHERE slug = %s
    """, (slug,))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Knowledge base article not found")

    doc = {
        'id': row[0], 'title': row[1], 'content': row[2],
        'pillar': row[3], 'roles': row[4] or [], 'scope': row[5],
        'legal_basis': row[6], 'sector': row[7],
        'topic_tags': row[8] or [], 'url': row[9]
    }

    if doc['sector'] and 'all' not in doc['roles']:
        cur.execute("""
            SELECT content, title, legal_basis FROM documents
            WHERE sector = %s AND scope = 'sector-specific'
              AND 'all' = ANY(roles) AND id != %s
            LIMIT 1
        """, (doc['sector'], row[0]))
        overview_row = cur.fetchone()
        if overview_row:
            doc['content'] = (overview_row[0] or '') + '<hr style="margin:2rem 0;border:none;border-top:1px solid #e5e7eb">' + (doc['content'] or '')
            if overview_row[2] and not doc['legal_basis']:
                doc['legal_basis'] = overview_row[2]

    cur.execute("""
        SELECT id, title, slug, content, pillar, legal_basis
        FROM documents WHERE scope = 'universal' AND id != %s
        ORDER BY title
    """, (row[0],))
    universal = [{'id': u[0], 'title': u[1], 'slug': u[2], 'content': u[3],
                  'pillar': u[4], 'legal_basis': u[5]} for u in cur.fetchall()]

    cur.close(); conn.close()
    return {'article': doc, 'universal': universal}


@app.post("/chat")
async def chat_endpoint(req: Request):
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenRouter API key missing")

    body = await req.json()
    messages = body.get("messages", [])

    last_user_msg = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )

    docs = vector_search(last_user_msg, limit=5)
    context_str = "\n\n".join([f"Source: {d['title']} ({d['url']})\n{d['content'][:1500]}" for d in docs])

    system_prompt = f"""You are l-Uffiċjal, the official digital assistant for the Malta Competition and Consumer Affairs Authority (MCCAA).
Use ONLY the following freshly scraped website text to answer the user's question accurately.
If the information cannot be found in the provided context, state that clearly but try to refer them to info@mccaa.org.mt.

IMPORTANT: You MUST ALWAYS append a "Sources" section at the very end of your response containing clickable markdown links [Source Title](url) to the EXACT MCCAA web pages from the context where you obtained the information. Do not output bare URLs.

CONTEXT FROM MCCAA WEBSITE:
{context_str}
"""

    llm_messages = [{"role": "system", "content": system_prompt}]
    for m in messages:
        role = m.get("role", "user")
        if role not in ("user", "assistant"):
            role = "assistant"
        llm_messages.append({"role": role, "content": m.get("content", "")})

    async def token_stream():
        try:
            stream = openai_client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=llm_messages,
                temperature=0.3,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    import json as _json
                    yield f'0:{_json.dumps(delta.content)}\n'
            yield f'd:{{"finishReason":"stop"}}\n'
        except Exception as e:
            import json as _json
            yield f'3:{_json.dumps(str(e))}\n'

    from fastapi.responses import StreamingResponse as SR
    return SR(
        token_stream(),
        media_type="text/plain; charset=utf-8",
        headers={"x-vercel-ai-data-stream": "v1"},
    )


# Legacy endpoint — superseded by the new 3-step wizard
@app.post("/wizard/generate")
async def wizard_generate(req: WizardRequest):
    return {"title": "Please use the updated wizard", "sector": req.role, "overview": "<p>This endpoint has been superseded by the new 3-step wizard.</p>"}


# ─── Admin Helpers ─────────────────────────────────────────────────────────

def embed_text(text: str) -> list:
    """Generate a 1536-dim embedding via OpenRouter."""
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenRouter not configured")
    res = openai_client.embeddings.create(input=text, model="openai/text-embedding-3-small")
    return res.data[0].embedding

def require_admin(x_admin_key: Optional[str] = Header(None)):
    if x_admin_key != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="Invalid or missing admin key")

class DocumentCreate(BaseModel):
    title: str
    url: str = ""
    content: str
    type: str = "manual"
    metadata: dict = {}
    sector: Optional[str] = None
    pillar: str = "technical"
    roles: List[str] = []
    topic_tags: List[str] = []
    scope: str = "sector-specific"
    slug: Optional[str] = None
    legal_basis: Optional[str] = None

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None
    metadata: Optional[dict] = None
    sector: Optional[str] = None
    pillar: Optional[str] = None
    roles: Optional[List[str]] = None
    topic_tags: Optional[List[str]] = None
    scope: Optional[str] = None
    slug: Optional[str] = None
    legal_basis: Optional[str] = None


# ─── Admin CRUD Endpoints ───────────────────────────────────────────────────

@app.get("/admin/documents")
async def list_documents(x_admin_key: Optional[str] = Header(None)):
    require_admin(x_admin_key)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, url, type, sector, pillar, scope, slug FROM documents ORDER BY id DESC")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [{"id": r[0], "title": r[1], "url": r[2], "type": r[3],
             "sector": r[4], "pillar": r[5], "scope": r[6], "slug": r[7]} for r in rows]

@app.get("/admin/documents/{doc_id}")
async def get_document(doc_id: int, x_admin_key: Optional[str] = Header(None)):
    require_admin(x_admin_key)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, url, content, type, metadata, sector, pillar, roles, topic_tags, scope, slug, legal_basis FROM documents WHERE id = %s", (doc_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": row[0], "title": row[1], "url": row[2], "content": row[3],
        "type": row[4], "metadata": row[5], "sector": row[6], "pillar": row[7],
        "roles": row[8] or [], "topic_tags": row[9] or [], "scope": row[10],
        "slug": row[11], "legal_basis": row[12]
    }

def generate_slug(title: str) -> str:
    import re
    slug = title.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug[:80]

@app.post("/admin/documents", status_code=201)
async def create_document(doc: DocumentCreate, background_tasks: BackgroundTasks, x_admin_key: Optional[str] = Header(None)):
    require_admin(x_admin_key)
    emb = embed_text(doc.content)
    slug = doc.slug or generate_slug(doc.title)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO documents (url, title, content, type, metadata, embedding,
            sector, pillar, roles, topic_tags, scope, slug, legal_basis)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (doc.url, doc.title, doc.content, doc.type, json.dumps(doc.metadata), emb,
         doc.sector, doc.pillar, doc.roles, doc.topic_tags, doc.scope, slug, doc.legal_basis)
    )
    new_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()

    # Invalidate affected syntheses immediately, then proactively regenerate for sector-specific
    _invalidate_syntheses(doc.sector, doc.scope, doc.roles, doc.pillar)
    if doc.scope == 'sector-specific' and doc.sector:
        background_tasks.add_task(_proactive_regen_sector_specific, doc.sector, doc.roles, doc.pillar)
    else:
        print(f"[Synthesis] {doc.scope} doc saved — run /admin/regenerate-syntheses to rebuild cross-cutting/universal combinations.")

    return {"id": new_id, "slug": slug, "message": "Document created and embedded successfully"}

@app.put("/admin/documents/{doc_id}")
async def update_document(doc_id: int, doc: DocumentUpdate, background_tasks: BackgroundTasks, x_admin_key: Optional[str] = Header(None)):
    require_admin(x_admin_key)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT title, url, content, type, metadata, sector, pillar, roles, topic_tags, scope, slug, legal_basis FROM documents WHERE id = %s", (doc_id,))
    existing = cur.fetchone()
    if not existing:
        cur.close(); conn.close()
        raise HTTPException(status_code=404, detail="Document not found")

    new_title   = doc.title      or existing[0]
    new_url     = doc.url        or existing[1]
    new_content = doc.content    or existing[2]
    new_type    = doc.type       or existing[3]
    new_meta    = doc.metadata   if doc.metadata is not None else existing[4]
    new_sector  = doc.sector     if doc.sector is not None else existing[5]
    new_pillar  = doc.pillar     or existing[6]
    new_roles   = doc.roles      if doc.roles is not None else existing[7]
    new_tags    = doc.topic_tags if doc.topic_tags is not None else existing[8]
    new_scope   = doc.scope      or existing[9]
    new_slug    = doc.slug       or existing[10] or generate_slug(new_title)
    new_legal   = doc.legal_basis if doc.legal_basis is not None else existing[11]

    emb = embed_text(new_content)
    cur.execute(
        """UPDATE documents SET title=%s, url=%s, content=%s, type=%s, metadata=%s, embedding=%s,
            sector=%s, pillar=%s, roles=%s, topic_tags=%s, scope=%s, slug=%s, legal_basis=%s
           WHERE id=%s""",
        (new_title, new_url, new_content, new_type, json.dumps(new_meta), emb,
         new_sector, new_pillar, new_roles, new_tags, new_scope, new_slug, new_legal, doc_id)
    )
    conn.commit(); cur.close(); conn.close()

    _invalidate_syntheses(new_sector, new_scope, new_roles, new_pillar)
    if new_scope == 'sector-specific' and new_sector:
        background_tasks.add_task(_proactive_regen_sector_specific, new_sector, new_roles, new_pillar)
    else:
        print(f"[Synthesis] {new_scope} doc updated — run /admin/regenerate-syntheses to rebuild.")

    return {"message": "Document updated and re-embedded successfully"}

@app.delete("/admin/documents/{doc_id}")
async def delete_document(doc_id: int, x_admin_key: Optional[str] = Header(None)):
    require_admin(x_admin_key)
    conn = get_db_connection()
    cur = conn.cursor()
    # Fetch metadata before deleting so we can invalidate
    cur.execute("SELECT sector, scope, roles, pillar FROM documents WHERE id = %s", (doc_id,))
    doc_meta = cur.fetchone()
    cur.execute("DELETE FROM documents WHERE id = %s RETURNING id", (doc_id,))
    deleted = cur.fetchone()
    conn.commit(); cur.close(); conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc_meta:
        _invalidate_syntheses(doc_meta[0], doc_meta[1], doc_meta[2] or [], doc_meta[3] or '')
    return {"message": "Document deleted"}

@app.get("/admin/sectors")
async def admin_list_sectors(x_admin_key: Optional[str] = Header(None)):
    require_admin(x_admin_key)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, slug, showcase, sort_order FROM sectors ORDER BY sort_order")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [{"id": r[0], "name": r[1], "slug": r[2], "showcase": r[3], "sort_order": r[4]} for r in rows]


# ─── Admin Utility Endpoints ─────────────────────────────────────────────────

@app.post("/admin/embed-missing")
async def embed_missing_documents(x_admin_key: Optional[str] = Header(None)):
    """
    Generate embeddings for all documents that are missing them.
    Necessary after bulk-seeding via seed_kb.py (which skips embeddings for speed).
    Once run, all KB documents become searchable by the l-Ufficjal chatbot.
    """
    require_admin(x_admin_key)
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenRouter not configured")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, content FROM documents WHERE embedding IS NULL")
    missing = cur.fetchall()

    success = 0; failed = 0
    for doc_id, content in missing:
        try:
            emb = embed_text(content or '')
            cur.execute("UPDATE documents SET embedding = %s WHERE id = %s", (emb, doc_id))
            success += 1
        except Exception as e:
            print(f"  ✗ Embed failed for doc {doc_id}: {e}")
            failed += 1

    conn.commit(); cur.close(); conn.close()
    return {
        "message": f"Embeddings generated for {success} documents ({failed} failed)",
        "total_missing": len(missing),
        "success": success,
        "failed": failed,
    }


@app.post("/admin/regenerate-syntheses")
async def regenerate_syntheses(background_tasks: BackgroundTasks, x_admin_key: Optional[str] = Header(None)):
    """
    Proactively regenerate ALL synthesis combinations that have content.
    Run after bulk KB imports or changes to cross-cutting/universal documents.
    Clears the existing cache and regenerates everything in the background.
    Progress is logged to the server console.
    """
    require_admin(x_admin_key)
    if not openai_client:
        raise HTTPException(status_code=500, detail="OpenRouter not configured")

    # Clear the entire cache so we start fresh
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM syntheses")
    old_count = cur.fetchone()[0]
    cur.execute("DELETE FROM syntheses")
    conn.commit(); cur.close(); conn.close()

    background_tasks.add_task(_regenerate_all_syntheses)
    return {
        "message": "Synthesis regeneration started in background. Check server logs for progress.",
        "cleared": old_count,
    }


@app.get("/admin/syntheses")
async def list_syntheses(x_admin_key: Optional[str] = Header(None)):
    """List all pre-generated synthesis cache entries."""
    require_admin(x_admin_key)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT sector, role, topic, title, generated_at FROM syntheses ORDER BY sector, role, topic")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [{"sector": r[0], "role": r[1], "topic": r[2], "title": r[3], "generated_at": str(r[4])} for r in rows]


@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    with open("/app/admin.html", "r") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
