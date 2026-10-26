"""파이프라인(`run_resume_pipeline`) 통합 테스트.

fake LLM/PDF/storage를 주입해 단계 부수효과(Resume/Match/Question/LlmCall/state)를
real postgres에서 검증한다. 실 어댑터 end-to-end는 어댑터 PR.
"""

import asyncio
import uuid
from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
import pytest_asyncio
from app.core.config import get_settings
from app.core.exceptions import LlmBudgetExceeded
from app.models.interview_question import InterviewQuestion
from app.models.job_description import JobDescription
from app.models.llm_call import LlmCall
from app.models.match import Match
from app.models.organization import Organization
from app.models.resume import Resume
from app.models.resume_processing_job import ResumeProcessingJob
from app.tasks.process_resume import run_resume_pipeline
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from .fakes import (
    FakeLLMClient,
    FakePDFExtractor,
    FakeStorage,
    RecordingProgressPublisher,
)


@pytest_asyncio.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """테스트 전용 NullPool 세션 팩토리(글로벌 엔진과 격리)."""
    engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


async def _seed(
    factory: async_sessionmaker[AsyncSession],
    *,
    jd_keywords: list[str],
    jd_embedding: list[float] | None = None,
) -> tuple[uuid.UUID, uuid.UUID]:
    """org/jd/resume/job을 시드하고 (resume_id, jd_id) 반환."""
    async with factory() as session, session.begin():
        org = Organization(name="t")
        session.add(org)
        await session.flush()
        jd = JobDescription(
            org_id=org.id,
            title="JD",
            raw_text="...",
            requirements_json={"keywords": jd_keywords},
            embedding=jd_embedding,
        )
        resume = Resume(org_id=org.id, pdf_key=f"org_{org.id}/resume_{uuid.uuid4()}.pdf")
        session.add_all([jd, resume])
        await session.flush()
        job = ResumeProcessingJob(
            resume_id=resume.id, jd_id=jd.id, state="queued", step_state_json={}
        )
        session.add(job)
        await session.flush()
        return resume.id, jd.id


def _run(coro: object) -> None:
    asyncio.run(coro)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_pipeline_high_grade_creates_match_and_questions(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    # 이력서·JD가 동일한 키워드/임베딩 → 상 등급
    resume_id, jd_id = await _seed(
        session_factory,
        jd_keywords=["python", "fastapi"],
        jd_embedding=[1.0] + [0.0] * 1535,
    )
    llm = FakeLLMClient()
    await run_resume_pipeline(
        session_factory,
        resume_id=resume_id,
        jd_id=jd_id,
        storage=FakeStorage(),
        pdf=FakePDFExtractor(),
        llm=llm,
        publisher=RecordingProgressPublisher(),
    )

    async with session_factory() as s:
        resume = await s.get_one(Resume, resume_id)
        match = (await s.execute(select(Match).where(Match.resume_id == resume_id))).scalar_one()
        questions = (
            (
                await s.execute(
                    select(InterviewQuestion).where(InterviewQuestion.match_id == match.id)
                )
            )
            .scalars()
            .all()
        )
        llm_calls = (await s.execute(select(LlmCall))).scalars().all()
        job = (
            await s.execute(
                select(ResumeProcessingJob).where(ResumeProcessingJob.resume_id == resume_id)
            )
        ).scalar_one()

    assert resume.parsed_text == "이력서 본문 텍스트"
    assert resume.embedding is not None and len(resume.embedding) == 1536
    assert match.grade == "상"
    assert len(questions) == 2
    assert {c.purpose for c in llm_calls} == {
        "resume_analysis",
        "embed",
        "generate_questions",
    }
    assert job.state == "done"
    assert job.step_state_json == {
        "parsed": True,
        "analyzed": True,
        "embedded": True,
        "scored": True,
        "questions": True,
    }
    assert llm.completion_calls == ["resume_analysis", "generate_questions"]
    assert llm.embed_calls == 1


@pytest.mark.asyncio
async def test_pipeline_low_grade_skips_question_generation(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    # JD 키워드와 이력서 키워드가 완전히 다르고 임베딩도 직교 → 하 등급
    resume_id, jd_id = await _seed(
        session_factory,
        jd_keywords=["rust", "go"],
        jd_embedding=[1.0] + [0.0] * 1535,
    )
    llm = FakeLLMClient()
    llm.embedding = [0.0, 1.0] + [0.0] * 1534  # JD와 직교
    await run_resume_pipeline(
        session_factory,
        resume_id=resume_id,
        jd_id=jd_id,
        storage=FakeStorage(),
        pdf=FakePDFExtractor(),
        llm=llm,
        publisher=RecordingProgressPublisher(),
    )

    async with session_factory() as s:
        match = (await s.execute(select(Match).where(Match.resume_id == resume_id))).scalar_one()
        questions = (await s.execute(select(InterviewQuestion))).scalars().all()

    assert match.grade == "하"
    assert questions == []
    # 질문 생성 LLM 호출은 일어나지 않음.
    assert llm.completion_calls == ["resume_analysis"]


@pytest.mark.asyncio
async def test_pipeline_is_idempotent(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    resume_id, jd_id = await _seed(
        session_factory,
        jd_keywords=["python", "fastapi"],
        jd_embedding=[1.0] + [0.0] * 1535,
    )
    llm = FakeLLMClient()
    publisher = RecordingProgressPublisher()
    args = {
        "resume_id": resume_id,
        "jd_id": jd_id,
        "storage": FakeStorage(),
        "pdf": FakePDFExtractor(),
        "llm": llm,
        "publisher": publisher,
    }
    await run_resume_pipeline(session_factory, **args)  # type: ignore[arg-type]
    await run_resume_pipeline(session_factory, **args)  # type: ignore[arg-type]

    async with session_factory() as s:
        matches = (await s.execute(select(Match))).scalars().all()
        questions = (await s.execute(select(InterviewQuestion))).scalars().all()
        llm_calls = (await s.execute(select(LlmCall))).scalars().all()

    # Match는 UNIQUE(jd, resume) — 1개 유지.
    assert len(matches) == 1
    # 질문도 2개만(재실행 시 questions 단계 skip).
    assert len(questions) == 2
    # LLM 호출도 1회분만 기록(2회분이 아님).
    assert len(llm_calls) == 3
    # 두 번째 실행에선 새 LLM 호출 0회.
    assert llm.embed_calls == 1


@pytest.mark.asyncio
async def test_pipeline_failure_sets_failed_state(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    resume_id, jd_id = await _seed(
        session_factory,
        jd_keywords=["python"],
        jd_embedding=[1.0] + [0.0] * 1535,
    )

    class _BoomLLM(FakeLLMClient):
        async def structured_completion(
            self,
            *,
            purpose: str,
            system: str,
            user: str,
            schema: type,  # type: ignore[override]
        ):
            raise RuntimeError("LLM 일시 오류")

    with pytest.raises(RuntimeError, match="LLM 일시 오류"):
        await run_resume_pipeline(
            session_factory,
            resume_id=resume_id,
            jd_id=jd_id,
            storage=FakeStorage(),
            pdf=FakePDFExtractor(),
            llm=_BoomLLM(),
            publisher=RecordingProgressPublisher(),
        )

    async with session_factory() as s:
        job = (
            await s.execute(
                select(ResumeProcessingJob).where(ResumeProcessingJob.resume_id == resume_id)
            )
        ).scalar_one()
    assert job.state == "failed"
    assert job.error_json is not None
    assert job.error_json["type"] == "RuntimeError"


@pytest.mark.asyncio
async def test_pipeline_publishes_progress(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    resume_id, jd_id = await _seed(
        session_factory,
        jd_keywords=["python", "fastapi"],
        jd_embedding=[1.0] + [0.0] * 1535,
    )
    publisher = RecordingProgressPublisher()
    await run_resume_pipeline(
        session_factory,
        resume_id=resume_id,
        jd_id=jd_id,
        storage=FakeStorage(),
        pdf=FakePDFExtractor(),
        llm=FakeLLMClient(),
        publisher=publisher,
    )
    steps = [e[2] for e in publisher.events]
    assert steps == ["parsed", "analyzed", "embedded", "scored", "done"]


async def _run_default(
    factory: async_sessionmaker[AsyncSession],
    resume_id: uuid.UUID,
    jd_id: uuid.UUID,
    llm: FakeLLMClient,
    **kwargs: object,
) -> None:
    await run_resume_pipeline(
        factory,
        resume_id=resume_id,
        jd_id=jd_id,
        storage=FakeStorage(),
        pdf=FakePDFExtractor(),
        llm=llm,
        publisher=RecordingProgressPublisher(),
        **kwargs,  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_pipeline_records_org_id_on_llm_calls(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    resume_id, jd_id = await _seed(
        session_factory, jd_keywords=["python", "fastapi"], jd_embedding=[1.0] + [0.0] * 1535
    )
    await _run_default(session_factory, resume_id, jd_id, FakeLLMClient())

    async with session_factory() as s:
        org_id = (await s.get_one(Resume, resume_id)).org_id
        llm_calls = (await s.execute(select(LlmCall))).scalars().all()
    assert llm_calls and all(c.org_id == org_id for c in llm_calls)


@pytest.mark.asyncio
async def test_pipeline_reuses_resume_analysis_for_second_jd(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    resume_id, jd_id = await _seed(
        session_factory, jd_keywords=["python", "fastapi"], jd_embedding=[1.0] + [0.0] * 1535
    )
    await _run_default(session_factory, resume_id, jd_id, FakeLLMClient())

    # 같은 이력서를 두 번째 JD로 평가.
    async with session_factory() as session, session.begin():
        org_id = (await session.get_one(Resume, resume_id)).org_id
        jd2 = JobDescription(
            org_id=org_id,
            title="JD2",
            raw_text="...",
            requirements_json={"keywords": ["python"]},
            embedding=[1.0] + [0.0] * 1535,
        )
        session.add(jd2)
        await session.flush()
        session.add(
            ResumeProcessingJob(
                resume_id=resume_id, jd_id=jd2.id, state="queued", step_state_json={}
            )
        )
        jd2_id = jd2.id

    llm = FakeLLMClient()
    await _run_default(session_factory, resume_id, jd2_id, llm)

    # 분석·임베딩은 재사용 — 질문 생성만 새로 호출.
    assert llm.completion_calls == ["generate_questions"]
    assert llm.embed_calls == 0
    async with session_factory() as s:
        match = (
            await s.execute(
                select(Match).where(Match.resume_id == resume_id, Match.jd_id == jd2_id)
            )
        ).scalar_one()
    assert match.grade == "상"


@pytest.mark.asyncio
async def test_pipeline_stops_when_daily_budget_exceeded(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    resume_id, jd_id = await _seed(
        session_factory, jd_keywords=["python"], jd_embedding=[1.0] + [0.0] * 1535
    )
    async with session_factory() as session, session.begin():
        org_id = (await session.get_one(Resume, resume_id)).org_id
        session.add(
            LlmCall(
                org_id=org_id,
                purpose="resume_analysis",
                model="gpt-4o-mini",
                prompt="p",
                response="r",
                tokens_in=1,
                tokens_out=1,
                latency_ms=1,
                cost_usd=Decimal("1.00"),
            )
        )

    llm = FakeLLMClient()
    with pytest.raises(LlmBudgetExceeded):
        await _run_default(session_factory, resume_id, jd_id, llm, daily_budget_usd=Decimal("1.00"))

    assert llm.completion_calls == []
    async with session_factory() as s:
        job = (
            await s.execute(
                select(ResumeProcessingJob).where(ResumeProcessingJob.resume_id == resume_id)
            )
        ).scalar_one()
    assert job.state == "failed"
    assert job.error_json is not None
    assert job.error_json["type"] == "LlmBudgetExceeded"
