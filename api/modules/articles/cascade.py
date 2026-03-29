# api/modules/articles/cascade.py
import json
from api.db import get_cursor
from api.queue import enqueue_task


def trigger_cascade(knowledge_unit_id: int) -> list[dict]:
    """Find all articles affected by a knowledge unit change and queue updates."""
    with get_cursor(commit=False) as cur:
        # Get the knowledge unit's classification
        cur.execute(
            "SELECT * FROM knowledge_units WHERE id = %s", (knowledge_unit_id,)
        )
        unit = cur.fetchone()
        if not unit:
            return []

        classification = unit["classification"] or {}
        sectors = classification.get("sectors", [])
        scope = classification.get("scope", "sector-specific")

        # Find directly referenced articles
        cur.execute(
            "SELECT * FROM articles WHERE %s = ANY(source_knowledge_unit_ids) AND status NOT IN ('archived', 'rejected')",
            (knowledge_unit_id,),
        )
        affected = [dict(r) for r in cur.fetchall()]
        affected_ids = {a["id"] for a in affected}

        # Find articles for the same sectors (they should incorporate new data)
        if sectors:
            placeholders = ",".join(["%s"] * len(sectors))
            cur.execute(
                f"""SELECT * FROM articles
                    WHERE sector IN ({placeholders})
                    AND status NOT IN ('archived', 'rejected')
                    AND id NOT IN (SELECT unnest(%s::int[]))""",
                (*sectors, list(affected_ids) or [0]),
            )
            for row in cur.fetchall():
                row_dict = dict(row)
                if row_dict["id"] not in affected_ids:
                    affected.append(row_dict)
                    affected_ids.add(row_dict["id"])

        # If scope is cross-cutting or universal, find articles with cross_cutting_summaries
        if scope in ("cross-cutting", "universal"):
            cur.execute(
                """SELECT * FROM articles
                   WHERE status NOT IN ('archived', 'rejected')
                   AND id NOT IN (SELECT unnest(%s::int[]))""",
                (list(affected_ids) or [0],),
            )
            for row in cur.fetchall():
                row_dict = dict(row)
                if row_dict["id"] not in affected_ids:
                    affected.append(row_dict)
                    affected_ids.add(row_dict["id"])

    # Update statuses and enqueue regeneration
    with get_cursor() as cur:
        for article in affected:
            if article["status"] == "published":
                cur.execute(
                    "UPDATE articles SET status = 'update_pending' WHERE id = %s",
                    (article["id"],),
                )

            enqueue_task("update_article", {
                "article_id": article["id"],
                "sector": article["sector"],
                "scope": article["scope"],
                "audience": article["audience"],
                "triggered_by_unit_id": knowledge_unit_id,
            })

    return affected
