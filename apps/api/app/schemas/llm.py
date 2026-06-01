"""LLM 호출의 입출력 스키마 + 사용량 메타데이터.

`LlmUsage`는 어댑터가 호출당 산출하고, 파이프라인이 `LlmCall` 기록에 사용한다.
`ResumeAnalysis`/`GeneratedQuestions`는 structured_completion의 출력 스키마.
"""

from decimal import Decimal

from pydantic import BaseModel


class LlmUsage(BaseModel):
    model: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    cost_usd: Decimal


class ResumeAnalysis(BaseModel):
    sections: dict[str, str]
    contact: dict[str, str]
    keywords: list[str]


class GeneratedQuestion(BaseModel):
    question: str
    question_type: str


class GeneratedQuestions(BaseModel):
    items: list[GeneratedQuestion]
