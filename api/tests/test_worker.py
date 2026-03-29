# api/tests/test_worker.py
import json
from unittest.mock import patch, MagicMock
from api.queue import enqueue_task
from api.db import get_cursor


@patch("api.queue.TASK_HANDLERS")
def test_worker_processes_crawl_task(mock_handlers):
    mock_handler = MagicMock(return_value={"pages_stored": 5})
    mock_handlers.get.return_value = mock_handler

    task_id = enqueue_task("crawl", {"url": "https://example.com"})

    from api.queue import process_next_task
    processed = process_next_task()

    assert processed is True
    mock_handler.assert_called_once()

    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM task_queue WHERE id = %s", (task_id,))
        task = cur.fetchone()
        assert task["status"] == "completed"


@patch("api.queue.TASK_HANDLERS")
def test_worker_handles_failure(mock_handlers):
    mock_handlers.get.return_value = MagicMock(side_effect=Exception("API timeout"))

    task_id = enqueue_task("crawl", {"url": "https://fail.com"})

    from api.queue import process_next_task
    processed = process_next_task()

    assert processed is True
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM task_queue WHERE id = %s", (task_id,))
        task = cur.fetchone()
        assert task["status"] == "failed"
        assert "API timeout" in task["error"]


def test_worker_returns_false_when_no_tasks():
    with get_cursor() as cur:
        cur.execute("DELETE FROM task_queue")

    from api.queue import process_next_task
    assert process_next_task() is False
