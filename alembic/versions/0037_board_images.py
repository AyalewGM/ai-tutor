"""Private pixel-only homework photos for shared boards."""

import sqlalchemy as sa

from alembic import op

revision = "0037_board_images"
down_revision = "0036_collaboration"
branch_labels = None
depends_on = None


def upgrade():
    # 0001 uses live metadata.create_all; support that existing bootstrap path.
    op.create_table(
        "board_images",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "board_id",
            sa.Uuid(),
            sa.ForeignKey("collaboration_boards.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("operation_id", sa.Uuid(), nullable=False),
        sa.Column("digest", sa.String(64), nullable=False),
        sa.Column("pixels", sa.LargeBinary(), nullable=False),
        sa.UniqueConstraint("board_id", "operation_id"),
        if_not_exists=True,
    )
    op.create_index("ix_board_images_board_id", "board_images", ["board_id"], if_not_exists=True)


def downgrade():
    op.drop_table("board_images")
