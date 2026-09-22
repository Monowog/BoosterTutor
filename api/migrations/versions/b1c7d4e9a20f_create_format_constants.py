"""create format_constants

Revision ID: b1c7d4e9a20f
Revises: e5d34f3256ae
Create Date: 2026-09-21

ADR 0013. Format-level constants for the fitness function, plus the one row
this project currently has values for. Hand-maintained: nothing writes here
automatically, so the seed below is part of the schema change rather than
something a job will refresh.

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b1c7d4e9a20f"
down_revision: Union[str, Sequence[str], None] = "e5d34f3256ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# The Hobbit, Premier Draft. Every value transcribed by hand from DraftDouble,
# which is where they were derived and where they are still in use.
HOB = {
    "set_code": "hob",
    "event_type": "PremierDraft",
    "format_avg_wr": 56.30,
    "replacement_offset": 3.00,
    "tax_value": 12.00,
    "picks_per_pack": 14,
    "target_creatures": 14,
    "target_removal": 4,
    "target_curve_1": 2,
    "target_curve_2": 8,
    "target_curve_3": 7,
    "target_curve_4": 4,
    "target_curve_5": 2,
    "target_curve_6": 1,
    "source": (
        "target_curve/creatures/removal: derived, DraftDouble "
        "scripts/derive_target_curve.py, 2026-09-19 (target_removal is a floor "
        "until the _removal_ tag is authored across the set); "
        "format_avg_wr: measured, DraftDouble docs/data-sources.md; "
        "picks_per_pack: structural, 17Lands draft data; "
        "replacement_offset: placeholder, never validated; "
        "tax_value: hand-picked 2026-09-21, ADR 0012 -- no measurable basis, "
        "and the three reference drafts gave no evidence for its magnitude"
    ),
}


def upgrade() -> None:
    """Upgrade schema."""
    format_constants = op.create_table(
        "format_constants",
        sa.Column("set_code", sa.String(length=8), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("format_avg_wr", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("replacement_offset", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("tax_value", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("picks_per_pack", sa.Integer(), nullable=False),
        sa.Column("target_creatures", sa.Integer(), nullable=False),
        sa.Column("target_removal", sa.Integer(), nullable=False),
        sa.Column("target_curve_1", sa.Integer(), nullable=False),
        sa.Column("target_curve_2", sa.Integer(), nullable=False),
        sa.Column("target_curve_3", sa.Integer(), nullable=False),
        sa.Column("target_curve_4", sa.Integer(), nullable=False),
        sa.Column("target_curve_5", sa.Integer(), nullable=False),
        sa.Column("target_curve_6", sa.Integer(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "set_code", "event_type", name=op.f("pk_format_constants")
        ),
    )
    # `create_table` hands back the table object, so the seed can be a bulk
    # insert against it rather than raw SQL with the column order repeated.
    op.bulk_insert(format_constants, [HOB])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("format_constants")
