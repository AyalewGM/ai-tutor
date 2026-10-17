"""Per-child practice links, parent invitations, and pilot entitlements.

Revision ID: 0036_multi_child_practice_links
Revises: 0035_extension_mode

- family_practice_passes: uniqueness moves from one-pass-per-family to
  one-pass-per-(parent, child) so each learner gets an independent link.
- learner_pass_sessions: display_name carries the activation-time nickname
  so redemption never mutates the canonical parent-managed learner name.
- parent_invitations: scoped, single-use, hashed-token invites for
  invite-only pilot registration.
- pilot_entitlements: time-bounded non-paying seat grants per family.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0036_multi_child_practice_links"
down_revision = "0035_extension_mode"
branch_labels = None
depends_on = None


def _upgrade_practice_pass_uniqueness() -> None:
    # Revision 0025 conditionally creates this table. On databases bootstrapped
    # from current ORM metadata, the per-child constraint may already exist,
    # while the historical parent-only constraint was never installed.
    constraints = {
        c["name"] for c in sa.inspect(op.get_bind()).get_unique_constraints(
            "family_practice_passes"
        )
    }
    if "uq_family_practice_pass_parent" in constraints:
        op.drop_constraint(
            "uq_family_practice_pass_parent", "family_practice_passes", type_="unique"
        )
    if "uq_family_practice_pass_child" not in constraints:
        op.create_unique_constraint(
            "uq_family_practice_pass_child",
            "family_practice_passes",
            ["parent_profile_id", "student_id"],
        )


def upgrade() -> None:
    _upgrade_practice_pass_uniqueness()
    op.add_column(
        "learner_pass_sessions",
        sa.Column("display_name", sa.String(32), nullable=True),
    )

    op.create_table(
        "parent_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("seats", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "accepted_parent_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("parent_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('PENDING','ACCEPTED','DECLINED','DISABLED')",
            name="ck_parent_invitation_status",
        ),
        sa.UniqueConstraint("token_hash", name="uq_parent_invitation_token"),
    )
    op.create_index(
        "ix_parent_invitations_token_hash", "parent_invitations", ["token_hash"]
    )
    op.create_index("ix_parent_invitations_status", "parent_invitations", ["status"])

    op.create_table(
        "pilot_entitlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "parent_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("parent_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("seats", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column(
            "invitation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("parent_invitations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "source IN ('INVITATION','ADMIN')", name="ck_pilot_entitlement_source"
        ),
        sa.CheckConstraint("seats >= 1", name="ck_pilot_entitlement_seats"),
        sa.UniqueConstraint("parent_profile_id", name="uq_pilot_entitlement_parent"),
    )


def downgrade() -> None:
    op.drop_table("pilot_entitlements")
    op.drop_index("ix_parent_invitations_status", table_name="parent_invitations")
    op.drop_index(
        "ix_parent_invitations_token_hash", table_name="parent_invitations"
    )
    op.drop_table("parent_invitations")
    op.drop_column("learner_pass_sessions", "display_name")
    op.drop_constraint(
        "uq_family_practice_pass_child", "family_practice_passes", type_="unique"
    )
    op.create_unique_constraint(
        "uq_family_practice_pass_parent",
        "family_practice_passes",
        ["parent_profile_id"],
    )
