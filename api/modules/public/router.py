# api/modules/public/router.py
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from api.db import get_cursor

router = APIRouter(tags=["public"])


@router.get("/sectors/top")
def get_top_sectors():
    """Return top 3 most visited sectors with published articles."""
    with get_cursor(commit=False) as cur:
        cur.execute("""
            SELECT s.*,
                   CASE WHEN s.article_id IS NOT NULL THEN true ELSE false END as has_business,
                   CASE WHEN s.consumer_article_id IS NOT NULL THEN true ELSE false END as has_consumer
            FROM sectors s
            WHERE s.article_id IS NOT NULL OR s.consumer_article_id IS NOT NULL
            ORDER BY s.visit_count DESC
            LIMIT 3
        """)
        return [dict(r) for r in cur.fetchall()]


@router.get("/sectors")
def get_all_sectors():
    """Return all sectors with published articles."""
    with get_cursor(commit=False) as cur:
        cur.execute("""
            SELECT s.*,
                   CASE WHEN s.article_id IS NOT NULL THEN true ELSE false END as has_business,
                   CASE WHEN s.consumer_article_id IS NOT NULL THEN true ELSE false END as has_consumer
            FROM sectors s
            WHERE s.article_id IS NOT NULL OR s.consumer_article_id IS NOT NULL
            ORDER BY s.sort_order, s.name
        """)
        return [dict(r) for r in cur.fetchall()]


@router.get("/articles/{slug}")
def get_article_by_slug(slug: str):
    """Return a published article by slug."""
    with get_cursor(commit=False) as cur:
        cur.execute(
            "SELECT * FROM articles WHERE slug = %s AND status IN ('published', 'update_pending')",
            (slug,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        return dict(row)


class VisitTrack(BaseModel):
    sector: str
    topic: Optional[str] = None


@router.post("/track/visit", status_code=200)
def track_visit(body: VisitTrack):
    """Track a sector/topic visit for analytics."""
    with get_cursor() as cur:
        cur.execute(
            "UPDATE sectors SET visit_count = visit_count + 1 WHERE slug = %s",
            (body.sector,),
        )
        if body.topic:
            cur.execute(
                """INSERT INTO topic_analytics (topic, sector, visit_count, last_visited_at)
                   VALUES (%s, %s, 1, NOW())
                   ON CONFLICT (topic, sector) DO UPDATE
                   SET visit_count = topic_analytics.visit_count + 1, last_visited_at = NOW()""",
                (body.topic, body.sector),
            )
    return {"tracked": True}


from api.modules.public.search import search_intent, get_embedding
from api.modules.public.conversation import (
    get_conversation, add_message, conversation_length, MAX_FOLLOW_UPS
)


class SearchRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None


@router.post("/search")
def search(body: SearchRequest):
    """Search the knowledge base with intent matching and conversational follow-up."""
    conversation_id = body.conversation_id or str(hash(body.query))

    add_message(conversation_id, "user", body.query)
    history = get_conversation(conversation_id)

    if conversation_length(conversation_id) > MAX_FOLLOW_UPS:
        return {
            "match_type": "partially_related",
            "article_slug": None,
            "message": "We weren't able to find an exact match. Please contact the MCCAA for further assistance.",
            "follow_up_question": None,
            "show_contact_form": True,
        }

    result = search_intent(body.query, history)

    if result.get("follow_up_question"):
        add_message(conversation_id, "assistant", result["follow_up_question"])

    result["show_contact_form"] = result["match_type"] in (
        "not_covered", "partially_related", "not_related"
    )

    return result
