# api/modules/ingestion/crawl.py
import uuid
import json
from firecrawl import FirecrawlApp

from api.db import get_cursor
from api.config import settings
from api.queue import enqueue_task


def run_crawl(url: str) -> dict:
    batch_id = str(uuid.uuid4())

    app = FirecrawlApp(api_key=settings.firecrawl_api_key)
    result = app.crawl(url)

    pages = result.data if hasattr(result, 'data') and result.data else []

    pages_stored = 0
    for page in pages:
        raw_content = page.markdown or json.dumps(page.model_dump())
        meta = page.metadata.model_dump() if hasattr(page.metadata, 'model_dump') else {}
        source_url = meta.get("sourceURL") or meta.get("url") or url
        with get_cursor() as cur:
            cur.execute(
                """INSERT INTO raw_sources (source_type, source_url, raw_content, raw_metadata, batch_id, status)
                   VALUES (%s, %s, %s, %s, %s, 'pending')""",
                ("crawl", source_url, raw_content, json.dumps(meta), batch_id),
            )
        pages_stored += 1

    consolidation_task_id = enqueue_task("consolidate", {"batch_id": batch_id})

    return {
        "batch_id": batch_id,
        "pages_stored": pages_stored,
        "consolidation_task_id": consolidation_task_id,
    }
