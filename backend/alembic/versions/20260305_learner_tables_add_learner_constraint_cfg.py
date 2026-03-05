"""add_learner_constraint_cfg

Creates learner scheduling tables (learner_tracks, learner_to_tracks,
learner_assignments), constraint_configurations table, and adds
learner-specific columns to the people table.

Revision ID: 20260305_learner_tables
Revises: 20260228_fix_capacity_flags
Create Date: 2026-03-05 07:32:22.844310

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.db.types import GUID


# revision identifiers, used by Alembic.
revision: str = "20260305_learner_tables"
down_revision: str | None = "20260228_fix_capacity_flags"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- learner_tracks ---
    op.create_table(
        "learner_tracks",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("track_number", sa.Integer, nullable=False, unique=True),
        sa.Column("default_fmit_week", sa.Integer, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.CheckConstraint("track_number BETWEEN 1 AND 7", name="check_track_number"),
        sa.CheckConstraint("default_fmit_week BETWEEN 1 AND 4", name="check_fmit_week"),
    )

    # --- learner_to_tracks ---
    op.create_table(
        "learner_to_tracks",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column(
            "learner_id",
            GUID(),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "track_id",
            GUID(),
            sa.ForeignKey("learner_tracks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("requires_fmit", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime),
        sa.CheckConstraint("end_date >= start_date", name="check_learner_dates"),
        sa.UniqueConstraint("learner_id", "start_date", name="uq_learner_start_date"),
    )

    # --- learner_assignments ---
    op.create_table(
        "learner_assignments",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column(
            "learner_id",
            GUID(),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_assignment_id",
            GUID(),
            sa.ForeignKey("assignments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "block_id",
            GUID(),
            sa.ForeignKey("blocks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("activity_type", sa.String(20), nullable=False),
        sa.Column("day_of_week", sa.Integer, nullable=False),
        sa.Column("time_of_day", sa.String(2), nullable=False),
        sa.Column("source", sa.String(20), server_default="solver"),
        sa.Column("created_at", sa.DateTime),
        sa.CheckConstraint(
            "activity_type IN ('FMIT', 'ASM', 'clinic', 'procedures', "
            "'post_call', 'inprocessing', 'outprocessing', 'didactics', 'advising')",
            name="check_learner_activity_type",
        ),
        sa.CheckConstraint("day_of_week BETWEEN 0 AND 4", name="check_learner_day"),
        sa.CheckConstraint("time_of_day IN ('AM', 'PM')", name="check_learner_time"),
        sa.UniqueConstraint(
            "learner_id",
            "block_id",
            "day_of_week",
            "time_of_day",
            name="uq_learner_slot",
        ),
    )

    # --- constraint_configurations ---
    op.create_table(
        "constraint_configurations",
        sa.Column("id", GUID(), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="'MEDIUM'"),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("updated_at", sa.DateTime),
        sa.Column("updated_by", sa.String(100), nullable=True),
        sa.CheckConstraint(
            "priority IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')",
            name="check_constraint_priority",
        ),
        sa.CheckConstraint("weight >= 0", name="check_constraint_weight_positive"),
    )

    # --- Add learner columns to people ---
    # Use batch mode for CHECK constraint modification
    op.add_column("people", sa.Column("learner_type", sa.String(10), nullable=True))
    op.add_column("people", sa.Column("med_school", sa.String(255), nullable=True))
    op.add_column("people", sa.Column("ms_year", sa.Integer, nullable=True))
    op.add_column("people", sa.Column("rotation_start", sa.DateTime, nullable=True))
    op.add_column("people", sa.Column("rotation_end", sa.DateTime, nullable=True))
    op.add_column(
        "people", sa.Column("requires_fmit", sa.Boolean, server_default="true")
    )

    # Update check_person_type to include new types
    op.drop_constraint("check_person_type", "people", type_="check")
    op.create_check_constraint(
        "check_person_type",
        "people",
        "type IN ('resident', 'faculty', 'med_student', 'rotating_intern')",
    )

    # Add check_learner_type constraint
    op.create_check_constraint(
        "check_learner_type",
        "people",
        "learner_type IS NULL OR learner_type IN ('MS', 'TY', 'PSYCH')",
    )


def downgrade() -> None:
    # Drop learner columns from people
    op.drop_constraint("check_learner_type", "people", type_="check")
    op.drop_constraint("check_person_type", "people", type_="check")
    op.create_check_constraint(
        "check_person_type",
        "people",
        "type IN ('resident', 'faculty')",
    )
    op.drop_column("people", "requires_fmit")
    op.drop_column("people", "rotation_end")
    op.drop_column("people", "rotation_start")
    op.drop_column("people", "ms_year")
    op.drop_column("people", "med_school")
    op.drop_column("people", "learner_type")

    # Drop tables
    op.drop_table("constraint_configurations")
    op.drop_table("learner_assignments")
    op.drop_table("learner_to_tracks")
    op.drop_table("learner_tracks")
