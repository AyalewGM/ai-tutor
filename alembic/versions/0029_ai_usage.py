"""AI usage ledger, per-model cost rates, and per-family daily limits.

Revision ID: 0029_ai_usage
Revises: 0028_region_codes
"""

import sqlalchemy as sa

from alembic import op

revision = "0029_ai_usage"
down_revision = "0028_region_codes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "ai_usage_events" not in tables:
        op.create_table(
            "ai_usage_events",
            sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "family_user_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id"),
                nullable=True,
            ),
            sa.Column(
                "student_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("students.id"),
                nullable=True,
            ),
            sa.Column(
                "session_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("tutor_sessions.id"),
                nullable=True,
            ),
            sa.Column("action", sa.String(40), nullable=False),
            sa.Column("provider", sa.String(40), nullable=True),
            sa.Column("model", sa.String(80), nullable=True),
            sa.Column("source", sa.String(20), nullable=False),
            sa.Column("input_tokens", sa.Integer, nullable=True),
            sa.Column("output_tokens", sa.Integer, nullable=True),
            sa.Column("tokens_estimated", sa.Boolean, nullable=False, server_default=sa.false()),
            sa.Column("estimated_cost_usd", sa.Numeric(12, 6), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_ai_usage_events_family_user_id", "ai_usage_events", ["family_user_id"])
        op.create_index("ix_ai_usage_events_student_id", "ai_usage_events", ["student_id"])
        op.create_index("ix_ai_usage_events_session_id", "ai_usage_events", ["session_id"])
        op.create_index("ix_ai_usage_events_created_at", "ai_usage_events", ["created_at"])

    if "ai_model_rates" not in tables:
        op.create_table(
            "ai_model_rates",
            sa.Column("provider", sa.String(40), primary_key=True),
            sa.Column("model", sa.String(80), primary_key=True),
            sa.Column("input_usd_per_1m", sa.Numeric(10, 4), nullable=False),
            sa.Column("output_usd_per_1m", sa.Numeric(10, 4), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.execute(
            sa.text(
                "INSERT INTO ai_model_rates (provider, model, input_usd_per_1m, "
                "output_usd_per_1m, updated_at) VALUES "
                "('openai', 'gpt-5', 1.25, 10.00, now()), "
                "('openai', 'gpt-5-mini', 0.25, 2.00, now()), "
                "('openai', 'gpt-4o-mini', 0.15, 0.60, now()), "
                "('gemini', 'gemini-3.8-flash', 0.30, 2.50, now()), "
                "('gemini', 'gemini-2.5-flash', 0.30, 2.50, now())"
            )
        )

    parent_cols = {c["name"] for c in inspector.get_columns("parent_profiles")}
    if "ai_daily_limit" not in parent_cols:
        op.add_column("parent_profiles", sa.Column("ai_daily_limit", sa.Integer))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    parent_cols = {c["name"] for c in inspector.get_columns("parent_profiles")}
    if "ai_daily_limit" in parent_cols:
        op.drop_column("parent_profiles", "ai_daily_limit")
    tables = set(inspector.get_table_names())
    if "ai_model_rates" in tables:
        op.drop_table("ai_model_rates")
    if "ai_usage_events" in tables:
        op.drop_table("ai_usage_events")
