"""curriculum content expectations

Revision ID: 0008
Revises: 0007
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
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
    op.create_index("ix_curriculum_expectations_curriculum_id", "curriculum_expectations", ["curriculum_id"])
    op.create_index("ix_curriculum_expectations_strand", "curriculum_expectations", ["strand"])

    op.create_table(
        "expectation_skill_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("expectation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mapping_type", sa.String(length=40), nullable=False, server_default="ALIGNS_TO"),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["curriculum_id"], ["curricula.id"]),
        sa.ForeignKeyConstraint(["expectation_id"], ["curriculum_expectations.id"]),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("expectation_id", "skill_id", name="uq_expectation_skill_mapping"),
    )
    op.create_index("ix_expectation_skill_mappings_curriculum_id", "expectation_skill_mappings", ["curriculum_id"])
    op.create_index("ix_expectation_skill_mappings_expectation_id", "expectation_skill_mappings", ["expectation_id"])
    op.create_index("ix_expectation_skill_mappings_skill_id", "expectation_skill_mappings", ["skill_id"])


def downgrade() -> None:
    op.drop_index("ix_expectation_skill_mappings_skill_id", table_name="expectation_skill_mappings")
    op.drop_index("ix_expectation_skill_mappings_expectation_id", table_name="expectation_skill_mappings")
    op.drop_index("ix_expectation_skill_mappings_curriculum_id", table_name="expectation_skill_mappings")
    op.drop_table("expectation_skill_mappings")
    op.drop_index("ix_curriculum_expectations_strand", table_name="curriculum_expectations")
    op.drop_index("ix_curriculum_expectations_curriculum_id", table_name="curriculum_expectations")
    op.drop_table("curriculum_expectations")
