"""Add learner awards (badges) table.

Revision ID: 0017_learner_awards
Revises: 0016_spaced_review
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0017_learner_awards"
down_revision: str | None = "0016_spaced_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("learner_awards"):
        return
    op.create_table(
        "learner_awards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("students.id"),
            nullable=False,
        ),
        sa.Column("badge_code", sa.String(50), nullable=False),
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skills.id"),
            nullable=True,
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tutor_sessions.id"),
            nullable=True,
        ),
        sa.Column("metadata_json", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "student_id", "badge_code", "skill_id", name="uq_learner_award"
        ),
    )
    op.create_index("ix_learner_awards_student_id", "learner_awards", ["student_id"])


def downgrade() -> None:
    op.drop_index("ix_learner_awards_student_id", table_name="learner_awards")
    op.drop_table("learner_awards")
