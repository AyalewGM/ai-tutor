"""Track learner-session activity for single-live-session links

Revision ID: 0037_learner_session_last_seen
Revises: 0036_multi_child_practice_links
Create Date: 2026-10-17

Adds learner_pass_sessions.last_seen_at so activation can reject while a
session is genuinely in use rather than while a row merely exists. Existing
rows are backfilled from created_at; NULL is treated as "not recently seen".
"""

import sqlalchemy as sa

from alembic import op

revision = "0037_learner_session_last_seen"
down_revision = "0036_multi_child_practice_links"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Some test/install paths create ORM tables before running Alembic. Do not
    # repeat DDL for a column the current model already provisioned.
    inspector = sa.inspect(op.get_bind())
    columns = {c["name"] for c in inspector.get_columns("learner_pass_sessions")}
    if "last_seen_at" in columns:
        return
    op.add_column(
        "learner_pass_sessions",
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "UPDATE learner_pass_sessions SET last_seen_at = created_at "
        "WHERE last_seen_at IS NULL"
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {c["name"] for c in inspector.get_columns("learner_pass_sessions")}
    if "last_seen_at" in columns:
        op.drop_column("learner_pass_sessions", "last_seen_at")
