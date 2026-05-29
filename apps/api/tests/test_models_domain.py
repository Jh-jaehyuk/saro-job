"""도메인 모델 메타데이터 등록 검증(DB 불필요, 경량)."""

from app.models import Base


def test_all_domain_tables_registered() -> None:
    tables = set(Base.metadata.tables.keys())
    assert {
        "organizations",
        "users",
        "job_descriptions",
        "resumes",
        "matches",
        "interview_questions",
        "resume_processing_jobs",
        "llm_calls",
    } <= tables


def test_match_has_unique_jd_resume_constraint() -> None:
    match = Base.metadata.tables["matches"]
    uniques = [c for c in match.constraints if c.__class__.__name__ == "UniqueConstraint"]
    cols = {tuple(sorted(col.name for col in u.columns)) for u in uniques}
    assert ("jd_id", "resume_id") in cols


def test_embedding_columns_present() -> None:
    assert "embedding" in Base.metadata.tables["resumes"].columns
    assert "embedding" in Base.metadata.tables["job_descriptions"].columns
