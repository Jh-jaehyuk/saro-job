"""Resume — 후보 이력서. 조직 스코프, 여러 JD에서 재평가 가능."""

import uuid
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Resume(Base, TimestampMixin):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # R2/MinIO 객체 키. 결정적 규칙: org_{org_id}/resume_{resume_id}.pdf
    pdf_key: Mapped[str] = mapped_column(String(512), nullable=False)
    parsed_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sections_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    contact_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    parse_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
