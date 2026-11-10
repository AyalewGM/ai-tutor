"""Recoverable board trash and a user-facing board title."""

import sqlalchemy as sa

from alembic import op

revision = "0040_board_management"
down_revision = "0039_board_clear_receipts"
branch_labels = None
depends_on = None


def upgrade():
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("collaboration_boards")}
    if "name" not in columns:
        op.add_column("collaboration_boards", sa.Column(
            "name", sa.String(100), nullable=False, server_default="Family whiteboard"))
    if "deleted_at" not in columns:
        op.add_column("collaboration_boards", sa.Column(
            "deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("collaboration_boards", "deleted_at")
    op.drop_column("collaboration_boards", "name")
