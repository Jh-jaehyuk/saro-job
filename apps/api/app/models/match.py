"""Match — JD와 Resume 한 쌍의 평가 결과. UNIQUE(jd_id, resume_id)."""

import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Match(Base, TimestampMixin):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("jd_id", "resume_id", name="uq_matches_jd_resume"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jd_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    category_scores_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    # "상" / "중" / "하". 검증은 Pydantic 스키마 경계(Literal)에서.
    grade: Mapped[str] = mapped_column(String(8), nullable=False)
    matched_keywords_json: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    missing_keywords_json: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
