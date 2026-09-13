"""Snapshot curriculum scope on diagnostic sessions.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("diagnostic_sessions")}
    if "curriculum_id" not in columns:
        op.add_column(
            "diagnostic_sessions", sa.Column("curriculum_id", sa.UUID(), nullable=True)
        )
    if "curriculum_enrollment_id" not in columns:
        op.add_column(
            "diagnostic_sessions",
            sa.Column("curriculum_enrollment_id", sa.UUID(), nullable=True),
        )

    inspector = sa.inspect(op.get_bind())
    constrained = {
        tuple(key.get("constrained_columns") or [])
        for key in inspector.get_foreign_keys("diagnostic_sessions")
    }
    if ("curriculum_id",) not in constrained:
        op.create_foreign_key(
            "fk_diagnostic_sessions_curriculum_id",
            "diagnostic_sessions",
            "curricula",
            ["curriculum_id"],
            ["id"],
        )
    if ("curriculum_enrollment_id",) not in constrained:
        op.create_foreign_key(
            "fk_diagnostic_sessions_curriculum_enrollment_id",
            "diagnostic_sessions",
            "student_curriculum_enrollments",
            ["curriculum_enrollment_id"],
            ["id"],
        )

    indexes = {
        index["name"] for index in sa.inspect(op.get_bind()).get_indexes("diagnostic_sessions")
    }
    if "ix_diagnostic_sessions_curriculum_id" not in indexes:
        op.create_index(
            "ix_diagnostic_sessions_curriculum_id", "diagnostic_sessions", ["curriculum_id"]
        )
    if "ix_diagnostic_sessions_curriculum_enrollment_id" not in indexes:
        op.create_index(
            "ix_diagnostic_sessions_curriculum_enrollment_id",
            "diagnostic_sessions",
            ["curriculum_enrollment_id"],
        )

    op.get_bind().execute(
        sa.text(
            """
            UPDATE diagnostic_sessions ds
            SET curriculum_id = sk.curriculum_id,
                curriculum_enrollment_id = (
                    SELECT e.id
                    FROM student_curriculum_enrollments e
                    WHERE e.student_id = ds.student_id
                      AND e.curriculum_id = sk.curriculum_id
                    ORDER BY e.effective_from DESC
                    LIMIT 1
                )
            FROM skills sk
            WHERE sk.id = ds.target_skill_id AND ds.curriculum_id IS NULL
            """
        )
    )


def downgrade() -> None:
    # Snapshot columns are intentionally retained on downgrade to avoid severing
    # historical evidence from the curriculum version that produced it.
    pass
