"""Add institutional events table.

Revision ID: 20260130_add_institutional_events
Revises: 20260129_add_gap_override_type
Create Date: 2026-01-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "20260130_add_institutional_events"
down_revision: str | None = "20260129_add_gap_override_type"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    event_type_enum = sa.Enum(
        "holiday",
        "conference",
        "retreat",
        "training",
        "closure",
        "other",
        name="institutionaleventtype",
    )
    event_scope_enum = sa.Enum(
        "all", "faculty", "resident", name="institutionaleventscope"
    )

    op.create_table(
        "institutional_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("event_type", event_type_enum, nullable=False),
        sa.Column("applies_to", event_scope_enum, nullable=False, server_default="all"),
        sa.Column(
            "activity_id",
            UUID(as_uuid=True),
            sa.ForeignKey("activities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("time_of_day", sa.String(length=2), nullable=True),
        sa.Column(
            "applies_to_inpatient",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "time_of_day IN ('AM', 'PM') OR time_of_day IS NULL",
            name="check_institutional_event_time_of_day",
        ),
        sa.CheckConstraint(
            "end_date >= start_date",
            name="check_institutional_event_dates",
        ),
    )

    op.create_index("ix_institutional_events_name", "institutional_events", ["name"])
    op.create_index(
        "ix_institutional_events_event_type",
        "institutional_events",
        ["event_type"],
    )
    op.create_index(
        "ix_institutional_events_applies_to",
        "institutional_events",
        ["applies_to"],
    )
    op.create_index(
        "ix_institutional_events_activity_id",
        "institutional_events",
        ["activity_id"],
    )
    op.create_index(
        "ix_institutional_events_is_active",
        "institutional_events",
        ["is_active"],
    )
    op.create_index(
        "ix_institutional_events_start_date",
        "institutional_events",
        ["start_date"],
    )
    op.create_index(
        "ix_institutional_events_end_date",
        "institutional_events",
        ["end_date"],
    )
    op.create_index(
        "ix_institutional_events_date_range",
        "institutional_events",
        ["start_date", "end_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_institutional_events_date_range", table_name="institutional_events"
    )
    op.drop_index("ix_institutional_events_end_date", table_name="institutional_events")
    op.drop_index(
        "ix_institutional_events_start_date", table_name="institutional_events"
    )
    op.drop_index(
        "ix_institutional_events_is_active", table_name="institutional_events"
    )
    op.drop_index(
        "ix_institutional_events_activity_id", table_name="institutional_events"
    )
    op.drop_index(
        "ix_institutional_events_applies_to", table_name="institutional_events"
    )
    op.drop_index(
        "ix_institutional_events_event_type", table_name="institutional_events"
    )
    op.drop_index("ix_institutional_events_name", table_name="institutional_events")
    op.drop_table("institutional_events")
    op.execute("DROP TYPE IF EXISTS institutionaleventscope")
    op.execute("DROP TYPE IF EXISTS institutionaleventtype")
