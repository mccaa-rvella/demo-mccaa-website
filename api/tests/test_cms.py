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
