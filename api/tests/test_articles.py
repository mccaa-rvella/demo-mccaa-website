import json
from unittest.mock import patch, MagicMock
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
    original = _create_article(slug="test-approve-update")
    client = get_client()
    client.post(
        f"/admin/articles/{original['id']}/approve",
        json={"approved_by": "admin"},
        headers=ADMIN_HEADERS,
    )

    updated = _create_article(
        slug="test-approve-update-v2",
        title="Toy Safety in Malta (Updated)",
        html_content="<h2>Updated</h2><p>New content</p>",
        status="update_pending",
        published_version_id=original["id"],
    )

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
