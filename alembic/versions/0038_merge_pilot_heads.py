"""merge multi-child practice links and collaboration lineages

Revision ID: 0038_merge_pilot_heads
Revises: 0037_board_images, 0037_learner_session_last_seen
Create Date: 2026-10-17

Unifies the two heads that diverged at 0035_extension_mode:
main's collaboration chain (0036_collaboration -> 0037_board_images) and
the #427 multi-child chain (0036_multi_child_practice_links ->
0037_learner_session_last_seen). Lineage union only — no schema changes;
both branches' DDL is applied by their own revisions.
"""

revision = "0038_merge_pilot_heads"
down_revision = ("0037_board_images", "0037_learner_session_last_seen")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
