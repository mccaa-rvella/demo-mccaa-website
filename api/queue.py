# api/queue.py
import json
import logging
import threading
import time
from datetime import datetime, date
from typing import Optional
from api.db import get_cursor

logger = logging.getLogger(__name__)


def enqueue_task(task_type: str, payload: dict) -> int:
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO task_queue (task_type, payload, status)
               VALUES (%s, %s, 'queued') RETURNING id""",
            (task_type, json.dumps(payload)),
        )
        return cur.fetchone()["id"]


def claim_next_task() -> Optional[dict]:
    with get_cursor() as cur:
        cur.execute(
            """UPDATE task_queue
               SET status = 'running', started_at = NOW()
               WHERE id = (
                   SELECT id FROM task_queue
                   WHERE status = 'queued'
                   ORDER BY created_at ASC
                   LIMIT 1
                   FOR UPDATE SKIP LOCKED
               )
               RETURNING *""",
        )
        row = cur.fetchone()
        if row:
            return dict(row)
        return None


class _DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def complete_task(task_id: int, result: dict):
    with get_cursor() as cur:
        cur.execute(
            """UPDATE task_queue
               SET status = 'completed', result = %s, completed_at = NOW()
               WHERE id = %s""",
            (json.dumps(result, cls=_DateTimeEncoder), task_id),
        )


def fail_task(task_id: int, error: str):
    with get_cursor() as cur:
        cur.execute(
            """UPDATE task_queue
               SET status = 'failed', error = %s, completed_at = NOW()
               WHERE id = %s""",
            (error, task_id),
        )


# Task handler registry — populated at import time
TASK_HANDLERS = {}


def register_handlers():
    """Register all task handlers. Called after all modules are imported."""
    from api.modules.ingestion.crawl import run_crawl
    from api.modules.ingestion.scrape import run_scrape
    from api.modules.ingestion.consolidation import run_consolidation
    from api.modules.classification.classifier import run_classification
    from api.modules.articles.generator import generate_article
    from api.modules.ingestion.json_schema import run_json_normalize

    TASK_HANDLERS.update({
        "crawl": lambda payload: run_crawl(payload["url"]),
        "scrape": lambda payload: run_scrape(payload["url"]),
        "consolidate": lambda payload: run_consolidation(payload["batch_id"]),
        "classify": lambda payload: run_classification(payload.get("unit_id") or payload["knowledge_unit_id"]),
        "json_normalize": lambda payload: run_json_normalize(payload["records"]),
        "generate_article": lambda payload: generate_article(
            sector=payload["sector"], scope=payload["scope"], audience=payload["audience"],
        ),
        "update_article": lambda payload: generate_article(
            sector=payload["sector"], scope=payload["scope"], audience=payload["audience"],
        ),
    })


def process_next_task() -> bool:
    """Claim and process the next queued task. Returns True if a task was processed."""
    task = claim_next_task()
    if not task:
        return False

    handler = TASK_HANDLERS.get(task["task_type"])
    if not handler:
        fail_task(task["id"], f"Unknown task type: {task['task_type']}")
        return True

    try:
        result = handler(task["payload"])
        complete_task(task["id"], result or {})
    except Exception as e:
        logger.exception(f"Task {task['id']} ({task['task_type']}) failed")
        fail_task(task["id"], str(e))

    return True


def start_worker(poll_interval: int = 2):
    """Start the background worker thread."""
    def _worker_loop():
        register_handlers()
        while True:
            try:
                if not process_next_task():
                    time.sleep(poll_interval)
            except Exception:
                logger.exception("Worker loop error")
                time.sleep(poll_interval)

    thread = threading.Thread(target=_worker_loop, daemon=True)
    thread.start()
    return thread
