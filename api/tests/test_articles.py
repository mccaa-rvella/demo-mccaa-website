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
