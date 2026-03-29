import json
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from api.config import settings
from api.db import get_cursor

router = APIRouter(prefix="/admin/classification", tags=["classification"])


def _require_auth(x_admin_key: Optional[str]):
    if x_admin_key != settings.admin_password:
        raise HTTPException(status_code=401, detail="Unauthorized")


class OverrideRequest(BaseModel):
    unit_id: int
    overrides: dict  # Can contain any classification fields + consumer_essential


@router.post("/override")
def override_classification(body: OverrideRequest, x_admin_key: Optional[str] = Header(None)):
    _require_auth(x_admin_key)

    with get_cursor() as cur:
        cur.execute("SELECT * FROM knowledge_units WHERE id = %s", (body.unit_id,))
        unit = cur.fetchone()
        if not unit:
            raise HTTPException(status_code=404, detail="Knowledge unit not found")

        # Merge overrides into existing classification
        existing_classification = unit["classification"] or {}
        existing_overrides = unit["admin_overrides"] or {}

        overrides_copy = dict(body.overrides)
        consumer_essential = overrides_copy.pop("consumer_essential", None)

        # Update admin_overrides (merge with existing)
        new_overrides = {**existing_overrides, **overrides_copy}

        # Update classification with overrides
        updated_classification = {**existing_classification, **overrides_copy}

        updates = [
            "classification = %s",
            "admin_overrides = %s",
            "updated_at = NOW()",
        ]
        values = [json.dumps(updated_classification), json.dumps(new_overrides)]

        if consumer_essential is not None:
            updates.append("consumer_essential = %s")
            values.append(consumer_essential)

        values.append(body.unit_id)
        cur.execute(
            f"UPDATE knowledge_units SET {', '.join(updates)} WHERE id = %s RETURNING *",
            values,
        )
        return dict(cur.fetchone())
