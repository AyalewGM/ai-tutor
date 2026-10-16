"""Private standalone family collaboration boards."""

import sqlalchemy as sa

from alembic import op

revision = "0036_collaboration"
down_revision = "0035_extension_mode"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "collaboration_boards",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("student_id", sa.Uuid(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("closed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_collaboration_boards_student_id", "collaboration_boards", ["student_id"])
    op.create_table(
        "board_operations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "board_id",
            sa.Uuid(),
            sa.ForeignKey("collaboration_boards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("operation_id", sa.Uuid(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("author", sa.String(80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.UniqueConstraint("board_id", "revision"),
        sa.UniqueConstraint("board_id", "operation_id"),
    )
    op.create_index("ix_board_operations_board_id", "board_operations", ["board_id"])


def downgrade():
    op.drop_table("board_operations")
    op.drop_table("collaboration_boards")
