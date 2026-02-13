"""Add indexes on most-queried columns for query performance.

Analysis of route handlers and service layer query patterns revealed several
heavily-filtered and ordered columns lacking indexes.  The tables below were
identified through EXPLAIN ANALYZE-style review of common query hot-paths:

  conflict_alerts  – status, faculty_id, fmit_week (range + ORDER BY),
                     severity, created_at
  swap_records     – status, requested_at (ORDER BY DESC)
  swap_approvals   – swap_id, faculty_id
  schedule_runs    – status, (start_date, end_date) range lookups
  schedule_drafts  – status, (status, target_start_date, target_end_date)
  schedule_draft_assignments – draft_id, person_id
  schedule_draft_flags       – draft_id
  rotation_templates         – name, rotation_type
  absences                   – (person_id, start_date, end_date) overlap checks,
                               status, absence_type
  call_assignments           – (person_id, date) composite for person call history
  users                      – role, is_active

All CREATE INDEX statements use ``if_not_exists=True`` for idempotency.

Revision ID: 20260212_query_perf_idx
Revises: 20260205_add_credential_flag_type
Create Date: 2026-02-12
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260212_query_perf_idx"
down_revision = "20260205_add_credential_flag_type"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes on most-queried columns."""

    # ── conflict_alerts ──────────────────────────────────────────────
    # Filtered by status in health dashboards, alert listings
    op.create_index(
        "idx_conflict_alerts_status",
        "conflict_alerts",
        ["status"],
        unique=False,
        if_not_exists=True,
    )
    # Filtered by faculty_id for per-faculty alert lookups
    op.create_index(
        "idx_conflict_alerts_faculty_id",
        "conflict_alerts",
        ["faculty_id"],
        unique=False,
        if_not_exists=True,
    )
    # Range queries and ORDER BY on fmit_week
    op.create_index(
        "idx_conflict_alerts_fmit_week",
        "conflict_alerts",
        ["fmit_week"],
        unique=False,
        if_not_exists=True,
    )
    # Composite: faculty alerts filtered by status within a date range
    op.create_index(
        "idx_conflict_alerts_faculty_status",
        "conflict_alerts",
        ["faculty_id", "status"],
        unique=False,
        if_not_exists=True,
    )
    # ORDER BY created_at DESC on alert listings
    op.create_index(
        "idx_conflict_alerts_created_at",
        "conflict_alerts",
        ["created_at"],
        unique=False,
        if_not_exists=True,
    )

    # ── swap_records ─────────────────────────────────────────────────
    # Heavily filtered by status (PENDING, APPROVED, EXECUTED, etc.)
    op.create_index(
        "idx_swap_records_status",
        "swap_records",
        ["status"],
        unique=False,
        if_not_exists=True,
    )
    # Composite: pending swap queue ordered by request time
    op.create_index(
        "idx_swap_records_status_requested",
        "swap_records",
        ["status", "requested_at"],
        unique=False,
        if_not_exists=True,
    )

    # ── swap_approvals ───────────────────────────────────────────────
    # FK lookups: approvals for a given swap
    op.create_index(
        "idx_swap_approvals_swap_id",
        "swap_approvals",
        ["swap_id"],
        unique=False,
        if_not_exists=True,
    )
    # FK lookups: approvals by a specific faculty member
    op.create_index(
        "idx_swap_approvals_faculty_id",
        "swap_approvals",
        ["faculty_id"],
        unique=False,
        if_not_exists=True,
    )

    # ── schedule_runs ────────────────────────────────────────────────
    # Filtered by status ("success", "failed", etc.) in analytics
    op.create_index(
        "idx_schedule_runs_status",
        "schedule_runs",
        ["status"],
        unique=False,
        if_not_exists=True,
    )
    # Range queries on (start_date, end_date)
    op.create_index(
        "idx_schedule_runs_date_range",
        "schedule_runs",
        ["start_date", "end_date"],
        unique=False,
        if_not_exists=True,
    )

    # ── schedule_drafts ──────────────────────────────────────────────
    # Filtered by status (DRAFT, PUBLISHED, etc.)
    op.create_index(
        "idx_schedule_drafts_status",
        "schedule_drafts",
        ["status"],
        unique=False,
        if_not_exists=True,
    )
    # Composite: draft lookup by status + date window
    op.create_index(
        "idx_schedule_drafts_status_dates",
        "schedule_drafts",
        ["status", "target_start_date", "target_end_date"],
        unique=False,
        if_not_exists=True,
    )

    # ── schedule_draft_assignments ───────────────────────────────────
    # FK lookup: all assignments within a draft
    op.create_index(
        "idx_sched_draft_asgn_draft_id",
        "schedule_draft_assignments",
        ["draft_id"],
        unique=False,
        if_not_exists=True,
    )
    # FK lookup: all draft assignments for a person
    op.create_index(
        "idx_sched_draft_asgn_person_id",
        "schedule_draft_assignments",
        ["person_id"],
        unique=False,
        if_not_exists=True,
    )

    # ── schedule_draft_flags ─────────────────────────────────────────
    # FK lookup: all flags for a draft
    op.create_index(
        "idx_sched_draft_flags_draft_id",
        "schedule_draft_flags",
        ["draft_id"],
        unique=False,
        if_not_exists=True,
    )

    # ── rotation_templates ───────────────────────────────────────────
    # Filtered by name (e.g., "FMIT" lookup) across multiple services
    op.create_index(
        "idx_rotation_templates_name",
        "rotation_templates",
        ["name"],
        unique=False,
        if_not_exists=True,
    )
    # Filtered by rotation_type in template listing and filtering
    op.create_index(
        "idx_rotation_templates_rotation_type",
        "rotation_templates",
        ["rotation_type"],
        unique=False,
        if_not_exists=True,
    )

    # ── absences ─────────────────────────────────────────────────────
    # Composite: overlap checks for a person's absences in a date range
    op.create_index(
        "idx_absences_person_dates",
        "absences",
        ["person_id", "start_date", "end_date"],
        unique=False,
        if_not_exists=True,
    )
    # Filtered by status (pending, approved, rejected, cancelled)
    op.create_index(
        "idx_absences_status",
        "absences",
        ["status"],
        unique=False,
        if_not_exists=True,
    )
    # Filtered by absence_type
    op.create_index(
        "idx_absences_type",
        "absences",
        ["absence_type"],
        unique=False,
        if_not_exists=True,
    )

    # ── call_assignments ─────────────────────────────────────────────
    # Composite: person's call history by date (common lookup pattern)
    op.create_index(
        "idx_call_assignments_person_date",
        "call_assignments",
        ["person_id", "date"],
        unique=False,
        if_not_exists=True,
    )

    # ── users ────────────────────────────────────────────────────────
    # Filtered by role in access control checks
    op.create_index(
        "idx_users_role",
        "users",
        ["role"],
        unique=False,
        if_not_exists=True,
    )
    # Filtered by is_active for authentication
    op.create_index(
        "idx_users_is_active",
        "users",
        ["is_active"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index("idx_users_is_active", table_name="users", if_exists=True)
    op.drop_index("idx_users_role", table_name="users", if_exists=True)
    op.drop_index(
        "idx_call_assignments_person_date",
        table_name="call_assignments",
        if_exists=True,
    )
    op.drop_index("idx_absences_type", table_name="absences", if_exists=True)
    op.drop_index("idx_absences_status", table_name="absences", if_exists=True)
    op.drop_index("idx_absences_person_dates", table_name="absences", if_exists=True)
    op.drop_index(
        "idx_rotation_templates_rotation_type",
        table_name="rotation_templates",
        if_exists=True,
    )
    op.drop_index(
        "idx_rotation_templates_name",
        table_name="rotation_templates",
        if_exists=True,
    )
    op.drop_index(
        "idx_sched_draft_flags_draft_id",
        table_name="schedule_draft_flags",
        if_exists=True,
    )
    op.drop_index(
        "idx_sched_draft_asgn_person_id",
        table_name="schedule_draft_assignments",
        if_exists=True,
    )
    op.drop_index(
        "idx_sched_draft_asgn_draft_id",
        table_name="schedule_draft_assignments",
        if_exists=True,
    )
    op.drop_index(
        "idx_schedule_drafts_status_dates",
        table_name="schedule_drafts",
        if_exists=True,
    )
    op.drop_index(
        "idx_schedule_drafts_status",
        table_name="schedule_drafts",
        if_exists=True,
    )
    op.drop_index(
        "idx_schedule_runs_date_range",
        table_name="schedule_runs",
        if_exists=True,
    )
    op.drop_index(
        "idx_schedule_runs_status",
        table_name="schedule_runs",
        if_exists=True,
    )
    op.drop_index(
        "idx_swap_approvals_faculty_id",
        table_name="swap_approvals",
        if_exists=True,
    )
    op.drop_index(
        "idx_swap_approvals_swap_id",
        table_name="swap_approvals",
        if_exists=True,
    )
    op.drop_index(
        "idx_swap_records_status_requested",
        table_name="swap_records",
        if_exists=True,
    )
    op.drop_index(
        "idx_swap_records_status",
        table_name="swap_records",
        if_exists=True,
    )
    op.drop_index(
        "idx_conflict_alerts_created_at",
        table_name="conflict_alerts",
        if_exists=True,
    )
    op.drop_index(
        "idx_conflict_alerts_faculty_status",
        table_name="conflict_alerts",
        if_exists=True,
    )
    op.drop_index(
        "idx_conflict_alerts_fmit_week",
        table_name="conflict_alerts",
        if_exists=True,
    )
    op.drop_index(
        "idx_conflict_alerts_faculty_id",
        table_name="conflict_alerts",
        if_exists=True,
    )
    op.drop_index(
        "idx_conflict_alerts_status",
        table_name="conflict_alerts",
        if_exists=True,
    )
