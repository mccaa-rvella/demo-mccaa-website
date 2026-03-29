# api/tests/test_public.py
import json
from fastapi.testclient import TestClient
from api.db import get_cursor


def get_client():
    from api.main import app
    return TestClient(app)


ADMIN_HEADERS = {"X-Admin-Key": "mccaa-admin-2026"}


def _seed_sector_with_article():
    """Create a sector with a published article (idempotent)."""
    client = get_client()
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO sectors (name, slug, showcase, visit_count)
               VALUES ('Toys', 'toys', true, 50)
               ON CONFLICT (slug) DO UPDATE SET visit_count = 50
               RETURNING id""",
        )
        sector_id = cur.fetchone()["id"]

    # Try creating the article; if it already exists, fetch it instead
    resp = client.post("/admin/articles", json={
        "title": "Toy Safety in Malta",
        "slug": "toy-safety-public-test",
        "sector": "toys",
        "scope": "sector-specific",
        "audience": "business",
        "html_content": "<h2>Toy Safety</h2><p>Content</p>",
        "tag_map": {"sec-1": {"topics": ["technical"], "actors": ["manufacturer"]}},
    }, headers=ADMIN_HEADERS)

    if resp.status_code == 409:
        # Already exists — look it up
        with get_cursor(commit=False) as cur:
            cur.execute("SELECT * FROM articles WHERE slug = 'toy-safety-public-test'")
            article = dict(cur.fetchone())
    else:
        article = resp.json()
        if article.get("status") != "published":
            client.post(
                f"/admin/articles/{article['id']}/approve",
                json={"approved_by": "admin"},
                headers=ADMIN_HEADERS,
            )

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
