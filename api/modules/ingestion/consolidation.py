# api/modules/ingestion/consolidation.py
import json
import anthropic

from api.db import get_cursor
from api.config import settings
from api.queue import enqueue_task


def run_consolidation(batch_id: str) -> dict:
    """Fetch pending raw_sources for batch, consolidate via Claude Sonnet, store knowledge_units."""
    # Fetch all pending raw_sources for this batch
    with get_cursor(commit=False) as cur:
        cur.execute(
            """SELECT id, raw_content, source_url FROM raw_sources
               WHERE batch_id = %s AND status = 'pending'
               ORDER BY id ASC""",
            (batch_id,),
        )
        sources = [dict(row) for row in cur.fetchall()]

    if not sources:
        return {"units_created": 0, "unit_ids": []}

    source_texts = [
        {"index": i, "content": s["raw_content"], "url": s.get("source_url")}
        for i, s in enumerate(sources)
    ]

    prompt = (
        "You are a knowledge consolidation assistant. Given the following web-crawled sources, "
        "identify thematic clusters and merge related content into coherent knowledge units. "
        "Each knowledge unit must have 'title', 'content', and 'source_indices' (list of input indices). "
        "Return a JSON array of knowledge unit objects. "
        "Output only valid JSON — no markdown fences, no explanation.\n\n"
        f"Sources:\n{json.dumps(source_texts, indent=2)}"
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_response = message.content[0].text.strip()
    consolidated_units = json.loads(raw_response)

    unit_ids = []
    source_ids = [s["id"] for s in sources]

    with get_cursor() as cur:
        for unit in consolidated_units:
            # Map source_indices back to actual raw_source IDs
            indices = unit.get("source_indices", [])
            attributed_source_ids = [
                sources[i]["id"] for i in indices if 0 <= i < len(sources)
            ]

            cur.execute(
                """INSERT INTO knowledge_units (title, content, source_ids, classification)
                   VALUES (%s, %s, %s, %s) RETURNING id""",
                (
                    unit["title"],
                    unit["content"],
                    attributed_source_ids,
                    json.dumps(unit.get("classification", {})),
                ),
            )
            unit_id = cur.fetchone()["id"]
            unit_ids.append(unit_id)
            enqueue_task("classify", {"knowledge_unit_id": unit_id})

        # Mark all raw_sources as consolidated
        cur.execute(
            """UPDATE raw_sources SET status = 'consolidated'
               WHERE batch_id = %s AND status = 'pending'""",
            (batch_id,),
        )

    return {"units_created": len(unit_ids), "unit_ids": unit_ids}
