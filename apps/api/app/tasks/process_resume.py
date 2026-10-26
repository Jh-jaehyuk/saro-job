"""이력서 처리 파이프라인 오케스트레이션 (ARCHITECTURE §6.2).

단계: parsed → analyzed → embedded → scored → questions → done.
각 단계는 외부 호출(R2/LLM)을 트랜잭션 *밖*에서 하고, 결과 저장 + LlmCall + 상태
갱신만 짧은 트랜잭션 안에서 commit한다(AGENTS §7). `step_state_json` 플래그로 완료
단계를 skip하여 멱등 재시도를 보장한다.

토큰 비용: 같은 이력서를 다른 JD로 다시 평가할 때는 이미 저장된 분석·임베딩을 재사용해
LLM을 다시 부르지 않는다. 각 LLM 호출 전에 조직별 일일 한도를 확인한다.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.core.sse import ProgressPublisher
from app.models.interview_question import InterviewQuestion
from app.models.job_description import JobDescription
from app.models.llm_call import LlmCall
from app.models.match import Match
from app.models.resume import Resume
from app.models.resume_processing_job import ResumeProcessingJob
from app.schemas.llm import GeneratedQuestions, LlmUsage, ResumeAnalysis
from app.services import llm_budget, scoring
from app.services.llm import LLMClient
from app.services.pdf import PDFExtractor
from app.services.storage import ObjectStorage

_STEP_PARSED = "parsed"
_STEP_ANALYZED = "analyzed"
_STEP_EMBEDDED = "embedded"
_STEP_SCORED = "scored"
_STEP_QUESTIONS = "questions"

_QUESTION_GRADES = {"상", "중"}

# 질문 생성 프롬프트에 넣는 부족 키워드 상한 — 질문 3~5개에 이 이상은 필요 없다.
_MAX_MISSING_FOR_QUESTIONS = 10


def _llm_call(
    org_id: uuid.UUID, purpose: str, prompt: str, response: str, usage: LlmUsage
) -> LlmCall:
    return LlmCall(
        org_id=org_id,
        purpose=purpose,
        model=usage.model,
        prompt=prompt,
        response=response,
        tokens_in=usage.tokens_in,
        tokens_out=usage.tokens_out,
        latency_ms=usage.latency_ms,
        cost_usd=usage.cost_usd,
    )


async def _get_job(
    session: AsyncSession, resume_id: uuid.UUID, jd_id: uuid.UUID
) -> ResumeProcessingJob:
    job = (
        await session.execute(
            select(ResumeProcessingJob).where(
                ResumeProcessingJob.resume_id == resume_id,
                ResumeProcessingJob.jd_id == jd_id,
            )
        )
    ).scalar_one()
    return job


async def run_resume_pipeline(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    resume_id: uuid.UUID,
    jd_id: uuid.UUID,
    storage: ObjectStorage,
    pdf: PDFExtractor,
    llm: LLMClient,
    publisher: ProgressPublisher,
    daily_budget_usd: Decimal = Decimal(0),
) -> None:
    """`daily_budget_usd`: 조직별 일일 LLM 비용 한도. 0이면 한도 없음."""
    try:
        await _run_stages(
            session_factory,
            resume_id=resume_id,
            jd_id=jd_id,
            storage=storage,
            pdf=pdf,
            llm=llm,
            publisher=publisher,
            daily_budget_usd=daily_budget_usd,
        )
    except Exception as exc:
        async with session_factory() as session, session.begin():
            job = await _get_job(session, resume_id, jd_id)
            job.state = "failed"
            job.error_json = {"type": type(exc).__name__, "message": str(exc)}
            job.finished_at = datetime.now(UTC)
        raise


async def _run_stages(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    resume_id: uuid.UUID,
    jd_id: uuid.UUID,
    storage: ObjectStorage,
    pdf: PDFExtractor,
    llm: LLMClient,
    publisher: ProgressPublisher,
    daily_budget_usd: Decimal,
) -> None:
    async def ensure_budget() -> None:
        async with session_factory() as session:
            await llm_budget.ensure_within_budget(session, org_id, daily_budget_usd)

    # 시작 표시 + 현재까지 완료된 단계 플래그 로드.
    async with session_factory() as session, session.begin():
        job = await _get_job(session, resume_id, jd_id)
        if job.started_at is None:
            job.started_at = datetime.now(UTC)
        job.state = "processing"
        steps: dict[str, Any] = dict(job.step_state_json)
        resume = await session.get_one(Resume, resume_id)
        pdf_key = resume.pdf_key
        org_id = resume.org_id

    # --- 1. PDF 파싱 (외부: R2 + 파서) ---
    if not steps.get(_STEP_PARSED):
        pdf_bytes = storage.get_object(pdf_key)
        extracted = pdf.extract(pdf_bytes)
        async with session_factory() as session, session.begin():
            resume = await session.get_one(Resume, resume_id)
            resume.parsed_text = extracted.text
            resume.parse_confidence = extracted.confidence
            await _mark_step(session, resume_id, jd_id, _STEP_PARSED)
        await publisher.publish(jd_id, resume_id=resume_id, step=_STEP_PARSED, percent=20)

    # --- 2. 섹션/키워드 분석 (외부: LLM) ---
    if not steps.get(_STEP_ANALYZED):
        async with session_factory() as session:
            resume = await session.get_one(Resume, resume_id)
            parsed_text = resume.parsed_text or ""
            already_analyzed = resume.sections_json is not None
    if not steps.get(_STEP_ANALYZED) and already_analyzed:
        # 다른 JD 평가에서 이미 분석한 이력서 — LLM 재호출 없이 재사용.
        async with session_factory() as session, session.begin():
            await _mark_step(session, resume_id, jd_id, _STEP_ANALYZED)
        await publisher.publish(jd_id, resume_id=resume_id, step=_STEP_ANALYZED, percent=40)
    elif not steps.get(_STEP_ANALYZED):
        await ensure_budget()
        analysis, usage = await llm.structured_completion(
            purpose="resume_analysis",
            system="이력서를 섹션/연락처/키워드로 구조화하라.",
            user=parsed_text,
            schema=ResumeAnalysis,
        )
        async with session_factory() as session, session.begin():
            resume = await session.get_one(Resume, resume_id)
            resume.sections_json = {
                "sections": analysis.sections,
                "keywords": analysis.keywords,
            }
            resume.contact_json = analysis.contact
            session.add(
                _llm_call(org_id, "resume_analysis", parsed_text, analysis.model_dump_json(), usage)
            )
            await _mark_step(session, resume_id, jd_id, _STEP_ANALYZED)
        await publisher.publish(jd_id, resume_id=resume_id, step=_STEP_ANALYZED, percent=40)

    # --- 3. 임베딩 (외부: LLM) ---
    if not steps.get(_STEP_EMBEDDED):
        async with session_factory() as session:
            resume = await session.get_one(Resume, resume_id)
            parsed_text = resume.parsed_text or ""
            already_embedded = resume.embedding is not None
    if not steps.get(_STEP_EMBEDDED) and already_embedded:
        async with session_factory() as session, session.begin():
            await _mark_step(session, resume_id, jd_id, _STEP_EMBEDDED)
        await publisher.publish(jd_id, resume_id=resume_id, step=_STEP_EMBEDDED, percent=60)
    elif not steps.get(_STEP_EMBEDDED):
        await ensure_budget()
        vector, usage = await llm.embed(parsed_text)
        async with session_factory() as session, session.begin():
            resume = await session.get_one(Resume, resume_id)
            resume.embedding = vector
            session.add(_llm_call(org_id, "embed", parsed_text, "<embedding>", usage))
            await _mark_step(session, resume_id, jd_id, _STEP_EMBEDDED)
        await publisher.publish(jd_id, resume_id=resume_id, step=_STEP_EMBEDDED, percent=60)

    # --- 4. 스코어링 (순수) → Match upsert ---
    if not steps.get(_STEP_SCORED):
        async with session_factory() as session, session.begin():
            resume = await session.get_one(Resume, resume_id)
            jd = await session.get_one(JobDescription, jd_id)
            result = scoring.score_match(
                jd_keywords=list(jd.requirements_json.get("keywords", [])),
                jd_embedding=list(jd.embedding) if jd.embedding is not None else [],
                resume_keywords=list((resume.sections_json or {}).get("keywords", [])),
                resume_embedding=(list(resume.embedding) if resume.embedding is not None else []),
            )
            match = (
                await session.execute(
                    select(Match).where(Match.jd_id == jd_id, Match.resume_id == resume_id)
                )
            ).scalar_one_or_none()
            if match is None:
                match = Match(jd_id=jd_id, resume_id=resume_id)
                session.add(match)
            match.overall_score = result.overall_score
            match.category_scores_json = result.category_scores
            match.grade = result.grade
            match.matched_keywords_json = result.matched_keywords
            match.missing_keywords_json = result.missing_keywords
            await _mark_step(session, resume_id, jd_id, _STEP_SCORED)
        await publisher.publish(jd_id, resume_id=resume_id, step=_STEP_SCORED, percent=80)

    # --- 5. 면접 질문 생성 (상/중 등급만, 외부: LLM) ---
    if not steps.get(_STEP_QUESTIONS):
        async with session_factory() as session:
            match = (
                await session.execute(
                    select(Match).where(Match.jd_id == jd_id, Match.resume_id == resume_id)
                )
            ).scalar_one()
            grade = match.grade
            match_id = match.id
            missing = list(match.missing_keywords_json)[:_MAX_MISSING_FOR_QUESTIONS]
        if grade in _QUESTION_GRADES:
            await ensure_budget()
            questions, usage = await llm.structured_completion(
                purpose="generate_questions",
                system="부족 역량 기반 면접 질문을 생성하라.",
                user=json.dumps(missing, ensure_ascii=False),
                schema=GeneratedQuestions,
            )
            async with session_factory() as session, session.begin():
                for order, q in enumerate(questions.items, start=1):
                    session.add(
                        InterviewQuestion(
                            match_id=match_id,
                            question=q.question,
                            question_type=q.question_type,
                            order=order,
                        )
                    )
                session.add(
                    _llm_call(
                        org_id,
                        "generate_questions",
                        json.dumps(missing, ensure_ascii=False),
                        questions.model_dump_json(),
                        usage,
                    )
                )
                await _mark_step(session, resume_id, jd_id, _STEP_QUESTIONS)
        else:
            async with session_factory() as session, session.begin():
                await _mark_step(session, resume_id, jd_id, _STEP_QUESTIONS)

    # --- 완료 ---
    async with session_factory() as session, session.begin():
        job = await _get_job(session, resume_id, jd_id)
        job.state = "done"
        job.finished_at = datetime.now(UTC)
    await publisher.publish(jd_id, resume_id=resume_id, step="done", percent=100)


async def _mark_step(
    session: AsyncSession, resume_id: uuid.UUID, jd_id: uuid.UUID, step: str
) -> None:
    job = await _get_job(session, resume_id, jd_id)
    # JSONB는 in-place 변경을 추적하지 못하므로 새 dict로 재할당한다.
    job.step_state_json = {**job.step_state_json, step: True}


async def process_resume(ctx: dict[str, Any], resume_id: str, jd_id: str) -> None:
    """ARQ 잡 진입점. ctx에서 ports를 꺼내 파이프라인을 실행하는 얇은 래퍼."""
    await run_resume_pipeline(
        cast("async_sessionmaker[AsyncSession]", ctx["session_factory"]),
        resume_id=uuid.UUID(resume_id),
        jd_id=uuid.UUID(jd_id),
        storage=cast(ObjectStorage, ctx["storage"]),
        pdf=cast(PDFExtractor, ctx["pdf"]),
        llm=cast(LLMClient, ctx["llm"]),
        publisher=cast(ProgressPublisher, ctx["publisher"]),
        daily_budget_usd=get_settings().llm_daily_budget_usd_per_org,
    )
