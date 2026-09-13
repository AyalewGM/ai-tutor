"""Add adaptive diagnostic placement tables.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "diagnostic_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("target_skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("recommended_skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id")),
        sa.Column("recommended_difficulty", sa.Integer()),
        sa.Column("placement_confidence", sa.Numeric(4, 3)),
        sa.Column("result_json", postgresql.JSONB()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_diagnostic_sessions_student_id", "diagnostic_sessions", ["student_id"])
    op.create_index("ix_diagnostic_sessions_target_skill_id", "diagnostic_sessions", ["target_skill_id"])

    op.create_table(
        "diagnostic_skill_states",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("diagnostic_sessions.id"), primary_key=True),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id"), primary_key=True),
        sa.Column("mastery_estimate", sa.Numeric(4, 3), nullable=False, server_default="0.500"),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, server_default="0.000"),
        sa.Column("evidence_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("independent_correct_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("attempted", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "diagnostic_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("diagnostic_sessions.id"), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("skills.id"), nullable=False),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("problems.id"), nullable=False),
        sa.Column("answer", sa.String(500), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("assistance_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("evidence_weight", sa.Numeric(4, 3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_diagnostic_attempts_session_id", "diagnostic_attempts", ["session_id"])
    op.create_index("ix_diagnostic_attempts_skill_id", "diagnostic_attempts", ["skill_id"])


def downgrade() -> None:
    op.drop_index("ix_diagnostic_attempts_skill_id", table_name="diagnostic_attempts")
    op.drop_index("ix_diagnostic_attempts_session_id", table_name="diagnostic_attempts")
    op.drop_table("diagnostic_attempts")
    op.drop_table("diagnostic_skill_states")
    op.drop_index("ix_diagnostic_sessions_target_skill_id", table_name="diagnostic_sessions")
    op.drop_index("ix_diagnostic_sessions_student_id", table_name="diagnostic_sessions")
    op.drop_table("diagnostic_sessions")
