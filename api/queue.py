# api/queue.py
import json
from datetime import datetime
from typing import Optional
from api.db import get_cursor


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


def complete_task(task_id: int, result: dict):
    with get_cursor() as cur:
        cur.execute(
            """UPDATE task_queue
               SET status = 'completed', result = %s, completed_at = NOW()
               WHERE id = %s""",
            (json.dumps(result), task_id),
        )


def fail_task(task_id: int, error: str):
    with get_cursor() as cur:
        cur.execute(
            """UPDATE task_queue
               SET status = 'failed', error = %s, completed_at = NOW()
               WHERE id = %s""",
            (error, task_id),
        )
