# api/tests/test_skills.py
import uuid
import pytest
from fastapi.testclient import TestClient


def _unique_name(prefix: str = "skill") -> str:
    """Generate a unique skill name to avoid UNIQUE constraint conflicts."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)


ADMIN_HEADERS = {"X-Admin-Key": "mccaa-admin-2026"}


def test_create_skill(client):
    name = _unique_name("plain-language-consumer")
    resp = client.post(
        "/admin/skills",
        json={
            "name": name,
            "description": "Write in plain language for consumers",
            "skill_content": "Use short sentences.",
            "is_active": True,
            "auto_select": True,
        },
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == name
    assert data["id"] is not None
    assert data["is_active"] is True


def test_list_skills(client):
    # Create a skill first so list is non-empty
    name = _unique_name("list-test")
    client.post(
        "/admin/skills",
        json={"name": name, "description": "For listing"},
        headers=ADMIN_HEADERS,
    )
    resp = client.get("/admin/skills", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    skills = resp.json()
    assert isinstance(skills, list)
    names = [s["name"] for s in skills]
    assert name in names


def test_update_skill(client):
    name = _unique_name("update-test")
    create_resp = client.post(
        "/admin/skills",
        json={"name": name, "description": "Original description"},
        headers=ADMIN_HEADERS,
    )
    assert create_resp.status_code == 201
    skill_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/admin/skills/{skill_id}",
        json={"description": "Updated description", "is_active": False},
        headers=ADMIN_HEADERS,
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["description"] == "Updated description"
    assert data["is_active"] is False


def test_delete_skill(client):
    name = _unique_name("delete-test")
    create_resp = client.post(
        "/admin/skills",
        json={"name": name, "description": "To be deleted"},
        headers=ADMIN_HEADERS,
    )
    assert create_resp.status_code == 201
    skill_id = create_resp.json()["id"]

    del_resp = client.delete(f"/admin/skills/{skill_id}", headers=ADMIN_HEADERS)
    assert del_resp.status_code == 204

    get_resp = client.get(f"/admin/skills/{skill_id}", headers=ADMIN_HEADERS)
    assert get_resp.status_code == 404


def test_skills_require_auth(client):
    # No header
    resp = client.get("/admin/skills")
    assert resp.status_code == 401

    # Wrong key
    resp = client.post(
        "/admin/skills",
        json={"name": "x", "description": "y"},
        headers={"X-Admin-Key": "wrong-key"},
    )
    assert resp.status_code == 401
