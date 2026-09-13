"""Add adaptive diagnostic session tables.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = set(inspector.get_table_names())

    if "diagnostic_sessions" not in existing:
        op.create_table(
            "diagnostic_sessions",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("student_id", sa.UUID(), nullable=False),
            sa.Column("target_skill_id", sa.UUID(), nullable=False),
            sa.Column("current_skill_id", sa.UUID(), nullable=False),
            sa.Column("blocked_skill_id", sa.UUID(), nullable=True),
            sa.Column("recommended_skill_id", sa.UUID(), nullable=True),
            sa.Column("status", sa.String(length=30), nullable=False),
            sa.Column("placement_reason", sa.String(length=120), nullable=True),
            sa.Column("question_count", sa.Integer(), nullable=False),
            sa.Column("max_questions", sa.Integer(), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
            sa.ForeignKeyConstraint(["target_skill_id"], ["skills.id"]),
            sa.ForeignKeyConstraint(["current_skill_id"], ["skills.id"]),
            sa.ForeignKeyConstraint(["blocked_skill_id"], ["skills.id"]),
            sa.ForeignKeyConstraint(["recommended_skill_id"], ["skills.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_diagnostic_sessions_student_id",
            "diagnostic_sessions",
            ["student_id"],
        )

    inspector = sa.inspect(op.get_bind())
    existing = set(inspector.get_table_names())
    if "diagnostic_attempts" not in existing:
        op.create_table(
            "diagnostic_attempts",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("diagnostic_session_id", sa.UUID(), nullable=False),
            sa.Column("skill_id", sa.UUID(), nullable=False),
            sa.Column("problem_id", sa.UUID(), nullable=False),
            sa.Column("student_answer", sa.Text(), nullable=False),
            sa.Column("normalized_answer", sa.Text(), nullable=True),
            sa.Column("is_correct", sa.Boolean(), nullable=False),
            sa.Column("misconception_id", sa.UUID(), nullable=True),
            sa.Column("evaluation_confidence", sa.Numeric(4, 3), nullable=True),
            sa.Column("sequence_number", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["diagnostic_session_id"],
                ["diagnostic_sessions.id"],
            ),
            sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
            sa.ForeignKeyConstraint(["problem_id"], ["problems.id"]),
            sa.ForeignKeyConstraint(["misconception_id"], ["misconceptions.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_diagnostic_attempts_diagnostic_session_id",
            "diagnostic_attempts",
            ["diagnostic_session_id"],
        )
        op.create_index(
            "ix_diagnostic_attempts_skill_id",
            "diagnostic_attempts",
            ["skill_id"],
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing = set(inspector.get_table_names())
    if "diagnostic_attempts" in existing:
        op.drop_table("diagnostic_attempts")
    if "diagnostic_sessions" in existing:
        op.drop_table("diagnostic_sessions")
