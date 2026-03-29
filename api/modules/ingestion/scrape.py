# api/modules/ingestion/scrape.py
import uuid
import json
from firecrawl import FirecrawlApp

from api.db import get_cursor
from api.config import settings
from api.queue import enqueue_task


def run_scrape(url: str) -> dict:
    batch_id = str(uuid.uuid4())

    app = FirecrawlApp(api_key=settings.firecrawl_api_key)
    result = app.scrape_url(url)

    if isinstance(result, dict):
        raw_content = result.get("markdown") or result.get("content") or json.dumps(result)
        metadata = result.get("metadata", {})
    else:
        raw_content = str(result)
        metadata = {}

    source_id = None
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO raw_sources (source_type, source_url, raw_content, raw_metadata, batch_id, status)
               VALUES (%s, %s, %s, %s, %s, 'pending') RETURNING id""",
            ("scrape", url, raw_content, json.dumps(metadata), batch_id),
        )
        source_id = cur.fetchone()["id"]

    consolidation_task_id = enqueue_task("consolidate", {"batch_id": batch_id})

    return {
        "batch_id": batch_id,
        "source_id": source_id,
        "consolidation_task_id": consolidation_task_id,
    }
