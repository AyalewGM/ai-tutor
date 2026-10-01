"""Add learn_content to skills for pre-practice instruction panels.

Revision ID: 0021_learn_content
Revises: 0020_answer_kinds
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0021_learn_content"
down_revision = "0020_answer_kinds"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("skills")}
    if "learn_content" not in columns:
        op.add_column("skills", sa.Column("learn_content", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("skills", "learn_content")
