"""Add daily_goal_questions to students for learner-picked daily targets.

Revision ID: 0022_daily_goal
Revises: 0021_learn_content
"""

import sqlalchemy as sa

from alembic import op

revision = "0022_daily_goal"
down_revision = "0021_learn_content"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("students")}
    if "daily_goal_questions" not in columns:
        op.add_column(
            "students", sa.Column("daily_goal_questions", sa.Integer(), nullable=True)
        )


def downgrade() -> None:
    op.drop_column("students", "daily_goal_questions")
