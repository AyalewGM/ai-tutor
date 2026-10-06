"""record curriculum version lifecycle migration

Revision ID: 0032_curriculum_lifecycle
Revises: 0031_stripe_billing

The curriculum_versions table is part of SQLAlchemy metadata used by fresh
environments, so lifecycle_status may already exist before Alembic runs.
This migration is intentionally idempotent for both metadata-created and
migration-created databases.
"""

import sqlalchemy as sa

from alembic import op

revision = "0032_curriculum_lifecycle"
down_revision = "0031_stripe_billing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("curriculum_versions")}
    if "lifecycle_status" not in columns:
        op.add_column(
            "curriculum_versions",
            sa.Column(
                "lifecycle_status",
                sa.String(length=30),
                nullable=False,
                server_default="DRAFT",
            ),
        )

    indexes = {index["name"] for index in inspector.get_indexes("curriculum_versions")}
    if "ix_curriculum_versions_lifecycle_status" not in indexes:
        op.create_index(
            "ix_curriculum_versions_lifecycle_status",
            "curriculum_versions",
            ["lifecycle_status"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = {index["name"] for index in inspector.get_indexes("curriculum_versions")}
    if "ix_curriculum_versions_lifecycle_status" in indexes:
        op.drop_index(
            "ix_curriculum_versions_lifecycle_status",
            table_name="curriculum_versions",
        )
    columns = {column["name"] for column in inspector.get_columns("curriculum_versions")}
    if "lifecycle_status" in columns:
        op.drop_column("curriculum_versions", "lifecycle_status")
