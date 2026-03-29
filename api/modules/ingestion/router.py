# api/modules/ingestion/router.py
import json
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from api.config import settings
from api.db import get_cursor
from api.queue import enqueue_task
from api.modules.ingestion.json_schema import validate_and_import  # Task 5 creates this

router = APIRouter(prefix="/admin/ingest", tags=["ingestion"])


def _require_auth(x_admin_key: Optional[str]):
    if x_admin_key != settings.admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")


class CrawlRequest(BaseModel):
    url: str


class ScrapeRequest(BaseModel):
    url: str


class ManualEntryRequest(BaseModel):
    title: str
    content: str
    classification: Optional[dict] = None


class JsonImportRequest(BaseModel):
    data: list[dict]


@router.post("/crawl", status_code=202)
def crawl(body: CrawlRequest, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    task_id = enqueue_task("crawl", {"url": body.url})
    return {"task_id": task_id, "message": "Crawl task enqueued"}


@router.post("/scrape", status_code=202)
def scrape(body: ScrapeRequest, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    task_id = enqueue_task("scrape", {"url": body.url})
    return {"task_id": task_id, "message": "Scrape task enqueued"}


@router.post("/manual", status_code=201)
def manual_entry(body: ManualEntryRequest, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)

    classification = body.classification or {}
    admin_overrides = body.classification if body.classification else None

    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO knowledge_units (title, content, classification, admin_overrides)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (
                body.title,
                body.content,
                json.dumps(classification),
                json.dumps(admin_overrides) if admin_overrides is not None else None,
            ),
        )
        row = cur.fetchone()
        unit_id = row["id"]

    if not body.classification:
        enqueue_task("classify", {"knowledge_unit_id": unit_id})

    return {"id": unit_id, "title": body.title}


@router.post("/json", status_code=202)
def json_import(body: JsonImportRequest, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    result = validate_and_import(body.data)
    return result
