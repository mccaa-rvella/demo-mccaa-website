# api/modules/cms/router.py
import json
from fastapi import APIRouter, HTTPException, Header, Response
from pydantic import BaseModel
from typing import Optional
from api.config import settings
from api.db import get_cursor

router = APIRouter(tags=["cms"])


def _require_auth(x_admin_key: Optional[str]):
    if x_admin_key != settings.admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")


# --- Exclusions ---

class ExclusionCreate(BaseModel):
    type: str  # "keyword" or "rule"
    value: str


@router.post("/admin/exclusions", status_code=201)
def create_exclusion(body: ExclusionCreate, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO exclusions (type, value) VALUES (%s, %s) RETURNING *",
            (body.type, body.value),
        )
        return dict(cur.fetchone())


@router.get("/admin/exclusions")
def list_exclusions(x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM exclusions ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]


@router.delete("/admin/exclusions/{exclusion_id}", status_code=204)
def delete_exclusion(exclusion_id: int, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    with get_cursor() as cur:
        cur.execute("DELETE FROM exclusions WHERE id = %s", (exclusion_id,))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Exclusion not found")
    return Response(status_code=204)


# --- Contact / Inquiries (public endpoint) ---

class ContactRequest(BaseModel):
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    message: Optional[str] = None
    search_context: dict = {}
    match_type: Optional[str] = None


@router.post("/contact", status_code=201)
def submit_contact(body: ContactRequest):
    with get_cursor() as cur:
        cur.execute(
            """INSERT INTO inquiries (user_name, user_email, message, search_context, match_type)
               VALUES (%s, %s, %s, %s, %s) RETURNING *""",
            (body.user_name, body.user_email, body.message,
             json.dumps(body.search_context), body.match_type),
        )
        return dict(cur.fetchone())


# --- Inquiries Admin ---

class InquiryUpdate(BaseModel):
    status: str


@router.get("/admin/inquiries/trends")
def inquiry_trends(x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    with get_cursor(commit=False) as cur:
        cur.execute("""
            SELECT
                search_context->>'query' as query,
                match_type,
                COUNT(*) as count,
                MAX(created_at) as last_seen
            FROM inquiries
            WHERE search_context->>'query' IS NOT NULL
            GROUP BY search_context->>'query', match_type
            ORDER BY count DESC
            LIMIT 50
        """)
        return [dict(r) for r in cur.fetchall()]


@router.get("/admin/inquiries")
def list_inquiries(
    status: Optional[str] = None,
    match_type: Optional[str] = None,
    x_admin_key: Optional[str] = Header(None),
):
    _require_auth(x_admin_key)
    query = "SELECT * FROM inquiries WHERE 1=1"
    params = []
    if status:
        query += " AND status = %s"
        params.append(status)
    if match_type:
        query += " AND match_type = %s"
        params.append(match_type)
    query += " ORDER BY created_at DESC"

    with get_cursor(commit=False) as cur:
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


@router.put("/admin/inquiries/{inquiry_id}")
def update_inquiry(inquiry_id: int, body: InquiryUpdate, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    with get_cursor() as cur:
        cur.execute(
            "UPDATE inquiries SET status = %s WHERE id = %s RETURNING *",
            (body.status, inquiry_id),
        )
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Inquiry not found")
        return dict(row)
