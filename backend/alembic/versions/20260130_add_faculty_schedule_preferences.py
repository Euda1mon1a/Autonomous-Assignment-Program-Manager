"""Add faculty schedule preferences.

Revision ID: 20260130_add_faculty_schedule_preferences
Revises: 20260130_add_institutional_events
Create Date: 2026-01-30
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "20260130_add_faculty_schedule_preferences"
down_revision: str | None = "20260130_add_institutional_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    preference_type_enum = sa.Enum(
        "clinic",
        "call",
        name="facultypreferencetype",
    )
    direction_enum = sa.Enum(
        "prefer",
        "avoid",
        name="facultypreferencedirection",
    )

    op.create_table(
        "faculty_schedule_preferences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "person_id",
            UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("preference_type", preference_type_enum, nullable=False),
        sa.Column("direction", direction_enum, nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("time_of_day", sa.String(length=2), nullable=True),
        sa.Column(
            "weight",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("6"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "person_id",
            "rank",
            name="uq_faculty_schedule_preference_rank",
        ),
        sa.CheckConstraint(
            "rank IN (1, 2)",
            name="check_faculty_schedule_preference_rank",
        ),
        sa.CheckConstraint(
            "day_of_week BETWEEN 0 AND 6",
            name="check_faculty_schedule_preference_day",
        ),
        sa.CheckConstraint(
            "time_of_day IN ('AM', 'PM') OR time_of_day IS NULL",
            name="check_faculty_schedule_preference_time",
        ),
        sa.CheckConstraint(
            "(preference_type = 'clinic' AND time_of_day IS NOT NULL) "
            "OR (preference_type = 'call' AND time_of_day IS NULL)",
            name="check_faculty_schedule_preference_type",
        ),
    )

    op.create_index(
        "ix_faculty_schedule_preferences_person_id",
        "faculty_schedule_preferences",
        ["person_id"],
    )
    op.create_index(
        "ix_faculty_schedule_preferences_preference_type",
        "faculty_schedule_preferences",
        ["preference_type"],
    )
    op.create_index(
        "ix_faculty_schedule_preferences_direction",
        "faculty_schedule_preferences",
        ["direction"],
    )
    op.create_index(
        "ix_faculty_schedule_preferences_is_active",
        "faculty_schedule_preferences",
        ["is_active"],
    )
    op.create_index(
        "ix_faculty_schedule_preferences_person_active",
        "faculty_schedule_preferences",
        ["person_id", "is_active"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_faculty_schedule_preferences_person_active",
        table_name="faculty_schedule_preferences",
    )
    op.drop_index(
        "ix_faculty_schedule_preferences_is_active",
        table_name="faculty_schedule_preferences",
    )
    op.drop_index(
        "ix_faculty_schedule_preferences_direction",
        table_name="faculty_schedule_preferences",
    )
    op.drop_index(
        "ix_faculty_schedule_preferences_preference_type",
        table_name="faculty_schedule_preferences",
    )
    op.drop_index(
        "ix_faculty_schedule_preferences_person_id",
        table_name="faculty_schedule_preferences",
    )
    op.drop_table("faculty_schedule_preferences")
    op.execute("DROP TYPE IF EXISTS facultypreferencedirection")
    op.execute("DROP TYPE IF EXISTS facultypreferencetype")
