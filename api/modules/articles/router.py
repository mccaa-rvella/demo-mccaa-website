import json
import psycopg2.errors
from fastapi import APIRouter, HTTPException, Header, Response
from pydantic import BaseModel
from typing import Optional
from api.config import settings
from api.db import get_cursor

router = APIRouter(prefix="/admin/articles", tags=["articles"])


def _require_auth(x_admin_key: Optional[str]):
    if x_admin_key != settings.admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")


class ArticleCreate(BaseModel):
    title: str
    slug: str
    sector: Optional[str] = None
    scope: str = "sector-specific"
    audience: str = "business"
    html_content: str = ""
    tag_map: dict = {}
    status: str = "draft"
    skills_used: list[str] = []
    source_knowledge_unit_ids: list[int] = []
    cross_cutting_summaries: list = []
    published_version_id: Optional[int] = None


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    html_content: Optional[str] = None
    tag_map: Optional[dict] = None
    sector: Optional[str] = None
    scope: Optional[str] = None
    audience: Optional[str] = None
    cross_cutting_summaries: Optional[list] = None


class ApproveRequest(BaseModel):
    approved_by: str


@router.post("", status_code=201)
def create_article(body: ArticleCreate, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    try:
        with get_cursor() as cur:
            cur.execute(
                """INSERT INTO articles (title, slug, sector, scope, audience, html_content,
                       tag_map, status, skills_used, source_knowledge_unit_ids,
                       cross_cutting_summaries, published_version_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING *""",
                (body.title, body.slug, body.sector, body.scope, body.audience,
                 body.html_content, json.dumps(body.tag_map), body.status,
                 body.skills_used, body.source_knowledge_unit_ids,
                 json.dumps(body.cross_cutting_summaries), body.published_version_id),
            )
            return dict(cur.fetchone())
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Article slug already exists")


@router.get("")
def list_articles(
    status: Optional[str] = None,
    audience: Optional[str] = None,
    x_admin_key: Optional[str] = Header(None),
):
    _require_auth(x_admin_key)
    query = "SELECT * FROM articles WHERE 1=1"
    params = []
    if status:
        query += " AND status = %s"
        params.append(status)
    if audience:
        query += " AND audience = %s"
        params.append(audience)
    query += " ORDER BY updated_at DESC"

    with get_cursor(commit=False) as cur:
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


@router.get("/{article_id}")
def get_article(article_id: int, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM articles WHERE id = %s", (article_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        return dict(row)


@router.put("/{article_id}")
def update_article(article_id: int, body: ArticleUpdate, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clauses = []
    values = []
    for key, val in updates.items():
        if key in ("tag_map", "cross_cutting_summaries"):
            set_clauses.append(f"{key} = %s")
            values.append(json.dumps(val))
        else:
            set_clauses.append(f"{key} = %s")
            values.append(val)
    set_clauses.append("updated_at = NOW()")
    values.append(article_id)

    with get_cursor() as cur:
        cur.execute(
            f"UPDATE articles SET {', '.join(set_clauses)} WHERE id = %s RETURNING *",
            values,
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        return dict(row)


@router.post("/{article_id}/approve")
def approve_article(article_id: int, body: ApproveRequest, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    with get_cursor() as cur:
        cur.execute("SELECT * FROM articles WHERE id = %s", (article_id,))
        article = cur.fetchone()
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        if article["published_version_id"]:
            cur.execute(
                "UPDATE articles SET status = 'archived' WHERE id = %s",
                (article["published_version_id"],),
            )

        cur.execute(
            """UPDATE articles SET status = 'published', approved_at = NOW(),
                   approved_by = %s, updated_at = NOW()
               WHERE id = %s RETURNING *""",
            (body.approved_by, article_id),
        )
        return dict(cur.fetchone())


@router.post("/{article_id}/reject")
def reject_article(article_id: int, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    with get_cursor() as cur:
        cur.execute(
            "UPDATE articles SET status = 'rejected', updated_at = NOW() WHERE id = %s RETURNING *",
            (article_id,),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        return dict(row)


@router.delete("/{article_id}", status_code=204)
def delete_article(article_id: int, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    with get_cursor() as cur:
        cur.execute("DELETE FROM articles WHERE id = %s", (article_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Article not found")
    return Response(status_code=204)
