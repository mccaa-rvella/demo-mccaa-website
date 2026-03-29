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
