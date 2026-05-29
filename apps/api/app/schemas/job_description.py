"""JobDescription API 스키마 (Pydantic v2). ORM과 분리, from_attributes로 매핑."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class JobDescriptionCreate(BaseModel):
    title: str
    raw_text: str


class JobDescriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    title: str
    raw_text: str
    requirements_json: dict[str, Any]
    created_at: datetime
    updated_at: datetime
