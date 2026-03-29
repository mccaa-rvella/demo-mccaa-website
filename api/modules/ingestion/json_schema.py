# api/modules/ingestion/json_schema.py
import json
import anthropic

from api.db import get_cursor
from api.config import settings
from api.queue import enqueue_task


_REQUIRED_FIELDS = {"title", "content"}
_VALID_CLASSIFICATION_KEYS = {"types", "sectors", "actors", "scope"}


def _is_valid_record(record: dict) -> bool:
    """Check whether a record satisfies the strict schema."""
    if not _REQUIRED_FIELDS.issubset(record.keys()):
        return False
    classification = record.get("classification")
    if classification is not None:
        if not isinstance(classification, dict):
            return False
        # Only known keys are allowed
        if not set(classification.keys()).issubset(_VALID_CLASSIFICATION_KEYS):
            return False
    return True


def _insert_knowledge_unit(cur, record: dict) -> int:
    classification = record.get("classification") or {}
    cur.execute(
        """INSERT INTO knowledge_units (title, content, classification)
           VALUES (%s, %s, %s) RETURNING id""",
        (record["title"], record["content"], json.dumps(classification)),
    )
    return cur.fetchone()["id"]


def validate_and_import(data: list[dict]) -> dict:
    """Validate records against strict schema; invalid ones are enqueued for AI normalisation."""
    valid_records = []
    invalid_records = []

    for record in data:
        if _is_valid_record(record):
            valid_records.append(record)
        else:
            invalid_records.append(record)

    created_ids = []
    with get_cursor() as cur:
        for record in valid_records:
            unit_id = _insert_knowledge_unit(cur, record)
            created_ids.append(unit_id)
            # Enqueue classify if classification is incomplete / missing
            classification = record.get("classification") or {}
            has_full_classification = all(
                k in classification for k in _VALID_CLASSIFICATION_KEYS
            )
            if not has_full_classification:
                enqueue_task("classify", {"knowledge_unit_id": unit_id})

    normalisation_task_id = None
    if invalid_records:
        normalisation_task_id = enqueue_task(
            "json_normalize", {"records": invalid_records}
        )

    return {
        "valid_count": len(valid_records),
        "invalid_count": len(invalid_records),
        "created_ids": created_ids,
        "normalisation_task_id": normalisation_task_id,
    }


def run_json_normalize(records: list[dict]) -> dict:
    """Use Claude Haiku to normalise invalid JSON records into the internal schema."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    prompt = (
        "You are a data normalisation assistant. Convert each of the following JSON records "
        "into the internal schema which requires 'title' and 'content' fields, and optionally "
        "a 'classification' object with keys: types (list), sectors (list), actors (list), scope (string). "
        "Return a JSON array of normalised records, one per input record. "
        "Output only valid JSON — no markdown fences, no explanation.\n\n"
        f"Records to normalise:\n{json.dumps(records, indent=2)}"
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_response = message.content[0].text.strip()
    normalised_records = json.loads(raw_response)

    created_ids = []
    with get_cursor() as cur:
        for record in normalised_records:
            unit_id = _insert_knowledge_unit(cur, record)
            created_ids.append(unit_id)
            classification = record.get("classification") or {}
            has_full_classification = all(
                k in classification for k in _VALID_CLASSIFICATION_KEYS
            )
            if not has_full_classification:
                enqueue_task("classify", {"knowledge_unit_id": unit_id})

    return {
        "normalised_count": len(created_ids),
        "created_ids": created_ids,
    }
