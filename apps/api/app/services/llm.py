"""LLMClient Port.

OpenAI 직접 호출은 금지(AGENTS §4) — 모든 LLM 접근은 이 인터페이스를 통한다.
구현체(`OpenAIClient`)는 어댑터 PR에서 추가한다. 각 메서드는 결과와 함께
`LlmUsage`(토큰·비용·지연)를 반환하여, 호출하는 파이프라인이 `LlmCall`을 기록한다.
"""

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

from app.schemas.llm import LlmUsage

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMClient(Protocol):
    async def embed(self, text: str) -> tuple[list[float], LlmUsage]:
        """임베딩 벡터(1536차원)와 사용량."""
        ...

    async def structured_completion(
        self, *, purpose: str, system: str, user: str, schema: type[T]
    ) -> tuple[T, LlmUsage]:
        """JSON Schema(`schema`)에 맞는 구조화 응답과 사용량. `purpose`는 LlmCall 기록용."""
        ...
