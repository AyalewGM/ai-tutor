"""Plans table: seat limits, AI caps, and USD/CAD pricing.

Replaces the hardcoded free=1/pro=5 seat policy. parent_profiles columns
become explicit per-family overrides; NULL means "follow the plan".

Revision ID: 0030_plans
Revises: 0029_ai_usage
"""

import sqlalchemy as sa

from alembic import op

revision = "0030_plans"
down_revision = "0029_ai_usage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "plans" not in tables:
        op.create_table(
            "plans",
            sa.Column("code", sa.String(40), primary_key=True),
            sa.Column("name", sa.String(120), nullable=False),
            sa.Column("monthly_price_usd", sa.Numeric(10, 2), nullable=False),
            sa.Column("monthly_price_cad", sa.Integer, nullable=False),
            sa.Column("max_students", sa.Integer, nullable=False),
            sa.Column("ai_daily_generations", sa.Integer, nullable=False),
            sa.Column("active", sa.Boolean, nullable=False, server_default=sa.true()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    if "platform_settings" not in tables:
        op.create_table(
            "platform_settings",
            sa.Column("key", sa.String(80), primary_key=True),
            sa.Column("value", sa.String(255), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )

    # 0001's Base.metadata.create_all pre-creates mapped tables on fresh
    # databases, so the existence checks above can skip seeding — seed
    # unconditionally and idempotently instead.
    # CAD = floor(USD x 1.36 placeholder rate): free -> 0, pro -> 13.
    op.execute(
        sa.text(
            "INSERT INTO plans (code, name, monthly_price_usd, monthly_price_cad, "
            "max_students, ai_daily_generations, active, updated_at) VALUES "
            "('free', 'Mihur Free', 0.00, 0, 1, 50, true, now()), "
            "('pro', 'Mihur Pro', 9.99, 13, 5, 300, true, now()) "
            "ON CONFLICT (code) DO NOTHING"
        )
    )
    op.execute(
        sa.text(
            "INSERT INTO platform_settings (key, value, updated_at) VALUES "
            "('usd_to_cad_3yr_avg', '1.36', now()) ON CONFLICT (key) DO NOTHING"
        )
    )

    # Plans now own tier semantics and the seat policy.
    constraints = {c["name"] for c in inspector.get_check_constraints("parent_profiles")}
    for name in (
        "ck_parent_subscription_seat_policy",
        "ck_parent_max_students_positive",
        "ck_parent_subscription_tier",
    ):
        if name in constraints:
            op.drop_constraint(name, "parent_profiles", type_="check")

    # Column becomes a per-family override; NULL = plan's max_students.
    # Existing free(1)/pro(5) values match the plan defaults, so clearing
    # them preserves behavior while letting plan changes propagate.
    op.alter_column("parent_profiles", "max_students", nullable=True)
    op.execute(
        sa.text(
            "UPDATE parent_profiles SET max_students = NULL "
            "WHERE (subscription_tier = 'free' AND max_students = 1) "
            "OR (subscription_tier = 'pro' AND max_students = 5)"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE parent_profiles SET max_students = CASE "
            "WHEN subscription_tier = 'pro' THEN 5 ELSE 1 END "
            "WHERE max_students IS NULL"
        )
    )
    op.alter_column("parent_profiles", "max_students", nullable=False)
    op.create_check_constraint(
        "ck_parent_subscription_seat_policy",
        "parent_profiles",
        "(subscription_tier = 'free' AND max_students = 1) OR "
        "(subscription_tier = 'pro' AND max_students = 5)",
    )
    op.create_check_constraint(
        "ck_parent_max_students_positive", "parent_profiles", "max_students >= 1"
    )
    op.create_check_constraint(
        "ck_parent_subscription_tier",
        "parent_profiles",
        "subscription_tier IN ('free', 'pro')",
    )
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "platform_settings" in tables:
        op.drop_table("platform_settings")
    if "plans" in tables:
        op.drop_table("plans")
