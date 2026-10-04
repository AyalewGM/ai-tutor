"""Stripe billing fields: plan price ids and per-family subscription state.

Adds Stripe Price ids to plans (operator-set) and the webhook-managed
subscription mirror on parent_profiles.

Revision ID: 0031_stripe_billing
Revises: 0030_plans
"""

import sqlalchemy as sa

from alembic import op

revision = "0031_stripe_billing"
down_revision = "0030_plans"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    plan_cols = {c["name"] for c in inspector.get_columns("plans")}
    if "stripe_price_id_usd" not in plan_cols:
        op.add_column("plans", sa.Column("stripe_price_id_usd", sa.String(255)))
    if "stripe_price_id_cad" not in plan_cols:
        op.add_column("plans", sa.Column("stripe_price_id_cad", sa.String(255)))

    profile_cols = {c["name"] for c in inspector.get_columns("parent_profiles")}
    if "stripe_customer_id" not in profile_cols:
        op.add_column("parent_profiles", sa.Column("stripe_customer_id", sa.String(255)))
        op.create_index(
            "ix_parent_profiles_stripe_customer_id",
            "parent_profiles",
            ["stripe_customer_id"],
            unique=True,
        )
    if "stripe_subscription_id" not in profile_cols:
        op.add_column("parent_profiles", sa.Column("stripe_subscription_id", sa.String(255)))
    if "subscription_status" not in profile_cols:
        op.add_column("parent_profiles", sa.Column("subscription_status", sa.String(20)))
    if "trial_ends_at" not in profile_cols:
        op.add_column("parent_profiles", sa.Column("trial_ends_at", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("parent_profiles", "trial_ends_at")
    op.drop_column("parent_profiles", "subscription_status")
    op.drop_column("parent_profiles", "stripe_subscription_id")
    op.drop_index("ix_parent_profiles_stripe_customer_id", table_name="parent_profiles")
    op.drop_column("parent_profiles", "stripe_customer_id")
    op.drop_column("plans", "stripe_price_id_cad")
    op.drop_column("plans", "stripe_price_id_usd")
