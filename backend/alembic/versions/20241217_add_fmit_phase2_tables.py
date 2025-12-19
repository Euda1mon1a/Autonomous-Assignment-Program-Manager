"""Add FMIT Phase 2 tables

Revision ID: 018
Revises: 017
Create Date: 2024-12-17

Tables added:
- swap_records: FMIT swap tracking
- swap_approvals: Swap approval workflow
- conflict_alerts: Schedule conflict alerts
- faculty_preferences: Faculty FMIT preferences

Note: This migration was moved after 017_add_users_table because
it references users.id in foreign key constraints.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '018'
down_revision: Union[str, None] = '017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create FMIT Phase 2 tables."""

    # Create swap_records table
    op.create_table(
        'swap_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_faculty_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('people.id'), nullable=False),
        sa.Column('source_week', sa.Date(), nullable=False),
        sa.Column('target_faculty_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('people.id'), nullable=False),
        sa.Column('target_week', sa.Date(), nullable=True),
        sa.Column('swap_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('requested_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('requested_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('executed_at', sa.DateTime(), nullable=True),
        sa.Column('executed_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('rolled_back_at', sa.DateTime(), nullable=True),
        sa.Column('rolled_back_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('rollback_reason', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
    )
    op.create_index('ix_swap_records_source_faculty_id', 'swap_records', ['source_faculty_id'])
    op.create_index('ix_swap_records_target_faculty_id', 'swap_records', ['target_faculty_id'])
    op.create_index('ix_swap_records_source_week', 'swap_records', ['source_week'])
    op.create_index('ix_swap_records_status', 'swap_records', ['status'])

    # Create swap_approvals table
    op.create_table(
        'swap_approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('swap_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('swap_records.id'), nullable=False),
        sa.Column('faculty_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('people.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('approved', sa.Boolean(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.Column('response_notes', sa.Text(), nullable=True),
    )
    op.create_index('ix_swap_approvals_swap_id', 'swap_approvals', ['swap_id'])

    # Create conflict_alerts table
    op.create_table(
        'conflict_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('faculty_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('people.id'), nullable=False),
        sa.Column('conflict_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default='warning'),
        sa.Column('fmit_week', sa.Date(), nullable=False),
        sa.Column('leave_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('absences.id'), nullable=True),
        sa.Column('swap_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='new'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )
    op.create_index('ix_conflict_alerts_faculty_id', 'conflict_alerts', ['faculty_id'])
    op.create_index('ix_conflict_alerts_status', 'conflict_alerts', ['status'])
    op.create_index('ix_conflict_alerts_fmit_week', 'conflict_alerts', ['fmit_week'])

    # Create faculty_preferences table
    op.create_table(
        'faculty_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('faculty_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('people.id'), unique=True, nullable=False),
        sa.Column('preferred_weeks', postgresql.JSON(), nullable=True),
        sa.Column('blocked_weeks', postgresql.JSON(), nullable=True),
        sa.Column('max_weeks_per_month', sa.Integer(), nullable=True, server_default='2'),
        sa.Column('max_consecutive_weeks', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('min_gap_between_weeks', sa.Integer(), nullable=True, server_default='2'),
        sa.Column('target_weeks_per_year', sa.Integer(), nullable=True, server_default='6'),
        sa.Column('notify_swap_requests', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('notify_schedule_changes', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('notify_conflict_alerts', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('notify_reminder_days', sa.Integer(), nullable=True, server_default='7'),
        sa.Column('preferred_contact_method', sa.Text(), nullable=True, server_default="'email'"),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_faculty_preferences_faculty_id', 'faculty_preferences', ['faculty_id'])


def downgrade() -> None:
    """Drop FMIT Phase 2 tables."""
    op.drop_table('faculty_preferences')
    op.drop_table('conflict_alerts')
    op.drop_table('swap_approvals')
    op.drop_table('swap_records')
