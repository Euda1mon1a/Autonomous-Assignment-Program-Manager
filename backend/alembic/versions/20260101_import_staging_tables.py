"""Add import staging tables for Excel import workflow

Revision ID: 20260101_import_staging
Revises: b15f4b13e203
Create Date: 2026-01-01

This migration adds staging tables for the Excel import workflow:
- import_batches: Track import sessions with status, file metadata, and rollback capability
- import_staged_assignments: Staged assignments from Excel before commit to live tables

Workflow:
1. Upload Excel -> Parse -> Stage (ImportStagedAssignment records)
2. Review staged vs existing (preview conflicts)
3. Apply (commit to assignments table) or Reject
4. Rollback available for applied batches (within 24-hour window)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = '20260101_import_staging'
down_revision: Union[str, None] = 'b15f4b13e203'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create import staging tables with enum types."""

    # Create import_batches table (enums are created by sa.Enum)
    op.create_table(
        'import_batches',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),

        # File info
        sa.Column('filename', sa.String(255), nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),  # SHA-256 for dedup detection
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),

        # Status tracking
        sa.Column(
            'status',
            sa.Enum(
                'staged', 'approved', 'rejected', 'applied', 'rolled_back', 'failed',
                name='importbatchstatus'
            ),
            nullable=False,
            server_default='staged'
        ),
        sa.Column(
            'conflict_resolution',
            sa.Enum(
                'replace', 'merge', 'upsert',
                name='conflictresolutionmode'
            ),
            nullable=False,
            server_default='upsert'
        ),

        # Target scope
        sa.Column('target_block', sa.Integer(), nullable=True),
        sa.Column('target_start_date', sa.Date(), nullable=True),
        sa.Column('target_end_date', sa.Date(), nullable=True),

        # Metadata
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('error_count', sa.Integer(), server_default='0'),
        sa.Column('warning_count', sa.Integer(), server_default='0'),

        # Apply tracking
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.Column('applied_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('rollback_available', sa.Boolean(), server_default='true'),
        sa.Column('rollback_expires_at', sa.DateTime(), nullable=True),

        # Rollback tracking
        sa.Column('rolled_back_at', sa.DateTime(), nullable=True),
        sa.Column('rolled_back_by_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )

    # Create indexes for import_batches
    op.create_index(
        'ix_import_batches_status',
        'import_batches',
        ['status']
    )
    op.create_index(
        'ix_import_batches_created_at',
        'import_batches',
        ['created_at']
    )
    op.create_index(
        'ix_import_batches_file_hash',
        'import_batches',
        ['file_hash']
    )

    # Create import_staged_assignments table
    op.create_table(
        'import_staged_assignments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'batch_id',
            UUID(as_uuid=True),
            sa.ForeignKey('import_batches.id', ondelete='CASCADE'),
            nullable=False
        ),

        # Source tracking
        sa.Column('row_number', sa.Integer(), nullable=True),
        sa.Column('sheet_name', sa.String(100), nullable=True),

        # Raw parsed data
        sa.Column('person_name', sa.String(255), nullable=False),
        sa.Column('assignment_date', sa.Date(), nullable=False),
        sa.Column('slot', sa.String(10), nullable=True),  # AM/PM or null for full day
        sa.Column('rotation_name', sa.String(255), nullable=True),
        sa.Column('raw_cell_value', sa.String(500), nullable=True),

        # Fuzzy match results
        sa.Column('matched_person_id', UUID(as_uuid=True), sa.ForeignKey('people.id'), nullable=True),
        sa.Column('person_match_confidence', sa.Integer(), nullable=True),  # 0-100
        sa.Column('matched_rotation_id', UUID(as_uuid=True), sa.ForeignKey('rotation_templates.id'), nullable=True),
        sa.Column('rotation_match_confidence', sa.Integer(), nullable=True),  # 0-100

        # Conflict detection
        sa.Column('conflict_type', sa.String(50), nullable=True),  # none/duplicate/overwrite
        sa.Column('existing_assignment_id', UUID(as_uuid=True), nullable=True),

        # Status
        sa.Column(
            'status',
            sa.Enum(
                'pending', 'approved', 'skipped', 'applied', 'failed',
                name='stagedassignmentstatus'
            ),
            nullable=False,
            server_default='pending'
        ),

        # Validation
        sa.Column('validation_errors', JSONB, nullable=True),
        sa.Column('validation_warnings', JSONB, nullable=True),

        # After apply - link to created assignment
        sa.Column('created_assignment_id', UUID(as_uuid=True), nullable=True),
    )

    # Create indexes for import_staged_assignments
    op.create_index(
        'ix_import_staged_assignments_batch_id',
        'import_staged_assignments',
        ['batch_id']
    )
    op.create_index(
        'ix_import_staged_assignments_status',
        'import_staged_assignments',
        ['status']
    )
    op.create_index(
        'ix_import_staged_assignments_assignment_date',
        'import_staged_assignments',
        ['assignment_date']
    )
    op.create_index(
        'ix_import_staged_assignments_matched_person_id',
        'import_staged_assignments',
        ['matched_person_id']
    )
    op.create_index(
        'ix_import_staged_assignments_batch_status',
        'import_staged_assignments',
        ['batch_id', 'status']
    )


def downgrade() -> None:
    """Drop import staging tables and enum types."""

    # Drop import_staged_assignments table (and its indexes)
    op.drop_index('ix_import_staged_assignments_batch_status', table_name='import_staged_assignments')
    op.drop_index('ix_import_staged_assignments_matched_person_id', table_name='import_staged_assignments')
    op.drop_index('ix_import_staged_assignments_assignment_date', table_name='import_staged_assignments')
    op.drop_index('ix_import_staged_assignments_status', table_name='import_staged_assignments')
    op.drop_index('ix_import_staged_assignments_batch_id', table_name='import_staged_assignments')
    op.drop_table('import_staged_assignments')

    # Drop import_batches table (and its indexes)
    op.drop_index('ix_import_batches_file_hash', table_name='import_batches')
    op.drop_index('ix_import_batches_created_at', table_name='import_batches')
    op.drop_index('ix_import_batches_status', table_name='import_batches')
    op.drop_table('import_batches')

    # Drop enum types
    op.execute('DROP TYPE stagedassignmentstatus')
    op.execute('DROP TYPE conflictresolutionmode')
    op.execute('DROP TYPE importbatchstatus')
