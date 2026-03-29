# api/modules/articles/generator.py
import json
import logging
import re
import anthropic
from api.config import settings
from api.db import get_cursor
from api.modules.skills.selector import select_skills_for_article

logger = logging.getLogger(__name__)

BUSINESS_ARTICLE_PROMPT = """You are an expert regulatory content writer for the MCCAA (Malta Competition and Consumer Affairs Authority).

Generate a comprehensive compliance article for the "{sector}" sector targeted at business users.

Source material (knowledge units):
{knowledge_units}

{skills_section}

Requirements:
1. Write in professional, authoritative tone
2. Structure the article with sections tagged by topic and actor
3. Each section must have a unique DOM ID (e.g., "sec-technical-manufacturer")
4. Tag each section with applicable topics: "technical" (technical regulations & product safety), "standardisation", "consumer" (consumer affairs), "competition"
5. Tag each section with applicable actors: "manufacturer", "importer", "distributor", "retailer", "online-retailer", "fulfilment-service-provider", "authorised-representative", "conformity-assessment-body", "notified-body"
6. Generate contextual summaries (2-3 sentences each) for relevant cross-cutting and universal topics
7. Each cross-cutting summary should reference the full article slug

{admin_edits_section}

Return ONLY a JSON object:
{{
  "title": "Article title",
  "html_content": "<div id='sec-...' data-topics='...' data-actors='...'>...</div>",
  "tag_map": {{"sec-id": {{"topics": [...], "actors": [...]}}}},
  "cross_cutting_summaries": [{{"topic": "...", "scope": "cross-cutting|universal", "summary": "...", "article_slug": "..."}}]
}}"""

CONSUMER_ARTICLE_PROMPT = """You are writing a consumer-friendly guide for the MCCAA (Malta Competition and Consumer Affairs Authority).

Generate a plain-language article about "{sector}" for consumers.

Source material (only consumer-essential topics):
{knowledge_units}

{skills_section}

Requirements:
1. Use simple, plain language — no jargon, no legal references unless essential
2. Focus on what consumers NEED to know: their rights, what to look for, what to do if something goes wrong
3. Structure with clear sections tagged by topic only (no actor tags — consumers don't think in supply chain terms)
4. Each section must have a unique DOM ID
5. Weave cross-cutting and universal content directly into the article (self-contained, no separate links)
6. Keep it concise — fewer, broader sections

{admin_edits_section}

Return ONLY a JSON object:
{{
  "title": "Article title",
  "html_content": "<div id='sec-...' data-topics='...'>...</div>",
  "tag_map": {{"sec-id": {{"topics": [...]}}}},
  "cross_cutting_summaries": []
}}"""


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    return text[:80]


def _gather_knowledge_units(sector: str, scope: str, audience: str) -> list[dict]:
    """Gather relevant knowledge units for article generation."""
    with get_cursor(commit=False) as cur:
        if audience == "consumer":
            cur.execute(
                """SELECT * FROM knowledge_units
                   WHERE consumer_essential = true
                   AND (classification->>'sectors')::jsonb ? %s
                   ORDER BY updated_at DESC""",
                (sector,),
            )
            units = [dict(r) for r in cur.fetchall()]
            cur.execute(
                """SELECT * FROM knowledge_units
                   WHERE consumer_essential = true
                   AND classification->>'scope' = 'universal'""",
            )
            units += [dict(r) for r in cur.fetchall()]
        else:
            cur.execute(
                """SELECT * FROM knowledge_units
                   WHERE (classification->>'sectors')::jsonb ? %s
                   ORDER BY updated_at DESC""",
                (sector,),
            )
            units = [dict(r) for r in cur.fetchall()]
            cur.execute(
                """SELECT * FROM knowledge_units
                   WHERE classification->>'scope' IN ('cross-cutting', 'universal')""",
            )
            units += [dict(r) for r in cur.fetchall()]

    # Deduplicate by id
    seen = set()
    unique = []
    for u in units:
        if u["id"] not in seen:
            seen.add(u["id"])
            unique.append(u)
    return unique


def generate_article(sector: str, scope: str, audience: str, admin_edits: list = None) -> dict:
    """Generate an article using Sonnet with relevant skills."""
    units = _gather_knowledge_units(sector, scope, audience)
    skills = select_skills_for_article(sector, scope, audience)

    # Format knowledge units for prompt
    units_text = "\n\n".join(
        f"[Unit {u['id']}] {u['title']}\nScope: {u['classification'].get('scope', 'unknown')}\n{u['content'][:3000]}"
        for u in units
    )

    # Format skills section
    skills_section = ""
    if skills:
        skills_text = "\n\n".join(
            f"### Skill: {s['name']}\n{s['skill_content']}"
            for s in skills
        )
        skills_section = f"Apply these writing skills:\n{skills_text}"

    # Format admin edits section
    admin_edits_section = ""
    if admin_edits:
        edits_text = "\n".join(
            f"- Section '{e['section_id']}': preserve this admin edit: {e['edited_html'][:500]}"
            for e in admin_edits
        )
        admin_edits_section = f"IMPORTANT — Preserve these admin edits:\n{edits_text}"

    prompt_template = CONSUMER_ARTICLE_PROMPT if audience == "consumer" else BUSINESS_ARTICLE_PROMPT
    prompt = prompt_template.format(
        sector=sector,
        knowledge_units=units_text,
        skills_section=skills_section,
        admin_edits_section=admin_edits_section,
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-sonnet-4-5-20250514",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        article_data = json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"Failed to parse article generation response: {text[:200]}") from exc

    slug = _slugify(article_data["title"])
    unit_ids = [u["id"] for u in units]
    skill_names = [s["name"] for s in skills]

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO articles (title, slug, sector, scope, audience, html_content,
                   tag_map, status, skills_used, source_knowledge_unit_ids, cross_cutting_summaries)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'draft', %s, %s, %s)
               RETURNING *""",
            (article_data["title"], slug, sector, scope, audience,
             article_data["html_content"], json.dumps(article_data["tag_map"]),
             skill_names, unit_ids, json.dumps(article_data.get("cross_cutting_summaries", []))),
        )
        article = dict(cur.fetchone())

    article["tag_map"] = article_data["tag_map"]
    article["cross_cutting_summaries"] = article_data.get("cross_cutting_summaries", [])
    return article
