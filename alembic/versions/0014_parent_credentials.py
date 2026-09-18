"""Add parent credentials.

Revision ID: 0014_parent_credentials
Revises: 0013_auth_sessions
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0014_parent_credentials"
down_revision: str | None = "0013_auth_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 0001 builds Base.metadata on fresh installs, so remain compatible with both
    # fresh databases and upgrades from an existing pilot database.
    if not sa.inspect(op.get_bind()).has_table("user_credentials"):
        op.create_table(
            "user_credentials",
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id"),
        )


def downgrade() -> None:
    if sa.inspect(op.get_bind()).has_table("user_credentials"):
        op.drop_table("user_credentials")
