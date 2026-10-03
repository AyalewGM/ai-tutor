"""Add cpa_level to tutor_sessions for CPA scaffolding state.

Revision ID: 0023_cpa_level
Revises: 0022_daily_goal
"""

import sqlalchemy as sa

from alembic import op

revision = "0023_cpa_level"
down_revision = "0022_daily_goal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("tutor_sessions")}
    if "cpa_level" not in columns:
        op.add_column(
            "tutor_sessions",
            sa.Column(
                "cpa_level",
                sa.String(length=10),
                server_default="ABSTRACT",
                nullable=False,
            ),
        )


def downgrade() -> None:
    op.drop_column("tutor_sessions", "cpa_level")
