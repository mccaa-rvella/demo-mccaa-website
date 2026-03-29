from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RawSourceOut(BaseModel):
    id: int
    source_type: str
    source_url: Optional[str] = None
    status: str
    batch_id: Optional[str] = None
    created_at: datetime


class KnowledgeUnitOut(BaseModel):
    id: int
    title: str
    content: str
    source_ids: list[int]
    classification: dict
    ai_confidence: Optional[float] = None
    admin_overrides: Optional[dict] = None
    consumer_essential: Optional[bool] = None
    created_at: datetime
    updated_at: datetime


class ArticleOut(BaseModel):
    id: int
    title: str
    slug: str
    sector: Optional[str] = None
    scope: str
    audience: str
    html_content: str
    tag_map: dict
    status: str
    skills_used: list[str]
    source_knowledge_unit_ids: list[int]
    cross_cutting_summaries: list
    admin_edits: list
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None


class SkillOut(BaseModel):
    id: int
    name: str
    description: str
    skill_content: str
    resources: dict
    is_active: bool
    auto_select: bool
    pinned_sectors: list[str]
    pinned_types: list[str]
    excluded_sectors: list[str]
    created_at: datetime
    updated_at: datetime


class ExclusionOut(BaseModel):
    id: int
    type: str
    value: str
    created_at: datetime


class InquiryOut(BaseModel):
    id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    message: Optional[str] = None
    search_context: dict
    match_type: Optional[str] = None
    created_at: datetime
    status: str


class TaskOut(BaseModel):
    id: int
    task_type: str
    payload: dict
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
