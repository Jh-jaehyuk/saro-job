"""Create domain models: job_descriptions, resumes, matches, interview_questions,
resume_processing_jobs, llm_calls.

`embedding`은 pgvector `Vector(1536)`(0001에서 확장 활성). JD/Resume 임베딩에는
ivfflat(vector_cosine_ops) 인덱스를 건다(빈 테이블 생성 OK).

Revision ID: 0003_domain_models
Revises: 0002_organizations_users
Create Date: 2026-05-29
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0003_domain_models"
down_revision: str | None = "0002_organizations_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_descriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("requirements_json", postgresql.JSONB(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_job_descriptions_org_id", "job_descriptions", ["org_id"])
    op.create_index(
        "ix_job_descriptions_embedding",
        "job_descriptions",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_with={"lists": 100},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.create_table(
        "resumes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pdf_key", sa.String(length=512), nullable=False),
        sa.Column("parsed_text", sa.Text(), nullable=True),
        sa.Column("sections_json", postgresql.JSONB(), nullable=True),
        sa.Column("contact_json", postgresql.JSONB(), nullable=True),
        sa.Column("parse_confidence", sa.Float(), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_resumes_org_id", "resumes", ["org_id"])
    op.create_index(
        "ix_resumes_embedding",
        "resumes",
        ["embedding"],
        postgresql_using="ivfflat",
        postgresql_with={"lists": 100},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.create_table(
        "matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "jd_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_descriptions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("category_scores_json", postgresql.JSONB(), nullable=False),
        sa.Column("grade", sa.String(length=8), nullable=False),
        sa.Column("matched_keywords_json", postgresql.JSONB(), nullable=False),
        sa.Column("missing_keywords_json", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("jd_id", "resume_id", name="uq_matches_jd_resume"),
    )
    op.create_index("ix_matches_jd_id", "matches", ["jd_id"])
    op.create_index("ix_matches_resume_id", "matches", ["resume_id"])

    op.create_table(
        "interview_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "match_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("matches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("question_type", sa.String(length=32), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("edited_by_user", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_interview_questions_match_id", "interview_questions", ["match_id"])

    op.create_table(
        "resume_processing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "resume_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resumes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "jd_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("job_descriptions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("error_json", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("step_state_json", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_resume_processing_jobs_resume_id", "resume_processing_jobs", ["resume_id"])
    op.create_index("ix_resume_processing_jobs_jd_id", "resume_processing_jobs", ["jd_id"])

    op.create_table(
        "llm_calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("purpose", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=False),
        sa.Column("tokens_out", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("llm_calls")
    op.drop_index("ix_resume_processing_jobs_jd_id", table_name="resume_processing_jobs")
    op.drop_index("ix_resume_processing_jobs_resume_id", table_name="resume_processing_jobs")
    op.drop_table("resume_processing_jobs")
    op.drop_index("ix_interview_questions_match_id", table_name="interview_questions")
    op.drop_table("interview_questions")
    op.drop_index("ix_matches_resume_id", table_name="matches")
    op.drop_index("ix_matches_jd_id", table_name="matches")
    op.drop_table("matches")
    op.drop_index("ix_resumes_embedding", table_name="resumes")
    op.drop_index("ix_resumes_org_id", table_name="resumes")
    op.drop_table("resumes")
    op.drop_index("ix_job_descriptions_embedding", table_name="job_descriptions")
    op.drop_index("ix_job_descriptions_org_id", table_name="job_descriptions")
    op.drop_table("job_descriptions")
