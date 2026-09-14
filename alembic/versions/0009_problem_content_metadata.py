"""Add deterministic curriculum-scoped problem metadata.

Revision ID: 0009
Revises: 0008
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _table_exists(table: str) -> bool:
    return table in set(_inspector().get_table_names())


def _index_names(table: str) -> set[str]:
    return {
        index["name"]
        for index in _inspector().get_indexes(table)
        if index.get("name")
    }


def upgrade() -> None:
    if not _table_exists("problem_content_metadata"):
        op.create_table(
            "problem_content_metadata",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("problem_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("objective", sa.String(length=500), nullable=False),
            sa.Column("evaluation_type", sa.String(length=50), nullable=False),
            sa.Column("diagnostic_eligible", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("guided_eligible", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("independent_eligible", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("mastery_eligible", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("llm_solution_required", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["problem_id"], ["problems.id"]),
            sa.ForeignKeyConstraint(["curriculum_id"], ["curricula.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("problem_id", name="uq_problem_content_metadata_problem"),
        )

    indexes = _index_names("problem_content_metadata")
    for name, columns in (
        ("ix_problem_content_metadata_problem_id", ["problem_id"]),
        ("ix_problem_content_metadata_curriculum_id", ["curriculum_id"]),
    ):
        if name not in indexes:
            op.create_index(name, "problem_content_metadata", columns)


def downgrade() -> None:
    if not _table_exists("problem_content_metadata"):
        return
    indexes = _index_names("problem_content_metadata")
    for name in (
        "ix_problem_content_metadata_curriculum_id",
        "ix_problem_content_metadata_problem_id",
    ):
        if name in indexes:
            op.drop_index(name, table_name="problem_content_metadata")
    op.drop_table("problem_content_metadata")
