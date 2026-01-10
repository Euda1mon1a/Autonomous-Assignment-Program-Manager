"""Add Block 0 orientation days (data migration)

Revision ID: 20251226_block0
Revises: 20251225_schema_ver
Create Date: 2025-12-26

Data migration to add Block 0 records for orientation days (July 1-2).

Context:
- Academic year runs Jul 1 - Jun 30
- Block 1 starts first Thursday (Jul 3 for AY 2025-2026)
- Jul 1-2 are orientation days, designated as "Block 0"
- Each day has AM and PM blocks (4 blocks total)

This migration inserts Block 0 records for 2025-07-01 and 2025-07-02
if they don't already exist.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251226_block0"
down_revision: str | None = "20251225_schema_ver"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Insert Block 0 orientation records for July 1-2, 2025."""
    # Insert Block 0 records (idempotent - uses ON CONFLICT DO NOTHING)
    # July 1, 2025 - AM
    op.execute(
        sa.text("""
            INSERT INTO blocks (id, date, time_of_day, block_number, is_weekend, is_holiday, holiday_name)
            VALUES (gen_random_uuid(), '2025-07-01', 'AM', 0, false, false, NULL)
            ON CONFLICT (date, time_of_day) DO NOTHING
        """)
    )

    # July 1, 2025 - PM
    op.execute(
        sa.text("""
            INSERT INTO blocks (id, date, time_of_day, block_number, is_weekend, is_holiday, holiday_name)
            VALUES (gen_random_uuid(), '2025-07-01', 'PM', 0, false, false, NULL)
            ON CONFLICT (date, time_of_day) DO NOTHING
        """)
    )

    # July 2, 2025 - AM
    op.execute(
        sa.text("""
            INSERT INTO blocks (id, date, time_of_day, block_number, is_weekend, is_holiday, holiday_name)
            VALUES (gen_random_uuid(), '2025-07-02', 'AM', 0, false, false, NULL)
            ON CONFLICT (date, time_of_day) DO NOTHING
        """)
    )

    # July 2, 2025 - PM
    op.execute(
        sa.text("""
            INSERT INTO blocks (id, date, time_of_day, block_number, is_weekend, is_holiday, holiday_name)
            VALUES (gen_random_uuid(), '2025-07-02', 'PM', 0, false, false, NULL)
            ON CONFLICT (date, time_of_day) DO NOTHING
        """)
    )


def downgrade() -> None:
    """Remove Block 0 orientation records."""
    # Delete all blocks with block_number = 0
    op.execute(sa.text("DELETE FROM blocks WHERE block_number = 0"))
