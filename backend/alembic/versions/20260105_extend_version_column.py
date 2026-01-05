"""extend_alembic_version_column_to_128_chars

Revision ID: 20260105_ext_ver_col
Revises: 20260104_add_archive_fields
Create Date: 2026-01-05 12:00:00.000000

CRITICAL FIX: Extends alembic_version.version_num from varchar(32) to varchar(128).

The default Alembic version column is varchar(32), which is too short for
descriptive migration names like '20260105_add_resident_weekly_requirements'.
This caused repeated container startup failures.

This migration:
1. Alters the alembic_version.version_num column to varchar(128)
2. Prevents future failures from descriptive migration names
3. Is idempotent - safe to run multiple times

Reference: PostgreSQL VARCHAR can be extended without data loss.

IMPORTANT: This migration MUST run before any migration with a revision ID
exceeding 32 characters. It's been inserted in the chain before
20260105_add_resident_weekly_requirements (which has 41 chars).
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '20260105_ext_ver_col'
down_revision: Union[str, None] = '20260104_add_archive_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Extend alembic_version.version_num to varchar(128).

    PostgreSQL allows increasing VARCHAR length without table rewrite.
    This is a safe, fast operation.
    """
    # Use raw SQL for direct column modification
    # This is safe because:
    # 1. Extending VARCHAR is always allowed in PostgreSQL
    # 2. No data is modified, only the constraint
    # 3. Operation is atomic
    op.execute(
        "ALTER TABLE alembic_version "
        "ALTER COLUMN version_num TYPE VARCHAR(128)"
    )


def downgrade() -> None:
    """Revert to varchar(32) - DANGEROUS if long revision IDs exist.

    WARNING: This will fail if any existing revision IDs exceed 32 chars.
    Only use if you're certain all revision IDs are <= 32 chars.
    """
    # Intentionally left as a no-op to prevent accidental data loss
    # If you really need to downgrade, manually run:
    # ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(32)
    pass
