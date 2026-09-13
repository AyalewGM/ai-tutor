"""Initial AI Tutor schema.

Revision ID: 0001
Revises:
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import app.models  # noqa: F401
from alembic import op

from app.core.database import Base

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
