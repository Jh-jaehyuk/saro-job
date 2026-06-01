"""적합도 스코어링 — 순수 함수(stdlib만). 코사인 유사도 + 키워드 매칭 가중합.

DB·외부 의존 없음. 결정론적이라 단위 테스트로 검증한다(AGENTS §9).
"""

import math

from app.schemas.match import Grade
from app.schemas.scoring import ScoreResult

# 카테고리 가중치(합 1.0). MVP 기본값 — 추후 evals로 조정.
_EMBEDDING_WEIGHT = 0.6
_KEYWORD_WEIGHT = 0.4

# grade 임계값.
_GRADE_HIGH = 0.75
_GRADE_MID = 0.5


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """두 벡터의 코사인 유사도. 길이 0 또는 영벡터면 0.0."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _grade(score: float) -> Grade:
    if score >= _GRADE_HIGH:
        return "상"
    if score >= _GRADE_MID:
        return "중"
    return "하"


def score_match(
    *,
    jd_keywords: list[str],
    jd_embedding: list[float],
    resume_keywords: list[str],
    resume_embedding: list[float],
) -> ScoreResult:
    """JD-이력서 적합도. 임베딩 코사인 + 키워드 매칭 비율의 가중합."""
    embedding_score = max(0.0, cosine_similarity(jd_embedding, resume_embedding))

    jd_set = {k.lower() for k in jd_keywords}
    resume_set = {k.lower() for k in resume_keywords}
    matched = sorted(jd_set & resume_set)
    missing = sorted(jd_set - resume_set)
    keyword_score = len(matched) / len(jd_set) if jd_set else 0.0

    overall = _EMBEDDING_WEIGHT * embedding_score + _KEYWORD_WEIGHT * keyword_score

    return ScoreResult(
        overall_score=overall,
        category_scores={"embedding": embedding_score, "keyword": keyword_score},
        grade=_grade(overall),
        matched_keywords=matched,
        missing_keywords=missing,
    )
