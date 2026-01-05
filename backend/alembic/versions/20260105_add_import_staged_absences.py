"""Add import_staged_absences table for absence import workflow

Revision ID: 20260105_add_import_staged_absences
Revises: 20260105_add_resident_weekly_requirements
Create Date: 2026-01-05

This migration adds the import_staged_absences table:
- Staging table for absences before commit to live absences table
- Includes overlap detection fields for identifying conflicts with existing absences
- Supports audit logging for PHI compliance

Workflow:
1. Upload Excel with absence data -> Parse -> Stage (ImportStagedAbsence records)
2. Detect overlaps with existing absences (exact, partial, contained, contains)
3. Review staged vs existing (preview overlaps)
4. Apply (commit to absences table) with merge/replace/skip options
5. Rollback available for applied batches (within 24-hour window)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '20260105_add_import_staged_absences'
down_revision: str | None = '20260105_add_resident_weekly_requirements'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create import_staged_absences table with overlap detection support."""

    # Create StagedAbsenceStatus enum
    staged_absence_status = sa.Enum(
        'pending', 'approved', 'skipped', 'applied', 'failed',
        name='stagedabsencestatus'
    )

    # Create OverlapType enum
    overlap_type = sa.Enum(
        'none', 'partial', 'exact', 'contained', 'contains',
        name='overlaptype'
    )

    # Create import_staged_absences table
    op.create_table(
        'import_staged_absences',
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
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('absence_type', sa.String(50), nullable=False),
        sa.Column('raw_cell_value', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),

        # Additional absence fields
        sa.Column('is_blocking', sa.Boolean(), nullable=True),
        sa.Column('return_date_tentative', sa.Boolean(), server_default='false'),
        sa.Column('tdy_location', sa.String(255), nullable=True),
        sa.Column('replacement_activity', sa.String(255), nullable=True),

        # Fuzzy match results
        sa.Column(
            'matched_person_id',
            UUID(as_uuid=True),
            sa.ForeignKey('people.id'),
            nullable=True
        ),
        sa.Column('person_match_confidence', sa.Integer(), nullable=True),  # 0-100

        # Overlap detection with existing absences
        sa.Column(
            'overlap_type',
            overlap_type,
            nullable=False,
            server_default='none'
        ),
        sa.Column('overlapping_absence_ids', JSONB, nullable=True),  # List of UUIDs
        sa.Column('overlap_details', JSONB, nullable=True),  # Details about each overlap

        # Status
        sa.Column(
            'status',
            staged_absence_status,
            nullable=False,
            server_default='pending'
        ),

        # Validation
        sa.Column('validation_errors', JSONB, nullable=True),
        sa.Column('validation_warnings', JSONB, nullable=True),

        # After apply - link to created/updated absence
        sa.Column('created_absence_id', UUID(as_uuid=True), nullable=True),
        sa.Column('merged_into_absence_id', UUID(as_uuid=True), nullable=True),

        # Constraints
        sa.CheckConstraint('end_date >= start_date', name='check_staged_absence_dates'),
        sa.CheckConstraint(
            "absence_type IN ('vacation', 'deployment', 'tdy', 'medical', 'family_emergency', "
            "'conference', 'bereavement', 'emergency_leave', 'sick', 'convalescent', 'maternity_paternity')",
            name='check_staged_absence_type'
        ),
    )

    # Create indexes for efficient querying
    op.create_index(
        'ix_import_staged_absences_batch_id',
        'import_staged_absences',
        ['batch_id']
    )
    op.create_index(
        'ix_import_staged_absences_status',
        'import_staged_absences',
        ['status']
    )
    op.create_index(
        'ix_import_staged_absences_matched_person_id',
        'import_staged_absences',
        ['matched_person_id']
    )
    op.create_index(
        'ix_import_staged_absences_date_range',
        'import_staged_absences',
        ['start_date', 'end_date']
    )
    op.create_index(
        'ix_import_staged_absences_overlap_type',
        'import_staged_absences',
        ['overlap_type']
    )
    op.create_index(
        'ix_import_staged_absences_batch_status',
        'import_staged_absences',
        ['batch_id', 'status']
    )

    # Create version table for audit trail (SQLAlchemy-Continuum)
    # This follows the pattern used by the Absence model for PHI compliance
    op.create_table(
        'import_staged_absences_version',
        sa.Column('id', UUID(as_uuid=True), nullable=False),
        sa.Column('batch_id', UUID(as_uuid=True), nullable=True),
        sa.Column('row_number', sa.Integer(), nullable=True),
        sa.Column('sheet_name', sa.String(100), nullable=True),
        sa.Column('person_name', sa.String(255), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('absence_type', sa.String(50), nullable=True),
        sa.Column('raw_cell_value', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_blocking', sa.Boolean(), nullable=True),
        sa.Column('return_date_tentative', sa.Boolean(), nullable=True),
        sa.Column('tdy_location', sa.String(255), nullable=True),
        sa.Column('replacement_activity', sa.String(255), nullable=True),
        sa.Column('matched_person_id', UUID(as_uuid=True), nullable=True),
        sa.Column('person_match_confidence', sa.Integer(), nullable=True),
        sa.Column('overlap_type', sa.String(20), nullable=True),
        sa.Column('overlapping_absence_ids', JSONB, nullable=True),
        sa.Column('overlap_details', JSONB, nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('validation_errors', JSONB, nullable=True),
        sa.Column('validation_warnings', JSONB, nullable=True),
        sa.Column('created_absence_id', UUID(as_uuid=True), nullable=True),
        sa.Column('merged_into_absence_id', UUID(as_uuid=True), nullable=True),
        # Version tracking columns
        sa.Column('transaction_id', sa.BigInteger(), nullable=False),
        sa.Column('operation_type', sa.SmallInteger(), nullable=False),
        sa.Column('end_transaction_id', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id', 'transaction_id'),
    )

    # Create index for version table queries
    op.create_index(
        'ix_import_staged_absences_version_txn',
        'import_staged_absences_version',
        ['transaction_id']
    )
    op.create_index(
        'ix_import_staged_absences_version_end_txn',
        'import_staged_absences_version',
        ['end_transaction_id']
    )


def downgrade() -> None:
    """Drop import_staged_absences table and related indexes."""

    # Drop version table
    op.drop_index('ix_import_staged_absences_version_end_txn', table_name='import_staged_absences_version')
    op.drop_index('ix_import_staged_absences_version_txn', table_name='import_staged_absences_version')
    op.drop_table('import_staged_absences_version')

    # Drop main table indexes
    op.drop_index('ix_import_staged_absences_batch_status', table_name='import_staged_absences')
    op.drop_index('ix_import_staged_absences_overlap_type', table_name='import_staged_absences')
    op.drop_index('ix_import_staged_absences_date_range', table_name='import_staged_absences')
    op.drop_index('ix_import_staged_absences_matched_person_id', table_name='import_staged_absences')
    op.drop_index('ix_import_staged_absences_status', table_name='import_staged_absences')
    op.drop_index('ix_import_staged_absences_batch_id', table_name='import_staged_absences')

    # Drop main table
    op.drop_table('import_staged_absences')

    # Drop enum types
    op.execute('DROP TYPE overlaptype')
    op.execute('DROP TYPE stagedabsencestatus')
