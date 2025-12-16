"""Add application settings table

Revision ID: 009
Revises: 008
Create Date: 2025-12-16 00:00:00.000000

Creates a singleton table for application settings, migrating from
file-based JSON storage to database persistence.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create application settings table with default values."""

    op.create_table(
        'application_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Scheduling algorithm
        sa.Column('scheduling_algorithm', sa.String(50), nullable=False, server_default='greedy'),

        # Work hour limits
        sa.Column('work_hours_per_week', sa.Integer(), nullable=False, server_default='80'),
        sa.Column('max_consecutive_days', sa.Integer(), nullable=False, server_default='6'),
        sa.Column('min_days_off_per_week', sa.Integer(), nullable=False, server_default='1'),

        # Supervision ratios
        sa.Column('pgy1_supervision_ratio', sa.String(10), nullable=False, server_default="'1:2'"),
        sa.Column('pgy2_supervision_ratio', sa.String(10), nullable=False, server_default="'1:4'"),
        sa.Column('pgy3_supervision_ratio', sa.String(10), nullable=False, server_default="'1:4'"),

        # Scheduling options
        sa.Column('enable_weekend_scheduling', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('enable_holiday_scheduling', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('default_block_duration_hours', sa.Integer(), nullable=False, server_default='4'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),

        # Constraints
        sa.CheckConstraint(
            "scheduling_algorithm IN ('greedy', 'min_conflicts', 'cp_sat', 'pulp', 'hybrid')",
            name='check_scheduling_algorithm'
        ),
        sa.CheckConstraint(
            'work_hours_per_week >= 40 AND work_hours_per_week <= 100',
            name='check_work_hours'
        ),
        sa.CheckConstraint(
            'max_consecutive_days >= 1 AND max_consecutive_days <= 7',
            name='check_consecutive_days'
        ),
        sa.CheckConstraint(
            'min_days_off_per_week >= 1 AND min_days_off_per_week <= 3',
            name='check_days_off'
        ),
        sa.CheckConstraint(
            'default_block_duration_hours >= 1 AND default_block_duration_hours <= 12',
            name='check_block_duration'
        ),
    )

    # Insert default settings row (singleton pattern)
    op.execute("""
        INSERT INTO application_settings (
            id,
            scheduling_algorithm,
            work_hours_per_week,
            max_consecutive_days,
            min_days_off_per_week,
            pgy1_supervision_ratio,
            pgy2_supervision_ratio,
            pgy3_supervision_ratio,
            enable_weekend_scheduling,
            enable_holiday_scheduling,
            default_block_duration_hours
        ) VALUES (
            gen_random_uuid(),
            'greedy',
            80,
            6,
            1,
            '1:2',
            '1:4',
            '1:4',
            true,
            false,
            4
        )
    """)


def downgrade() -> None:
    """Drop application settings table."""
    op.drop_table('application_settings')
