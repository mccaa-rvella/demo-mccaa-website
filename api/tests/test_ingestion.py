# api/tests/test_ingestion.py
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


ADMIN_HEADERS = {"X-Admin-Key": "mccaa-admin-2026"}


@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)


def test_crawl_enqueues_task(client):
    with patch("api.modules.ingestion.router.enqueue_task", return_value=42) as mock_enqueue:
        resp = client.post(
            "/admin/ingest/crawl",
            json={"url": "https://example.com"},
            headers=ADMIN_HEADERS,
        )
    assert resp.status_code == 202
    data = resp.json()
    assert "task_id" in data
    assert data["task_id"] == 42
    mock_enqueue.assert_called_once_with("crawl", {"url": "https://example.com"})


def test_scrape_enqueues_task(client):
    with patch("api.modules.ingestion.router.enqueue_task", return_value=99) as mock_enqueue:
        resp = client.post(
            "/admin/ingest/scrape",
            json={"url": "https://example.com/page"},
            headers=ADMIN_HEADERS,
        )
    assert resp.status_code == 202
    data = resp.json()
    assert "task_id" in data
    assert data["task_id"] == 99
    mock_enqueue.assert_called_once_with("scrape", {"url": "https://example.com/page"})


def test_manual_entry_creates_knowledge_unit(client, db_cursor):
    resp = client.post(
        "/admin/ingest/manual",
        json={
            "title": "Test Manual Entry",
            "content": "Some content about regulations.",
            "classification": {"sector": "food", "pillar": "labelling"},
        },
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["title"] == "Test Manual Entry"

    unit_id = data["id"]
    db_cursor.execute("SELECT * FROM knowledge_units WHERE id = %s", (unit_id,))
    row = db_cursor.fetchone()
    assert row is not None
    assert row["title"] == "Test Manual Entry"
    assert row["content"] == "Some content about regulations."


def test_manual_entry_without_classification_enqueues_classify(client, db_cursor):
    with patch("api.modules.ingestion.router.enqueue_task", return_value=77) as mock_enqueue:
        resp = client.post(
            "/admin/ingest/manual",
            json={
                "title": "Unclassified Entry",
                "content": "Content without classification.",
            },
            headers=ADMIN_HEADERS,
        )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data

    mock_enqueue.assert_called_once_with("classify", {"knowledge_unit_id": data["id"]})


def test_ingest_requires_auth(client):
    resp = client.post(
        "/admin/ingest/crawl",
        json={"url": "https://example.com"},
    )
    assert resp.status_code == 401
