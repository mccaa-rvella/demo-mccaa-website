# api/tests/test_queue.py
import json
from api.queue import enqueue_task, claim_next_task, complete_task, fail_task


def test_enqueue_creates_queued_task(db_cursor):
    task_id = enqueue_task("crawl", {"url": "https://example.com"})
    db_cursor.execute("SELECT * FROM task_queue WHERE id = %s", (task_id,))
    row = db_cursor.fetchone()
    assert row["status"] == "queued"
    assert row["task_type"] == "crawl"
    assert row["payload"]["url"] == "https://example.com"


def test_claim_next_gets_oldest_queued(db_cursor):
    db_cursor.execute("DELETE FROM task_queue")
    db_cursor.connection.commit()
    id1 = enqueue_task("crawl", {"url": "https://a.com"})
    id2 = enqueue_task("classify", {"unit_id": 1})
    task = claim_next_task()
    assert task["id"] == id1
    assert task["status"] == "running"


def test_claim_next_returns_none_when_empty(db_cursor):
    db_cursor.execute("DELETE FROM task_queue")
    db_cursor.connection.commit()
    task = claim_next_task()
    assert task is None


def test_complete_task_stores_result(db_cursor):
    task_id = enqueue_task("classify", {"unit_id": 1})
    claim_next_task()
    complete_task(task_id, {"classification": {"types": ["technical"]}})
    db_cursor.execute("SELECT * FROM task_queue WHERE id = %s", (task_id,))
    row = db_cursor.fetchone()
    assert row["status"] == "completed"
    assert row["result"]["classification"]["types"] == ["technical"]
    assert row["completed_at"] is not None


def test_fail_task_stores_error(db_cursor):
    task_id = enqueue_task("crawl", {"url": "https://fail.com"})
    claim_next_task()
    fail_task(task_id, "Connection timeout")
    db_cursor.execute("SELECT * FROM task_queue WHERE id = %s", (task_id,))
    row = db_cursor.fetchone()
    assert row["status"] == "failed"
    assert row["error"] == "Connection timeout"
