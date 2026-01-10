"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # People table (residents and faculty)
    op.create_table(
        "people",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), unique=True),
        sa.Column("pgy_level", sa.Integer()),
        sa.Column("performs_procedures", sa.Boolean(), default=False),
        sa.Column("specialties", postgresql.ARRAY(sa.String())),
        sa.Column("primary_duty", sa.String(255)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.CheckConstraint("type IN ('resident', 'faculty')", name="check_person_type"),
        sa.CheckConstraint(
            "pgy_level IS NULL OR pgy_level BETWEEN 1 AND 3", name="check_pgy_level"
        ),
    )
    op.create_index("idx_people_type", "people", ["type"])

    # Blocks table (half-day scheduling blocks)
    op.create_table(
        "blocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time_of_day", sa.String(2), nullable=False),
        sa.Column("block_number", sa.Integer(), nullable=False),
        sa.Column("is_weekend", sa.Boolean(), default=False),
        sa.Column("is_holiday", sa.Boolean(), default=False),
        sa.Column("holiday_name", sa.String(255)),
        sa.UniqueConstraint("date", "time_of_day", name="unique_block_per_half_day"),
        sa.CheckConstraint("time_of_day IN ('AM', 'PM')", name="check_time_of_day"),
    )
    op.create_index("idx_blocks_date", "blocks", ["date"])
    op.create_index("idx_blocks_block_number", "blocks", ["block_number"])

    # Rotation templates table
    op.create_table(
        "rotation_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("activity_type", sa.String(255), nullable=False),
        sa.Column("abbreviation", sa.String(10)),
        sa.Column("clinic_location", sa.String(255)),
        sa.Column("max_residents", sa.Integer()),
        sa.Column("requires_specialty", sa.String(255)),
        sa.Column("requires_procedure_credential", sa.Boolean(), default=False),
        sa.Column("supervision_required", sa.Boolean(), default=True),
        sa.Column("max_supervision_ratio", sa.Integer(), default=4),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Assignments table (the schedule)
    op.create_table(
        "assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "block_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("blocks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "rotation_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("rotation_templates.id"),
        ),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("activity_override", sa.String(255)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("block_id", "person_id", name="unique_person_per_block"),
        sa.CheckConstraint(
            "role IN ('primary', 'supervising', 'backup')", name="check_role"
        ),
    )
    op.create_index("idx_assignments_block", "assignments", ["block_id"])
    op.create_index("idx_assignments_person", "assignments", ["person_id"])

    # Absences table (leave, deployments, TDY)
    op.create_table(
        "absences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("absence_type", sa.String(50), nullable=False),
        sa.Column("deployment_orders", sa.Boolean(), default=False),
        sa.Column("tdy_location", sa.String(255)),
        sa.Column("replacement_activity", sa.String(255)),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.CheckConstraint("end_date >= start_date", name="check_absence_dates"),
        sa.CheckConstraint(
            "absence_type IN ('vacation', 'deployment', 'tdy', 'medical', 'family_emergency', 'conference')",
            name="check_absence_type",
        ),
    )
    op.create_index("idx_absences_person", "absences", ["person_id"])
    op.create_index("idx_absences_dates", "absences", ["start_date", "end_date"])

    # Call assignments table
    op.create_table(
        "call_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("call_type", sa.String(50), nullable=False),
        sa.Column("is_weekend", sa.Boolean(), default=False),
        sa.Column("is_holiday", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "date", "person_id", "call_type", name="unique_call_per_day"
        ),
        sa.CheckConstraint(
            "call_type IN ('overnight', 'weekend', 'backup')", name="check_call_type"
        ),
    )
    op.create_index("idx_call_date", "call_assignments", ["date"])
    op.create_index("idx_call_person", "call_assignments", ["person_id"])

    # Schedule runs table (audit trail)
    op.create_table(
        "schedule_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("algorithm", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("total_blocks_assigned", sa.Integer()),
        sa.Column("acgme_violations", sa.Integer(), default=0),
        sa.Column("runtime_seconds", sa.Numeric(10, 2)),
        sa.Column("config_json", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_schedule_runs_date", "schedule_runs", ["created_at"])


def downgrade() -> None:
    op.drop_table("schedule_runs")
    op.drop_table("call_assignments")
    op.drop_table("absences")
    op.drop_table("assignments")
    op.drop_table("rotation_templates")
    op.drop_table("blocks")
    op.drop_table("people")
