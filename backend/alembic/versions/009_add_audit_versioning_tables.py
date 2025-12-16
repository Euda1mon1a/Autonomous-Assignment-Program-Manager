"""Add audit versioning tables for SQLAlchemy-Continuum

Revision ID: 009
Revises: 008
Create Date: 2025-12-16 00:00:00.000000

Creates version history tables for audit trail tracking:
- transaction: Tracks all versioned transactions with timestamp
- assignment_version: History of assignment changes
- absence_version: History of absence changes
- schedule_run_version: History of schedule run changes

This enables full accountability tracking - who changed what, when.
Query example:
    assignment = db.query(Assignment).first()
    for version in assignment.versions:
        print(f"Changed at {version.transaction.issued_at}")
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
    """Create audit versioning tables."""

    # Transaction table - tracks all versioned transactions
    op.create_table(
        'transaction',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('issued_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('user_id', sa.String(255)),  # Who made the change
        sa.Column('remote_addr', sa.String(50)),  # IP address if available
    )
    op.create_index('idx_transaction_issued_at', 'transaction', ['issued_at'])
    op.create_index('idx_transaction_user_id', 'transaction', ['user_id'])

    # Assignment version table - mirrors assignments table structure
    op.create_table(
        'assignment_version',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('block_id', postgresql.UUID(as_uuid=True)),
        sa.Column('person_id', postgresql.UUID(as_uuid=True)),
        sa.Column('rotation_template_id', postgresql.UUID(as_uuid=True)),
        sa.Column('role', sa.String(50)),
        sa.Column('activity_override', sa.String(255)),
        sa.Column('notes', sa.Text()),
        sa.Column('override_reason', sa.Text()),
        sa.Column('override_acknowledged_at', sa.DateTime()),
        sa.Column('explain_json', postgresql.JSONB()),
        sa.Column('confidence', sa.Float()),
        sa.Column('score', sa.Float()),
        sa.Column('alternatives_json', postgresql.JSONB()),
        sa.Column('audit_hash', sa.String(64)),
        sa.Column('created_by', sa.String(255)),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        # Version tracking columns
        sa.Column('transaction_id', sa.BigInteger(), sa.ForeignKey('transaction.id'), nullable=False),
        sa.Column('operation_type', sa.SmallInteger(), nullable=False),  # 0=insert, 1=update, 2=delete
        sa.Column('end_transaction_id', sa.BigInteger(), sa.ForeignKey('transaction.id')),
        sa.PrimaryKeyConstraint('id', 'transaction_id'),
    )
    op.create_index('idx_assignment_version_transaction', 'assignment_version', ['transaction_id'])
    op.create_index('idx_assignment_version_end_transaction', 'assignment_version', ['end_transaction_id'])
    op.create_index('idx_assignment_version_operation', 'assignment_version', ['operation_type'])

    # Absence version table - mirrors absences table structure
    op.create_table(
        'absence_version',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=True)),
        sa.Column('start_date', sa.Date()),
        sa.Column('end_date', sa.Date()),
        sa.Column('absence_type', sa.String(50)),
        sa.Column('is_blocking', sa.Boolean()),
        sa.Column('deployment_orders', sa.Boolean()),
        sa.Column('tdy_location', sa.String(255)),
        sa.Column('replacement_activity', sa.String(255)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime()),
        # Version tracking columns
        sa.Column('transaction_id', sa.BigInteger(), sa.ForeignKey('transaction.id'), nullable=False),
        sa.Column('operation_type', sa.SmallInteger(), nullable=False),
        sa.Column('end_transaction_id', sa.BigInteger(), sa.ForeignKey('transaction.id')),
        sa.PrimaryKeyConstraint('id', 'transaction_id'),
    )
    op.create_index('idx_absence_version_transaction', 'absence_version', ['transaction_id'])
    op.create_index('idx_absence_version_end_transaction', 'absence_version', ['end_transaction_id'])
    op.create_index('idx_absence_version_operation', 'absence_version', ['operation_type'])

    # Schedule run version table - mirrors schedule_runs table structure
    op.create_table(
        'schedule_run_version',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_date', sa.Date()),
        sa.Column('end_date', sa.Date()),
        sa.Column('algorithm', sa.String(50)),
        sa.Column('status', sa.String(50)),
        sa.Column('total_blocks_assigned', sa.Integer()),
        sa.Column('acgme_violations', sa.Integer()),
        sa.Column('acgme_override_count', sa.Integer()),
        sa.Column('runtime_seconds', sa.Numeric(10, 2)),
        sa.Column('config_json', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime()),
        # Version tracking columns
        sa.Column('transaction_id', sa.BigInteger(), sa.ForeignKey('transaction.id'), nullable=False),
        sa.Column('operation_type', sa.SmallInteger(), nullable=False),
        sa.Column('end_transaction_id', sa.BigInteger(), sa.ForeignKey('transaction.id')),
        sa.PrimaryKeyConstraint('id', 'transaction_id'),
    )
    op.create_index('idx_schedule_run_version_transaction', 'schedule_run_version', ['transaction_id'])
    op.create_index('idx_schedule_run_version_end_transaction', 'schedule_run_version', ['end_transaction_id'])
    op.create_index('idx_schedule_run_version_operation', 'schedule_run_version', ['operation_type'])


def downgrade() -> None:
    """Drop audit versioning tables."""
    op.drop_table('schedule_run_version')
    op.drop_table('absence_version')
    op.drop_table('assignment_version')
    op.drop_table('transaction')
