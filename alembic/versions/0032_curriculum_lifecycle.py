"""add curriculum version lifecycle status

Revision ID: 0032_curriculum_lifecycle
Revises: 0031_stripe_billing
"""

import sqlalchemy as sa

from alembic import op

revision = "0032_curriculum_lifecycle"
down_revision = "0031_stripe_billing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "curriculum_versions",
        sa.Column("lifecycle_status", sa.String(length=30), nullable=False, server_default="DRAFT"),
    )
    op.create_index(
        "ix_curriculum_versions_lifecycle_status",
        "curriculum_versions",
        ["lifecycle_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_curriculum_versions_lifecycle_status", table_name="curriculum_versions")
    op.drop_column("curriculum_versions", "lifecycle_status")
