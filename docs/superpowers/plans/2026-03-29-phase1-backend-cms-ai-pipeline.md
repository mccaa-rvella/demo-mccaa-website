# Phase 1: Backend — CMS + AI Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the modular backend that handles data ingestion (crawl, scrape, manual, JSON), AI classification, article generation with skills, and an approval workflow.

**Architecture:** Modular monolith — single FastAPI service split into focused modules. DB-backed task queue for long-running AI operations (crawling, classification, article generation). PostgreSQL + pgvector for storage and vector search.

**Tech Stack:** Python 3.11+, FastAPI, PostgreSQL + pgvector, Anthropic SDK (Claude Sonnet), OpenAI embeddings, Firecrawl, Pydantic v2

**Spec:** `docs/superpowers/specs/2026-03-29-mccaa-knowledge-platform-design.md`

---

## File Structure

```
api/
├── main.py                          # App startup, lifespan, mount routers
├── config.py                        # Settings from env vars (Pydantic BaseSettings)
├── db.py                            # Connection pool, table creation, migrations
├── queue.py                         # Task queue: enqueue, poll, run workers
├── models.py                        # Pydantic models shared across modules
├── modules/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── router.py               # Admin endpoints: POST /admin/ingest/crawl, /scrape, /json, /manual
│   │   ├── crawl.py                # Firecrawl crawl integration
│   │   ├── scrape.py               # Firecrawl single-page scrape
│   │   ├── consolidation.py        # AI consolidation: raw_sources → knowledge_units
│   │   └── json_schema.py          # Strict JSON schema + AI normalisation fallback
│   ├── classification/
│   │   ├── __init__.py
│   │   ├── router.py               # Admin endpoints: POST /admin/classification/override
│   │   └── classifier.py           # AI classification + consumer relevance assessment
│   ├── articles/
│   │   ├── __init__.py
│   │   ├── router.py               # Admin CRUD + approval endpoints
│   │   ├── generator.py            # AI article generation (business + consumer)
│   │   ├── cascade.py              # Update cascade: detect affected articles, queue re-gen
│   │   └── diff.py                 # HTML diff for approval review
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── router.py               # Admin CRUD for skills
│   │   └── selector.py             # AI skill selection based on description matching
│   ├── cms/
│   │   ├── __init__.py
│   │   ├── router.py               # Exclusions CRUD, analytics dashboard, admin panel
│   │   └── templates/
│   │       └── admin.html           # Admin panel UI (evolved from existing)
│   └── public/
│       ├── __init__.py
│       ├── router.py               # Public API: GET /sectors, /articles/{slug}, /search, POST /contact
│       ├── search.py               # Vector search + intent matching + exclusion check
│       └── conversation.py         # Conversational follow-up state machine
├── tests/
│   ├── conftest.py                 # Fixtures: test DB, client, seed data
│   ├── test_db.py                  # Schema creation tests
│   ├── test_queue.py               # Task queue tests
│   ├── test_ingestion.py           # Ingestion endpoint + crawl/scrape/consolidation tests
│   ├── test_classification.py      # Classification + consumer relevance tests
│   ├── test_articles.py            # Article CRUD + generation + approval tests
│   ├── test_skills.py              # Skills CRUD + selection tests
│   ├── test_cascade.py             # Cascade update logic tests
│   ├── test_public.py              # Public API endpoint tests
│   └── test_search.py              # Search + intent matching + conversation tests
├── Dockerfile
└── requirements.txt
```

---

### Task 1: Project Foundation — Config, DB, and Schema

**Files:**
- Create: `api/config.py`
- Create: `api/db.py`
- Create: `api/models.py`
- Create: `api/modules/__init__.py`
- Modify: `api/requirements.txt`
- Create: `api/tests/__init__.py`
- Create: `api/tests/conftest.py`
- Create: `api/tests/test_db.py`

- [ ] **Step 1: Update requirements.txt**

```
fastapi
uvicorn
psycopg2-binary
openai
python-dotenv
pydantic
pydantic-settings
anthropic
firecrawl-py
httpx
pytest
pytest-asyncio
```

- [ ] **Step 2: Write config.py**

```python
# api/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_host: str = "127.0.0.1"
    db_port: str = "5432"
    db_user: str = "postgres"
    db_pass: str = "mysecretpassword"
    db_name: str = "mccaa_website"
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    openai_api_key: str = ""
    admin_password: str = "mccaa-admin-2026"
    firecrawl_api_key: str = ""
    queue_poll_interval: int = 2  # seconds

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Step 3: Write db.py with schema creation**

```python
# api/db.py
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from api.config import settings

_pool = None


def get_connection():
    return psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_pass,
        dbname=settings.db_name,
    )


@contextmanager
def get_cursor(commit=True):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
            if commit:
                conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS raw_sources (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(20) NOT NULL,
    source_url TEXT,
    raw_content TEXT NOT NULL,
    raw_metadata JSONB DEFAULT '{}',
    batch_id UUID,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_units (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_ids INT[] DEFAULT '{}',
    classification JSONB DEFAULT '{}',
    ai_confidence FLOAT,
    admin_overrides JSONB,
    consumer_essential BOOLEAN,
    embedding vector(1536),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sectors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    showcase BOOLEAN DEFAULT false,
    sort_order INT DEFAULT 0,
    article_id INT,
    consumer_article_id INT,
    visit_count INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    slug VARCHAR(80) UNIQUE NOT NULL,
    sector VARCHAR(200),
    scope VARCHAR(20) NOT NULL,
    audience VARCHAR(10) NOT NULL DEFAULT 'business',
    html_content TEXT NOT NULL DEFAULT '',
    tag_map JSONB DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    published_version_id INT REFERENCES articles(id),
    skills_used TEXT[] DEFAULT '{}',
    source_knowledge_unit_ids INT[] DEFAULT '{}',
    cross_cutting_summaries JSONB DEFAULT '[]',
    admin_edits JSONB DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) NOT NULL UNIQUE,
    description VARCHAR(1024) NOT NULL,
    skill_content TEXT NOT NULL DEFAULT '',
    resources JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    auto_select BOOLEAN DEFAULT true,
    pinned_sectors TEXT[] DEFAULT '{}',
    pinned_types TEXT[] DEFAULT '{}',
    excluded_sectors TEXT[] DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS exclusions (
    id SERIAL PRIMARY KEY,
    type VARCHAR(10) NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS topic_analytics (
    id SERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    sector VARCHAR(200),
    visit_count INT DEFAULT 0,
    last_visited_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inquiries (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(200),
    user_email VARCHAR(200),
    message TEXT,
    search_context JSONB DEFAULT '{}',
    match_type VARCHAR(20),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'new'
);

CREATE TABLE IF NOT EXISTS task_queue (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(30) NOT NULL,
    payload JSONB DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    result JSONB,
    error TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_task_queue_status ON task_queue(status, created_at);
CREATE INDEX IF NOT EXISTS idx_articles_sector ON articles(sector);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_topic_analytics_unique ON topic_analytics(topic, sector);
CREATE INDEX IF NOT EXISTS idx_knowledge_units_embedding ON knowledge_units USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
"""


def ensure_schema():
    with get_cursor() as cur:
        cur.execute(SCHEMA_SQL)
```

- [ ] **Step 4: Write shared Pydantic models**

```python
# api/models.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RawSourceOut(BaseModel):
    id: int
    source_type: str
    source_url: Optional[str] = None
    status: str
    batch_id: Optional[str] = None
    created_at: datetime


class KnowledgeUnitOut(BaseModel):
    id: int
    title: str
    content: str
    source_ids: list[int]
    classification: dict
    ai_confidence: Optional[float] = None
    admin_overrides: Optional[dict] = None
    consumer_essential: Optional[bool] = None
    created_at: datetime
    updated_at: datetime


class ArticleOut(BaseModel):
    id: int
    title: str
    slug: str
    sector: Optional[str] = None
    scope: str
    audience: str
    html_content: str
    tag_map: dict
    status: str
    skills_used: list[str]
    source_knowledge_unit_ids: list[int]
    cross_cutting_summaries: list
    admin_edits: list
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None


class SkillOut(BaseModel):
    id: int
    name: str
    description: str
    skill_content: str
    resources: dict
    is_active: bool
    auto_select: bool
    pinned_sectors: list[str]
    pinned_types: list[str]
    excluded_sectors: list[str]
    created_at: datetime
    updated_at: datetime


class ExclusionOut(BaseModel):
    id: int
    type: str
    value: str
    created_at: datetime


class InquiryOut(BaseModel):
    id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    message: Optional[str] = None
    search_context: dict
    match_type: Optional[str] = None
    created_at: datetime
    status: str


class TaskOut(BaseModel):
    id: int
    task_type: str
    payload: dict
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
```

- [ ] **Step 5: Create module init files**

```python
# api/modules/__init__.py
# (empty)
```

- [ ] **Step 6: Write the failing test for schema creation**

```python
# api/tests/conftest.py
import os
import pytest
import psycopg2
from psycopg2.extras import RealDictCursor

TEST_DB_NAME = "mccaa_website_test"


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create a test database and run schema migrations."""
    os.environ["DB_NAME"] = TEST_DB_NAME
    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=os.environ.get("DB_PORT", "5432"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASS", "mysecretpassword"),
        dbname="postgres",
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
    cur.execute(f"CREATE DATABASE {TEST_DB_NAME}")
    cur.close()
    conn.close()

    from api.db import ensure_schema
    ensure_schema()

    yield

    conn = psycopg2.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=os.environ.get("DB_PORT", "5432"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASS", "mysecretpassword"),
        dbname="postgres",
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}")
    cur.close()
    conn.close()


@pytest.fixture
def db_cursor():
    """Provide a test database cursor that rolls back after each test."""
    from api.db import get_connection
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    yield cur
    conn.rollback()
    cur.close()
    conn.close()
```

```python
# api/tests/__init__.py
# (empty)
```

```python
# api/tests/test_db.py
def test_all_tables_exist(db_cursor):
    db_cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = {row["table_name"] for row in db_cursor.fetchall()}
    expected = {
        "raw_sources",
        "knowledge_units",
        "sectors",
        "articles",
        "skills",
        "exclusions",
        "topic_analytics",
        "inquiries",
        "task_queue",
    }
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"


def test_vector_extension_enabled(db_cursor):
    db_cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
    assert db_cursor.fetchone() is not None


def test_raw_sources_columns(db_cursor):
    db_cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'raw_sources'
    """)
    cols = {row["column_name"] for row in db_cursor.fetchall()}
    assert {"id", "source_type", "source_url", "raw_content", "raw_metadata",
            "batch_id", "status", "created_at"}.issubset(cols)


def test_articles_columns(db_cursor):
    db_cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'articles'
    """)
    cols = {row["column_name"] for row in db_cursor.fetchall()}
    assert {"id", "title", "slug", "sector", "scope", "audience", "html_content",
            "tag_map", "status", "published_version_id", "skills_used",
            "source_knowledge_unit_ids", "cross_cutting_summaries", "admin_edits",
            "approved_at", "approved_by"}.issubset(cols)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/test_db.py -v`
Expected: 4 tests PASS

- [ ] **Step 8: Commit**

```bash
git add api/config.py api/db.py api/models.py api/modules/__init__.py api/requirements.txt api/tests/
git commit -m "feat: add project foundation — config, DB schema, shared models, test infrastructure"
```

---

### Task 2: Task Queue

**Files:**
- Create: `api/queue.py`
- Create: `api/tests/test_queue.py`

- [ ] **Step 1: Write failing tests for task queue**

```python
# api/tests/test_queue.py
import json
from api.queue import enqueue_task, claim_next_task, complete_task, fail_task


def test_enqueue_creates_queued_task(db_cursor):
    task_id = enqueue_task("crawl", {"url": "https://example.com"})
    db_cursor.execute("SELECT * FROM task_queue WHERE id = %s", (task_id,))
    row = db_cursor.fetchone()
    assert row["status"] == "queued"
    assert row["task_type"] == "crawl"
    assert row["payload"]["url"] == "https://example.com"


def test_claim_next_gets_oldest_queued(db_cursor):
    id1 = enqueue_task("crawl", {"url": "https://a.com"})
    id2 = enqueue_task("classify", {"unit_id": 1})
    task = claim_next_task()
    assert task["id"] == id1
    assert task["status"] == "running"


def test_claim_next_returns_none_when_empty(db_cursor):
    # Clear any leftover tasks
    db_cursor.execute("DELETE FROM task_queue")
    db_cursor.connection.commit()
    task = claim_next_task()
    assert task is None


def test_complete_task_stores_result(db_cursor):
    task_id = enqueue_task("classify", {"unit_id": 1})
    claim_next_task()
    complete_task(task_id, {"classification": {"types": ["technical"]}})
    db_cursor.execute("SELECT * FROM task_queue WHERE id = %s", (task_id,))
    row = db_cursor.fetchone()
    assert row["status"] == "completed"
    assert row["result"]["classification"]["types"] == ["technical"]
    assert row["completed_at"] is not None


def test_fail_task_stores_error(db_cursor):
    task_id = enqueue_task("crawl", {"url": "https://fail.com"})
    claim_next_task()
    fail_task(task_id, "Connection timeout")
    db_cursor.execute("SELECT * FROM task_queue WHERE id = %s", (task_id,))
    row = db_cursor.fetchone()
    assert row["status"] == "failed"
    assert row["error"] == "Connection timeout"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd api && python -m pytest tests/test_queue.py -v`
Expected: FAIL — `ImportError: cannot import name 'enqueue_task'`

- [ ] **Step 3: Implement queue.py**

```python
# api/queue.py
import json
from datetime import datetime
from typing import Optional
from api.db import get_cursor


def enqueue_task(task_type: str, payload: dict) -> int:
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO task_queue (task_type, payload, status)
               VALUES (%s, %s, 'queued') RETURNING id""",
            (task_type, json.dumps(payload)),
        )
        return cur.fetchone()["id"]


def claim_next_task() -> Optional[dict]:
    with get_cursor() as cur:
        cur.execute(
            """UPDATE task_queue
               SET status = 'running', started_at = NOW()
               WHERE id = (
                   SELECT id FROM task_queue
                   WHERE status = 'queued'
                   ORDER BY created_at ASC
                   LIMIT 1
                   FOR UPDATE SKIP LOCKED
               )
               RETURNING *""",
        )
        row = cur.fetchone()
        if row:
            return dict(row)
        return None


def complete_task(task_id: int, result: dict):
    with get_cursor() as cur:
        cur.execute(
            """UPDATE task_queue
               SET status = 'completed', result = %s, completed_at = NOW()
               WHERE id = %s""",
            (json.dumps(result), task_id),
        )


def fail_task(task_id: int, error: str):
    with get_cursor() as cur:
        cur.execute(
            """UPDATE task_queue
               SET status = 'failed', error = %s, completed_at = NOW()
               WHERE id = %s""",
            (error, task_id),
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/test_queue.py -v`
Expected: 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add api/queue.py api/tests/test_queue.py
git commit -m "feat: add DB-backed task queue with enqueue, claim, complete, fail"
```

---

### Task 3: Skills Module — CRUD

**Files:**
- Create: `api/modules/skills/__init__.py`
- Create: `api/modules/skills/router.py`
- Create: `api/modules/skills/selector.py`
- Create: `api/tests/test_skills.py`

- [ ] **Step 1: Write failing tests for skills CRUD**

```python
# api/tests/test_skills.py
from fastapi.testclient import TestClient


def get_client():
    from api.main import app
    return TestClient(app)


ADMIN_HEADERS = {"X-Admin-Key": "mccaa-admin-2026"}

SAMPLE_SKILL = {
    "name": "plain-language-consumer",
    "description": "Write in plain language for consumer articles. Use when generating consumer-facing content.",
    "skill_content": "# Plain Language\n\n## Instructions\n- Use short sentences\n- Avoid jargon\n- Define technical terms",
    "resources": {"glossary.md": "# Glossary\n- CE Marking: A certification mark..."},
}


def test_create_skill():
    client = get_client()
    resp = client.post("/admin/skills", json=SAMPLE_SKILL, headers=ADMIN_HEADERS)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "plain-language-consumer"
    assert data["is_active"] is True
    assert data["auto_select"] is True


def test_list_skills():
    client = get_client()
    client.post("/admin/skills", json=SAMPLE_SKILL, headers=ADMIN_HEADERS)
    resp = client.get("/admin/skills", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    skills = resp.json()
    assert len(skills) >= 1
    assert any(s["name"] == "plain-language-consumer" for s in skills)


def test_update_skill():
    client = get_client()
    create_resp = client.post("/admin/skills", json=SAMPLE_SKILL, headers=ADMIN_HEADERS)
    skill_id = create_resp.json()["id"]
    resp = client.put(
        f"/admin/skills/{skill_id}",
        json={"pinned_sectors": ["toys"], "is_active": False},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["pinned_sectors"] == ["toys"]
    assert resp.json()["is_active"] is False


def test_delete_skill():
    client = get_client()
    create_resp = client.post("/admin/skills", json=SAMPLE_SKILL, headers=ADMIN_HEADERS)
    skill_id = create_resp.json()["id"]
    resp = client.delete(f"/admin/skills/{skill_id}", headers=ADMIN_HEADERS)
    assert resp.status_code == 204


def test_skills_require_auth():
    client = get_client()
    resp = client.get("/admin/skills")
    assert resp.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd api && python -m pytest tests/test_skills.py -v`
Expected: FAIL

- [ ] **Step 3: Create skills __init__.py**

```python
# api/modules/skills/__init__.py
# (empty)
```

- [ ] **Step 4: Implement skills router**

```python
# api/modules/skills/router.py
import json
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from api.config import settings
from api.db import get_cursor
from api.models import SkillOut

router = APIRouter(prefix="/admin/skills", tags=["skills"])


def require_admin(x_admin_key: str = Header(None)):
    if x_admin_key != settings.admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")


class SkillCreate(BaseModel):
    name: str
    description: str
    skill_content: str = ""
    resources: dict = {}
    is_active: bool = True
    auto_select: bool = True
    pinned_sectors: list[str] = []
    pinned_types: list[str] = []
    excluded_sectors: list[str] = []


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    skill_content: Optional[str] = None
    resources: Optional[dict] = None
    is_active: Optional[bool] = None
    auto_select: Optional[bool] = None
    pinned_sectors: Optional[list[str]] = None
    pinned_types: Optional[list[str]] = None
    excluded_sectors: Optional[list[str]] = None


@router.post("", status_code=201)
def create_skill(body: SkillCreate, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO skills (name, description, skill_content, resources,
                   is_active, auto_select, pinned_sectors, pinned_types, excluded_sectors)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING *""",
            (body.name, body.description, body.skill_content,
             json.dumps(body.resources), body.is_active, body.auto_select,
             body.pinned_sectors, body.pinned_types, body.excluded_sectors),
        )
        row = cur.fetchone()
        return dict(row)


@router.get("")
def list_skills(x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor() as cur:
        cur.execute("SELECT * FROM skills ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]


@router.get("/{skill_id}")
def get_skill(skill_id: int, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor() as cur:
        cur.execute("SELECT * FROM skills WHERE id = %s", (skill_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Skill not found")
        return dict(row)


@router.put("/{skill_id}")
def update_skill(skill_id: int, body: SkillUpdate, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clauses = []
    values = []
    for key, val in updates.items():
        if key == "resources":
            set_clauses.append(f"{key} = %s")
            values.append(json.dumps(val))
        elif isinstance(val, list):
            set_clauses.append(f"{key} = %s")
            values.append(val)
        else:
            set_clauses.append(f"{key} = %s")
            values.append(val)
    set_clauses.append("updated_at = NOW()")
    values.append(skill_id)

    with get_cursor() as cur:
        cur.execute(
            f"UPDATE skills SET {', '.join(set_clauses)} WHERE id = %s RETURNING *",
            values,
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Skill not found")
        return dict(row)


@router.delete("/{skill_id}", status_code=204)
def delete_skill(skill_id: int, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor() as cur:
        cur.execute("DELETE FROM skills WHERE id = %s", (skill_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Skill not found")
```

- [ ] **Step 5: Implement skill selector**

```python
# api/modules/skills/selector.py
import anthropic
from api.config import settings
from api.db import get_cursor


def select_skills_for_article(sector: str, scope: str, audience: str) -> list[dict]:
    """Select relevant skills for article generation.

    1. Load all active skills
    2. Include pinned skills for this sector/type
    3. Exclude skills excluded for this sector
    4. For remaining auto_select skills, ask Sonnet to pick relevant ones
    """
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM skills WHERE is_active = true")
        all_skills = [dict(r) for r in cur.fetchall()]

    if not all_skills:
        return []

    selected = []
    candidates = []

    for skill in all_skills:
        # Always include pinned skills for this sector or type
        if sector and sector in (skill.get("pinned_sectors") or []):
            selected.append(skill)
            continue
        if audience in (skill.get("pinned_types") or []):
            selected.append(skill)
            continue
        # Always exclude skills excluded for this sector
        if sector and sector in (skill.get("excluded_sectors") or []):
            continue
        # Remaining auto_select skills are candidates for AI selection
        if skill.get("auto_select"):
            candidates.append(skill)

    if not candidates or not settings.anthropic_api_key:
        return selected

    # Ask Sonnet to pick relevant skills from candidates
    skill_descriptions = "\n".join(
        f"- {s['name']}: {s['description']}" for s in candidates
    )
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": (
                f"I am generating a {audience} article about the '{sector}' sector "
                f"(scope: {scope}). Which of these skills are relevant?\n\n"
                f"{skill_descriptions}\n\n"
                "Return ONLY a JSON array of skill names that are relevant. "
                "Example: [\"skill-a\", \"skill-b\"]. Return [] if none are relevant."
            ),
        }],
    )
    try:
        import json
        text = response.content[0].text.strip()
        # Extract JSON array from response
        start = text.index("[")
        end = text.rindex("]") + 1
        chosen_names = json.loads(text[start:end])
        for skill in candidates:
            if skill["name"] in chosen_names:
                selected.append(skill)
    except (json.JSONDecodeError, ValueError):
        pass  # If AI response is unparseable, skip auto-selected skills

    return selected
```

- [ ] **Step 6: Update main.py to mount skills router**

We need to refactor `api/main.py` to mount modular routers. For now, we'll create a minimal new main.py that imports and mounts the skills router alongside the existing functionality. The full migration of existing endpoints happens later.

```python
# At the top of api/main.py, after existing imports and before the app definition,
# we'll progressively add router mounts. For now, add after the app is created
# and CORS middleware is added:

# --- New modular routers ---
from api.modules.skills.router import router as skills_router
app.include_router(skills_router)
```

Note: The existing `api/main.py` structure needs to be preserved during migration. Add the router import and mount after the existing CORS middleware setup. The exact insertion point depends on the current file structure — insert after `app.add_middleware(CORSMiddleware, ...)`.

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/test_skills.py -v`
Expected: 5 tests PASS

- [ ] **Step 8: Commit**

```bash
git add api/modules/skills/ api/tests/test_skills.py api/main.py
git commit -m "feat: add skills module — CRUD endpoints and AI skill selector"
```

---

### Task 4: Ingestion Module — Crawl & Scrape

**Files:**
- Create: `api/modules/ingestion/__init__.py`
- Create: `api/modules/ingestion/router.py`
- Create: `api/modules/ingestion/crawl.py`
- Create: `api/modules/ingestion/scrape.py`
- Create: `api/tests/test_ingestion.py`

- [ ] **Step 1: Write failing tests for ingestion endpoints**

```python
# api/tests/test_ingestion.py
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def get_client():
    from api.main import app
    return TestClient(app)


ADMIN_HEADERS = {"X-Admin-Key": "mccaa-admin-2026"}


def test_crawl_enqueues_task():
    client = get_client()
    with patch("api.modules.ingestion.router.enqueue_task", return_value=1) as mock_enqueue:
        resp = client.post(
            "/admin/ingest/crawl",
            json={"url": "https://mccaa.org.mt/consumer"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 202
        assert resp.json()["task_id"] == 1
        mock_enqueue.assert_called_once()
        call_args = mock_enqueue.call_args
        assert call_args[0][0] == "crawl"
        assert call_args[0][1]["url"] == "https://mccaa.org.mt/consumer"


def test_scrape_enqueues_task():
    client = get_client()
    with patch("api.modules.ingestion.router.enqueue_task", return_value=2) as mock_enqueue:
        resp = client.post(
            "/admin/ingest/scrape",
            json={"url": "https://mccaa.org.mt/specific-page"},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 202
        assert resp.json()["task_id"] == 2
        mock_enqueue.assert_called_once_with("scrape", {"url": "https://mccaa.org.mt/specific-page"})


def test_manual_entry_creates_knowledge_unit(db_cursor):
    client = get_client()
    resp = client.post(
        "/admin/ingest/manual",
        json={
            "title": "CE Marking for Toys",
            "content": "All toys placed on the EU market must bear the CE marking...",
            "classification": {
                "types": ["technical"],
                "sectors": ["toys"],
                "actors": ["manufacturer", "importer"],
                "scope": "sector-specific",
            },
        },
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "CE Marking for Toys"
    assert data["classification"]["types"] == ["technical"]


def test_manual_entry_without_classification_enqueues_classify(db_cursor):
    client = get_client()
    with patch("api.modules.ingestion.router.enqueue_task", return_value=3) as mock_enqueue:
        resp = client.post(
            "/admin/ingest/manual",
            json={
                "title": "New Consumer Rights",
                "content": "Consumers have the right to...",
            },
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 201
        mock_enqueue.assert_called_once()
        assert mock_enqueue.call_args[0][0] == "classify"


def test_ingest_requires_auth():
    client = get_client()
    resp = client.post("/admin/ingest/crawl", json={"url": "https://example.com"})
    assert resp.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd api && python -m pytest tests/test_ingestion.py -v`
Expected: FAIL

- [ ] **Step 3: Create ingestion __init__.py**

```python
# api/modules/ingestion/__init__.py
# (empty)
```

- [ ] **Step 4: Implement crawl.py**

```python
# api/modules/ingestion/crawl.py
import uuid
import json
from firecrawl import FirecrawlApp
from api.config import settings
from api.db import get_cursor
from api.queue import enqueue_task


def run_crawl(url: str) -> dict:
    """Crawl a URL using Firecrawl, store pages as raw_sources, then enqueue consolidation."""
    batch_id = str(uuid.uuid4())

    firecrawl = FirecrawlApp(api_key=settings.firecrawl_api_key)
    result = firecrawl.crawl_url(url, params={"limit": 100})

    pages_stored = 0
    with get_cursor() as cur:
        for page in result.get("data", []):
            content = page.get("markdown", "") or page.get("content", "")
            if not content.strip():
                continue
            metadata = {
                "title": page.get("metadata", {}).get("title", ""),
                "source_url": page.get("metadata", {}).get("sourceURL", url),
            }
            cur.execute(
                """INSERT INTO raw_sources (source_type, source_url, raw_content, raw_metadata, batch_id, status)
                   VALUES ('crawl', %s, %s, %s, %s, 'pending')""",
                (metadata["source_url"], content, json.dumps(metadata), batch_id),
            )
            pages_stored += 1

    # Enqueue consolidation for this batch
    consolidation_task_id = enqueue_task("consolidate", {"batch_id": batch_id})

    return {
        "batch_id": batch_id,
        "pages_stored": pages_stored,
        "consolidation_task_id": consolidation_task_id,
    }
```

- [ ] **Step 5: Implement scrape.py**

```python
# api/modules/ingestion/scrape.py
import uuid
import json
from firecrawl import FirecrawlApp
from api.config import settings
from api.db import get_cursor
from api.queue import enqueue_task


def run_scrape(url: str) -> dict:
    """Scrape a single URL using Firecrawl, store as raw_source, then enqueue consolidation."""
    batch_id = str(uuid.uuid4())

    firecrawl = FirecrawlApp(api_key=settings.firecrawl_api_key)
    result = firecrawl.scrape_url(url, params={"formats": ["markdown"]})

    content = result.get("markdown", "") or result.get("content", "")
    metadata = {
        "title": result.get("metadata", {}).get("title", ""),
        "source_url": url,
    }

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO raw_sources (source_type, source_url, raw_content, raw_metadata, batch_id, status)
               VALUES ('scrape', %s, %s, %s, %s, 'pending') RETURNING id""",
            (url, content, json.dumps(metadata), batch_id),
        )
        source_id = cur.fetchone()["id"]

    consolidation_task_id = enqueue_task("consolidate", {"batch_id": batch_id})

    return {
        "batch_id": batch_id,
        "source_id": source_id,
        "consolidation_task_id": consolidation_task_id,
    }
```

- [ ] **Step 6: Implement ingestion router**

```python
# api/modules/ingestion/router.py
import json
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from api.config import settings
from api.db import get_cursor
from api.queue import enqueue_task

router = APIRouter(prefix="/admin/ingest", tags=["ingestion"])


def require_admin(x_admin_key: str = Header(None)):
    if x_admin_key != settings.admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")


class CrawlRequest(BaseModel):
    url: str


class ScrapeRequest(BaseModel):
    url: str


class ManualEntryRequest(BaseModel):
    title: str
    content: str
    classification: Optional[dict] = None


class JsonImportRequest(BaseModel):
    data: list[dict]


@router.post("/crawl", status_code=202)
def start_crawl(body: CrawlRequest, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    task_id = enqueue_task("crawl", {"url": body.url})
    return {"task_id": task_id, "message": "Crawl task enqueued"}


@router.post("/scrape", status_code=202)
def start_scrape(body: ScrapeRequest, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    task_id = enqueue_task("scrape", {"url": body.url})
    return {"task_id": task_id, "message": "Scrape task enqueued"}


@router.post("/manual", status_code=201)
def manual_entry(body: ManualEntryRequest, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor() as cur:
        classification = body.classification or {}
        admin_overrides = body.classification if body.classification else None
        cur.execute(
            """INSERT INTO knowledge_units (title, content, classification, admin_overrides)
               VALUES (%s, %s, %s, %s) RETURNING *""",
            (body.title, body.content, json.dumps(classification),
             json.dumps(admin_overrides) if admin_overrides else None),
        )
        unit = dict(cur.fetchone())

    # If no classification provided, enqueue AI classification
    if not body.classification:
        enqueue_task("classify", {"unit_id": unit["id"]})

    return unit


@router.post("/json", status_code=202)
def import_json(body: JsonImportRequest, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    from api.modules.ingestion.json_schema import validate_and_import
    result = validate_and_import(body.data)
    return result
```

- [ ] **Step 7: Mount ingestion router in main.py**

Add after the skills router mount in `api/main.py`:

```python
from api.modules.ingestion.router import router as ingestion_router
app.include_router(ingestion_router)
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/test_ingestion.py -v`
Expected: 5 tests PASS

- [ ] **Step 9: Commit**

```bash
git add api/modules/ingestion/ api/tests/test_ingestion.py api/main.py
git commit -m "feat: add ingestion module — crawl, scrape, manual entry endpoints"
```

---

### Task 5: Ingestion Module — JSON Schema & AI Normalisation

**Files:**
- Create: `api/modules/ingestion/json_schema.py`
- Add tests to: `api/tests/test_ingestion.py`

- [ ] **Step 1: Write failing tests for JSON import**

Append to `api/tests/test_ingestion.py`:

```python
def test_json_import_valid_schema(db_cursor):
    client = get_client()
    valid_data = [
        {
            "title": "Toy Safety Requirements",
            "content": "All toys must comply with EN 71...",
            "classification": {
                "types": ["technical"],
                "sectors": ["toys"],
                "actors": ["manufacturer"],
                "scope": "sector-specific",
            },
        }
    ]
    resp = client.post(
        "/admin/ingest/json",
        json={"data": valid_data},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 202
    assert resp.json()["valid_count"] == 1


def test_json_import_invalid_schema_triggers_normalisation():
    client = get_client()
    invalid_data = [
        {"name": "Some regulation", "text": "This is about consumer rights..."}
    ]
    with patch("api.modules.ingestion.json_schema.enqueue_task", return_value=10):
        resp = client.post(
            "/admin/ingest/json",
            json={"data": invalid_data},
            headers=ADMIN_HEADERS,
        )
        assert resp.status_code == 202
        assert resp.json()["invalid_count"] == 1
        assert resp.json()["normalisation_task_id"] is not None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd api && python -m pytest tests/test_ingestion.py::test_json_import_valid_schema tests/test_ingestion.py::test_json_import_invalid_schema_triggers_normalisation -v`
Expected: FAIL

- [ ] **Step 3: Implement json_schema.py**

```python
# api/modules/ingestion/json_schema.py
import json
from typing import Any
from api.db import get_cursor
from api.queue import enqueue_task

REQUIRED_FIELDS = {"title", "content"}
OPTIONAL_FIELDS = {"classification"}
CLASSIFICATION_FIELDS = {"types", "sectors", "actors", "scope"}


def validate_record(record: dict) -> bool:
    """Check if a record matches the strict schema."""
    if not isinstance(record, dict):
        return False
    if not REQUIRED_FIELDS.issubset(record.keys()):
        return False
    if "classification" in record:
        cls = record["classification"]
        if not isinstance(cls, dict):
            return False
        if not CLASSIFICATION_FIELDS.issubset(cls.keys()):
            return False
    return True


def validate_and_import(data: list[dict]) -> dict:
    """Validate JSON data against strict schema.

    Valid records → insert directly as knowledge_units.
    Invalid records → enqueue AI normalisation task.
    """
    valid_records = []
    invalid_records = []

    for record in data:
        if validate_record(record):
            valid_records.append(record)
        else:
            invalid_records.append(record)

    # Insert valid records directly
    created_ids = []
    with get_cursor() as cur:
        for record in valid_records:
            classification = record.get("classification", {})
            cur.execute(
                """INSERT INTO knowledge_units (title, content, classification, admin_overrides)
                   VALUES (%s, %s, %s, %s) RETURNING id""",
                (record["title"], record["content"],
                 json.dumps(classification), json.dumps(classification) if classification else None),
            )
            created_ids.append(cur.fetchone()["id"])

    # Enqueue classification for valid records without classification
    for i, record in enumerate(valid_records):
        if not record.get("classification"):
            enqueue_task("classify", {"unit_id": created_ids[i]})

    # Enqueue normalisation for invalid records
    normalisation_task_id = None
    if invalid_records:
        normalisation_task_id = enqueue_task(
            "json_normalize", {"records": invalid_records}
        )

    return {
        "valid_count": len(valid_records),
        "invalid_count": len(invalid_records),
        "created_ids": created_ids,
        "normalisation_task_id": normalisation_task_id,
    }


def run_json_normalize(records: list[dict]) -> dict:
    """Use AI to normalise invalid JSON records into the internal schema."""
    import anthropic
    from api.config import settings

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": (
                "Normalize these JSON records into the MCCAA knowledge base schema.\n\n"
                f"Records:\n{json.dumps(records, indent=2)}\n\n"
                "Required schema per record:\n"
                '{"title": "...", "content": "...", "classification": {"types": [...], "sectors": [...], "actors": [...], "scope": "..."}}\n\n'
                "Return ONLY a JSON array of normalised records."
            ),
        }],
    )

    text = response.content[0].text.strip()
    start = text.index("[")
    end = text.rindex("]") + 1
    normalised = json.loads(text[start:end])

    # Store normalised records as knowledge units
    created_ids = []
    with get_cursor() as cur:
        for record in normalised:
            classification = record.get("classification", {})
            cur.execute(
                """INSERT INTO knowledge_units (title, content, classification)
                   VALUES (%s, %s, %s) RETURNING id""",
                (record["title"], record["content"], json.dumps(classification)),
            )
            created_ids.append(cur.fetchone()["id"])

    # Enqueue classification for records without full classification
    for i, record in enumerate(normalised):
        cls = record.get("classification", {})
        if not cls.get("types") or not cls.get("sectors"):
            enqueue_task("classify", {"unit_id": created_ids[i]})

    return {"normalised_count": len(normalised), "created_ids": created_ids}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/test_ingestion.py -v`
Expected: 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add api/modules/ingestion/json_schema.py api/tests/test_ingestion.py
git commit -m "feat: add JSON import with strict schema validation and AI normalisation fallback"
```

---

### Task 6: Ingestion Module — AI Consolidation

**Files:**
- Create: `api/modules/ingestion/consolidation.py`
- Create: `api/tests/test_consolidation.py`

- [ ] **Step 1: Write failing tests**

```python
# api/tests/test_consolidation.py
import json
from unittest.mock import patch, MagicMock
from api.db import get_cursor


def _seed_raw_sources(batch_id: str) -> list[int]:
    """Insert sample raw_sources for testing consolidation."""
    ids = []
    with get_cursor() as cur:
        for i, (title, content) in enumerate([
            ("Toy Safety Directive", "The Toy Safety Directive 2009/48/EC establishes safety requirements..."),
            ("CE Marking for Toys", "CE marking on toys indicates conformity with EU legislation..."),
            ("Toy Chemical Safety", "Chemical properties of toys must comply with REACH and EN 71-3..."),
        ]):
            cur.execute(
                """INSERT INTO raw_sources (source_type, source_url, raw_content, raw_metadata, batch_id, status)
                   VALUES ('crawl', %s, %s, %s, %s, 'pending') RETURNING id""",
                (f"https://example.com/page{i}", content,
                 json.dumps({"title": title}), batch_id),
            )
            ids.append(cur.fetchone()["id"])
    return ids


MOCK_CONSOLIDATION_RESPONSE = json.dumps([
    {
        "title": "Toy Safety Requirements",
        "content": "Comprehensive overview of toy safety including the Directive 2009/48/EC, CE marking, and chemical safety...",
        "source_indices": [0, 1, 2],
    }
])


@patch("api.modules.ingestion.consolidation.anthropic")
def test_consolidate_merges_related_sources(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=MOCK_CONSOLIDATION_RESPONSE)]
    )

    batch_id = "test-batch-001"
    source_ids = _seed_raw_sources(batch_id)

    from api.modules.ingestion.consolidation import run_consolidation
    result = run_consolidation(batch_id)

    assert result["units_created"] == 1

    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM knowledge_units WHERE title = 'Toy Safety Requirements'")
        unit = cur.fetchone()
        assert unit is not None
        assert set(unit["source_ids"]) == set(source_ids)


@patch("api.modules.ingestion.consolidation.anthropic")
def test_consolidation_marks_sources_as_consolidated(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=MOCK_CONSOLIDATION_RESPONSE)]
    )

    batch_id = "test-batch-002"
    source_ids = _seed_raw_sources(batch_id)

    from api.modules.ingestion.consolidation import run_consolidation
    run_consolidation(batch_id)

    with get_cursor(commit=False) as cur:
        cur.execute("SELECT status FROM raw_sources WHERE batch_id = %s", (batch_id,))
        statuses = [row["status"] for row in cur.fetchall()]
        assert all(s == "consolidated" for s in statuses)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd api && python -m pytest tests/test_consolidation.py -v`
Expected: FAIL

- [ ] **Step 3: Implement consolidation.py**

```python
# api/modules/ingestion/consolidation.py
import json
import anthropic
from api.config import settings
from api.db import get_cursor
from api.queue import enqueue_task

CONSOLIDATION_PROMPT = """You are an expert in EU/Maltese regulatory content.

Given the following web pages extracted from a crawl, identify thematic clusters and consolidate them into coherent knowledge units. Related pages should be merged into a single unit.

Pages:
{pages}

Return a JSON array where each element is:
{{
  "title": "Descriptive title for the consolidated knowledge unit",
  "content": "Merged, coherent content from the related pages. Preserve all factual detail. If information conflicts, keep the most recent/authoritative version and note the conflict.",
  "source_indices": [0, 2, 5]  // indices of the pages that were merged
}}

Return ONLY the JSON array, no other text."""


def run_consolidation(batch_id: str) -> dict:
    """Consolidate raw_sources in a batch into knowledge_units."""
    with get_cursor(commit=False) as cur:
        cur.execute(
            "SELECT * FROM raw_sources WHERE batch_id = %s AND status = 'pending' ORDER BY id",
            (batch_id,),
        )
        sources = [dict(r) for r in cur.fetchall()]

    if not sources:
        return {"units_created": 0, "message": "No pending sources in batch"}

    # Build page summaries for the AI
    pages_text = "\n\n".join(
        f"[Page {i}] Title: {s['raw_metadata'].get('title', 'Untitled')}\n"
        f"URL: {s['source_url']}\n"
        f"Content:\n{s['raw_content'][:3000]}"
        for i, s in enumerate(sources)
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": CONSOLIDATION_PROMPT.format(pages=pages_text),
        }],
    )

    text = response.content[0].text.strip()
    start = text.index("[")
    end = text.rindex("]") + 1
    units_data = json.loads(text[start:end])

    created_unit_ids = []
    with get_cursor() as cur:
        for unit in units_data:
            source_indices = unit["source_indices"]
            source_ids = [sources[i]["id"] for i in source_indices]
            cur.execute(
                """INSERT INTO knowledge_units (title, content, source_ids)
                   VALUES (%s, %s, %s) RETURNING id""",
                (unit["title"], unit["content"], source_ids),
            )
            created_unit_ids.append(cur.fetchone()["id"])

        # Mark sources as consolidated
        cur.execute(
            "UPDATE raw_sources SET status = 'consolidated' WHERE batch_id = %s",
            (batch_id,),
        )

    # Enqueue classification for each new knowledge unit
    for unit_id in created_unit_ids:
        enqueue_task("classify", {"unit_id": unit_id})

    return {"units_created": len(created_unit_ids), "unit_ids": created_unit_ids}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/test_consolidation.py -v`
Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add api/modules/ingestion/consolidation.py api/tests/test_consolidation.py
git commit -m "feat: add AI consolidation — merges crawled pages into knowledge units"
```

---

### Task 7: Classification Module

**Files:**
- Create: `api/modules/classification/__init__.py`
- Create: `api/modules/classification/router.py`
- Create: `api/modules/classification/classifier.py`
- Create: `api/tests/test_classification.py`

- [ ] **Step 1: Write failing tests**

```python
# api/tests/test_classification.py
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.db import get_cursor


def get_client():
    from api.main import app
    return TestClient(app)


ADMIN_HEADERS = {"X-Admin-Key": "mccaa-admin-2026"}

MOCK_CLASSIFICATION_RESPONSE = json.dumps({
    "types": ["technical", "consumer"],
    "sectors": ["toys"],
    "actors": ["manufacturer", "importer", "distributor"],
    "scope": "sector-specific",
    "consumer_essential": True,
    "confidence": 0.92,
})


def _create_knowledge_unit() -> int:
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO knowledge_units (title, content)
               VALUES ('Toy Safety Directive', 'The directive establishes essential safety requirements...')
               RETURNING id""",
        )
        return cur.fetchone()["id"]


@patch("api.modules.classification.classifier.anthropic")
def test_classify_unit(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=MOCK_CLASSIFICATION_RESPONSE)]
    )

    unit_id = _create_knowledge_unit()

    from api.modules.classification.classifier import run_classification
    result = run_classification(unit_id)

    assert result["classification"]["types"] == ["technical", "consumer"]
    assert result["classification"]["sectors"] == ["toys"]
    assert result["consumer_essential"] is True

    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM knowledge_units WHERE id = %s", (unit_id,))
        unit = cur.fetchone()
        assert unit["classification"]["types"] == ["technical", "consumer"]
        assert unit["consumer_essential"] is True
        assert unit["ai_confidence"] == 0.92


def test_override_classification():
    client = get_client()
    unit_id = _create_knowledge_unit()

    # First classify it
    with get_cursor() as cur:
        cur.execute(
            """UPDATE knowledge_units SET classification = %s, consumer_essential = true
               WHERE id = %s""",
            (json.dumps({"types": ["technical"], "sectors": ["toys"], "actors": ["manufacturer"], "scope": "sector-specific"}), unit_id),
        )

    # Override via API
    resp = client.post(
        "/admin/classification/override",
        json={
            "unit_id": unit_id,
            "overrides": {
                "sectors": ["toys", "electronics"],
                "consumer_essential": False,
            },
        },
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200

    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM knowledge_units WHERE id = %s", (unit_id,))
        unit = cur.fetchone()
        assert unit["admin_overrides"]["sectors"] == ["toys", "electronics"]
        assert unit["consumer_essential"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd api && python -m pytest tests/test_classification.py -v`
Expected: FAIL

- [ ] **Step 3: Create classification __init__.py**

```python
# api/modules/classification/__init__.py
# (empty)
```

- [ ] **Step 4: Implement classifier.py**

```python
# api/modules/classification/classifier.py
import json
import anthropic
from api.config import settings
from api.db import get_cursor

CLASSIFICATION_PROMPT = """You are an expert in EU/Maltese regulatory frameworks under the MCCAA.

Classify this knowledge unit:

Title: {title}
Content: {content}

Determine:
1. types: Which MCCAA areas apply? Options: "technical" (technical regulations & product safety), "standardisation", "consumer" (consumer affairs), "competition". Can be multiple.
2. sectors: Which product/industry sectors? E.g., "toys", "electronics", "food", "pressure-vessels", "lifts". Can be multiple.
3. actors: Which supply chain actors does this apply to? Options: "manufacturer", "importer", "distributor", "retailer", "online-retailer", "fulfilment-service-provider", "authorised-representative", "conformity-assessment-body", "notified-body". Can be multiple.
4. scope: "sector-specific" (applies to specific sectors), "cross-cutting" (applies across some sectors, e.g. CE marking), or "universal" (applies to all sectors, e.g. market surveillance).
5. consumer_essential: Would a consumer need to know this to protect their interests? true/false.
6. confidence: How confident are you in this classification? 0.0 to 1.0.

Return ONLY a JSON object with these fields. Example:
{{"types": ["technical"], "sectors": ["toys"], "actors": ["manufacturer", "importer"], "scope": "sector-specific", "consumer_essential": true, "confidence": 0.85}}"""


def run_classification(unit_id: int) -> dict:
    """Classify a knowledge unit using AI."""
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM knowledge_units WHERE id = %s", (unit_id,))
        unit = cur.fetchone()

    if not unit:
        raise ValueError(f"Knowledge unit {unit_id} not found")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": CLASSIFICATION_PROMPT.format(
                title=unit["title"], content=unit["content"][:4000]
            ),
        }],
    )

    text = response.content[0].text.strip()
    start = text.index("{")
    end = text.rindex("}") + 1
    classification_data = json.loads(text[start:end])

    consumer_essential = classification_data.pop("consumer_essential", None)
    confidence = classification_data.pop("confidence", None)
    classification = {
        "types": classification_data.get("types", []),
        "sectors": classification_data.get("sectors", []),
        "actors": classification_data.get("actors", []),
        "scope": classification_data.get("scope", "sector-specific"),
    }

    with get_cursor() as cur:
        cur.execute(
            """UPDATE knowledge_units
               SET classification = %s, ai_confidence = %s, consumer_essential = %s, updated_at = NOW()
               WHERE id = %s""",
            (json.dumps(classification), confidence, consumer_essential, unit_id),
        )

    # Pipeline automation (spec 3.5): after classification, trigger article generation or cascade
    _trigger_post_classification(unit_id, classification, consumer_essential)

    return {
        "unit_id": unit_id,
        "classification": classification,
        "consumer_essential": consumer_essential,
        "confidence": confidence,
    }


def _trigger_post_classification(unit_id: int, classification: dict, consumer_essential: bool):
    """After classification, check if articles need generating or updating."""
    from api.queue import enqueue_task
    from api.modules.articles.cascade import trigger_cascade

    sectors = classification.get("sectors", [])
    scope = classification.get("scope", "sector-specific")

    # Check if any existing articles reference this unit or its sector
    with get_cursor(commit=False) as cur:
        for sector in sectors:
            # Check for existing business article
            cur.execute(
                "SELECT id FROM articles WHERE sector = %s AND audience = 'business' AND status != 'archived' LIMIT 1",
                (sector,),
            )
            if cur.fetchone():
                # Existing article — trigger cascade update
                trigger_cascade(unit_id)
            else:
                # No article yet — generate new one
                enqueue_task("generate_article", {
                    "sector": sector, "scope": scope, "audience": "business",
                })

            # Check for consumer article if consumer-essential
            if consumer_essential:
                cur.execute(
                    "SELECT id FROM articles WHERE sector = %s AND audience = 'consumer' AND status != 'archived' LIMIT 1",
                    (sector,),
                )
                if cur.fetchone():
                    trigger_cascade(unit_id)
                else:
                    enqueue_task("generate_article", {
                        "sector": sector, "scope": scope, "audience": "consumer",
                    })
```

- [ ] **Step 5: Implement classification router**

```python
# api/modules/classification/router.py
import json
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from api.config import settings
from api.db import get_cursor

router = APIRouter(prefix="/admin/classification", tags=["classification"])


def require_admin(x_admin_key: str = Header(None)):
    if x_admin_key != settings.admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")


class OverrideRequest(BaseModel):
    unit_id: int
    overrides: dict  # Can contain any classification fields + consumer_essential


@router.post("/override")
def override_classification(body: OverrideRequest, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)

    with get_cursor() as cur:
        cur.execute("SELECT * FROM knowledge_units WHERE id = %s", (body.unit_id,))
        unit = cur.fetchone()
        if not unit:
            raise HTTPException(status_code=404, detail="Knowledge unit not found")

        # Merge overrides into existing classification
        existing_classification = unit["classification"] or {}
        existing_overrides = unit["admin_overrides"] or {}

        consumer_essential = body.overrides.pop("consumer_essential", None)

        # Update admin_overrides (merge with existing)
        new_overrides = {**existing_overrides, **body.overrides}

        # Update classification with overrides
        updated_classification = {**existing_classification, **body.overrides}

        updates = [
            "classification = %s",
            "admin_overrides = %s",
            "updated_at = NOW()",
        ]
        values = [json.dumps(updated_classification), json.dumps(new_overrides)]

        if consumer_essential is not None:
            updates.append("consumer_essential = %s")
            values.append(consumer_essential)

        values.append(body.unit_id)
        cur.execute(
            f"UPDATE knowledge_units SET {', '.join(updates)} WHERE id = %s RETURNING *",
            values,
        )
        return dict(cur.fetchone())
```

- [ ] **Step 6: Mount classification router in main.py**

Add after the ingestion router mount in `api/main.py`:

```python
from api.modules.classification.router import router as classification_router
app.include_router(classification_router)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/test_classification.py -v`
Expected: 2 tests PASS

- [ ] **Step 8: Commit**

```bash
git add api/modules/classification/ api/tests/test_classification.py api/main.py
git commit -m "feat: add classification module — AI classification and admin overrides"
```

---

### Task 8: Articles Module — CRUD & Approval

**Files:**
- Create: `api/modules/articles/__init__.py`
- Create: `api/modules/articles/router.py`
- Create: `api/modules/articles/diff.py`
- Create: `api/tests/test_articles.py`

- [ ] **Step 1: Write failing tests**

```python
# api/tests/test_articles.py
import json
from fastapi.testclient import TestClient
from api.db import get_cursor


def get_client():
    from api.main import app
    return TestClient(app)


ADMIN_HEADERS = {"X-Admin-Key": "mccaa-admin-2026"}


def _create_article(**kwargs) -> dict:
    defaults = {
        "title": "Toy Safety in Malta",
        "slug": "toy-safety-malta",
        "sector": "toys",
        "scope": "sector-specific",
        "audience": "business",
        "html_content": "<h2>Toy Safety</h2><p>Content here</p>",
        "tag_map": {"section-1": {"topics": ["technical"], "actors": ["manufacturer"]}},
    }
    defaults.update(kwargs)
    client = get_client()
    resp = client.post("/admin/articles", json=defaults, headers=ADMIN_HEADERS)
    return resp.json()


def test_create_article():
    article = _create_article(slug="test-create-article")
    assert article["title"] == "Toy Safety in Malta"
    assert article["status"] == "draft"
    assert article["audience"] == "business"


def test_list_articles():
    _create_article(slug="test-list-1")
    client = get_client()
    resp = client.get("/admin/articles", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_approve_article():
    article = _create_article(slug="test-approve")
    client = get_client()
    resp = client.post(
        f"/admin/articles/{article['id']}/approve",
        json={"approved_by": "admin@mccaa.org.mt"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"
    assert resp.json()["approved_by"] == "admin@mccaa.org.mt"


def test_approve_update_pending_article():
    # Create and publish original
    original = _create_article(slug="test-approve-update")
    client = get_client()
    client.post(
        f"/admin/articles/{original['id']}/approve",
        json={"approved_by": "admin"},
        headers=ADMIN_HEADERS,
    )

    # Create updated version
    updated = _create_article(
        slug="test-approve-update-v2",
        title="Toy Safety in Malta (Updated)",
        html_content="<h2>Updated</h2><p>New content</p>",
        status="update_pending",
        published_version_id=original["id"],
    )

    # Approve the update
    resp = client.post(
        f"/admin/articles/{updated['id']}/approve",
        json={"approved_by": "admin"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"


def test_reject_update():
    original = _create_article(slug="test-reject-update")
    client = get_client()
    client.post(
        f"/admin/articles/{original['id']}/approve",
        json={"approved_by": "admin"},
        headers=ADMIN_HEADERS,
    )

    updated = _create_article(
        slug="test-reject-update-v2",
        status="update_pending",
        published_version_id=original["id"],
    )

    resp = client.post(
        f"/admin/articles/{updated['id']}/reject",
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


def test_edit_article():
    article = _create_article(slug="test-edit")
    client = get_client()
    resp = client.put(
        f"/admin/articles/{article['id']}",
        json={"html_content": "<h2>Edited</h2><p>Admin edit</p>"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert "Edited" in resp.json()["html_content"]


def test_delete_article():
    article = _create_article(slug="test-delete")
    client = get_client()
    resp = client.delete(f"/admin/articles/{article['id']}", headers=ADMIN_HEADERS)
    assert resp.status_code == 204
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd api && python -m pytest tests/test_articles.py -v`
Expected: FAIL

- [ ] **Step 3: Create articles __init__.py**

```python
# api/modules/articles/__init__.py
# (empty)
```

- [ ] **Step 4: Implement articles router**

```python
# api/modules/articles/router.py
import json
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from api.config import settings
from api.db import get_cursor

router = APIRouter(prefix="/admin/articles", tags=["articles"])


def require_admin(x_admin_key: str = Header(None)):
    if x_admin_key != settings.admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")


class ArticleCreate(BaseModel):
    title: str
    slug: str
    sector: Optional[str] = None
    scope: str = "sector-specific"
    audience: str = "business"
    html_content: str = ""
    tag_map: dict = {}
    status: str = "draft"
    skills_used: list[str] = []
    source_knowledge_unit_ids: list[int] = []
    cross_cutting_summaries: list = []
    published_version_id: Optional[int] = None


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    html_content: Optional[str] = None
    tag_map: Optional[dict] = None
    sector: Optional[str] = None
    scope: Optional[str] = None
    audience: Optional[str] = None
    cross_cutting_summaries: Optional[list] = None


class ApproveRequest(BaseModel):
    approved_by: str


@router.post("", status_code=201)
def create_article(body: ArticleCreate, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO articles (title, slug, sector, scope, audience, html_content,
                   tag_map, status, skills_used, source_knowledge_unit_ids,
                   cross_cutting_summaries, published_version_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING *""",
            (body.title, body.slug, body.sector, body.scope, body.audience,
             body.html_content, json.dumps(body.tag_map), body.status,
             body.skills_used, body.source_knowledge_unit_ids,
             json.dumps(body.cross_cutting_summaries), body.published_version_id),
        )
        return dict(cur.fetchone())


@router.get("")
def list_articles(
    status: Optional[str] = None,
    audience: Optional[str] = None,
    x_admin_key: str = Header(None),
):
    require_admin(x_admin_key)
    query = "SELECT * FROM articles WHERE 1=1"
    params = []
    if status:
        query += " AND status = %s"
        params.append(status)
    if audience:
        query += " AND audience = %s"
        params.append(audience)
    query += " ORDER BY updated_at DESC"

    with get_cursor(commit=False) as cur:
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


@router.get("/{article_id}")
def get_article(article_id: int, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM articles WHERE id = %s", (article_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        return dict(row)


@router.put("/{article_id}")
def update_article(article_id: int, body: ArticleUpdate, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clauses = []
    values = []
    for key, val in updates.items():
        if key in ("tag_map", "cross_cutting_summaries"):
            set_clauses.append(f"{key} = %s")
            values.append(json.dumps(val))
        else:
            set_clauses.append(f"{key} = %s")
            values.append(val)
    set_clauses.append("updated_at = NOW()")
    values.append(article_id)

    with get_cursor() as cur:
        cur.execute(
            f"UPDATE articles SET {', '.join(set_clauses)} WHERE id = %s RETURNING *",
            values,
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        return dict(row)


@router.post("/{article_id}/approve")
def approve_article(article_id: int, body: ApproveRequest, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor() as cur:
        cur.execute("SELECT * FROM articles WHERE id = %s", (article_id,))
        article = cur.fetchone()
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        # If this is an update to a published article, archive the old version
        if article["published_version_id"]:
            cur.execute(
                "UPDATE articles SET status = 'archived' WHERE id = %s",
                (article["published_version_id"],),
            )

        cur.execute(
            """UPDATE articles SET status = 'published', approved_at = NOW(),
                   approved_by = %s, updated_at = NOW()
               WHERE id = %s RETURNING *""",
            (body.approved_by, article_id),
        )
        return dict(cur.fetchone())


@router.post("/{article_id}/reject")
def reject_article(article_id: int, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor() as cur:
        cur.execute(
            "UPDATE articles SET status = 'rejected', updated_at = NOW() WHERE id = %s RETURNING *",
            (article_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        return dict(row)


@router.delete("/{article_id}", status_code=204)
def delete_article(article_id: int, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor() as cur:
        cur.execute("DELETE FROM articles WHERE id = %s", (article_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Article not found")
```

- [ ] **Step 5: Implement diff.py**

```python
# api/modules/articles/diff.py
from difflib import HtmlDiff


def generate_html_diff(old_html: str, new_html: str) -> str:
    """Generate an HTML diff between old and new article content."""
    differ = HtmlDiff()
    old_lines = old_html.splitlines()
    new_lines = new_html.splitlines()
    return differ.make_table(
        old_lines, new_lines,
        fromdesc="Published Version",
        todesc="New Version",
        context=True,
        numlines=3,
    )
```

- [ ] **Step 6: Mount articles router in main.py**

Add after the classification router mount in `api/main.py`:

```python
from api.modules.articles.router import router as articles_router
app.include_router(articles_router)
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/test_articles.py -v`
Expected: 7 tests PASS

- [ ] **Step 8: Commit**

```bash
git add api/modules/articles/ api/tests/test_articles.py api/main.py
git commit -m "feat: add articles module — CRUD, approval workflow, diff generation"
```

---

### Task 9: Articles Module — AI Generation

**Files:**
- Create: `api/modules/articles/generator.py`
- Add tests to: `api/tests/test_articles.py`

- [ ] **Step 1: Write failing tests for article generation**

Append to `api/tests/test_articles.py`:

```python
from unittest.mock import patch, MagicMock

MOCK_GENERATION_RESPONSE = json.dumps({
    "title": "Toy Safety Compliance in Malta",
    "html_content": '<div id="sec-technical" data-topics="technical" data-actors="manufacturer,importer"><h2>Technical Regulations</h2><p>Content...</p></div>',
    "tag_map": {
        "sec-technical": {"topics": ["technical"], "actors": ["manufacturer", "importer"]},
    },
    "cross_cutting_summaries": [
        {
            "topic": "CE Marking",
            "scope": "cross-cutting",
            "summary": "CE marking is mandatory for toys placed on the EU market.",
            "article_slug": "ce-marking",
        }
    ],
})


@patch("api.modules.articles.generator.select_skills_for_article")
@patch("api.modules.articles.generator.anthropic")
def test_generate_business_article(mock_anthropic, mock_skills):
    mock_skills.return_value = []
    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=MOCK_GENERATION_RESPONSE)]
    )

    # Seed a knowledge unit
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO knowledge_units (title, content, classification)
               VALUES ('Toy Directive', 'Content...', %s) RETURNING id""",
            (json.dumps({"types": ["technical"], "sectors": ["toys"], "actors": ["manufacturer"], "scope": "sector-specific"}),),
        )
        unit_id = cur.fetchone()["id"]

    from api.modules.articles.generator import generate_article
    result = generate_article(
        sector="toys", scope="sector-specific", audience="business"
    )

    assert result["title"] == "Toy Safety Compliance in Malta"
    assert "sec-technical" in result["tag_map"]
    assert len(result["cross_cutting_summaries"]) == 1

    # Verify article was saved as draft
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM articles WHERE slug = %s", (result["slug"],))
        article = cur.fetchone()
        assert article is not None
        assert article["status"] == "draft"
        assert article["audience"] == "business"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd api && python -m pytest tests/test_articles.py::test_generate_business_article -v`
Expected: FAIL

- [ ] **Step 3: Implement generator.py**

```python
# api/modules/articles/generator.py
import json
import re
import anthropic
from api.config import settings
from api.db import get_cursor
from api.modules.skills.selector import select_skills_for_article

BUSINESS_ARTICLE_PROMPT = """You are an expert regulatory content writer for the MCCAA (Malta Competition and Consumer Affairs Authority).

Generate a comprehensive compliance article for the "{sector}" sector targeted at business users.

Source material (knowledge units):
{knowledge_units}

{skills_section}

Requirements:
1. Write in professional, authoritative tone
2. Structure the article with sections tagged by topic and actor
3. Each section must have a unique DOM ID (e.g., "sec-technical-manufacturer")
4. Tag each section with applicable topics: "technical" (technical regulations & product safety), "standardisation", "consumer" (consumer affairs), "competition"
5. Tag each section with applicable actors: "manufacturer", "importer", "distributor", "retailer", "online-retailer", "fulfilment-service-provider", "authorised-representative", "conformity-assessment-body", "notified-body"
6. Generate contextual summaries (2-3 sentences each) for relevant cross-cutting and universal topics
7. Each cross-cutting summary should reference the full article slug

{admin_edits_section}

Return ONLY a JSON object:
{{
  "title": "Article title",
  "html_content": "<div id='sec-...' data-topics='...' data-actors='...'>...</div>",
  "tag_map": {{"sec-id": {{"topics": [...], "actors": [...]}}}},
  "cross_cutting_summaries": [{{"topic": "...", "scope": "cross-cutting|universal", "summary": "...", "article_slug": "..."}}]
}}"""

CONSUMER_ARTICLE_PROMPT = """You are writing a consumer-friendly guide for the MCCAA (Malta Competition and Consumer Affairs Authority).

Generate a plain-language article about "{sector}" for consumers.

Source material (only consumer-essential topics):
{knowledge_units}

{skills_section}

Requirements:
1. Use simple, plain language — no jargon, no legal references unless essential
2. Focus on what consumers NEED to know: their rights, what to look for, what to do if something goes wrong
3. Structure with clear sections tagged by topic only (no actor tags — consumers don't think in supply chain terms)
4. Each section must have a unique DOM ID
5. Weave cross-cutting and universal content directly into the article (self-contained, no separate links)
6. Keep it concise — fewer, broader sections

{admin_edits_section}

Return ONLY a JSON object:
{{
  "title": "Article title",
  "html_content": "<div id='sec-...' data-topics='...'>...</div>",
  "tag_map": {{"sec-id": {{"topics": [...]}}}},
  "cross_cutting_summaries": []
}}"""


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    return text[:80]


def _gather_knowledge_units(sector: str, scope: str, audience: str) -> list[dict]:
    """Gather relevant knowledge units for article generation."""
    with get_cursor(commit=False) as cur:
        if audience == "consumer":
            # Only consumer-essential units
            cur.execute(
                """SELECT * FROM knowledge_units
                   WHERE consumer_essential = true
                   AND (classification->>'sectors')::jsonb ? %s
                   ORDER BY updated_at DESC""",
                (sector,),
            )
            units = [dict(r) for r in cur.fetchall()]
            # Also include universal consumer-essential units
            cur.execute(
                """SELECT * FROM knowledge_units
                   WHERE consumer_essential = true
                   AND classification->>'scope' = 'universal'""",
            )
            units += [dict(r) for r in cur.fetchall()]
        else:
            # Business: sector-specific units
            cur.execute(
                """SELECT * FROM knowledge_units
                   WHERE (classification->>'sectors')::jsonb ? %s
                   ORDER BY updated_at DESC""",
                (sector,),
            )
            units = [dict(r) for r in cur.fetchall()]
            # Cross-cutting and universal units
            cur.execute(
                """SELECT * FROM knowledge_units
                   WHERE classification->>'scope' IN ('cross-cutting', 'universal')""",
            )
            units += [dict(r) for r in cur.fetchall()]

    # Deduplicate by id
    seen = set()
    unique = []
    for u in units:
        if u["id"] not in seen:
            seen.add(u["id"])
            unique.append(u)
    return unique


def generate_article(sector: str, scope: str, audience: str, admin_edits: list = None) -> dict:
    """Generate an article using Sonnet with relevant skills."""
    units = _gather_knowledge_units(sector, scope, audience)
    skills = select_skills_for_article(sector, scope, audience)

    # Format knowledge units for prompt
    units_text = "\n\n".join(
        f"[Unit {u['id']}] {u['title']}\nScope: {u['classification'].get('scope', 'unknown')}\n{u['content'][:3000]}"
        for u in units
    )

    # Format skills section
    skills_section = ""
    if skills:
        skills_text = "\n\n".join(
            f"### Skill: {s['name']}\n{s['skill_content']}"
            for s in skills
        )
        skills_section = f"Apply these writing skills:\n{skills_text}"

    # Format admin edits section
    admin_edits_section = ""
    if admin_edits:
        edits_text = "\n".join(
            f"- Section '{e['section_id']}': preserve this admin edit: {e['edited_html'][:500]}"
            for e in admin_edits
        )
        admin_edits_section = f"IMPORTANT — Preserve these admin edits:\n{edits_text}"

    prompt_template = CONSUMER_ARTICLE_PROMPT if audience == "consumer" else BUSINESS_ARTICLE_PROMPT
    prompt = prompt_template.format(
        sector=sector,
        knowledge_units=units_text,
        skills_section=skills_section,
        admin_edits_section=admin_edits_section,
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    start = text.index("{")
    end = text.rindex("}") + 1
    article_data = json.loads(text[start:end])

    slug = _slugify(article_data["title"])
    unit_ids = [u["id"] for u in units]
    skill_names = [s["name"] for s in skills]

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO articles (title, slug, sector, scope, audience, html_content,
                   tag_map, status, skills_used, source_knowledge_unit_ids, cross_cutting_summaries)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'draft', %s, %s, %s)
               RETURNING *""",
            (article_data["title"], slug, sector, scope, audience,
             article_data["html_content"], json.dumps(article_data["tag_map"]),
             skill_names, unit_ids, json.dumps(article_data.get("cross_cutting_summaries", []))),
        )
        article = dict(cur.fetchone())

    article["tag_map"] = article_data["tag_map"]
    article["cross_cutting_summaries"] = article_data.get("cross_cutting_summaries", [])
    return article
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/test_articles.py -v`
Expected: 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add api/modules/articles/generator.py api/tests/test_articles.py
git commit -m "feat: add AI article generation — business and consumer, with skill integration"
```

---

### Task 10: Articles Module — Cascade Updates

**Files:**
- Create: `api/modules/articles/cascade.py`
- Create: `api/tests/test_cascade.py`

- [ ] **Step 1: Write failing tests**

```python
# api/tests/test_cascade.py
import json
from unittest.mock import patch
from api.db import get_cursor
from api.queue import enqueue_task


def _seed_article(slug: str, sector: str, scope: str, unit_ids: list[int], status: str = "published") -> int:
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO articles (title, slug, sector, scope, audience, html_content,
                   status, source_knowledge_unit_ids)
               VALUES (%s, %s, %s, %s, 'business', '<p>content</p>', %s, %s)
               RETURNING id""",
            (f"Article for {sector}", slug, sector, scope, status, unit_ids),
        )
        return cur.fetchone()["id"]


def _seed_knowledge_unit(title: str, sectors: list[str], scope: str) -> int:
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO knowledge_units (title, content, classification)
               VALUES (%s, 'content', %s) RETURNING id""",
            (title, json.dumps({"types": ["technical"], "sectors": sectors, "actors": [], "scope": scope})),
        )
        return cur.fetchone()["id"]


@patch("api.modules.articles.cascade.enqueue_task")
def test_cascade_detects_affected_articles(mock_enqueue):
    unit_id = _seed_knowledge_unit("Toy Safety", ["toys"], "sector-specific")
    article_id = _seed_article("cascade-test-1", "toys", "sector-specific", [unit_id])

    from api.modules.articles.cascade import trigger_cascade
    affected = trigger_cascade(unit_id)

    assert article_id in [a["id"] for a in affected]
    mock_enqueue.assert_called()
    call_args = mock_enqueue.call_args_list
    assert any(c[0][0] == "update_article" for c in call_args)


@patch("api.modules.articles.cascade.enqueue_task")
def test_cascade_sets_update_pending_on_published(mock_enqueue):
    unit_id = _seed_knowledge_unit("CE Marking", ["toys"], "cross-cutting")
    article_id = _seed_article("cascade-test-2", "toys", "sector-specific", [unit_id], status="published")

    from api.modules.articles.cascade import trigger_cascade
    trigger_cascade(unit_id)

    with get_cursor(commit=False) as cur:
        cur.execute("SELECT status FROM articles WHERE id = %s", (article_id,))
        assert cur.fetchone()["status"] == "update_pending"


@patch("api.modules.articles.cascade.enqueue_task")
def test_cascade_replaces_draft(mock_enqueue):
    unit_id = _seed_knowledge_unit("Competition Rules", ["toys"], "universal")
    article_id = _seed_article("cascade-test-3", "toys", "sector-specific", [unit_id], status="draft")

    from api.modules.articles.cascade import trigger_cascade
    trigger_cascade(unit_id)

    # Draft articles should be directly updated, not set to update_pending
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT status FROM articles WHERE id = %s", (article_id,))
        # Draft remains draft — the update_article task will replace its content
        assert cur.fetchone()["status"] == "draft"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd api && python -m pytest tests/test_cascade.py -v`
Expected: FAIL

- [ ] **Step 3: Implement cascade.py**

```python
# api/modules/articles/cascade.py
import json
from api.db import get_cursor
from api.queue import enqueue_task


def trigger_cascade(knowledge_unit_id: int) -> list[dict]:
    """Find all articles affected by a knowledge unit change and queue updates."""
    with get_cursor(commit=False) as cur:
        # Get the knowledge unit's classification
        cur.execute(
            "SELECT * FROM knowledge_units WHERE id = %s", (knowledge_unit_id,)
        )
        unit = cur.fetchone()
        if not unit:
            return []

        classification = unit["classification"] or {}
        sectors = classification.get("sectors", [])
        scope = classification.get("scope", "sector-specific")

        # Find directly referenced articles
        cur.execute(
            "SELECT * FROM articles WHERE %s = ANY(source_knowledge_unit_ids) AND status != 'archived'",
            (knowledge_unit_id,),
        )
        affected = [dict(r) for r in cur.fetchall()]
        affected_ids = {a["id"] for a in affected}

        # Find articles for the same sectors (they should incorporate new data)
        if sectors:
            placeholders = ",".join(["%s"] * len(sectors))
            cur.execute(
                f"""SELECT * FROM articles
                    WHERE sector IN ({placeholders})
                    AND status NOT IN ('archived', 'rejected')
                    AND id NOT IN (SELECT unnest(%s::int[]))""",
                (*sectors, list(affected_ids) or [0]),
            )
            for row in cur.fetchall():
                row_dict = dict(row)
                if row_dict["id"] not in affected_ids:
                    affected.append(row_dict)
                    affected_ids.add(row_dict["id"])

        # If scope is cross-cutting or universal, find articles with cross_cutting_summaries
        if scope in ("cross-cutting", "universal"):
            cur.execute(
                """SELECT * FROM articles
                   WHERE status NOT IN ('archived', 'rejected')
                   AND id NOT IN (SELECT unnest(%s::int[]))""",
                (list(affected_ids) or [0],),
            )
            for row in cur.fetchall():
                row_dict = dict(row)
                if row_dict["id"] not in affected_ids:
                    affected.append(row_dict)
                    affected_ids.add(row_dict["id"])

    # Update statuses and enqueue regeneration
    with get_cursor() as cur:
        for article in affected:
            if article["status"] == "published":
                cur.execute(
                    "UPDATE articles SET status = 'update_pending' WHERE id = %s",
                    (article["id"],),
                )

            enqueue_task("update_article", {
                "article_id": article["id"],
                "sector": article["sector"],
                "scope": article["scope"],
                "audience": article["audience"],
                "triggered_by_unit_id": knowledge_unit_id,
            })

    return affected
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/test_cascade.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add api/modules/articles/cascade.py api/tests/test_cascade.py
git commit -m "feat: add cascade update logic — detect affected articles and queue re-generation"
```

---

### Task 11: CMS Module — Exclusions & Inquiries

**Files:**
- Create: `api/modules/cms/__init__.py`
- Create: `api/modules/cms/router.py`
- Create: `api/tests/test_cms.py`

- [ ] **Step 1: Write failing tests**

```python
# api/tests/test_cms.py
import json
from fastapi.testclient import TestClient


def get_client():
    from api.main import app
    return TestClient(app)


ADMIN_HEADERS = {"X-Admin-Key": "mccaa-admin-2026"}


# --- Exclusions ---

def test_create_keyword_exclusion():
    client = get_client()
    resp = client.post(
        "/admin/exclusions",
        json={"type": "keyword", "value": "taxation"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    assert resp.json()["value"] == "taxation"


def test_create_rule_exclusion():
    client = get_client()
    resp = client.post(
        "/admin/exclusions",
        json={
            "type": "rule",
            "value": "Financial regulation — anything related to banking, insurance, investment falls under MFSA, not MCCAA",
        },
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    assert resp.json()["type"] == "rule"


def test_list_exclusions():
    client = get_client()
    client.post("/admin/exclusions", json={"type": "keyword", "value": "immigration"}, headers=ADMIN_HEADERS)
    resp = client.get("/admin/exclusions", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_delete_exclusion():
    client = get_client()
    create_resp = client.post("/admin/exclusions", json={"type": "keyword", "value": "delete-me"}, headers=ADMIN_HEADERS)
    exc_id = create_resp.json()["id"]
    resp = client.delete(f"/admin/exclusions/{exc_id}", headers=ADMIN_HEADERS)
    assert resp.status_code == 204


# --- Inquiries ---

def test_list_inquiries():
    client = get_client()
    # First create an inquiry via public endpoint
    client.post("/contact", json={
        "user_name": "John Doe",
        "user_email": "john@example.com",
        "message": "I need help with food safety",
        "search_context": {"query": "food safety", "match": "none"},
        "match_type": "not_covered",
    })
    resp = client.get("/admin/inquiries", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_update_inquiry_status():
    client = get_client()
    client.post("/contact", json={
        "user_name": "Jane",
        "user_email": "jane@example.com",
        "message": "Question about banking",
        "search_context": {},
        "match_type": "not_related",
    })
    inquiries = client.get("/admin/inquiries", headers=ADMIN_HEADERS).json()
    inq_id = inquiries[0]["id"]
    resp = client.put(
        f"/admin/inquiries/{inq_id}",
        json={"status": "reviewed"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "reviewed"


# --- Inquiry Trends ---

def test_inquiry_trends():
    client = get_client()
    # Create several inquiries
    for topic in ["food safety", "food safety", "banking"]:
        client.post("/contact", json={
            "user_name": "User",
            "user_email": "user@example.com",
            "message": f"Question about {topic}",
            "search_context": {"query": topic},
            "match_type": "not_covered",
        })
    resp = client.get("/admin/inquiries/trends", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    # Should return aggregated data
    trends = resp.json()
    assert isinstance(trends, list)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd api && python -m pytest tests/test_cms.py -v`
Expected: FAIL

- [ ] **Step 3: Create cms __init__.py**

```python
# api/modules/cms/__init__.py
# (empty)
```

- [ ] **Step 4: Implement CMS router**

```python
# api/modules/cms/router.py
import json
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from api.config import settings
from api.db import get_cursor

router = APIRouter(tags=["cms"])


def require_admin(x_admin_key: str = Header(None)):
    if x_admin_key != settings.admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")


# --- Exclusions ---

class ExclusionCreate(BaseModel):
    type: str  # "keyword" or "rule"
    value: str


@router.post("/admin/exclusions", status_code=201)
def create_exclusion(body: ExclusionCreate, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO exclusions (type, value) VALUES (%s, %s) RETURNING *",
            (body.type, body.value),
        )
        return dict(cur.fetchone())


@router.get("/admin/exclusions")
def list_exclusions(x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM exclusions ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]


@router.delete("/admin/exclusions/{exclusion_id}", status_code=204)
def delete_exclusion(exclusion_id: int, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor() as cur:
        cur.execute("DELETE FROM exclusions WHERE id = %s", (exclusion_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Exclusion not found")


# --- Contact / Inquiries (public endpoint) ---

class ContactRequest(BaseModel):
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    message: Optional[str] = None
    search_context: dict = {}
    match_type: Optional[str] = None


@router.post("/contact", status_code=201)
def submit_contact(body: ContactRequest):
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO inquiries (user_name, user_email, message, search_context, match_type)
               VALUES (%s, %s, %s, %s, %s) RETURNING *""",
            (body.user_name, body.user_email, body.message,
             json.dumps(body.search_context), body.match_type),
        )
        return dict(cur.fetchone())


# --- Inquiries Admin ---

class InquiryUpdate(BaseModel):
    status: str


@router.get("/admin/inquiries")
def list_inquiries(
    status: Optional[str] = None,
    match_type: Optional[str] = None,
    x_admin_key: str = Header(None),
):
    require_admin(x_admin_key)
    query = "SELECT * FROM inquiries WHERE 1=1"
    params = []
    if status:
        query += " AND status = %s"
        params.append(status)
    if match_type:
        query += " AND match_type = %s"
        params.append(match_type)
    query += " ORDER BY created_at DESC"

    with get_cursor(commit=False) as cur:
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


@router.put("/admin/inquiries/{inquiry_id}")
def update_inquiry(inquiry_id: int, body: InquiryUpdate, x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor() as cur:
        cur.execute(
            "UPDATE inquiries SET status = %s WHERE id = %s RETURNING *",
            (body.status, inquiry_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Inquiry not found")
        return dict(row)


@router.get("/admin/inquiries/trends")
def inquiry_trends(x_admin_key: str = Header(None)):
    require_admin(x_admin_key)
    with get_cursor(commit=False) as cur:
        cur.execute("""
            SELECT
                search_context->>'query' as query,
                match_type,
                COUNT(*) as count,
                MAX(created_at) as last_seen
            FROM inquiries
            WHERE search_context->>'query' IS NOT NULL
            GROUP BY search_context->>'query', match_type
            ORDER BY count DESC
            LIMIT 50
        """)
        return [dict(r) for r in cur.fetchall()]
```

- [ ] **Step 5: Mount CMS router in main.py**

Add after the articles router mount in `api/main.py`:

```python
from api.modules.cms.router import router as cms_router
app.include_router(cms_router)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/test_cms.py -v`
Expected: 7 tests PASS

- [ ] **Step 7: Commit**

```bash
git add api/modules/cms/ api/tests/test_cms.py api/main.py
git commit -m "feat: add CMS module — exclusions CRUD, contact form, inquiries management with trends"
```

---

### Task 12: Public API — Sectors, Articles, Analytics

**Files:**
- Create: `api/modules/public/__init__.py`
- Create: `api/modules/public/router.py`
- Create: `api/tests/test_public.py`

- [ ] **Step 1: Write failing tests**

```python
# api/tests/test_public.py
import json
from fastapi.testclient import TestClient
from api.db import get_cursor


def get_client():
    from api.main import app
    return TestClient(app)


ADMIN_HEADERS = {"X-Admin-Key": "mccaa-admin-2026"}


def _seed_sector_with_article():
    """Create a sector with a published article."""
    client = get_client()
    # Create sector
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO sectors (name, slug, showcase, visit_count)
               VALUES ('Toys', 'toys', true, 50)
               ON CONFLICT (slug) DO UPDATE SET visit_count = 50
               RETURNING id""",
        )
        sector_id = cur.fetchone()["id"]

    # Create and publish article
    article = client.post("/admin/articles", json={
        "title": "Toy Safety in Malta",
        "slug": "toy-safety-public-test",
        "sector": "toys",
        "scope": "sector-specific",
        "audience": "business",
        "html_content": "<h2>Toy Safety</h2><p>Content</p>",
        "tag_map": {"sec-1": {"topics": ["technical"], "actors": ["manufacturer"]}},
    }, headers=ADMIN_HEADERS).json()

    client.post(
        f"/admin/articles/{article['id']}/approve",
        json={"approved_by": "admin"},
        headers=ADMIN_HEADERS,
    )

    # Link article to sector
    with get_cursor() as cur:
        cur.execute(
            "UPDATE sectors SET article_id = %s WHERE id = %s",
            (article["id"], sector_id),
        )

    return article


def test_get_top_sectors():
    _seed_sector_with_article()
    client = get_client()
    resp = client.get("/sectors/top")
    assert resp.status_code == 200
    sectors = resp.json()
    assert len(sectors) <= 3
    assert sectors[0]["name"] == "Toys"


def test_get_all_sectors():
    _seed_sector_with_article()
    client = get_client()
    resp = client.get("/sectors")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_get_published_article_by_slug():
    article = _seed_sector_with_article()
    client = get_client()
    resp = client.get(f"/articles/{article['slug']}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Toy Safety in Malta"
    assert resp.json()["status"] == "published"


def test_get_unpublished_article_returns_404():
    client = get_client()
    # Create but don't approve
    client.post("/admin/articles", json={
        "title": "Draft Article",
        "slug": "draft-only-article",
        "sector": "toys",
        "scope": "sector-specific",
        "html_content": "<p>draft</p>",
    }, headers=ADMIN_HEADERS)

    resp = client.get("/articles/draft-only-article")
    assert resp.status_code == 404


def test_track_visit_increments_count():
    _seed_sector_with_article()
    client = get_client()

    with get_cursor(commit=False) as cur:
        cur.execute("SELECT visit_count FROM sectors WHERE slug = 'toys'")
        before = cur.fetchone()["visit_count"]

    client.post("/track/visit", json={"sector": "toys", "topic": "technical"})

    with get_cursor(commit=False) as cur:
        cur.execute("SELECT visit_count FROM sectors WHERE slug = 'toys'")
        after = cur.fetchone()["visit_count"]

    assert after == before + 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd api && python -m pytest tests/test_public.py -v`
Expected: FAIL

- [ ] **Step 3: Create public __init__.py**

```python
# api/modules/public/__init__.py
# (empty)
```

- [ ] **Step 4: Implement public router**

```python
# api/modules/public/router.py
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from api.db import get_cursor

router = APIRouter(tags=["public"])


@router.get("/sectors/top")
def get_top_sectors():
    """Return top 3 most visited sectors with published articles."""
    with get_cursor(commit=False) as cur:
        cur.execute("""
            SELECT s.*,
                   CASE WHEN s.article_id IS NOT NULL THEN true ELSE false END as has_business,
                   CASE WHEN s.consumer_article_id IS NOT NULL THEN true ELSE false END as has_consumer
            FROM sectors s
            WHERE s.article_id IS NOT NULL OR s.consumer_article_id IS NOT NULL
            ORDER BY s.visit_count DESC
            LIMIT 3
        """)
        return [dict(r) for r in cur.fetchall()]


@router.get("/sectors")
def get_all_sectors():
    """Return all sectors with published articles."""
    with get_cursor(commit=False) as cur:
        cur.execute("""
            SELECT s.*,
                   CASE WHEN s.article_id IS NOT NULL THEN true ELSE false END as has_business,
                   CASE WHEN s.consumer_article_id IS NOT NULL THEN true ELSE false END as has_consumer
            FROM sectors s
            WHERE s.article_id IS NOT NULL OR s.consumer_article_id IS NOT NULL
            ORDER BY s.sort_order, s.name
        """)
        return [dict(r) for r in cur.fetchall()]


@router.get("/articles/{slug}")
def get_article_by_slug(slug: str):
    """Return a published article by slug."""
    with get_cursor(commit=False) as cur:
        cur.execute(
            "SELECT * FROM articles WHERE slug = %s AND status IN ('published', 'update_pending')",
            (slug,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        return dict(row)


class VisitTrack(BaseModel):
    sector: str
    topic: Optional[str] = None


@router.post("/track/visit", status_code=200)
def track_visit(body: VisitTrack):
    """Track a sector/topic visit for analytics."""
    with get_cursor() as cur:
        # Increment sector visit count
        cur.execute(
            "UPDATE sectors SET visit_count = visit_count + 1 WHERE slug = %s",
            (body.sector,),
        )
        # Upsert topic analytics
        if body.topic:
            cur.execute(
                """INSERT INTO topic_analytics (topic, sector, visit_count, last_visited_at)
                   VALUES (%s, %s, 1, NOW())
                   ON CONFLICT (topic, sector) DO UPDATE
                   SET visit_count = topic_analytics.visit_count + 1, last_visited_at = NOW()""",
                (body.topic, body.sector),
            )
    return {"tracked": True}
```

- [ ] **Step 5: Mount public router in main.py**

Add after the CMS router mount in `api/main.py`:

```python
from api.modules.public.router import router as public_router
app.include_router(public_router)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/test_public.py -v`
Expected: 5 tests PASS

Note: The `track_visit` test may fail due to a missing unique constraint on `topic_analytics(topic, sector)`. If so, add to `db.py` SCHEMA_SQL:
```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_topic_analytics_unique ON topic_analytics(topic, sector);
```

- [ ] **Step 7: Commit**

```bash
git add api/modules/public/ api/tests/test_public.py api/main.py
git commit -m "feat: add public API — sectors, articles, visit tracking"
```

---

### Task 13: Public API — Search & Intent Matching

**Files:**
- Create: `api/modules/public/search.py`
- Create: `api/modules/public/conversation.py`
- Create: `api/tests/test_search.py`

- [ ] **Step 1: Write failing tests**

```python
# api/tests/test_search.py
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.db import get_cursor


def get_client():
    from api.main import app
    return TestClient(app)


ADMIN_HEADERS = {"X-Admin-Key": "mccaa-admin-2026"}


def _seed_published_article():
    client = get_client()
    article = client.post("/admin/articles", json={
        "title": "Toy Safety Regulations",
        "slug": "toy-safety-search-test",
        "sector": "toys",
        "scope": "sector-specific",
        "audience": "business",
        "html_content": "<h2>Toy Safety</h2><p>Toys must comply with EN 71</p>",
        "tag_map": {},
    }, headers=ADMIN_HEADERS).json()
    client.post(
        f"/admin/articles/{article['id']}/approve",
        json={"approved_by": "admin"},
        headers=ADMIN_HEADERS,
    )
    return article


def _seed_exclusion():
    client = get_client()
    client.post("/admin/exclusions", json={"type": "keyword", "value": "taxation"}, headers=ADMIN_HEADERS)
    client.post(
        "/admin/exclusions",
        json={"type": "rule", "value": "Financial regulation — banking, insurance, investment falls under MFSA, not MCCAA"},
        headers=ADMIN_HEADERS,
    )


@patch("api.modules.public.search.get_embedding")
@patch("api.modules.public.search.anthropic")
def test_search_strong_match(mock_anthropic, mock_embedding):
    _seed_published_article()
    mock_embedding.return_value = [0.1] * 1536

    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps({
            "match_type": "strong_match",
            "article_slug": "toy-safety-search-test",
            "message": None,
            "follow_up_question": None,
        }))]
    )

    client = get_client()
    resp = client.post("/search", json={"query": "toy safety regulations"})
    assert resp.status_code == 200
    assert resp.json()["match_type"] == "strong_match"
    assert resp.json()["article_slug"] == "toy-safety-search-test"


@patch("api.modules.public.search.get_embedding")
@patch("api.modules.public.search.anthropic")
def test_search_not_related(mock_anthropic, mock_embedding):
    _seed_exclusion()
    mock_embedding.return_value = [0.1] * 1536

    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps({
            "match_type": "not_related",
            "article_slug": None,
            "message": "This area most probably does not fall under the remit of the MCCAA.",
            "follow_up_question": None,
        }))]
    )

    client = get_client()
    resp = client.post("/search", json={"query": "how do I pay less income tax"})
    assert resp.status_code == 200
    assert resp.json()["match_type"] == "not_related"


@patch("api.modules.public.search.get_embedding")
@patch("api.modules.public.search.anthropic")
def test_search_ambiguous_returns_follow_up(mock_anthropic, mock_embedding):
    mock_embedding.return_value = [0.1] * 1536

    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps({
            "match_type": "ambiguous",
            "article_slug": None,
            "message": None,
            "follow_up_question": "Are you asking about toy safety as a manufacturer or as a consumer?",
        }))]
    )

    client = get_client()
    resp = client.post("/search", json={"query": "toys"})
    assert resp.status_code == 200
    assert resp.json()["match_type"] == "ambiguous"
    assert resp.json()["follow_up_question"] is not None


def test_conversation_follow_up():
    """Test that follow-up messages include conversation history."""
    client = get_client()
    # First message
    with patch("api.modules.public.search.get_embedding", return_value=[0.1]*1536), \
         patch("api.modules.public.search.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps({
                "match_type": "ambiguous",
                "article_slug": None,
                "message": None,
                "follow_up_question": "Are you a business or consumer?",
            }))]
        )
        resp1 = client.post("/search", json={
            "query": "product safety",
            "conversation_id": "conv-123",
        })
        assert resp1.json()["match_type"] == "ambiguous"

    # Follow-up
    with patch("api.modules.public.search.get_embedding", return_value=[0.1]*1536), \
         patch("api.modules.public.search.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps({
                "match_type": "strong_match",
                "article_slug": "toy-safety-search-test",
                "message": None,
                "follow_up_question": None,
            }))]
        )
        resp2 = client.post("/search", json={
            "query": "I'm a manufacturer of toys",
            "conversation_id": "conv-123",
        })
        assert resp2.json()["match_type"] == "strong_match"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd api && python -m pytest tests/test_search.py -v`
Expected: FAIL

- [ ] **Step 3: Implement search.py**

```python
# api/modules/public/search.py
import json
import anthropic
from openai import OpenAI
from api.config import settings
from api.db import get_cursor


def get_embedding(text: str) -> list[float]:
    """Generate embedding using OpenAI."""
    client = OpenAI(api_key=settings.openai_api_key or settings.openrouter_api_key,
                    base_url="https://api.openai.com/v1" if settings.openai_api_key else "https://openrouter.ai/api/v1")
    response = client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding


def vector_search(query_embedding: list[float], limit: int = 5) -> list[dict]:
    """Find articles by vector similarity."""
    with get_cursor(commit=False) as cur:
        cur.execute(
            """SELECT id, title, slug, sector, scope, audience,
                      1 - (embedding <=> %s::vector) as similarity
               FROM knowledge_units
               WHERE embedding IS NOT NULL
               ORDER BY embedding <=> %s::vector
               LIMIT %s""",
            (query_embedding, query_embedding, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def get_exclusions() -> dict:
    """Load all exclusions."""
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM exclusions")
        rows = cur.fetchall()
    return {
        "keywords": [r["value"] for r in rows if r["type"] == "keyword"],
        "rules": [r["value"] for r in rows if r["type"] == "rule"],
    }


def get_published_articles_summary() -> list[dict]:
    """Get summary of all published articles for intent matching."""
    with get_cursor(commit=False) as cur:
        cur.execute(
            """SELECT slug, title, sector, scope, audience, tag_map
               FROM articles WHERE status IN ('published', 'update_pending')
               ORDER BY sector, audience"""
        )
        return [dict(r) for r in cur.fetchall()]


SEARCH_INTENT_PROMPT = """You are the MCCAA's knowledge base search assistant.

The user is searching for: "{query}"

{conversation_history}

Available published articles:
{articles_summary}

Exclusion keywords (topics NOT under MCCAA remit):
{exclusion_keywords}

Exclusion rules (detailed reasoning):
{exclusion_rules}

Determine the best match. Return ONLY a JSON object:
{{
  "match_type": "strong_match" | "ambiguous" | "not_covered" | "partially_related" | "not_related",
  "article_slug": "slug-if-strong-match" or null,
  "message": "message to show user if not_covered/partially_related/not_related" or null,
  "follow_up_question": "clarifying question if ambiguous" or null
}}

Rules:
- "strong_match": clearly matches one published article
- "ambiguous": could match multiple articles or needs clarification (max 3 follow-ups per conversation)
- "not_covered": topic is within MCCAA remit but no article exists yet
- "partially_related": topic may be within MCCAA remit but uncertain
- "not_related": topic clearly outside MCCAA remit (matches exclusions)"""


def search_intent(query: str, conversation_history: list[dict] = None) -> dict:
    """Match user query to articles, exclusions, or follow-up questions."""
    articles = get_published_articles_summary()
    exclusions = get_exclusions()

    articles_text = "\n".join(
        f"- [{a['slug']}] {a['title']} (sector: {a['sector']}, audience: {a['audience']})"
        for a in articles
    )

    history_text = ""
    if conversation_history:
        history_text = "Conversation so far:\n" + "\n".join(
            f"- {'User' if m['role'] == 'user' else 'System'}: {m['content']}"
            for m in conversation_history
        )

    prompt = SEARCH_INTENT_PROMPT.format(
        query=query,
        conversation_history=history_text,
        articles_summary=articles_text or "(no articles published yet)",
        exclusion_keywords=", ".join(exclusions["keywords"]) or "(none)",
        exclusion_rules="\n".join(f"- {r}" for r in exclusions["rules"]) or "(none)",
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    start = text.index("{")
    end = text.rindex("}") + 1
    return json.loads(text[start:end])
```

- [ ] **Step 4: Implement conversation.py**

```python
# api/modules/public/conversation.py
from typing import Optional

# In-memory conversation store (for demo; production would use Redis or DB)
_conversations: dict[str, list[dict]] = {}

MAX_FOLLOW_UPS = 3


def get_conversation(conversation_id: str) -> list[dict]:
    """Get conversation history."""
    return _conversations.get(conversation_id, [])


def add_message(conversation_id: str, role: str, content: str):
    """Add a message to conversation history."""
    if conversation_id not in _conversations:
        _conversations[conversation_id] = []
    _conversations[conversation_id].append({"role": role, "content": content})


def conversation_length(conversation_id: str) -> int:
    """Get number of exchanges in a conversation."""
    history = _conversations.get(conversation_id, [])
    return len([m for m in history if m["role"] == "user"])


def clear_conversation(conversation_id: str):
    """Clear a conversation."""
    _conversations.pop(conversation_id, None)
```

- [ ] **Step 5: Add search endpoint to public router**

Append to `api/modules/public/router.py`:

```python
from api.modules.public.search import search_intent, get_embedding
from api.modules.public.conversation import (
    get_conversation, add_message, conversation_length, MAX_FOLLOW_UPS
)


class SearchRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None


@router.post("/search")
def search(body: SearchRequest):
    """Search the knowledge base with intent matching and conversational follow-up."""
    conversation_id = body.conversation_id or str(hash(body.query))

    # Add user message to conversation
    add_message(conversation_id, "user", body.query)

    # Get conversation history for context
    history = get_conversation(conversation_id)

    # Check if we've exceeded follow-up limit
    if conversation_length(conversation_id) > MAX_FOLLOW_UPS:
        return {
            "match_type": "partially_related",
            "article_slug": None,
            "message": "We weren't able to find an exact match. Please contact the MCCAA for further assistance.",
            "follow_up_question": None,
            "show_contact_form": True,
        }

    # Run intent matching
    result = search_intent(body.query, history)

    # Add system response to conversation
    if result.get("follow_up_question"):
        add_message(conversation_id, "assistant", result["follow_up_question"])

    # Add contact form flag
    result["show_contact_form"] = result["match_type"] in (
        "not_covered", "partially_related", "not_related"
    )

    return result
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/test_search.py -v`
Expected: 4 tests PASS

- [ ] **Step 7: Commit**

```bash
git add api/modules/public/search.py api/modules/public/conversation.py api/modules/public/router.py api/tests/test_search.py
git commit -m "feat: add search and intent matching — vector search, exclusions, conversational follow-up"
```

---

### Task 14: Task Queue Worker — Wire Up Pipeline

**Files:**
- Modify: `api/queue.py`
- Modify: `api/main.py`
- Create: `api/tests/test_worker.py`

- [ ] **Step 1: Write failing tests for the worker**

```python
# api/tests/test_worker.py
import json
from unittest.mock import patch, MagicMock
from api.queue import enqueue_task
from api.db import get_cursor


@patch("api.queue.TASK_HANDLERS")
def test_worker_processes_crawl_task(mock_handlers):
    mock_handler = MagicMock(return_value={"pages_stored": 5})
    mock_handlers.get.return_value = mock_handler

    task_id = enqueue_task("crawl", {"url": "https://example.com"})

    from api.queue import process_next_task
    processed = process_next_task()

    assert processed is True
    mock_handler.assert_called_once()

    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM task_queue WHERE id = %s", (task_id,))
        task = cur.fetchone()
        assert task["status"] == "completed"


@patch("api.queue.TASK_HANDLERS")
def test_worker_handles_failure(mock_handlers):
    mock_handlers.get.return_value = MagicMock(side_effect=Exception("API timeout"))

    task_id = enqueue_task("crawl", {"url": "https://fail.com"})

    from api.queue import process_next_task
    processed = process_next_task()

    assert processed is True
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM task_queue WHERE id = %s", (task_id,))
        task = cur.fetchone()
        assert task["status"] == "failed"
        assert "API timeout" in task["error"]


def test_worker_returns_false_when_no_tasks():
    with get_cursor() as cur:
        cur.execute("DELETE FROM task_queue")

    from api.queue import process_next_task
    assert process_next_task() is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd api && python -m pytest tests/test_worker.py -v`
Expected: FAIL — `ImportError: cannot import name 'process_next_task'`

- [ ] **Step 3: Update queue.py with task dispatch**

Add to `api/queue.py`:

```python
import logging
import threading
import time

logger = logging.getLogger(__name__)

# Task handler registry — populated at import time
TASK_HANDLERS = {}


def register_handlers():
    """Register all task handlers. Called after all modules are imported."""
    from api.modules.ingestion.crawl import run_crawl
    from api.modules.ingestion.scrape import run_scrape
    from api.modules.ingestion.consolidation import run_consolidation
    from api.modules.classification.classifier import run_classification
    from api.modules.articles.generator import generate_article

    from api.modules.ingestion.json_schema import run_json_normalize

    TASK_HANDLERS.update({
        "crawl": lambda payload: run_crawl(payload["url"]),
        "scrape": lambda payload: run_scrape(payload["url"]),
        "consolidate": lambda payload: run_consolidation(payload["batch_id"]),
        "classify": lambda payload: run_classification(payload["unit_id"]),
        "json_normalize": lambda payload: run_json_normalize(payload["records"]),
        "generate_article": lambda payload: generate_article(
            sector=payload["sector"], scope=payload["scope"], audience=payload["audience"],
        ),
        "update_article": lambda payload: generate_article(
            sector=payload["sector"], scope=payload["scope"], audience=payload["audience"],
        ),
    })


def process_next_task() -> bool:
    """Claim and process the next queued task. Returns True if a task was processed."""
    task = claim_next_task()
    if not task:
        return False

    handler = TASK_HANDLERS.get(task["task_type"])
    if not handler:
        fail_task(task["id"], f"Unknown task type: {task['task_type']}")
        return True

    try:
        result = handler(task["payload"])
        complete_task(task["id"], result or {})
    except Exception as e:
        logger.exception(f"Task {task['id']} ({task['task_type']}) failed")
        fail_task(task["id"], str(e))

    return True


def start_worker(poll_interval: int = 2):
    """Start the background worker thread."""
    def _worker_loop():
        register_handlers()
        while True:
            try:
                if not process_next_task():
                    time.sleep(poll_interval)
            except Exception:
                logger.exception("Worker loop error")
                time.sleep(poll_interval)

    thread = threading.Thread(target=_worker_loop, daemon=True)
    thread.start()
    return thread
```

- [ ] **Step 4: Update main.py to start worker on startup**

Add to the lifespan or startup event in `api/main.py`:

```python
from api.db import ensure_schema
from api.queue import start_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_schema()
    start_worker()
    yield

# Update the app creation to use the lifespan:
app = FastAPI(title="MCCAA Knowledge Platform", lifespan=lifespan)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd api && python -m pytest tests/test_worker.py -v`
Expected: 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add api/queue.py api/main.py api/tests/test_worker.py
git commit -m "feat: add task queue worker — dispatches crawl, scrape, consolidate, classify, generate tasks"
```

---

### Task 15: Main.py Refactor — Mount All Routers & Clean Up

**Files:**
- Modify: `api/main.py`

- [ ] **Step 1: Refactor main.py**

The existing `api/main.py` has ~1000 lines of inline endpoints. Now that all functionality is in modules, refactor `main.py` to:
1. Import and mount all module routers
2. Keep the lifespan (schema + worker startup)
3. Keep CORS middleware
4. Remove old inline endpoints that are now covered by modules
5. Keep any legacy endpoints that aren't yet migrated (wizard endpoints for backwards compatibility during transition)

```python
# api/main.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from api.config import settings
from api.db import ensure_schema
from api.queue import start_worker

# Module routers
from api.modules.skills.router import router as skills_router
from api.modules.ingestion.router import router as ingestion_router
from api.modules.classification.router import router as classification_router
from api.modules.articles.router import router as articles_router
from api.modules.cms.router import router as cms_router
from api.modules.public.router import router as public_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_schema()
    start_worker()
    yield


app = FastAPI(title="MCCAA Knowledge Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all module routers
app.include_router(skills_router)
app.include_router(ingestion_router)
app.include_router(classification_router)
app.include_router(articles_router)
app.include_router(cms_router)
app.include_router(public_router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

Note: The old `api/main.py` should be backed up or the legacy wizard/chat endpoints preserved in a separate `api/modules/legacy/router.py` if still needed during transition. The implementation agent should check which existing endpoints are still used by the frontend before removing them.

- [ ] **Step 2: Run all tests to verify nothing is broken**

Run: `cd api && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add api/main.py
git commit -m "refactor: clean up main.py — mount all module routers, remove inline endpoints"
```

---

### Task 16: Docker Compose Update

**Files:**
- Modify: `docker-compose.yml`
- Modify: `api/Dockerfile`

- [ ] **Step 1: Update Dockerfile**

```dockerfile
# api/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Update docker-compose.yml**

```yaml
version: "3.8"

services:
  db:
    image: ankane/pgvector:latest
    ports:
      - "5434:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: mysecretpassword
      POSTGRES_DB: mccaa_website
    volumes:
      - pgdata:/var/lib/postgresql/data

  api:
    build: ./api
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      DB_HOST: db
      DB_USER: postgres
      DB_PASS: mysecretpassword
      DB_NAME: mccaa_website
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ADMIN_PASSWORD: ${ADMIN_PASSWORD:-mccaa-admin-2026}
      FIRECRAWL_API_KEY: ${FIRECRAWL_API_KEY}
    volumes:
      - ./api:/app

volumes:
  pgdata:
```

- [ ] **Step 3: Test Docker build**

Run: `docker-compose build api`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml api/Dockerfile
git commit -m "chore: update Docker setup for modular backend"
```

---

### Task 17: Integration Test — Full Pipeline

**Files:**
- Create: `api/tests/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
# api/tests/test_integration.py
"""
Integration test: verifies the full pipeline from manual entry through
classification to article generation.

Uses mocked AI calls to avoid external dependencies.
"""
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.db import get_cursor


def get_client():
    from api.main import app
    return TestClient(app)


ADMIN_HEADERS = {"X-Admin-Key": "mccaa-admin-2026"}


MOCK_CLASSIFICATION = json.dumps({
    "types": ["technical"],
    "sectors": ["toys"],
    "actors": ["manufacturer", "importer"],
    "scope": "sector-specific",
    "consumer_essential": True,
    "confidence": 0.9,
})

MOCK_ARTICLE = json.dumps({
    "title": "Toy Safety Compliance Guide",
    "html_content": '<div id="sec-1" data-topics="technical"><h2>Safety Requirements</h2><p>Details...</p></div>',
    "tag_map": {"sec-1": {"topics": ["technical"], "actors": ["manufacturer"]}},
    "cross_cutting_summaries": [],
})


@patch("api.modules.articles.generator.anthropic")
@patch("api.modules.articles.generator.select_skills_for_article", return_value=[])
@patch("api.modules.classification.classifier.anthropic")
def test_full_pipeline_manual_entry_to_article(mock_class_anthropic, mock_skills, mock_gen_anthropic):
    # Mock classification
    mock_class_client = MagicMock()
    mock_class_anthropic.Anthropic.return_value = mock_class_client
    mock_class_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=MOCK_CLASSIFICATION)]
    )

    # Mock article generation
    mock_gen_client = MagicMock()
    mock_gen_anthropic.Anthropic.return_value = mock_gen_client
    mock_gen_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=MOCK_ARTICLE)]
    )

    client = get_client()

    # Step 1: Manual entry (no classification — triggers AI classification)
    resp = client.post("/admin/ingest/manual", json={
        "title": "Toy Safety Directive 2009/48/EC",
        "content": "The Toy Safety Directive establishes essential safety requirements for toys...",
    }, headers=ADMIN_HEADERS)
    assert resp.status_code == 201
    unit_id = resp.json()["id"]

    # Step 2: Run classification manually (simulating what the worker would do)
    from api.modules.classification.classifier import run_classification
    class_result = run_classification(unit_id)
    assert class_result["classification"]["sectors"] == ["toys"]
    assert class_result["consumer_essential"] is True

    # Step 3: Generate business article
    from api.modules.articles.generator import generate_article
    article = generate_article(sector="toys", scope="sector-specific", audience="business")
    assert article["title"] == "Toy Safety Compliance Guide"
    assert article["status"] == "draft"

    # Step 4: Approve article
    resp = client.post(
        f"/admin/articles/{article['id']}/approve",
        json={"approved_by": "admin@mccaa.org.mt"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"

    # Step 5: Verify article is accessible via public API
    resp = client.get(f"/articles/{article['slug']}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"
```

- [ ] **Step 2: Run integration test**

Run: `cd api && python -m pytest tests/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Run full test suite**

Run: `cd api && python -m pytest tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add api/tests/test_integration.py
git commit -m "test: add full pipeline integration test — manual entry through to published article"
```

---

## Summary

| Task | Component | Tests |
|------|-----------|-------|
| 1 | Config, DB schema, shared models | 4 |
| 2 | Task queue | 5 |
| 3 | Skills CRUD + selector | 5 |
| 4 | Ingestion: crawl, scrape, manual | 5 |
| 5 | Ingestion: JSON import + normalisation | 2 |
| 6 | AI consolidation | 2 |
| 7 | Classification + overrides | 2 |
| 8 | Articles CRUD + approval | 7 |
| 9 | AI article generation | 1 |
| 10 | Cascade updates | 3 |
| 11 | CMS: exclusions + inquiries | 7 |
| 12 | Public API: sectors, articles, analytics | 5 |
| 13 | Search + intent matching + conversation | 4 |
| 14 | Task queue worker | 3 |
| 15 | Main.py refactor | All existing |
| 16 | Docker compose update | Build test |
| 17 | Full pipeline integration test | 1 |
| **Total** | | **~56 tests** |
