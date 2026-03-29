import json
import logging
import anthropic
from api.config import settings
from api.db import get_cursor

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """You are an expert in EU/Maltese regulatory frameworks under the MCCAA.

Classify this knowledge unit:

Title: {title}
Content: {content}

Determine:
1. types: Which MCCAA areas apply? Options: "technical" (technical regulations & product safety), "standardisation", "consumer" (consumer affairs), "competition". Can be multiple.
2. sectors: Which product/industry sectors? E.g., "toys", "electronics", "food", "pressure-vessels", "lifts". Can be multiple.
3. actors: Which supply chain actors does this apply to? Options: "manufacturer", "importer", "distributor", "retailer", "online-retailer", "fulfilment-service-provider", "authorised-representative", "conformity-assessment-body", "notified-body". Can be multiple.
4. scope: "sector-specific" (applies to specific sectors), "cross-cutting" (applies across some sectors, e.g. CE marking), or "universal" (applies to all sectors, e.g. market surveillance).
5. consumer_essential: Would a consumer need to know this to protect their interests? true/false.
6. confidence: How confident are you in this classification? 0.0 to 1.0.

Return ONLY a JSON object with these fields. Example:
{{"types": ["technical"], "sectors": ["toys"], "actors": ["manufacturer", "importer"], "scope": "sector-specific", "consumer_essential": true, "confidence": 0.85}}"""


def run_classification(unit_id: int) -> dict:
    """Classify a knowledge unit using AI."""
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM knowledge_units WHERE id = %s", (unit_id,))
        unit = cur.fetchone()

    if not unit:
        raise ValueError(f"Knowledge unit {unit_id} not found")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": CLASSIFICATION_PROMPT.format(
                title=unit["title"], content=unit["content"][:4000]
            ),
        }],
    )

    text = response.content[0].text.strip()
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        classification_data = json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to parse classification response: {text[:200]}") from exc

    consumer_essential = classification_data.pop("consumer_essential", None)
    confidence = classification_data.pop("confidence", None)
    classification = {
        "types": classification_data.get("types", []),
        "sectors": classification_data.get("sectors", []),
        "actors": classification_data.get("actors", []),
        "scope": classification_data.get("scope", "sector-specific"),
    }

    with get_cursor() as cur:
        cur.execute(
            """UPDATE knowledge_units
               SET classification = %s, ai_confidence = %s, consumer_essential = %s, updated_at = NOW()
               WHERE id = %s""",
            (json.dumps(classification), confidence, consumer_essential, unit_id),
        )

    # Pipeline automation (spec 3.5): after classification, trigger article generation or cascade
    _trigger_post_classification(unit_id, classification, consumer_essential)

    return {
        "unit_id": unit_id,
        "classification": classification,
        "consumer_essential": consumer_essential,
        "confidence": confidence,
    }


def _trigger_post_classification(unit_id: int, classification: dict, consumer_essential: bool):
    """After classification, check if articles need generating or updating."""
    try:
        from api.queue import enqueue_task
        from api.modules.articles.cascade import trigger_cascade

        sectors = classification.get("sectors", [])
        scope = classification.get("scope", "sector-specific")

        # Check if any existing articles reference this unit or its sector
        with get_cursor(commit=False) as cur:
            for sector in sectors:
                # Check for existing business article
                cur.execute(
                    "SELECT id FROM articles WHERE sector = %s AND audience = 'business' AND status != 'archived' LIMIT 1",
                    (sector,),
                )
                if cur.fetchone():
                    # Existing article — trigger cascade update
                    trigger_cascade(unit_id)
                else:
                    # No article yet — generate new one
                    enqueue_task("generate_article", {
                        "sector": sector, "scope": scope, "audience": "business",
                    })

                # Check for consumer article if consumer-essential
                if consumer_essential:
                    cur.execute(
                        "SELECT id FROM articles WHERE sector = %s AND audience = 'consumer' AND status != 'archived' LIMIT 1",
                        (sector,),
                    )
                    if cur.fetchone():
                        trigger_cascade(unit_id)
                    else:
                        enqueue_task("generate_article", {
                            "sector": sector, "scope": scope, "audience": "consumer",
                        })
    except Exception as exc:
        logger.warning("Post-classification trigger failed for unit %s: %s", unit_id, exc)
