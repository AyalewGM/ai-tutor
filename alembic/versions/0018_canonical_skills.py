"""canonical skill mapping layer.

Revision ID: 0018_canonical_skills
Revises: 0017_learner_awards

The original 0001 migration creates the *current* SQLAlchemy metadata rather than
an immutable 0001 schema. Fresh databases can therefore already contain tables
added by later model revisions. Keep this migration safe for both fresh and
existing databases until that legacy bootstrap is replaced.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0018_canonical_skills"
down_revision = "0017_learner_awards"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "canonical_skills" not in tables:
        op.create_table(
            "canonical_skills",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("code", sa.String(length=120), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("subject", sa.String(length=80), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code"),
        )
        op.create_index(
            "ix_canonical_skills_code", "canonical_skills", ["code"], unique=True
        )

    if "curriculum_skill_mappings" not in tables:
        op.create_table(
            "curriculum_skill_mappings",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("canonical_skill_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("mapping_type", sa.String(length=40), nullable=False),
            sa.Column(
                "provenance_json",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["canonical_skill_id"], ["canonical_skills.id"]),
            sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("skill_id", name="uq_curriculum_skill_mapping_skill"),
        )
        op.create_index(
            "ix_curriculum_skill_mappings_canonical_skill_id",
            "curriculum_skill_mappings",
            ["canonical_skill_id"],
        )
        op.create_index(
            "ix_curriculum_skill_mappings_skill_id",
            "curriculum_skill_mappings",
            ["skill_id"],
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "curriculum_skill_mappings" in tables:
        op.drop_table("curriculum_skill_mappings")
    if "canonical_skills" in tables:
        op.drop_table("canonical_skills")
