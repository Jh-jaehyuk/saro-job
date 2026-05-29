"""Match / InterviewQuestion API 스키마."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

Grade = Literal["상", "중", "하"]


class MatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    jd_id: uuid.UUID
    resume_id: uuid.UUID
    overall_score: float
    category_scores_json: dict[str, Any]
    grade: Grade
    matched_keywords_json: list[Any]
    missing_keywords_json: list[Any]
    created_at: datetime
    updated_at: datetime


class InterviewQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    match_id: uuid.UUID
    question: str
    question_type: str
    order: int
    edited_by_user: bool
