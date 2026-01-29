"""Add schedule overrides for post-release coverage changes.

Revision ID: 20260129_add_schedule_overrides
Revises: 20260129_link_activities_to_procedures
Create Date: 2026-01-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260129_add_schedule_overrides"
down_revision = "20260129_link_activities_to_procedures"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "schedule_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "half_day_assignment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("half_day_assignments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "original_person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "replacement_person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "override_type",
            sa.String(length=20),
            nullable=False,
            server_default="'coverage'",
        ),
        sa.Column("reason", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("time_of_day", sa.String(length=2), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column(
            "deactivated_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "supersedes_override_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("schedule_overrides.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "override_type IN ('coverage', 'cancellation')",
            name="ck_schedule_override_type",
        ),
        sa.CheckConstraint(
            "time_of_day IN ('AM', 'PM')",
            name="ck_schedule_override_time_of_day",
        ),
        sa.CheckConstraint(
            "(override_type = 'coverage' AND replacement_person_id IS NOT NULL) "
            "OR (override_type = 'cancellation' AND replacement_person_id IS NULL)",
            name="ck_schedule_override_replacement",
        ),
    )

    op.create_index(
        "idx_schedule_overrides_effective",
        "schedule_overrides",
        ["effective_date", "time_of_day"],
    )
    op.create_index(
        "idx_schedule_overrides_active",
        "schedule_overrides",
        ["is_active"],
    )
    op.create_index(
        "idx_schedule_overrides_assignment",
        "schedule_overrides",
        ["half_day_assignment_id"],
    )
    op.create_index(
        "idx_schedule_overrides_replacement",
        "schedule_overrides",
        ["replacement_person_id"],
    )
    op.create_index(
        "idx_schedule_overrides_original",
        "schedule_overrides",
        ["original_person_id"],
    )
    op.create_index(
        "idx_schedule_overrides_created_by",
        "schedule_overrides",
        ["created_by_id"],
    )
    op.create_index(
        "uq_schedule_overrides_active_assignment",
        "schedule_overrides",
        ["half_day_assignment_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_schedule_overrides_active_assignment",
        table_name="schedule_overrides",
    )
    op.drop_index(
        "idx_schedule_overrides_created_by",
        table_name="schedule_overrides",
    )
    op.drop_index(
        "idx_schedule_overrides_original",
        table_name="schedule_overrides",
    )
    op.drop_index(
        "idx_schedule_overrides_replacement",
        table_name="schedule_overrides",
    )
    op.drop_index(
        "idx_schedule_overrides_assignment",
        table_name="schedule_overrides",
    )
    op.drop_index(
        "idx_schedule_overrides_active",
        table_name="schedule_overrides",
    )
    op.drop_index(
        "idx_schedule_overrides_effective",
        table_name="schedule_overrides",
    )
    op.drop_table("schedule_overrides")
