"""Add privacy notice acknowledgements.

Revision ID: 0015_privacy_notice_ack
Revises: 0014_parent_credentials
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0015_privacy_notice_ack"
down_revision: str | None = "0014_parent_credentials"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if not sa.inspect(op.get_bind()).has_table("privacy_notice_acknowledgements"):
        op.create_table(
            "privacy_notice_acknowledgements",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("notice_version", sa.String(length=80), nullable=False),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "notice_version", name="uq_privacy_notice_ack_user_version"),
        )
        op.create_index(
            "ix_privacy_notice_acknowledgements_user_id",
            "privacy_notice_acknowledgements",
            ["user_id"],
        )


def downgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("privacy_notice_acknowledgements"):
        op.drop_index(
            "ix_privacy_notice_acknowledgements_user_id",
            table_name="privacy_notice_acknowledgements",
        )
        op.drop_table("privacy_notice_acknowledgements")
