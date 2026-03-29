# api/modules/skills/router.py
from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel
from typing import Optional
import psycopg2

from api.db import get_cursor
from api.config import settings

router = APIRouter(prefix="/admin/skills", tags=["skills"])


def _require_auth(x_admin_key: Optional[str]):
    if x_admin_key != settings.admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")


class SkillCreate(BaseModel):
    name: str
    description: str
    skill_content: str = ""
    resources: dict = {}
    is_active: bool = True
    auto_select: bool = True
    pinned_sectors: list = []
    pinned_types: list = []
    excluded_sectors: list = []


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    skill_content: Optional[str] = None
    resources: Optional[dict] = None
    is_active: Optional[bool] = None
    auto_select: Optional[bool] = None
    pinned_sectors: Optional[list] = None
    pinned_types: Optional[list] = None
    excluded_sectors: Optional[list] = None


@router.post("", status_code=201)
def create_skill(
    skill: SkillCreate,
    x_admin_key: Optional[str] = Header(None),
):
    _require_auth(x_admin_key)
    try:
        with get_cursor() as cur:
            cur.execute(
                """
                INSERT INTO skills
                    (name, description, skill_content, resources, is_active,
                     auto_select, pinned_sectors, pinned_types, excluded_sectors)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    skill.name,
                    skill.description,
                    skill.skill_content,
                    psycopg2.extras.Json(skill.resources),
                    skill.is_active,
                    skill.auto_select,
                    skill.pinned_sectors,
                    skill.pinned_types,
                    skill.excluded_sectors,
                ),
            )
            row = cur.fetchone()
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Skill name already exists")
    return dict(row)


@router.get("")
def list_skills(x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM skills ORDER BY id")
        rows = cur.fetchall()
    return [dict(r) for r in rows]


@router.get("/{skill_id}")
def get_skill(skill_id: int, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    with get_cursor(commit=False) as cur:
        cur.execute("SELECT * FROM skills WHERE id = %s", (skill_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Skill not found")
    return dict(row)


@router.put("/{skill_id}")
def update_skill(
    skill_id: int,
    skill: SkillUpdate,
    x_admin_key: Optional[str] = Header(None),
):
    _require_auth(x_admin_key)
    updates = skill.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clauses = []
    values = []
    for field, value in updates.items():
        if field == "resources":
            set_clauses.append(f"{field} = %s")
            values.append(psycopg2.extras.Json(value))
        elif field in ("pinned_sectors", "pinned_types", "excluded_sectors"):
            set_clauses.append(f"{field} = %s")
            values.append(value)
        else:
            set_clauses.append(f"{field} = %s")
            values.append(value)

    set_clauses.append("updated_at = NOW()")
    values.append(skill_id)

    sql = f"UPDATE skills SET {', '.join(set_clauses)} WHERE id = %s RETURNING *"
    try:
        with get_cursor() as cur:
            cur.execute(sql, values)
            row = cur.fetchone()
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Skill name already exists")
    if not row:
        raise HTTPException(status_code=404, detail="Skill not found")
    return dict(row)


@router.delete("/{skill_id}", status_code=204)
def delete_skill(skill_id: int, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)
    with get_cursor() as cur:
        cur.execute("DELETE FROM skills WHERE id = %s RETURNING id", (skill_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Skill not found")
    return Response(status_code=204)
