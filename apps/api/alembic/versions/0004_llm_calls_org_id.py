"""Add llm_calls.org_id for per-organization daily LLM budget.

기존 기록은 조직을 알 수 없으므로 NULL 허용. (org_id, created_at) 복합 인덱스로
"오늘 이 조직이 쓴 비용" 합산을 빠르게 한다.

Revision ID: 0004_llm_calls_org_id
Revises: 0003_domain_models
Create Date: 2026-10-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_llm_calls_org_id"
down_revision: str | None = "0003_domain_models"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "llm_calls",
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index("ix_llm_calls_org_id_created_at", "llm_calls", ["org_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_llm_calls_org_id_created_at", table_name="llm_calls")
    op.drop_column("llm_calls", "org_id")
