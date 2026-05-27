"""Enable pgvector extension.

이력서·JD 임베딩 컬럼이 의존하는 `vector` 타입을 사용 가능하게 만든다.
이 PR에는 도메인 테이블이 없고, 다음 PR에서 임베딩 컬럼이 도입될 때 이 확장이
필요하므로 분리된 마이그레이션으로 미리 깔아 둔다.

Revision ID: 0001_enable_pgvector
Revises:
Create Date: 2026-05-27
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0001_enable_pgvector"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector;")
