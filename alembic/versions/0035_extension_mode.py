"""extension learning mode support

Revision ID: 0035_extension_mode
Revises: 0034_learning_effectiveness

Adds the optional extension (challenge) tier:
- problem_content_metadata.extension_eligible flags problems that are served
  only on explicit student opt-in and never gate mastery.
The matching TutorState.EXTENSION value is used to mark attempts so they stay
out of mastery evidence and skill-progress gating.
"""

import sqlalchemy as sa

from alembic import op

revision = "0035_extension_mode"
down_revision = "0034_learning_effectiveness"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("problem_content_metadata")}
    if "extension_eligible" not in cols:
        op.add_column(
            "problem_content_metadata",
            sa.Column(
                "extension_eligible",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )


def downgrade() -> None:
    op.drop_column("problem_content_metadata", "extension_eligible")
