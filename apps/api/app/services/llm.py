"""LLMClient Port + OpenAI 어댑터.

OpenAI 직접 호출은 금지(AGENTS §4) — 모든 LLM 접근은 이 인터페이스를 통한다.
각 메서드는 결과와 함께 `LlmUsage`(토큰·비용·지연)를 반환하여, 호출하는 파이프라인이
`LlmCall`을 기록한다.

비용 안전장치: 가격표에 없는 모델은 생성 시점에 거절하고(비용 미기록 방지), 입력은
`llm_max_input_chars`로 자르며, 출력은 `llm_max_output_tokens`로 제한한다.
"""

import json
import time
from decimal import Decimal
from typing import Protocol, TypeVar, runtime_checkable

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.core.exceptions import LlmResponseInvalid
from app.schemas.llm import LlmUsage

T = TypeVar("T", bound=BaseModel)

_PER_MILLION = Decimal(1_000_000)

# USD / 1M tokens (입력, 출력). 모델을 바꾸면 여기에도 추가한다.
MODEL_PRICES_USD_PER_1M: dict[str, tuple[Decimal, Decimal]] = {
    "gpt-4o-mini": (Decimal("0.15"), Decimal("0.60")),
    "gpt-4.1-nano": (Decimal("0.10"), Decimal("0.40")),
    "gpt-4.1-mini": (Decimal("0.40"), Decimal("1.60")),
    "text-embedding-3-small": (Decimal("0.02"), Decimal("0")),
}


def estimate_cost_usd(model: str, tokens_in: int, tokens_out: int) -> Decimal:
    """가격표 기준 호출 비용(USD). 모르는 모델은 KeyError — 비용 0으로 새지 않게."""
    price_in, price_out = MODEL_PRICES_USD_PER_1M[model]
    cost = (price_in * tokens_in + price_out * tokens_out) / _PER_MILLION
    return cost.quantize(Decimal("0.000001"))


def truncate_input(text: str, max_chars: int) -> str:
    """입력 상한 적용. 이력서 앞부분(인적사항·최근 경력)이 가장 중요하므로 앞을 남긴다."""
    return text if len(text) <= max_chars else text[:max_chars]


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


class OpenAIClient:
    """OpenAI Chat Completions + Embeddings 어댑터."""

    def __init__(self, settings: Settings, *, client: AsyncOpenAI | None = None) -> None:
        for model in (settings.llm_chat_model, settings.llm_embedding_model):
            if model not in MODEL_PRICES_USD_PER_1M:
                raise ValueError(f"가격표에 없는 모델: {model}")
        self._client = client or AsyncOpenAI(api_key=settings.openai_api_key)
        self._chat_model = settings.llm_chat_model
        self._embedding_model = settings.llm_embedding_model
        self._max_input_chars = settings.llm_max_input_chars
        self._max_output_tokens = settings.llm_max_output_tokens

    async def embed(self, text: str) -> tuple[list[float], LlmUsage]:
        started = time.monotonic()
        resp = await self._client.embeddings.create(
            model=self._embedding_model,
            input=truncate_input(text, self._max_input_chars),
        )
        tokens_in = resp.usage.prompt_tokens
        return list(resp.data[0].embedding), LlmUsage(
            model=self._embedding_model,
            tokens_in=tokens_in,
            tokens_out=0,
            latency_ms=int((time.monotonic() - started) * 1000),
            cost_usd=estimate_cost_usd(self._embedding_model, tokens_in, 0),
        )

    async def structured_completion(
        self, *, purpose: str, system: str, user: str, schema: type[T]
    ) -> tuple[T, LlmUsage]:
        started = time.monotonic()
        # strict 모드는 dict[str, str] 같은 자유 키 객체를 받지 않으므로 strict=False로
        # 스키마를 안내하고, 검증은 Pydantic이 맡는다.
        resp = await self._client.chat.completions.create(
            model=self._chat_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": truncate_input(user, self._max_input_chars)},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": schema.model_json_schema(),
                    "strict": False,
                },
            },
            max_completion_tokens=self._max_output_tokens,
            temperature=0,
        )
        content = resp.choices[0].message.content or ""
        try:
            parsed = schema.model_validate(json.loads(content))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise LlmResponseInvalid(details={"purpose": purpose, "error": str(exc)}) from exc
        usage = resp.usage
        tokens_in = usage.prompt_tokens if usage else 0
        tokens_out = usage.completion_tokens if usage else 0
        return parsed, LlmUsage(
            model=self._chat_model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=int((time.monotonic() - started) * 1000),
            cost_usd=estimate_cost_usd(self._chat_model, tokens_in, tokens_out),
        )
