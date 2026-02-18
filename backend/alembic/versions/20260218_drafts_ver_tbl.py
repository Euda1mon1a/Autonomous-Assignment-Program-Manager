"""Create schedule_drafts_version table for Continuum audit trail.

The ScheduleDraft model has __versioned__ = {} but the version table
was never created in migrations, causing crashes when draft mode is used.

Revision ID: 20260218_drafts_ver_tbl
Revises: 20260212_query_perf_idx
Create Date: 2026-02-18
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "20260218_drafts_ver_tbl"
down_revision = "20260212_query_perf_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table already exists (may have been created manually)
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables "
            "  WHERE table_name = 'schedule_drafts_version'"
            ")"
        )
    )
    if result.scalar():
        return

    op.create_table(
        "schedule_drafts_version",
        # Primary model columns
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", UUID(as_uuid=True), nullable=True),
        sa.Column("target_block", sa.Integer(), nullable=True),
        sa.Column("target_start_date", sa.Date(), nullable=True),
        sa.Column("target_end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("source_schedule_run_id", UUID(as_uuid=True), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("published_by_id", UUID(as_uuid=True), nullable=True),
        sa.Column("archived_version_id", UUID(as_uuid=True), nullable=True),
        sa.Column("rollback_available", sa.Boolean(), nullable=True),
        sa.Column("rollback_expires_at", sa.DateTime(), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(), nullable=True),
        sa.Column("rolled_back_by_id", UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("change_summary", sa.JSON(), nullable=True),
        sa.Column("flags_total", sa.Integer(), nullable=True),
        sa.Column("flags_acknowledged", sa.Integer(), nullable=True),
        sa.Column("override_comment", sa.Text(), nullable=True),
        sa.Column("override_by_id", UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by_id", UUID(as_uuid=True), nullable=True),
        sa.Column("approval_reason", sa.Text(), nullable=True),
        sa.Column("lock_date_at_approval", sa.Date(), nullable=True),
        # Continuum versioning columns
        sa.Column(
            "transaction_id",
            sa.BigInteger(),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("operation_type", sa.SmallInteger(), nullable=False),
        sa.Column("end_transaction_id", sa.BigInteger(), nullable=True),
        # Continuum _mod columns (track which columns changed)
        sa.Column("created_at_mod", sa.Boolean(), nullable=True),
        sa.Column("created_by_id_mod", sa.Boolean(), nullable=True),
        sa.Column("target_block_mod", sa.Boolean(), nullable=True),
        sa.Column("target_start_date_mod", sa.Boolean(), nullable=True),
        sa.Column("target_end_date_mod", sa.Boolean(), nullable=True),
        sa.Column("status_mod", sa.Boolean(), nullable=True),
        sa.Column("source_type_mod", sa.Boolean(), nullable=True),
        sa.Column("source_schedule_run_id_mod", sa.Boolean(), nullable=True),
        sa.Column("published_at_mod", sa.Boolean(), nullable=True),
        sa.Column("published_by_id_mod", sa.Boolean(), nullable=True),
        sa.Column("archived_version_id_mod", sa.Boolean(), nullable=True),
        sa.Column("rollback_available_mod", sa.Boolean(), nullable=True),
        sa.Column("rollback_expires_at_mod", sa.Boolean(), nullable=True),
        sa.Column("rolled_back_at_mod", sa.Boolean(), nullable=True),
        sa.Column("rolled_back_by_id_mod", sa.Boolean(), nullable=True),
        sa.Column("notes_mod", sa.Boolean(), nullable=True),
        sa.Column("change_summary_mod", sa.Boolean(), nullable=True),
        sa.Column("flags_total_mod", sa.Boolean(), nullable=True),
        sa.Column("flags_acknowledged_mod", sa.Boolean(), nullable=True),
        sa.Column("override_comment_mod", sa.Boolean(), nullable=True),
        sa.Column("override_by_id_mod", sa.Boolean(), nullable=True),
        sa.Column("approved_at_mod", sa.Boolean(), nullable=True),
        sa.Column("approved_by_id_mod", sa.Boolean(), nullable=True),
        sa.Column("approval_reason_mod", sa.Boolean(), nullable=True),
        sa.Column("lock_date_at_approval_mod", sa.Boolean(), nullable=True),
        # Primary key
        sa.PrimaryKeyConstraint("id", "transaction_id"),
    )
    op.create_index(
        "ix_schedule_drafts_version_transaction_id",
        "schedule_drafts_version",
        ["transaction_id"],
    )
    op.create_index(
        "ix_schedule_drafts_version_end_transaction_id",
        "schedule_drafts_version",
        ["end_transaction_id"],
    )
    op.create_index(
        "ix_schedule_drafts_version_operation_type",
        "schedule_drafts_version",
        ["operation_type"],
    )


def downgrade() -> None:
    op.drop_table("schedule_drafts_version")
