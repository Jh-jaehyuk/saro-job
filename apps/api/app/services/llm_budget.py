"""조직별 일일 LLM 비용 한도.

`LlmCall.cost_usd`를 UTC 자정 기준으로 합산해 한도와 비교한다. 수익화 전 서비스라
한 조직이 예산을 소진하지 않도록, enqueue 전(API)과 각 LLM 호출 전(워커)에 확인한다.
세션은 인자로 받고 commit하지 않는다(AGENTS §7).
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import LlmBudgetExceeded
from app.models.llm_call import LlmCall


def _start_of_today_utc() -> datetime:
    return datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


async def spent_today_usd(session: AsyncSession, org_id: uuid.UUID) -> Decimal:
    total = (
        await session.execute(
            select(func.coalesce(func.sum(LlmCall.cost_usd), 0)).where(
                LlmCall.org_id == org_id,
                LlmCall.created_at >= _start_of_today_utc(),
            )
        )
    ).scalar_one()
    return Decimal(total)


async def ensure_within_budget(session: AsyncSession, org_id: uuid.UUID, limit: Decimal) -> None:
    """오늘 사용액이 한도 이상이면 `LlmBudgetExceeded`. limit<=0이면 한도 없음."""
    if limit <= 0:
        return
    spent = await spent_today_usd(session, org_id)
    if spent >= limit:
        raise LlmBudgetExceeded(details={"spent_usd": str(spent), "limit_usd": str(limit)})
