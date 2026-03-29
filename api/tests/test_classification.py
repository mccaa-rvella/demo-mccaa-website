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


@patch("api.modules.classification.classifier._trigger_post_classification")
@patch("api.modules.classification.classifier.anthropic")
def test_classify_unit(mock_anthropic, mock_trigger):
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

    mock_trigger.assert_called_once_with(
        unit_id,
        {"types": ["technical", "consumer"], "sectors": ["toys"], "actors": ["manufacturer", "importer", "distributor"], "scope": "sector-specific"},
        True,
    )

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
        assert unit["classification"]["sectors"] == ["toys", "electronics"]
