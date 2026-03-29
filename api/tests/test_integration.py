# api/tests/test_integration.py
"""
Integration test: verifies the full pipeline from manual entry through
classification to article generation.

Uses mocked AI calls to avoid external dependencies.
"""
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.db import get_cursor


def get_client():
    from api.main import app
    return TestClient(app)


ADMIN_HEADERS = {"X-Admin-Key": "mccaa-admin-2026"}


MOCK_CLASSIFICATION = json.dumps({
    "types": ["technical"],
    "sectors": ["toys"],
    "actors": ["manufacturer", "importer"],
    "scope": "sector-specific",
    "consumer_essential": True,
    "confidence": 0.9,
})

MOCK_ARTICLE = json.dumps({
    "title": "Toy Safety Compliance Guide",
    "html_content": '<div id="sec-1" data-topics="technical"><h2>Safety Requirements</h2><p>Details...</p></div>',
    "tag_map": {"sec-1": {"topics": ["technical"], "actors": ["manufacturer"]}},
    "cross_cutting_summaries": [],
})


@patch("api.modules.articles.generator.anthropic")
@patch("api.modules.articles.generator.select_skills_for_article", return_value=[])
@patch("api.modules.classification.classifier.anthropic")
@patch("api.modules.classification.classifier._trigger_post_classification")
def test_full_pipeline_manual_entry_to_article(mock_trigger, mock_class_anthropic, mock_skills, mock_gen_anthropic):
    # Mock classification
    mock_class_client = MagicMock()
    mock_class_anthropic.Anthropic.return_value = mock_class_client
    mock_class_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=MOCK_CLASSIFICATION)]
    )

    # Mock article generation
    mock_gen_client = MagicMock()
    mock_gen_anthropic.Anthropic.return_value = mock_gen_client
    mock_gen_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=MOCK_ARTICLE)]
    )

    client = get_client()

    # Step 1: Manual entry (no classification — triggers AI classification)
    resp = client.post("/admin/ingest/manual", json={
        "title": "Toy Safety Directive 2009/48/EC",
        "content": "The Toy Safety Directive establishes essential safety requirements for toys...",
    }, headers=ADMIN_HEADERS)
    assert resp.status_code == 201
    unit_id = resp.json()["id"]

    # Step 2: Run classification manually (simulating what the worker would do)
    from api.modules.classification.classifier import run_classification
    class_result = run_classification(unit_id)
    assert class_result["classification"]["sectors"] == ["toys"]
    assert class_result["consumer_essential"] is True

    # Step 3: Generate business article
    from api.modules.articles.generator import generate_article
    article = generate_article(sector="toys", scope="sector-specific", audience="business")
    assert article["title"] == "Toy Safety Compliance Guide"
    assert article["status"] == "draft"

    # Step 4: Approve article
    resp = client.post(
        f"/admin/articles/{article['id']}/approve",
        json={"approved_by": "admin@mccaa.org.mt"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"

    # Step 5: Verify article is accessible via public API
    resp = client.get(f"/articles/{article['slug']}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"
