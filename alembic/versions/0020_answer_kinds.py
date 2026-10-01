"""Add answer_kind and choices to problems for richer item types.

Revision ID: 0020_answer_kinds
Revises: 0019_freemium_family_privacy
"""

import re

import sqlalchemy as sa

from alembic import op

revision = "0020_answer_kinds"
down_revision = "0019_freemium_family_privacy"
branch_labels = None
depends_on = None

_FRACTION = re.compile(r"^\s*-?\d+\s*/\s*-?\d+\s*$")
_INTEGER = re.compile(r"^\s*-?\d+\s*$")


def upgrade() -> None:
    columns = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("problems")}
    if "answer_kind" not in columns:
        op.add_column(
            "problems",
            sa.Column("answer_kind", sa.String(length=20), nullable=False, server_default="FREE_TEXT"),
        )
    if "choices" not in columns:
        op.add_column("problems", sa.Column("choices", sa.JSON(), nullable=True))

    # Backfill: a canonical answer that is a bare fraction grades more fairly as
    # FRACTION (equivalents accepted); a bare integer as INTEGER.
    op.execute(
        sa.text(
            "UPDATE problems SET answer_kind = 'FRACTION' "
            "WHERE answer_kind = 'FREE_TEXT' "
            "AND canonical_answer ~ :fraction"
        ).bindparams(fraction=r"^\s*-?\d+\s*/\s*-?\d+\s*$")
    )
    op.execute(
        sa.text(
            "UPDATE problems SET answer_kind = 'INTEGER' "
            "WHERE answer_kind = 'FREE_TEXT' "
            "AND canonical_answer ~ :integer"
        ).bindparams(integer=r"^\s*-?\d+\s*$")
    )


def downgrade() -> None:
    op.drop_column("problems", "choices")
    op.drop_column("problems", "answer_kind")
