"""Resume API 스키마 + PDF 추출 결과 모델."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PdfExtractResult(BaseModel):
    """`PDFExtractor.extract`의 반환형. confidence는 추출 신뢰도(0~1)."""

    text: str
    confidence: float = Field(ge=0.0, le=1.0)


class ResumeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    pdf_key: str
    parsed_text: str | None = None
    sections_json: dict[str, Any] | None = None
    contact_json: dict[str, Any] | None = None
    parse_confidence: float | None = None
    created_at: datetime
    updated_at: datetime
