"""테스트용 fake 어댑터.

실제 OpenAI/PDF/R2 의존 없이 파이프라인 단계의 부수효과(LlmCall·Match·Question·상태)만
검증한다. 실 어댑터는 다음 PR에서 VCR 카세트와 함께 도입.
"""

import uuid
from decimal import Decimal

from app.core.sse import ProgressPublisher
from app.schemas.llm import (
    GeneratedQuestion,
    GeneratedQuestions,
    LlmUsage,
    ResumeAnalysis,
)
from app.schemas.resume import PdfExtractResult
from pydantic import BaseModel

_USAGE = LlmUsage(
    model="fake-1",
    tokens_in=10,
    tokens_out=20,
    latency_ms=5,
    cost_usd=Decimal("0.000123"),
)


class FakeStorage:
    def __init__(self, payload: bytes = b"%PDF-fake") -> None:
        self.payload = payload
        self.fetched: list[str] = []

    def build_resume_key(self, org_id: uuid.UUID, resume_id: uuid.UUID) -> str:
        return f"org_{org_id}/resume_{resume_id}.pdf"

    def generate_upload_url(self, key: str, *, expires_in: int = 3600) -> str:
        return f"https://fake/{key}?sig=u"

    def generate_download_url(self, key: str, *, expires_in: int = 3600) -> str:
        return f"https://fake/{key}?sig=d"

    def get_object(self, key: str) -> bytes:
        self.fetched.append(key)
        return self.payload


class FakePDFExtractor:
    def __init__(self, text: str = "이력서 본문 텍스트", confidence: float = 0.9) -> None:
        self.text = text
        self.confidence = confidence
        self.calls = 0

    def extract(self, pdf_bytes: bytes) -> PdfExtractResult:
        self.calls += 1
        return PdfExtractResult(text=self.text, confidence=self.confidence)


class FakeLLMClient:
    """canned 응답을 반환하고 호출 횟수를 추적한다."""

    def __init__(
        self,
        *,
        analysis: ResumeAnalysis | None = None,
        embedding: list[float] | None = None,
        questions: GeneratedQuestions | None = None,
    ) -> None:
        self.analysis = analysis or ResumeAnalysis(
            sections={"experience": "5년"},
            contact={"email": "a@b.com"},
            keywords=["python", "fastapi"],
        )
        self.embedding = embedding if embedding is not None else [1.0] + [0.0] * 1535
        self.questions = questions or GeneratedQuestions(
            items=[
                GeneratedQuestion(question="가장 큰 도전?", question_type="technical"),
                GeneratedQuestion(question="협업 사례?", question_type="behavioral"),
            ]
        )
        self.embed_calls = 0
        self.completion_calls: list[str] = []

    async def embed(self, text: str) -> tuple[list[float], LlmUsage]:
        self.embed_calls += 1
        return self.embedding, _USAGE

    async def structured_completion(
        self, *, purpose: str, system: str, user: str, schema: type[BaseModel]
    ) -> tuple[BaseModel, LlmUsage]:
        self.completion_calls.append(purpose)
        if schema is ResumeAnalysis:
            return self.analysis, _USAGE
        if schema is GeneratedQuestions:
            return self.questions, _USAGE
        raise NotImplementedError(f"FakeLLMClient: unknown schema {schema}")


class RecordingProgressPublisher:
    def __init__(self) -> None:
        self.events: list[tuple[uuid.UUID, uuid.UUID, str, int]] = []

    async def publish(
        self,
        jd_id: uuid.UUID,
        *,
        resume_id: uuid.UUID,
        step: str,
        percent: int,
    ) -> None:
        self.events.append((jd_id, resume_id, step, percent))


# 타입 검증용(런타임에 isinstance Protocol 동작 확인은 test_ports_protocol에서).
_publisher: ProgressPublisher = RecordingProgressPublisher()
