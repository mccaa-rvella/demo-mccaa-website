# api/tests/test_consolidation.py
import json
import uuid
import pytest
from unittest.mock import patch, MagicMock

import api.modules.ingestion.consolidation  # ensure module is loaded before patching


MOCK_CONSOLIDATION_RESPONSE = json.dumps([
    {
        "title": "Toy Safety Requirements",
        "content": "Comprehensive overview...",
        "source_indices": [0, 1, 2],
    }
])


def _seed_raw_sources(db_cursor, batch_id: str, count: int = 3) -> list[int]:
    """Insert raw_sources rows and return their IDs."""
    ids = []
    for i in range(count):
        db_cursor.execute(
            """INSERT INTO raw_sources (source_type, source_url, raw_content, batch_id, status)
               VALUES (%s, %s, %s, %s, 'pending') RETURNING id""",
            ("crawl", f"https://example.com/page{i}", f"Content about toys {i}", batch_id),
        )
        ids.append(db_cursor.fetchone()["id"])
    db_cursor.connection.commit()
    return ids


def _make_mock_anthropic(response_text: str):
    """Build a mock anthropic module that returns response_text from messages.create."""
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=response_text)]

    mock_client_instance = MagicMock()
    mock_client_instance.messages.create.return_value = mock_message

    mock_anthropic = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client_instance
    return mock_anthropic


def test_consolidate_merges_related_sources(db_cursor):
    """Consolidation should create 1 knowledge unit that references all 3 source IDs."""
    batch_id = str(uuid.uuid4())
    source_ids = _seed_raw_sources(db_cursor, batch_id, count=3)

    mock_anthropic = _make_mock_anthropic(MOCK_CONSOLIDATION_RESPONSE)

    with patch("api.modules.ingestion.consolidation.anthropic", mock_anthropic):
        with patch("api.modules.ingestion.consolidation.enqueue_task", return_value=99):
            result = api.modules.ingestion.consolidation.run_consolidation(batch_id)

    assert result["units_created"] == 1
    assert len(result["unit_ids"]) == 1

    unit_id = result["unit_ids"][0]
    db_cursor.execute("SELECT * FROM knowledge_units WHERE id = %s", (unit_id,))
    row = db_cursor.fetchone()
    assert row is not None
    assert row["title"] == "Toy Safety Requirements"
    # All 3 source IDs should be attributed
    assert set(row["source_ids"]) == set(source_ids)


def test_consolidation_marks_sources_as_consolidated(db_cursor):
    """After consolidation, all raw_sources in the batch should have status='consolidated'."""
    batch_id = str(uuid.uuid4())
    source_ids = _seed_raw_sources(db_cursor, batch_id, count=3)

    mock_anthropic = _make_mock_anthropic(MOCK_CONSOLIDATION_RESPONSE)

    with patch("api.modules.ingestion.consolidation.anthropic", mock_anthropic):
        with patch("api.modules.ingestion.consolidation.enqueue_task", return_value=99):
            api.modules.ingestion.consolidation.run_consolidation(batch_id)

    db_cursor.execute(
        "SELECT status FROM raw_sources WHERE batch_id = %s",
        (batch_id,),
    )
    rows = db_cursor.fetchall()
    assert len(rows) == 3
    for row in rows:
        assert row["status"] == "consolidated"
