"""Add day_type and operational_intent columns to blocks table

Revision ID: 20260111_day_type_cols
Revises: 20260111_wed_pattern_audit
Create Date: 2026-01-11

Adds MEDCOM day-type system columns to blocks table:
- day_type: NORMAL, FEDERAL_HOLIDAY, TRAINING_HOLIDAY, MINIMAL_MANNING, EO_CLOSURE, INAUGURATION_DAY
- operational_intent: NORMAL, REDUCED_CAPACITY, NON_OPERATIONAL
- actual_date: For observed holidays (e.g., July 4 Sat → observed July 3 Fri)

This enables proper federal holiday handling per OPM observed date rules
and future support for DONSA, minimal manning, and EO closures.
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260111_day_type_cols"
down_revision: str | None = "20260111_wed_pattern_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add day_type, operational_intent, and actual_date columns to blocks."""

    # Create DayType enum
    day_type_enum = sa.Enum(
        "NORMAL",
        "FEDERAL_HOLIDAY",
        "TRAINING_HOLIDAY",
        "MINIMAL_MANNING",
        "EO_CLOSURE",
        "INAUGURATION_DAY",
        name="daytype",
    )

    # Create OperationalIntent enum
    operational_intent_enum = sa.Enum(
        "NORMAL",
        "REDUCED_CAPACITY",
        "NON_OPERATIONAL",
        name="operationalintent",
    )

    # Add columns to blocks table
    op.add_column(
        "blocks",
        sa.Column("day_type", day_type_enum, nullable=False, server_default="NORMAL"),
    )
    op.add_column(
        "blocks",
        sa.Column(
            "operational_intent",
            operational_intent_enum,
            nullable=False,
            server_default="NORMAL",
        ),
    )
    op.add_column(
        "blocks",
        sa.Column("actual_date", sa.Date(), nullable=True),
    )

    # Backfill existing holiday blocks with FEDERAL_HOLIDAY and REDUCED_CAPACITY
    op.execute("""
        UPDATE blocks
        SET day_type = 'FEDERAL_HOLIDAY',
            operational_intent = 'REDUCED_CAPACITY'
        WHERE is_holiday = true
    """)

    # Create index for efficient holiday querying
    op.create_index(
        "ix_blocks_day_type",
        "blocks",
        ["day_type"],
    )


def downgrade() -> None:
    """Remove day_type, operational_intent, and actual_date columns."""

    # Drop index
    op.drop_index("ix_blocks_day_type", table_name="blocks")

    # Drop columns
    op.drop_column("blocks", "actual_date")
    op.drop_column("blocks", "operational_intent")
    op.drop_column("blocks", "day_type")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS operationalintent")
    op.execute("DROP TYPE IF EXISTS daytype")
