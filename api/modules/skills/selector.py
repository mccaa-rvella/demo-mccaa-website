# api/modules/skills/selector.py
import json
import anthropic

from api.db import get_cursor
from api.config import settings


def select_skills_for_article(sector: str, scope: str, audience: str) -> list[dict]:
    """
    Select relevant skills for an article given sector, scope, and audience.

    Logic:
    1. Load all active skills
    2. Always include pinned skills for this sector/type (scope or audience as type)
    3. Exclude skills that have this sector in excluded_sectors
    4. For remaining auto_select skills, ask Claude Haiku to pick relevant ones
    """
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM skills WHERE is_active = true ORDER BY id")
        all_skills = [dict(r) for r in cur.fetchall()]

    selected = []
    auto_candidates = []

    for skill in all_skills:
        pinned_sectors = skill.get("pinned_sectors") or []
        pinned_types = skill.get("pinned_types") or []
        excluded_sectors = skill.get("excluded_sectors") or []

        # Exclude if this sector is in excluded list
        if sector in excluded_sectors:
            continue

        # Always include if pinned for this sector or type
        if sector in pinned_sectors or scope in pinned_types or audience in pinned_types:
            selected.append(skill)
            continue

        # Collect auto_select candidates for Claude to review
        if skill.get("auto_select"):
            auto_candidates.append(skill)

    # Ask Claude Haiku to pick from auto-select candidates
    if auto_candidates:
        haiku_picks = _ask_haiku(sector, scope, audience, auto_candidates)
        selected.extend(haiku_picks)

    return selected


def _ask_haiku(sector: str, scope: str, audience: str, candidates: list[dict]) -> list[dict]:
    """Ask Claude Haiku to select relevant skills from a list of candidates."""
    if not settings.anthropic_api_key:
        return []

    candidate_summary = json.dumps(
        [{"id": s["id"], "name": s["name"], "description": s["description"]} for s in candidates],
        indent=2,
    )

    prompt = f"""You are selecting writing skills/techniques for an article.

Article context:
- Sector: {sector}
- Scope: {scope}
- Audience: {audience}

Available skills (id, name, description):
{candidate_summary}

Return a JSON array of skill IDs that are relevant for this article. Only include IDs from the list above.
Respond with ONLY a JSON array of integers, e.g. [1, 3, 5] or [] if none are relevant."""

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    try:
        chosen_ids = set(json.loads(raw))
    except (json.JSONDecodeError, TypeError):
        return []

    return [s for s in candidates if s["id"] in chosen_ids]
