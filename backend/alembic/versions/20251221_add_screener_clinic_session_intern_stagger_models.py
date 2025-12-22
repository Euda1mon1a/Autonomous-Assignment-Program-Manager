"""Add screener, clinic session, and intern stagger models

Revision ID: 20251221
Revises: 20251219_add_template_id_to_email_logs
Create Date: 2025-12-21 00:00:00.000000

Adds screener, clinic session, and intern stagger pattern models:

1. Person table enhancements:
   - screener_role: Role type (dedicated, rn, emt, resident)
   - can_screen: Whether this person can serve as screener
   - screening_efficiency: Efficiency percentage (0-100)

2. ClinicSession table:
   - Tracks daily clinic staffing metrics
   - Monitors screener-to-physician ratios
   - Records staffing adequacy and RN fallback usage

3. InternStaggerPattern table:
   - Defines PGY-1 orientation staggered start patterns
   - Tracks overlap periods for handoff and supervision
   - Supports Group A/B intern scheduling strategies

See docs/planning/PRODUCTION_FORK_IMPLEMENTATION_PLAN.md for details.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20251221'
down_revision: Union[str, None] = '20251220_add_chaos_experiments'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add screener fields to people table and create clinic session/intern stagger tables.
    """
    # ============================================
    # 1. Add screener fields to people table
    # ============================================
    op.add_column(
        'people',
        sa.Column('screener_role', sa.String(50), nullable=True)
    )
    op.add_column(
        'people',
        sa.Column('can_screen', sa.Boolean(), server_default='false', nullable=True)
    )
    op.add_column(
        'people',
        sa.Column('screening_efficiency', sa.Integer(), server_default='100', nullable=True)
    )

    # Add check constraints for screener fields
    op.create_check_constraint(
        'check_screener_role',
        'people',
        "screener_role IS NULL OR screener_role IN ('dedicated', 'rn', 'emt', 'resident')"
    )
    op.create_check_constraint(
        'check_screening_efficiency',
        'people',
        "screening_efficiency IS NULL OR screening_efficiency BETWEEN 0 AND 100"
    )

    # ============================================
    # 2. Create clinic_sessions table
    # ============================================
    op.create_table(
        'clinic_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('session_type', sa.String(2), nullable=False),
        sa.Column('clinic_type', sa.String(50), nullable=False),
        sa.Column('physician_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('screener_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('screener_ratio', sa.Float(), nullable=True),
        sa.Column('staffing_status', sa.String(20), nullable=False),
        sa.Column('rn_fallback_used', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    # Add indexes for clinic_sessions
    op.create_index('ix_clinic_sessions_date', 'clinic_sessions', ['date'])

    # Add check constraints for clinic_sessions
    op.create_check_constraint(
        'check_session_type',
        'clinic_sessions',
        "session_type IN ('am', 'pm')"
    )
    op.create_check_constraint(
        'check_clinic_type',
        'clinic_sessions',
        "clinic_type IN ('family_medicine', 'sports_medicine', 'pediatrics', 'procedures')"
    )
    op.create_check_constraint(
        'check_staffing_status',
        'clinic_sessions',
        "staffing_status IN ('optimal', 'adequate', 'suboptimal', 'inadequate', 'unstaffed')"
    )
    op.create_check_constraint(
        'check_physician_count',
        'clinic_sessions',
        "physician_count >= 0"
    )
    op.create_check_constraint(
        'check_screener_count',
        'clinic_sessions',
        "screener_count >= 0"
    )
    op.create_check_constraint(
        'check_screener_ratio',
        'clinic_sessions',
        "screener_ratio IS NULL OR screener_ratio >= 0"
    )

    # ============================================
    # 3. Create intern_stagger_patterns table
    # ============================================
    op.create_table(
        'intern_stagger_patterns',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('intern_a_start', sa.Time(), nullable=False),
        sa.Column('intern_b_start', sa.Time(), nullable=False),
        sa.Column('overlap_duration_minutes', sa.Integer(), nullable=False),
        sa.Column('overlap_efficiency', sa.Integer(), nullable=False, server_default='85'),
        sa.Column('min_intern_a_experience_weeks', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
    )

    # Add check constraints for intern_stagger_patterns
    op.create_check_constraint(
        'check_overlap_duration',
        'intern_stagger_patterns',
        "overlap_duration_minutes > 0"
    )
    op.create_check_constraint(
        'check_overlap_efficiency',
        'intern_stagger_patterns',
        "overlap_efficiency BETWEEN 0 AND 100"
    )
    op.create_check_constraint(
        'check_min_experience',
        'intern_stagger_patterns',
        "min_intern_a_experience_weeks >= 0"
    )


def downgrade() -> None:
    """Remove screener, clinic session, and intern stagger tables/fields."""
    # Drop intern_stagger_patterns table
    op.drop_constraint('check_min_experience', 'intern_stagger_patterns', type_='check')
    op.drop_constraint('check_overlap_efficiency', 'intern_stagger_patterns', type_='check')
    op.drop_constraint('check_overlap_duration', 'intern_stagger_patterns', type_='check')
    op.drop_table('intern_stagger_patterns')

    # Drop clinic_sessions table
    op.drop_constraint('check_screener_ratio', 'clinic_sessions', type_='check')
    op.drop_constraint('check_screener_count', 'clinic_sessions', type_='check')
    op.drop_constraint('check_physician_count', 'clinic_sessions', type_='check')
    op.drop_constraint('check_staffing_status', 'clinic_sessions', type_='check')
    op.drop_constraint('check_clinic_type', 'clinic_sessions', type_='check')
    op.drop_constraint('check_session_type', 'clinic_sessions', type_='check')
    op.drop_index('ix_clinic_sessions_date', 'clinic_sessions')
    op.drop_table('clinic_sessions')

    # Drop screener fields from people table
    op.drop_constraint('check_screening_efficiency', 'people', type_='check')
    op.drop_constraint('check_screener_role', 'people', type_='check')
    op.drop_column('people', 'screening_efficiency')
    op.drop_column('people', 'can_screen')
    op.drop_column('people', 'screener_role')
