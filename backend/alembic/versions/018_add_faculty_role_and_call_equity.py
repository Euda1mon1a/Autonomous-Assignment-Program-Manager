"""Add faculty_role and call equity tracking fields

Revision ID: 018
Revises: 017
Create Date: 2025-12-19 00:00:00.000000

Adds faculty role-based scheduling fields to the people table:
- faculty_role: Role type (pd, apd, oic, dept_chief, sports_med, core)
- sunday_call_count: Separate Sunday call equity tracking
- weekday_call_count: Mon-Thurs call equity tracking
- fmit_weeks_count: FMIT weeks this year (target ~6 max)

See docs/architecture/FACULTY_SCHEDULING_SPECIFICATION.md for details.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '018'
down_revision: Union[str, None] = '017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add faculty role and call equity tracking fields to people table.

    Faculty roles determine scheduling constraints:
    - PD: 0 clinic/week, avoid Tuesday call
    - APD: 2 clinic/week, avoid Tuesday call
    - OIC: 2 clinic/week
    - Dept Chief: 1 clinic/week, prefers Wednesday call
    - Sports Med: 0 regular clinic, 4 SM clinic/week
    - Core: max 4 clinic/week
    """
    # Add faculty_role column
    op.add_column(
        'people',
        sa.Column('faculty_role', sa.String(50), nullable=True)
    )

    # Add call equity tracking fields
    op.add_column(
        'people',
        sa.Column('sunday_call_count', sa.Integer(), server_default='0', nullable=True)
    )
    op.add_column(
        'people',
        sa.Column('weekday_call_count', sa.Integer(), server_default='0', nullable=True)
    )
    op.add_column(
        'people',
        sa.Column('fmit_weeks_count', sa.Integer(), server_default='0', nullable=True)
    )

    # Add check constraint for valid faculty roles
    op.create_check_constraint(
        'check_faculty_role',
        'people',
        "faculty_role IS NULL OR faculty_role IN ('pd', 'apd', 'oic', 'dept_chief', 'sports_med', 'core')"
    )


def downgrade() -> None:
    """Remove faculty role and call equity fields."""
    # Drop check constraint first
    op.drop_constraint('check_faculty_role', 'people', type_='check')

    # Drop columns
    op.drop_column('people', 'fmit_weeks_count')
    op.drop_column('people', 'weekday_call_count')
    op.drop_column('people', 'sunday_call_count')
    op.drop_column('people', 'faculty_role')
