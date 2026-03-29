# api/tests/test_search.py
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.db import get_cursor


def get_client():
    from api.main import app
    return TestClient(app)


ADMIN_HEADERS = {"X-Admin-Key": "mccaa-admin-2026"}


def _seed_published_article():
    client = get_client()
    article = client.post("/admin/articles", json={
        "title": "Toy Safety Regulations",
        "slug": "toy-safety-search-test",
        "sector": "toys",
        "scope": "sector-specific",
        "audience": "business",
        "html_content": "<h2>Toy Safety</h2><p>Toys must comply with EN 71</p>",
        "tag_map": {},
    }, headers=ADMIN_HEADERS).json()
    client.post(
        f"/admin/articles/{article['id']}/approve",
        json={"approved_by": "admin"},
        headers=ADMIN_HEADERS,
    )
    return article


def _seed_exclusion():
    client = get_client()
    client.post("/admin/exclusions", json={"type": "keyword", "value": "taxation"}, headers=ADMIN_HEADERS)
    client.post(
        "/admin/exclusions",
        json={"type": "rule", "value": "Financial regulation — banking, insurance, investment falls under MFSA, not MCCAA"},
        headers=ADMIN_HEADERS,
    )


@patch("api.modules.public.search.get_embedding")
@patch("api.modules.public.search.anthropic")
def test_search_strong_match(mock_anthropic, mock_embedding):
    _seed_published_article()
    mock_embedding.return_value = [0.1] * 1536

    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps({
            "match_type": "strong_match",
            "article_slug": "toy-safety-search-test",
            "message": None,
            "follow_up_question": None,
        }))]
    )

    client = get_client()
    resp = client.post("/search", json={"query": "toy safety regulations"})
    assert resp.status_code == 200
    assert resp.json()["match_type"] == "strong_match"
    assert resp.json()["article_slug"] == "toy-safety-search-test"


@patch("api.modules.public.search.get_embedding")
@patch("api.modules.public.search.anthropic")
def test_search_not_related(mock_anthropic, mock_embedding):
    _seed_exclusion()
    mock_embedding.return_value = [0.1] * 1536

    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps({
            "match_type": "not_related",
            "article_slug": None,
            "message": "This area most probably does not fall under the remit of the MCCAA.",
            "follow_up_question": None,
        }))]
    )

    client = get_client()
    resp = client.post("/search", json={"query": "how do I pay less income tax"})
    assert resp.status_code == 200
    assert resp.json()["match_type"] == "not_related"


@patch("api.modules.public.search.get_embedding")
@patch("api.modules.public.search.anthropic")
def test_search_ambiguous_returns_follow_up(mock_anthropic, mock_embedding):
    mock_embedding.return_value = [0.1] * 1536

    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps({
            "match_type": "ambiguous",
            "article_slug": None,
            "message": None,
            "follow_up_question": "Are you asking about toy safety as a manufacturer or as a consumer?",
        }))]
    )

    client = get_client()
    resp = client.post("/search", json={"query": "toys"})
    assert resp.status_code == 200
    assert resp.json()["match_type"] == "ambiguous"
    assert resp.json()["follow_up_question"] is not None


def test_conversation_follow_up():
    """Test that follow-up messages include conversation history."""
    client = get_client()
    with patch("api.modules.public.search.get_embedding", return_value=[0.1]*1536), \
         patch("api.modules.public.search.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps({
                "match_type": "ambiguous",
                "article_slug": None,
                "message": None,
                "follow_up_question": "Are you a business or consumer?",
            }))]
        )
        resp1 = client.post("/search", json={
            "query": "product safety",
            "conversation_id": "conv-123",
        })
        assert resp1.json()["match_type"] == "ambiguous"

    with patch("api.modules.public.search.get_embedding", return_value=[0.1]*1536), \
         patch("api.modules.public.search.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text=json.dumps({
                "match_type": "strong_match",
                "article_slug": "toy-safety-search-test",
                "message": None,
                "follow_up_question": None,
            }))]
        )
        resp2 = client.post("/search", json={
            "query": "I'm a manufacturer of toys",
            "conversation_id": "conv-123",
        })
        assert resp2.json()["match_type"] == "strong_match"
