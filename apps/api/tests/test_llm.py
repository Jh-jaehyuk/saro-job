"""OpenAIClient 어댑터 + 비용 계산 테스트.

실 OpenAI 호출 없이 httpx `MockTransport`로 응답을 고정한다(카세트 대신 — 응답 형태만
검증하면 충분하고, 키 없이 CI에서 돈다). 비용 계산·입력 자르기는 순수 함수 단위 테스트.
"""

import json
from decimal import Decimal

import httpx
import pytest
from app.core.config import Settings
from app.core.exceptions import LlmResponseInvalid
from app.schemas.llm import GeneratedQuestions
from app.services.llm import LLMClient, OpenAIClient, estimate_cost_usd, truncate_input
from openai import AsyncOpenAI


def test_estimate_cost_usd_uses_price_table() -> None:
    # gpt-4o-mini: $0.15 / 1M in, $0.60 / 1M out
    assert estimate_cost_usd("gpt-4o-mini", 1_000_000, 0) == Decimal("0.150000")
    assert estimate_cost_usd("gpt-4o-mini", 2_000, 500) == Decimal("0.000600")


def test_estimate_cost_usd_rejects_unknown_model() -> None:
    with pytest.raises(KeyError):
        estimate_cost_usd("unknown-model", 1, 1)


def test_truncate_input_keeps_head() -> None:
    assert truncate_input("abcdef", 3) == "abc"
    assert truncate_input("ab", 3) == "ab"


def test_openai_client_rejects_unpriced_model() -> None:
    with pytest.raises(ValueError, match="가격표"):
        OpenAIClient(Settings(openai_api_key="sk-test", llm_chat_model="gpt-unknown"))


def _client(handler: httpx.MockTransport, **overrides: object) -> OpenAIClient:
    settings = Settings(openai_api_key="sk-test", **overrides)  # type: ignore[arg-type]
    sdk = AsyncOpenAI(
        api_key="sk-test",
        base_url="https://api.test/v1",
        http_client=httpx.AsyncClient(transport=handler),
        max_retries=0,
    )
    return OpenAIClient(settings, client=sdk)


def _chat_response(content: str) -> dict[str, object]:
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 0,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": {"prompt_tokens": 2_000, "completion_tokens": 500, "total_tokens": 2_500},
    }


def test_openai_client_satisfies_protocol() -> None:
    client: LLMClient = _client(httpx.MockTransport(lambda r: httpx.Response(500)))
    assert isinstance(client, LLMClient)


async def test_structured_completion_parses_and_limits_request() -> None:
    seen: list[dict[str, object]] = []
    payload = {"items": [{"question": "Q1", "question_type": "technical"}]}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return httpx.Response(200, json=_chat_response(json.dumps(payload)))

    client = _client(httpx.MockTransport(handler), llm_max_input_chars=5)
    result, usage = await client.structured_completion(
        purpose="generate_questions", system="sys", user="1234567890", schema=GeneratedQuestions
    )

    assert result.items[0].question == "Q1"
    assert usage.model == "gpt-4o-mini"
    assert (usage.tokens_in, usage.tokens_out) == (2_000, 500)
    assert usage.cost_usd == Decimal("0.000600")
    body = seen[0]
    assert body["model"] == "gpt-4o-mini"
    assert body["max_completion_tokens"] == 1_024
    messages = body["messages"]
    assert isinstance(messages, list)
    assert messages[1]["content"] == "12345"  # 입력 상한 적용


async def test_structured_completion_invalid_json_raises_app_error() -> None:
    client = _client(
        httpx.MockTransport(lambda r: httpx.Response(200, json=_chat_response("not json")))
    )
    with pytest.raises(LlmResponseInvalid):
        await client.structured_completion(
            purpose="generate_questions", system="s", user="u", schema=GeneratedQuestions
        )


async def test_embed_returns_vector_and_cost() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "object": "list",
                "model": "text-embedding-3-small",
                "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}],
                "usage": {"prompt_tokens": 1_000_000, "total_tokens": 1_000_000},
            },
        )

    vector, usage = await _client(httpx.MockTransport(handler)).embed("text")
    assert vector == [0.1, 0.2]
    assert usage.tokens_out == 0
    assert usage.cost_usd == Decimal("0.020000")
