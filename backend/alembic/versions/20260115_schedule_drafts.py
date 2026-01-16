"""Add schedule draft tables for staging workflow.

Revision ID: 20260115_schedule_drafts
Revises: 20260114_sm_constraints
Create Date: 2026-01-15

Adds staging tables for schedule preview and publish workflow:
- schedule_drafts: Tracks draft schedules with publish/rollback capability
- schedule_draft_assignments: Staged assignments before commit to live
- schedule_draft_flags: Flags requiring review before publish
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260115_schedule_drafts"
down_revision = "20260114_sm_constraints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types using DO blocks to handle idempotency
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE schedule_draft_status AS ENUM (
                'draft', 'published', 'rolled_back', 'discarded'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE draft_source_type AS ENUM (
                'solver', 'manual', 'swap', 'import'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE draft_assignment_change_type AS ENUM (
                'add', 'modify', 'delete'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE draft_flag_type AS ENUM (
                'conflict', 'acgme_violation', 'coverage_gap', 'manual_review'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE draft_flag_severity AS ENUM (
                'error', 'warning', 'info'
            );
        EXCEPTION WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create schedule_drafts table
    op.create_table(
        "schedule_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        # Scope
        sa.Column("target_block", sa.Integer(), nullable=True),
        sa.Column("target_start_date", sa.Date(), nullable=False),
        sa.Column("target_end_date", sa.Date(), nullable=False),
        # Status
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft",
                "published",
                "rolled_back",
                "discarded",
                name="schedule_draft_status",
                create_type=False,
            ),
            nullable=False,
            server_default="draft",
        ),
        # Source tracking
        sa.Column(
            "source_type",
            postgresql.ENUM(
                "solver",
                "manual",
                "swap",
                "import",
                name="draft_source_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "source_schedule_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("schedule_runs.id"),
            nullable=True,
        ),
        # Publish tracking
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column(
            "published_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        # Archive/rollback
        sa.Column("archived_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rollback_available", sa.Boolean(), default=True),
        sa.Column("rollback_expires_at", sa.DateTime(), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime(), nullable=True),
        sa.Column(
            "rolled_back_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        # Metadata
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("change_summary", postgresql.JSONB(), nullable=True),
        # Flag tracking
        sa.Column("flags_total", sa.Integer(), default=0),
        sa.Column("flags_acknowledged", sa.Integer(), default=0),
        sa.Column("override_comment", sa.Text(), nullable=True),
        sa.Column(
            "override_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )

    # Create indexes for schedule_drafts
    op.create_index("idx_schedule_drafts_status", "schedule_drafts", ["status"])
    op.create_index("idx_schedule_drafts_block", "schedule_drafts", ["target_block"])
    op.create_index(
        "idx_schedule_drafts_dates",
        "schedule_drafts",
        ["target_start_date", "target_end_date"],
    )

    # Create schedule_draft_assignments table
    op.create_table(
        "schedule_draft_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "draft_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("schedule_drafts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Assignment data
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id"),
            nullable=False,
        ),
        sa.Column("assignment_date", sa.Date(), nullable=False),
        sa.Column("time_of_day", sa.String(10), nullable=True),
        sa.Column("activity_code", sa.String(50), nullable=True),
        sa.Column(
            "rotation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rotation_templates.id"),
            nullable=True,
        ),
        # Change tracking
        sa.Column(
            "change_type",
            postgresql.ENUM(
                "add",
                "modify",
                "delete",
                name="draft_assignment_change_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "existing_assignment_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        # After publish
        sa.Column(
            "created_assignment_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        # Unique constraint
        sa.UniqueConstraint(
            "draft_id",
            "person_id",
            "assignment_date",
            "time_of_day",
            name="uq_draft_assignment_slot",
        ),
    )

    # Create indexes for schedule_draft_assignments
    op.create_index(
        "idx_draft_assignments_draft", "schedule_draft_assignments", ["draft_id"]
    )
    op.create_index(
        "idx_draft_assignments_person", "schedule_draft_assignments", ["person_id"]
    )
    op.create_index(
        "idx_draft_assignments_date", "schedule_draft_assignments", ["assignment_date"]
    )

    # Create schedule_draft_flags table
    op.create_table(
        "schedule_draft_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "draft_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("schedule_drafts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Flag details
        sa.Column(
            "flag_type",
            postgresql.ENUM(
                "conflict",
                "acgme_violation",
                "coverage_gap",
                "manual_review",
                name="draft_flag_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            postgresql.ENUM(
                "error",
                "warning",
                "info",
                name="draft_flag_severity",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        # Related entities
        sa.Column(
            "assignment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("schedule_draft_assignments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id"),
            nullable=True,
        ),
        sa.Column("affected_date", sa.Date(), nullable=True),
        # Resolution
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column(
            "acknowledged_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
    )

    # Create indexes for schedule_draft_flags
    op.create_index("idx_draft_flags_draft", "schedule_draft_flags", ["draft_id"])
    op.create_index("idx_draft_flags_type", "schedule_draft_flags", ["flag_type"])
    op.create_index("idx_draft_flags_severity", "schedule_draft_flags", ["severity"])
    op.create_index(
        "idx_draft_flags_acknowledged", "schedule_draft_flags", ["acknowledged_at"]
    )


def downgrade() -> None:
    # Drop tables in reverse order (due to FK constraints)
    op.drop_table("schedule_draft_flags")
    op.drop_table("schedule_draft_assignments")
    op.drop_table("schedule_drafts")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS draft_flag_severity;")
    op.execute("DROP TYPE IF EXISTS draft_flag_type;")
    op.execute("DROP TYPE IF EXISTS draft_assignment_change_type;")
    op.execute("DROP TYPE IF EXISTS draft_source_type;")
    op.execute("DROP TYPE IF EXISTS schedule_draft_status;")
