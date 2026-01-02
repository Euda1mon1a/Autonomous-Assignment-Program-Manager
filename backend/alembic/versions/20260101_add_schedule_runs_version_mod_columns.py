"""Add missing _mod columns to schedule_runs_version table

Revision ID: 20260101_mod_columns
Revises: 20251231_rotation_colors
Create Date: 2026-01-01

SQLAlchemy-Continuum with PropertyModTrackerPlugin requires *_mod boolean columns
in version tables to track which specific properties were modified in each transaction.

The schedule_runs_version table was missing these columns, causing errors like:
    ERROR: column "start_date_mod" of relation "schedule_runs_version" does not exist

This migration adds the required _mod columns for all tracked properties.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20260101_mod_columns'
down_revision: Union[str, None] = '8e3f0e0b83c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add _mod columns to schedule_runs_version for PropertyModTrackerPlugin."""

    # List of columns in schedule_runs that need _mod tracking columns
    # These correspond to the columns in the schedule_runs table (minus 'id' which is the PK)
    mod_columns = [
        'start_date_mod',
        'end_date_mod',
        'algorithm_mod',
        'status_mod',
        'total_blocks_assigned_mod',
        'acgme_violations_mod',
        'acgme_override_count_mod',
        'runtime_seconds_mod',
        'config_json_mod',
        'created_at_mod',
    ]

    for col_name in mod_columns:
        op.add_column(
            'schedule_runs_version',
            sa.Column(col_name, sa.Boolean(), nullable=True)
        )


def downgrade() -> None:
    """Remove _mod columns from schedule_runs_version."""

    mod_columns = [
        'start_date_mod',
        'end_date_mod',
        'algorithm_mod',
        'status_mod',
        'total_blocks_assigned_mod',
        'acgme_violations_mod',
        'acgme_override_count_mod',
        'runtime_seconds_mod',
        'config_json_mod',
        'created_at_mod',
    ]

    for col_name in mod_columns:
        op.drop_column('schedule_runs_version', col_name)
