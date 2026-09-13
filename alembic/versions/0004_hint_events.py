"""Add persisted graduated hint events.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "hint_events" in set(inspector.get_table_names()):
        return
    op.create_table(
        "hint_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("problem_id", sa.UUID(), nullable=False),
        sa.Column("attempt_id", sa.UUID(), nullable=True),
        sa.Column("tutor_turn_id", sa.UUID(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("trigger", sa.String(length=50), nullable=False),
        sa.Column("generation_source", sa.String(length=30), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("llm_model", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["tutor_sessions.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"]),
        sa.ForeignKeyConstraint(["attempt_id"], ["attempts.id"]),
        sa.ForeignKeyConstraint(["tutor_turn_id"], ["tutor_turns.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("level >= 1 AND level <= 4", name="ck_hint_events_level"),
    )
    op.create_index("ix_hint_events_session_id", "hint_events", ["session_id"])
    op.create_index("ix_hint_events_problem_id", "hint_events", ["problem_id"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "hint_events" in set(inspector.get_table_names()):
        op.drop_table("hint_events")
