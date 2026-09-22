"""canonical skill mapping layer

Revision ID: 0018_canonical_skills
Revises: 0017_learner_awards
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0018_canonical_skills"
down_revision = "0017_learner_awards"
branch_labels = None
depends_on = None


def upgrade() -> None:
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
    op.create_index("ix_canonical_skills_code", "canonical_skills", ["code"], unique=True)
    op.create_table(
        "curriculum_skill_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("canonical_skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mapping_type", sa.String(length=40), nullable=False),
        sa.Column("provenance_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["canonical_skill_id"], ["canonical_skills.id"]),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("skill_id", name="uq_curriculum_skill_mapping_skill"),
    )
    op.create_index("ix_curriculum_skill_mappings_canonical_skill_id", "curriculum_skill_mappings", ["canonical_skill_id"])
    op.create_index("ix_curriculum_skill_mappings_skill_id", "curriculum_skill_mappings", ["skill_id"])


def downgrade() -> None:
    op.drop_index("ix_curriculum_skill_mappings_skill_id", table_name="curriculum_skill_mappings")
    op.drop_index("ix_curriculum_skill_mappings_canonical_skill_id", table_name="curriculum_skill_mappings")
    op.drop_table("curriculum_skill_mappings")
    op.drop_index("ix_canonical_skills_code", table_name="canonical_skills")
    op.drop_table("canonical_skills")
