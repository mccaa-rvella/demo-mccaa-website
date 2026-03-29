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
