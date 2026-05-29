"""LLMClient Port.

OpenAI 직접 호출은 금지(AGENTS §4) — 모든 LLM 접근은 이 인터페이스를 통한다.
구현체(`OpenAIClient`, LlmCall 기록, Structured Outputs)는 파이프라인 PR에서 추가한다.
지금은 파이프라인(§6.2)이 필요로 하는 최소 계약만 둔다.
"""

from typing import Protocol, TypeVar, runtime_checkable

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


@runtime_checkable
class LLMClient(Protocol):
    async def embed(self, text: str) -> list[float]:
        """텍스트 임베딩 벡터(1536차원)를 반환."""
        ...

    async def structured_completion(
        self, *, purpose: str, system: str, user: str, schema: type[T]
    ) -> T:
        """JSON Schema(`schema`)에 맞는 구조화 응답을 반환. `purpose`는 LlmCall 기록용."""
        ...
