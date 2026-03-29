# api/modules/public/search.py
import json
import logging
import anthropic
from openai import OpenAI
from api.config import settings
from api.db import get_cursor

logger = logging.getLogger(__name__)


def get_embedding(text: str) -> list[float]:
    """Generate embedding using OpenAI."""
    client = OpenAI(api_key=settings.openai_api_key or settings.openrouter_api_key,
                    base_url="https://api.openai.com/v1" if settings.openai_api_key else "https://openrouter.ai/api/v1")
    response = client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding


def vector_search(query_embedding: list[float], limit: int = 5) -> list[dict]:
    """Find articles by vector similarity."""
    with get_cursor(commit=False) as cur:
        cur.execute(
            """SELECT id, title, slug, sector, scope, audience,
                      1 - (embedding <=> %s::vector) as similarity
               FROM knowledge_units
               WHERE embedding IS NOT NULL
               ORDER BY embedding <=> %s::vector
               LIMIT %s""",
            (query_embedding, query_embedding, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def get_exclusions() -> dict:
    """Load all exclusions."""
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM exclusions")
        rows = cur.fetchall()
    return {
        "keywords": [r["value"] for r in rows if r["type"] == "keyword"],
        "rules": [r["value"] for r in rows if r["type"] == "rule"],
    }


def get_published_articles_summary() -> list[dict]:
    """Get summary of all published articles for intent matching."""
    with get_cursor(commit=False) as cur:
        cur.execute(
            """SELECT slug, title, sector, scope, audience, tag_map
               FROM articles WHERE status IN ('published', 'update_pending')
               ORDER BY sector, audience"""
        )
        return [dict(r) for r in cur.fetchall()]


SEARCH_INTENT_PROMPT = """You are the MCCAA's knowledge base search assistant.

The user is searching for: "{query}"

{conversation_history}

Available published articles:
{articles_summary}

Exclusion keywords (topics NOT under MCCAA remit):
{exclusion_keywords}

Exclusion rules (detailed reasoning):
{exclusion_rules}

Determine the best match. Return ONLY a JSON object:
{{
  "match_type": "strong_match" | "ambiguous" | "not_covered" | "partially_related" | "not_related",
  "article_slug": "slug-if-strong-match" or null,
  "message": "message to show user if not_covered/partially_related/not_related" or null,
  "follow_up_question": "clarifying question if ambiguous" or null
}}

Rules:
- "strong_match": clearly matches one published article
- "ambiguous": could match multiple articles or needs clarification (max 3 follow-ups per conversation)
- "not_covered": topic is within MCCAA remit but no article exists yet
- "partially_related": topic may be within MCCAA remit but uncertain
- "not_related": topic clearly outside MCCAA remit (matches exclusions)"""


def search_intent(query: str, conversation_history: list[dict] = None) -> dict:
    """Match user query to articles, exclusions, or follow-up questions."""
    articles = get_published_articles_summary()
    exclusions = get_exclusions()

    articles_text = "\n".join(
        f"- [{a['slug']}] {a['title']} (sector: {a['sector']}, audience: {a['audience']})"
        for a in articles
    )

    history_text = ""
    if conversation_history:
        history_text = "Conversation so far:\n" + "\n".join(
            f"- {'User' if m['role'] == 'user' else 'System'}: {m['content']}"
            for m in conversation_history
        )

    prompt = SEARCH_INTENT_PROMPT.format(
        query=query,
        conversation_history=history_text,
        articles_summary=articles_text or "(no articles published yet)",
        exclusion_keywords=", ".join(exclusions["keywords"]) or "(none)",
        exclusion_rules="\n".join(f"- {r}" for r in exclusions["rules"]) or "(none)",
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to parse search intent response: {text[:200]}") from exc
