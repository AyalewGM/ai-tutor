"""Add active remediation skill to tutor sessions.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-13
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_names() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {column["name"] for column in inspector.get_columns("tutor_sessions")}


def _foreign_key_names() -> set[str]:
    inspector = sa.inspect(op.get_bind())
    return {
        constraint["name"]
        for constraint in inspector.get_foreign_keys("tutor_sessions")
        if constraint.get("name")
    }


def upgrade() -> None:
    columns = _column_names()
    if "active_skill_id" not in columns:
        op.add_column(
            "tutor_sessions",
            sa.Column("active_skill_id", sa.UUID(), nullable=True),
        )
    if "remediation_reason" not in columns:
        op.add_column(
            "tutor_sessions",
            sa.Column("remediation_reason", sa.String(length=120), nullable=True),
        )

    if "fk_tutor_sessions_active_skill" not in _foreign_key_names():
        op.create_foreign_key(
            "fk_tutor_sessions_active_skill",
            "tutor_sessions",
            "skills",
            ["active_skill_id"],
            ["id"],
        )

    op.execute(
        "UPDATE tutor_sessions "
        "SET active_skill_id = primary_skill_id "
        "WHERE active_skill_id IS NULL"
    )


def downgrade() -> None:
    if "fk_tutor_sessions_active_skill" in _foreign_key_names():
        op.drop_constraint("fk_tutor_sessions_active_skill", "tutor_sessions", type_="foreignkey")

    columns = _column_names()
    if "remediation_reason" in columns:
        op.drop_column("tutor_sessions", "remediation_reason")
    if "active_skill_id" in columns:
        op.drop_column("tutor_sessions", "active_skill_id")
