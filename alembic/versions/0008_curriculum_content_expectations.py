"""Add curriculum content expectations and explicit skill mappings.

Revision ID: 0008
Revises: 0007

The repository's legacy 0001 migration calls ``Base.metadata.create_all()``.
On a fresh database that can pre-create tables registered by later model
imports. This migration is therefore intentionally idempotent at the
schema-object level, matching the approach used by 0006.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0008"
down_revision = "0007"
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


def _ensure_expectations() -> None:
    if not _table_exists("curriculum_expectations"):
        op.create_table(
            "curriculum_expectations",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("curriculum_version", sa.String(length=80), nullable=False),
            sa.Column("source_identifier", sa.String(length=120), nullable=False),
            sa.Column("title", sa.String(length=500), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("strand", sa.String(length=160), nullable=True),
            sa.Column("parent_source_identifier", sa.String(length=120), nullable=True),
            sa.Column("source_uri", sa.Text(), nullable=False),
            sa.Column(
                "provenance_json",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["curriculum_id"], ["curricula.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "curriculum_id",
                "curriculum_version",
                "source_identifier",
                name="uq_expectation_curriculum_version_source",
            ),
        )

    indexes = _index_names("curriculum_expectations")
    if "ix_curriculum_expectations_curriculum_id" not in indexes:
        op.create_index(
            "ix_curriculum_expectations_curriculum_id",
            "curriculum_expectations",
            ["curriculum_id"],
        )
    if "ix_curriculum_expectations_strand" not in indexes:
        op.create_index(
            "ix_curriculum_expectations_strand",
            "curriculum_expectations",
            ["strand"],
        )


def _ensure_mappings() -> None:
    if not _table_exists("expectation_skill_mappings"):
        op.create_table(
            "expectation_skill_mappings",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("expectation_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "mapping_type",
                sa.String(length=40),
                nullable=False,
                server_default="ALIGNS_TO",
            ),
            sa.Column(
                "provenance_json",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["curriculum_id"], ["curricula.id"]),
            sa.ForeignKeyConstraint(
                ["expectation_id"],
                ["curriculum_expectations.id"],
            ),
            sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "expectation_id",
                "skill_id",
                name="uq_expectation_skill_mapping",
            ),
        )

    indexes = _index_names("expectation_skill_mappings")
    for name, columns in (
        ("ix_expectation_skill_mappings_curriculum_id", ["curriculum_id"]),
        ("ix_expectation_skill_mappings_expectation_id", ["expectation_id"]),
        ("ix_expectation_skill_mappings_skill_id", ["skill_id"]),
    ):
        if name not in indexes:
            op.create_index(name, "expectation_skill_mappings", columns)


def upgrade() -> None:
    _ensure_expectations()
    _ensure_mappings()


def downgrade() -> None:
    if _table_exists("expectation_skill_mappings"):
        indexes = _index_names("expectation_skill_mappings")
        for name in (
            "ix_expectation_skill_mappings_skill_id",
            "ix_expectation_skill_mappings_expectation_id",
            "ix_expectation_skill_mappings_curriculum_id",
        ):
            if name in indexes:
                op.drop_index(name, table_name="expectation_skill_mappings")
        op.drop_table("expectation_skill_mappings")

    if _table_exists("curriculum_expectations"):
        indexes = _index_names("curriculum_expectations")
        for name in (
            "ix_curriculum_expectations_strand",
            "ix_curriculum_expectations_curriculum_id",
        ):
            if name in indexes:
                op.drop_index(name, table_name="curriculum_expectations")
        op.drop_table("curriculum_expectations")
