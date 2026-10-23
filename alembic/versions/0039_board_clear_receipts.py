"""Durable idempotency receipts for scoped family-board clear operations."""

import sqlalchemy as sa
from alembic import op

revision = "0039_board_clear_receipts"
down_revision = "0038_merge_pilot_heads"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "board_clear_receipts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("board_id", sa.Uuid(), sa.ForeignKey("collaboration_boards.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operation_id", sa.Uuid(), nullable=False),
        sa.Column("author", sa.String(80), nullable=False),
        sa.Column("page_id", sa.Uuid(), nullable=True),
        sa.Column("expected_revision", sa.Integer(), nullable=False),
        sa.Column("result_revision", sa.Integer(), nullable=False),
        sa.Column("target_ids", sa.JSON(), nullable=False),
        sa.UniqueConstraint("board_id", "operation_id"),
    )
    op.create_index("ix_board_clear_receipts_board_id", "board_clear_receipts", ["board_id"])


def downgrade():
    op.drop_index("ix_board_clear_receipts_board_id", table_name="board_clear_receipts")
    op.drop_table("board_clear_receipts")
