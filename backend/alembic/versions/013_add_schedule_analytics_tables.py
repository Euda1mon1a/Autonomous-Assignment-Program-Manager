"""Add schedule analytics tables

Revision ID: 013
Revises: 012
Create Date: 2025-12-17 00:00:00.000000

Creates tables for schedule analytics and version tracking:
- schedule_versions: Tracks all versions of schedule with metadata
- metric_snapshots: Stores calculated metrics per schedule version
- schedule_diffs: Tracks changes between schedule versions

This enables:
- Version history tracking for schedules
- Metric trending over time (fairness, satisfaction, stability, compliance, resilience)
- Change analysis between schedule versions
- Audit trail for schedule modifications
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '013'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create schedule analytics tables."""

    # Table 1: schedule_versions - tracks all versions of a schedule
    op.create_table(
        'schedule_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Link to schedule run
        sa.Column(
            'schedule_run_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('schedule_runs.id', ondelete='CASCADE'),
        ),

        # Version metadata
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('trigger_type', sa.String(50), nullable=False),

        # Version lineage
        sa.Column(
            'parent_version_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('schedule_versions.id', ondelete='SET NULL'),
        ),

        # Model information
        sa.Column('model_hash', sa.String(64)),

        # Summary statistics
        sa.Column('total_assignments', sa.Integer()),
        sa.Column('total_persons', sa.Integer()),
        sa.Column('date_range_start', sa.Date()),
        sa.Column('date_range_end', sa.Date()),

        # Constraints
        sa.CheckConstraint(
            "trigger_type IN ('generation', 'swap', 'absence', 'manual_edit', 'auto_rebalance')",
            name='check_trigger_type'
        ),
    )
    op.create_index('idx_schedule_versions_run', 'schedule_versions', ['schedule_run_id'])
    op.create_index('idx_schedule_versions_created', 'schedule_versions', ['created_at'])
    op.create_index('idx_schedule_versions_trigger', 'schedule_versions', ['trigger_type'])
    op.create_index('idx_schedule_versions_parent', 'schedule_versions', ['parent_version_id'])

    # Table 2: metric_snapshots - stores calculated metrics per version
    op.create_table(
        'metric_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Link to schedule version
        sa.Column(
            'schedule_version_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('schedule_versions.id', ondelete='CASCADE'),
            nullable=False,
        ),

        # Metric details
        sa.Column('category', sa.String(20), nullable=False),
        sa.Column('metric_name', sa.String(50), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),

        # Computation metadata
        sa.Column('computed_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('methodology_version', sa.String(20), server_default="'1.0'"),

        # Constraints
        sa.CheckConstraint(
            "category IN ('fairness', 'satisfaction', 'stability', 'compliance', 'resilience')",
            name='check_metric_category'
        ),
    )
    op.create_index('ix_metrics_version_category', 'metric_snapshots', ['schedule_version_id', 'category'])
    op.create_index('ix_metrics_name_time', 'metric_snapshots', ['metric_name', 'computed_at'])
    op.create_index('idx_metrics_category', 'metric_snapshots', ['category'])

    # Table 3: schedule_diffs - tracks changes between versions
    op.create_table(
        'schedule_diffs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),

        # Version comparison
        sa.Column(
            'from_version_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('schedule_versions.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'to_version_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('schedule_versions.id', ondelete='CASCADE'),
            nullable=False,
        ),

        # Diff computation
        sa.Column('computed_at', sa.DateTime(), server_default=sa.func.now()),

        # Change details (JSONB for flexibility)
        sa.Column('assignments_added', postgresql.JSONB(), server_default='{}'),
        sa.Column('assignments_removed', postgresql.JSONB(), server_default='{}'),
        sa.Column('assignments_modified', postgresql.JSONB(), server_default='{}'),

        # Summary statistics
        sa.Column('total_changes', sa.Integer()),
        sa.Column('persons_affected', sa.Integer()),
        sa.Column('blocks_affected', sa.Integer()),
    )
    op.create_index('idx_diffs_from_version', 'schedule_diffs', ['from_version_id'])
    op.create_index('idx_diffs_to_version', 'schedule_diffs', ['to_version_id'])
    op.create_index('idx_diffs_computed', 'schedule_diffs', ['computed_at'])
    op.create_index('idx_diffs_from_to', 'schedule_diffs', ['from_version_id', 'to_version_id'])


def downgrade() -> None:
    """Drop schedule analytics tables."""
    op.drop_table('schedule_diffs')
    op.drop_table('metric_snapshots')
    op.drop_table('schedule_versions')
