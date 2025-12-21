"""Add scheduled_jobs and job_executions tables

Revision ID: 20251220_add_scheduled_jobs
Revises: 20251219_add_template_id
Create Date: 2025-12-20 00:00:00.000000

Adds tables for background job scheduler:
- scheduled_jobs: Job definitions and configurations
- job_executions: Job execution history and results
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251220_add_scheduled_jobs'
down_revision: Union[str, None] = '20251219_add_template_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create scheduled_jobs and job_executions tables."""

    # Create scheduled_jobs table
    op.create_table(
        'scheduled_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('job_func', sa.String(500), nullable=False),
        sa.Column('trigger_type', sa.String(50), nullable=False),
        sa.Column('trigger_config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('args', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('kwargs', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('next_run_time', sa.DateTime(), nullable=True),
        sa.Column('last_run_time', sa.DateTime(), nullable=True),
        sa.Column('run_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_instances', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('misfire_grace_time', sa.Integer(), nullable=True),
        sa.Column('coalesce', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(255), nullable=True),
    )

    # Create indexes for scheduled_jobs
    op.create_index('ix_scheduled_jobs_name', 'scheduled_jobs', ['name'])
    op.create_index('ix_scheduled_jobs_next_run_time', 'scheduled_jobs', ['next_run_time'])
    op.create_index('ix_scheduled_jobs_enabled', 'scheduled_jobs', ['enabled'])

    # Create job_executions table
    op.create_table(
        'job_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_name', sa.String(255), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('result', postgresql.JSONB(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('traceback', sa.Text(), nullable=True),
        sa.Column('runtime_seconds', sa.Integer(), nullable=True),
        sa.Column('scheduled_run_time', sa.DateTime(), nullable=False),
    )

    # Create indexes for job_executions
    op.create_index('ix_job_executions_job_id', 'job_executions', ['job_id'])
    op.create_index('ix_job_executions_job_name', 'job_executions', ['job_name'])
    op.create_index('ix_job_executions_started_at', 'job_executions', ['started_at'])
    op.create_index('ix_job_executions_status', 'job_executions', ['status'])


def downgrade() -> None:
    """Drop scheduled_jobs and job_executions tables."""

    # Drop job_executions indexes
    op.drop_index('ix_job_executions_status', table_name='job_executions')
    op.drop_index('ix_job_executions_started_at', table_name='job_executions')
    op.drop_index('ix_job_executions_job_name', table_name='job_executions')
    op.drop_index('ix_job_executions_job_id', table_name='job_executions')

    # Drop job_executions table
    op.drop_table('job_executions')

    # Drop scheduled_jobs indexes
    op.drop_index('ix_scheduled_jobs_enabled', table_name='scheduled_jobs')
    op.drop_index('ix_scheduled_jobs_next_run_time', table_name='scheduled_jobs')
    op.drop_index('ix_scheduled_jobs_name', table_name='scheduled_jobs')

    # Drop scheduled_jobs table
    op.drop_table('scheduled_jobs')
