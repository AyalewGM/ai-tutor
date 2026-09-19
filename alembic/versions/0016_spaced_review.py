"""Add spaced review schedules and independent evidence timestamps.

Revision ID: 0016_spaced_review
Revises: 0015_privacy_notice_ack
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0016_spaced_review"
down_revision: str | None = "0015_privacy_notice_ack"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("skill_review_schedules"):
        op.create_table(
            "skill_review_schedules",
            sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("interval_index", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("status", sa.String(length=30), nullable=False, server_default="SCHEDULED"),
            sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("last_outcome", sa.String(length=40), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
            sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
            sa.PrimaryKeyConstraint("student_id", "skill_id"),
        )
        op.create_index(
            "ix_skill_review_schedules_due_at",
            "skill_review_schedules",
            ["due_at"],
        )

    inspector = sa.inspect(bind)
    student_skill_columns = {c["name"] for c in inspector.get_columns("student_skills")}
    if "last_independent_evidence_at" not in student_skill_columns:
        op.add_column(
            "student_skills",
            sa.Column("last_independent_evidence_at", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    student_skill_columns = {c["name"] for c in inspector.get_columns("student_skills")}
    if "last_independent_evidence_at" in student_skill_columns:
        op.drop_column("student_skills", "last_independent_evidence_at")

    inspector = sa.inspect(bind)
    if inspector.has_table("skill_review_schedules"):
        op.drop_index("ix_skill_review_schedules_due_at", table_name="skill_review_schedules")
        op.drop_table("skill_review_schedules")
