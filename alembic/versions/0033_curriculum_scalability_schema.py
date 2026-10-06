"""create canonical curriculum scalability schema

Revision ID: 0033_curriculum_scalability_schema
Revises: 0032_curriculum_lifecycle

The legacy bootstrap can create current SQLAlchemy metadata on fresh databases.
Every operation therefore checks the live schema so this migration also works
for production databases upgraded through the historical Alembic chain.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0033_curriculum_scalability_schema"
down_revision = "0032_curriculum_lifecycle"
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _indexes(table: str) -> set[str]:
    return {
        index["name"]
        for index in sa.inspect(op.get_bind()).get_indexes(table)
        if index.get("name")
    }


def _index(table: str, name: str, columns: list[str], *, unique: bool = False) -> None:
    if name not in _indexes(table):
        op.create_index(name, table, columns, unique=unique)


def upgrade() -> None:
    if "canonical_concepts" not in _tables():
        op.create_table(
            "canonical_concepts",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("code", sa.String(120), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("subject", sa.String(80), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code"),
        )
    _index("canonical_concepts", "ix_canonical_concepts_code", ["code"], unique=True)

    if "canonical_skill_concepts" not in _tables():
        op.create_table(
            "canonical_skill_concepts",
            sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("concept_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.ForeignKeyConstraint(["skill_id"], ["canonical_skills.id"]),
            sa.ForeignKeyConstraint(["concept_id"], ["canonical_concepts.id"]),
            sa.PrimaryKeyConstraint("skill_id", "concept_id"),
        )

    if "canonical_skill_prerequisites" not in _tables():
        op.create_table(
            "canonical_skill_prerequisites",
            sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("prerequisite_skill_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.ForeignKeyConstraint(["skill_id"], ["canonical_skills.id"]),
            sa.ForeignKeyConstraint(["prerequisite_skill_id"], ["canonical_skills.id"]),
            sa.PrimaryKeyConstraint("skill_id", "prerequisite_skill_id"),
        )

    if "canonical_misconceptions" not in _tables():
        op.create_table(
            "canonical_misconceptions",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("code", sa.String(120), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("canonical_skill_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.ForeignKeyConstraint(["canonical_skill_id"], ["canonical_skills.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code"),
        )
    _index("canonical_misconceptions", "ix_canonical_misconceptions_code", ["code"], unique=True)
    _index(
        "canonical_misconceptions",
        "ix_canonical_misconceptions_canonical_skill_id",
        ["canonical_skill_id"],
    )

    if "problem_families" not in _tables():
        op.create_table(
            "problem_families",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("code", sa.String(120), nullable=False),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("canonical_skill_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("generator_key", sa.String(160), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.ForeignKeyConstraint(["canonical_skill_id"], ["canonical_skills.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code"),
        )
    _index("problem_families", "ix_problem_families_code", ["code"], unique=True)
    _index(
        "problem_families",
        "ix_problem_families_canonical_skill_id",
        ["canonical_skill_id"],
    )

    if "curriculum_versions" not in _tables():
        op.create_table(
            "curriculum_versions",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("curriculum_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("version", sa.String(80), nullable=False),
            sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True),
            sa.Column("source_uri", sa.Text(), nullable=True),
            sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("review_status", sa.String(30), nullable=False, server_default="DRAFT"),
            sa.Column("lifecycle_status", sa.String(30), nullable=False, server_default="DRAFT"),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.ForeignKeyConstraint(["curriculum_id"], ["curricula.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "curriculum_id",
                "version",
                name="uq_curriculum_versions_curriculum_version",
            ),
        )
    _index("curriculum_versions", "ix_curriculum_versions_curriculum_id", ["curriculum_id"])
    _index(
        "curriculum_versions",
        "ix_curriculum_versions_lifecycle_status",
        ["lifecycle_status"],
    )

    if "curriculum_standards" not in _tables():
        op.create_table(
            "curriculum_standards",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("curriculum_version_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("code", sa.String(160), nullable=False),
            sa.Column("title", sa.String(500), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("strand", sa.String(160), nullable=True),
            sa.Column("sequence", sa.Integer(), nullable=True),
            sa.Column("source_uri", sa.Text(), nullable=True),
            sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.ForeignKeyConstraint(["curriculum_version_id"], ["curriculum_versions.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "curriculum_version_id",
                "code",
                name="uq_curriculum_standard_version_code",
            ),
        )
    _index(
        "curriculum_standards",
        "ix_curriculum_standards_curriculum_version_id",
        ["curriculum_version_id"],
    )
    _index("curriculum_standards", "ix_curriculum_standards_code", ["code"])

    if "standard_skill_mappings" not in _tables():
        op.create_table(
            "standard_skill_mappings",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("standard_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("canonical_skill_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("mapping_type", sa.String(40), nullable=False, server_default="ALIGNS_TO"),
            sa.Column("coverage", sa.String(40), nullable=True),
            sa.Column("review_status", sa.String(30), nullable=False, server_default="DRAFT"),
            sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("reviewed_by", sa.String(120), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["standard_id"], ["curriculum_standards.id"]),
            sa.ForeignKeyConstraint(["canonical_skill_id"], ["canonical_skills.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "standard_id",
                "canonical_skill_id",
                name="uq_standard_canonical_skill_mapping",
            ),
        )
    _index("standard_skill_mappings", "ix_standard_skill_mappings_standard_id", ["standard_id"])
    _index(
        "standard_skill_mappings",
        "ix_standard_skill_mappings_canonical_skill_id",
        ["canonical_skill_id"],
    )


def downgrade() -> None:
    tables = _tables()
    for table in (
        "standard_skill_mappings",
        "curriculum_standards",
        "curriculum_versions",
        "problem_families",
        "canonical_misconceptions",
        "canonical_skill_prerequisites",
        "canonical_skill_concepts",
        "canonical_concepts",
    ):
        if table in tables:
            op.drop_table(table)
