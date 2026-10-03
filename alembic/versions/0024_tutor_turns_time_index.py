"""Composite (session_id, created_at) index for tutor_turns analytics scans.

Revision ID: 0024_tutor_turns_time_index
Revises: 0023_cpa_level
"""

import sqlalchemy as sa

from alembic import op

revision = "0024_tutor_turns_time_index"
down_revision = "0023_cpa_level"
branch_labels = None
depends_on = None


def upgrade() -> None:
    indexes = {i["name"] for i in sa.inspect(op.get_bind()).get_indexes("tutor_turns")}
    if "ix_tutor_turns_session_created" not in indexes:
        op.create_index(
            "ix_tutor_turns_session_created",
            "tutor_turns",
            ["session_id", "created_at"],
        )


def downgrade() -> None:
    op.drop_index("ix_tutor_turns_session_created", table_name="tutor_turns")
