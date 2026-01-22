"""Add academic_blocks table with UUID primary keys.

Creates the academic_blocks table to represent 28-day scheduling periods
as first-class entities. Pre-populates with AY 2025-2026 blocks.

Revision ID: 20260120_academic_blocks
Revises: 20260120_add_rot_activities
Create Date: 2026-01-20
"""

import uuid
from datetime import date, datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260120_academic_blocks"
down_revision = "20260120_add_rot_activities"
branch_labels = None
depends_on = None


def get_block_dates_for_year(academic_year: int) -> list[dict]:
    """Calculate block dates for an academic year.

    This mirrors the logic in app/utils/academic_blocks.py.
    """
    from datetime import timedelta

    # Find first Thursday on or after July 1
    start = date(academic_year, 7, 1)
    days_until_thursday = (3 - start.weekday()) % 7
    first_thursday = start + timedelta(days=days_until_thursday)

    blocks = []

    # Block 0: Orientation (July 1 until first Thursday - 1)
    if first_thursday > start:
        blocks.append(
            {
                "block_number": 0,
                "academic_year": academic_year,
                "start_date": start,
                "end_date": first_thursday - timedelta(days=1),
                "name": "Orientation",
                "is_orientation": True,
                "is_variable_length": True,
            }
        )
    else:
        # If July 1 is Thursday, Block 0 has 0 days - skip it
        pass

    # Blocks 1-12: 28 days each, Thursday-Wednesday
    current_start = first_thursday
    for block_num in range(1, 13):
        block_end = current_start + timedelta(days=27)  # 28 days inclusive
        blocks.append(
            {
                "block_number": block_num,
                "academic_year": academic_year,
                "start_date": current_start,
                "end_date": block_end,
                "name": f"Block {block_num}",
                "is_orientation": False,
                "is_variable_length": False,
            }
        )
        current_start = block_end + timedelta(days=1)

    # Block 13: Variable length, ends June 30
    end_of_year = date(academic_year + 1, 6, 30)
    if current_start <= end_of_year:
        blocks.append(
            {
                "block_number": 13,
                "academic_year": academic_year,
                "start_date": current_start,
                "end_date": end_of_year,
                "name": "Block 13",
                "is_orientation": False,
                "is_variable_length": True,
            }
        )

    return blocks


def upgrade() -> None:
    """Create academic_blocks table, populate with AY 2025-2026, add FK to block_assignments."""

    # Step 1: Create the table
    op.create_table(
        "academic_blocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("block_number", sa.Integer(), nullable=False),
        sa.Column("academic_year", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(50), nullable=True),
        sa.Column("is_orientation", sa.Boolean(), nullable=False, default=False),
        sa.Column("is_variable_length", sa.Boolean(), nullable=False, default=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("block_number", "academic_year", name="uq_block_year"),
        sa.CheckConstraint(
            "block_number >= 0 AND block_number <= 13",
            name="ck_academic_block_number_range",
        ),
        sa.CheckConstraint(
            "academic_year >= 2020 AND academic_year <= 2100",
            name="ck_academic_year_range",
        ),
        sa.CheckConstraint(
            "end_date >= start_date",
            name="ck_academic_block_date_order",
        ),
    )

    # Create index for common queries
    op.create_index(
        "ix_academic_blocks_year",
        "academic_blocks",
        ["academic_year"],
    )

    # Pre-populate with AY 2025-2026
    now = datetime.utcnow().isoformat()
    blocks = get_block_dates_for_year(2025)

    for block in blocks:
        block_id = str(uuid.uuid4())
        op.execute(
            sa.text(
                """
            INSERT INTO academic_blocks (
                id, block_number, academic_year, start_date, end_date,
                name, is_orientation, is_variable_length, created_at
            ) VALUES (
                :id, :block_number, :academic_year, :start_date, :end_date,
                :name, :is_orientation, :is_variable_length, :now
            )
            """
            ).bindparams(
                id=block_id,
                block_number=block["block_number"],
                academic_year=block["academic_year"],
                start_date=block["start_date"],
                end_date=block["end_date"],
                name=block["name"],
                is_orientation=block["is_orientation"],
                is_variable_length=block["is_variable_length"],
                now=now,
            )
        )


    # Step 3: Add FK column to block_assignments
    op.add_column(
        "block_assignments",
        sa.Column(
            "academic_block_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academic_blocks.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_block_assignments_academic_block_id",
        "block_assignments",
        ["academic_block_id"],
    )

    # Step 4: Backfill FK from existing block_number + academic_year
    op.execute(
        sa.text(
            """
        UPDATE block_assignments ba
        SET academic_block_id = ab.id
        FROM academic_blocks ab
        WHERE ba.block_number = ab.block_number
          AND ba.academic_year = ab.academic_year
        """
        )
    )


def downgrade() -> None:
    """Remove FK and academic_blocks table."""
    # Drop FK column from block_assignments
    op.drop_index("ix_block_assignments_academic_block_id", table_name="block_assignments")
    op.drop_column("block_assignments", "academic_block_id")

    # Drop academic_blocks table
    op.drop_index("ix_academic_blocks_year", table_name="academic_blocks")
    op.drop_table("academic_blocks")
