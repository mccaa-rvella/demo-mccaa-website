def test_all_tables_exist(db_cursor):
    db_cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = {row["table_name"] for row in db_cursor.fetchall()}
    expected = {
        "raw_sources", "knowledge_units", "sectors", "articles",
        "skills", "exclusions", "topic_analytics", "inquiries", "task_queue",
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
