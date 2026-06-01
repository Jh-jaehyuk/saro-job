"""스코어링 결과 스키마. scoring.py(순수)와 파이프라인이 공유한다."""

from pydantic import BaseModel

from app.schemas.match import Grade


class ScoreResult(BaseModel):
    overall_score: float
    category_scores: dict[str, float]
    grade: Grade
    matched_keywords: list[str]
    missing_keywords: list[str]
