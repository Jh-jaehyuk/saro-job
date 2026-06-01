"""scoring.py 순수 단위 테스트(DB 없음)."""

import math

from app.services.scoring import cosine_similarity, score_match


def test_cosine_identical_vectors_is_one() -> None:
    assert math.isclose(cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]), 1.0)


def test_cosine_orthogonal_is_zero() -> None:
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_cosine_zero_vector_is_zero() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0
    assert cosine_similarity([], [1.0]) == 0.0


def test_score_match_high_grade() -> None:
    result = score_match(
        jd_keywords=["python", "fastapi"],
        jd_embedding=[1.0, 0.0],
        resume_keywords=["Python", "FastAPI"],  # 대소문자 무시 매칭
        resume_embedding=[1.0, 0.0],
    )
    # 임베딩 1.0 * 0.6 + 키워드 1.0 * 0.4 = 1.0 → 상
    assert math.isclose(result.overall_score, 1.0)
    assert result.grade == "상"
    assert result.matched_keywords == ["fastapi", "python"]
    assert result.missing_keywords == []


def test_score_match_low_grade_and_missing_keywords() -> None:
    result = score_match(
        jd_keywords=["python", "fastapi", "kubernetes"],
        jd_embedding=[1.0, 0.0],
        resume_keywords=["java"],
        resume_embedding=[0.0, 1.0],  # 직교 → 임베딩 0
    )
    # 임베딩 0 * 0.6 + 키워드 0 * 0.4 = 0 → 하
    assert result.overall_score == 0.0
    assert result.grade == "하"
    assert result.matched_keywords == []
    assert set(result.missing_keywords) == {"python", "fastapi", "kubernetes"}


def test_score_match_mid_grade() -> None:
    # 임베딩 1.0*0.6=0.6, 키워드 0/2*0.4=0 → 0.6 → 중
    result = score_match(
        jd_keywords=["go", "rust"],
        jd_embedding=[1.0, 1.0],
        resume_keywords=["python"],
        resume_embedding=[1.0, 1.0],
    )
    assert result.grade == "중"
    assert math.isclose(result.category_scores["embedding"], 1.0)
    assert result.category_scores["keyword"] == 0.0
