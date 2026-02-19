"""Add composite indexes on most-queried columns.

Analysis of repository and service layer query patterns (EXPLAIN ANALYZE review)
identified several hot-paths that perform multi-column filtering, ordering, or
range scans without a matching composite index.  While individual single-column
indexes exist on some of these columns, PostgreSQL cannot efficiently combine
them for multi-predicate queries — a composite index lets the planner satisfy
the full WHERE clause in a single B-tree scan.

Tables and query patterns addressed:

  swap_records           – source_week / target_week date lookups (find_by_week),
                           (target_faculty_id, status) for pending-swap inbox
  notifications          – (recipient_id, is_read, created_at) covering index
                           for the user notification inbox query
  import_batches         – (status, created_at) for paginated batch listing
  import_staged_assignments – (batch_id, row_number) for ordered batch preview
  import_staged_absences – batch_id FK for cascade lookups
  procedure_credentials  – (person_id, status, expiration_date) for active creds,
                           (procedure_id, status, expiration_date) for qualified
                           faculty, (status, expiration_date) for expiry alerts
  activity_log           – (user_id, action_type, created_at) composite for
                           filtered audit-log queries
  weekly_patterns        – (rotation_template_id, day_of_week, time_of_day)
                           composite for ordered pattern retrieval

All CREATE INDEX statements use ``if_not_exists=True`` for idempotency.

Revision ID: 20260219_composite_query_idx
Revises: 20260218_drafts_ver_tbl
Create Date: 2026-02-19
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260219_composite_query_idx"
down_revision = "20260218_drafts_ver_tbl"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add composite indexes on most-queried columns."""

    # ── swap_records ───────────────────────────────────────────────────
    # Date lookups in find_by_week: OR(source_week = ?, target_week = ?)
    # Separate indexes let Postgres BitmapOr-scan both legs efficiently.
    # Ref: swap_repository.py:208-217
    op.create_index(
        "idx_swap_records_source_week",
        "swap_records",
        ["source_week"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "idx_swap_records_target_week",
        "swap_records",
        ["target_week"],
        unique=False,
        if_not_exists=True,
    )
    # Composite: pending-swap inbox for a faculty member
    # find_pending_for_faculty filters (target_faculty_id, status)
    # then ORDER BY requested_at DESC.
    # Ref: swap_repository.py:236-246
    op.create_index(
        "idx_swap_records_target_faculty_status",
        "swap_records",
        ["target_faculty_id", "status"],
        unique=False,
        if_not_exists=True,
    )

    # ── notifications ──────────────────────────────────────────────────
    # User inbox: filter(recipient_id, is_read).order_by(created_at DESC)
    # Individual indexes exist but the planner must intersect three
    # separate scans.  A composite covering index satisfies the full
    # predicate + sort in one B-tree walk.
    # Ref: notifications/service.py:501-508
    op.create_index(
        "idx_notifications_recipient_read_created",
        "notifications",
        ["recipient_id", "is_read", "created_at"],
        unique=False,
        if_not_exists=True,
    )

    # ── import_batches ─────────────────────────────────────────────────
    # Paginated listing: filter(status).order_by(created_at DESC)
    # Ref: import_staging_service.py:791-803
    op.create_index(
        "idx_import_batches_status_created",
        "import_batches",
        ["status", "created_at"],
        unique=False,
        if_not_exists=True,
    )

    # ── import_staged_assignments ──────────────────────────────────────
    # Batch preview: filter(batch_id).order_by(row_number)
    # Ref: import_staging_service.py:322-336
    op.create_index(
        "idx_import_staged_asgn_batch_row",
        "import_staged_assignments",
        ["batch_id", "row_number"],
        unique=False,
        if_not_exists=True,
    )

    # ── import_staged_absences ─────────────────────────────────────────
    # FK lookup: all staged absences within a batch (CASCADE path)
    op.create_index(
        "idx_import_staged_absences_batch_id",
        "import_staged_absences",
        ["batch_id"],
        unique=False,
        if_not_exists=True,
    )

    # ── procedure_credentials ──────────────────────────────────────────
    # Active credentials for a person: filter(person_id, status, expiration_date)
    # Ref: procedure_credential.py:103-114
    op.create_index(
        "idx_proc_creds_person_status_exp",
        "procedure_credentials",
        ["person_id", "status", "expiration_date"],
        unique=False,
        if_not_exists=True,
    )
    # Qualified faculty for a procedure: filter(procedure_id, status, expiration_date)
    # Ref: procedure_credential.py:158-167
    op.create_index(
        "idx_proc_creds_procedure_status_exp",
        "procedure_credentials",
        ["procedure_id", "status", "expiration_date"],
        unique=False,
        if_not_exists=True,
    )
    # Expiring-soon alert: filter(status, expiration_date range).order_by(expiration_date)
    # Ref: procedure_credential.py:219-232
    op.create_index(
        "idx_proc_creds_status_expiration",
        "procedure_credentials",
        ["status", "expiration_date"],
        unique=False,
        if_not_exists=True,
    )

    # ── activity_log ───────────────────────────────────────────────────
    # Filtered audit queries: filter(user_id, action_type).order_by(created_at)
    # Single-column indexes exist but cannot satisfy the composite predicate.
    op.create_index(
        "idx_activity_log_user_action_created",
        "activity_log",
        ["user_id", "action_type", "created_at"],
        unique=False,
        if_not_exists=True,
    )

    # ── weekly_patterns ────────────────────────────────────────────────
    # Pattern retrieval: filter(rotation_template_id).order_by(day_of_week, time_of_day)
    # A single-column index on rotation_template_id exists but does not
    # cover the sort columns, forcing a filesort.
    # Ref: weekly_pattern_repository.py:46-49
    op.create_index(
        "idx_weekly_patterns_template_day_time",
        "weekly_patterns",
        ["rotation_template_id", "day_of_week", "time_of_day"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    """Remove composite query indexes."""
    op.drop_index(
        "idx_weekly_patterns_template_day_time",
        table_name="weekly_patterns",
        if_exists=True,
    )
    op.drop_index(
        "idx_activity_log_user_action_created",
        table_name="activity_log",
        if_exists=True,
    )
    op.drop_index(
        "idx_proc_creds_status_expiration",
        table_name="procedure_credentials",
        if_exists=True,
    )
    op.drop_index(
        "idx_proc_creds_procedure_status_exp",
        table_name="procedure_credentials",
        if_exists=True,
    )
    op.drop_index(
        "idx_proc_creds_person_status_exp",
        table_name="procedure_credentials",
        if_exists=True,
    )
    op.drop_index(
        "idx_import_staged_absences_batch_id",
        table_name="import_staged_absences",
        if_exists=True,
    )
    op.drop_index(
        "idx_import_staged_asgn_batch_row",
        table_name="import_staged_assignments",
        if_exists=True,
    )
    op.drop_index(
        "idx_import_batches_status_created",
        table_name="import_batches",
        if_exists=True,
    )
    op.drop_index(
        "idx_notifications_recipient_read_created",
        table_name="notifications",
        if_exists=True,
    )
    op.drop_index(
        "idx_swap_records_target_faculty_status",
        table_name="swap_records",
        if_exists=True,
    )
    op.drop_index(
        "idx_swap_records_target_week",
        table_name="swap_records",
        if_exists=True,
    )
    op.drop_index(
        "idx_swap_records_source_week",
        table_name="swap_records",
        if_exists=True,
    )
