"""Add activities table for slot-level schedule events.

Revision ID: 20260109_add_activities
Revises: 20260108_add_weekend_config
Create Date: 2026-01-09

Activities are distinct from Rotations:
- Rotation = Multi-week block assignment (e.g., "Neurology" for 4 weeks)
- Activity = Slot-level event (e.g., "FM Clinic AM", "LEC Wednesday PM")

Default activities seeded:
- FM Clinic (fm_clinic) - Family medicine clinic sessions
- Specialty (specialty) - Rotation-specific specialty work
- LEC (lec) - Protected lecture/education time
- Elective (elective) - Flexible/elective time
- Inpatient (inpatient) - Hospital ward coverage
- Call (call) - Extended call duty
- Procedure (procedure) - Procedural clinic
- OFF (off) - Day off
- Recovery (recovery) - Post-call recovery
- Conference (conference) - Educational conferences
"""

import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260109_add_activities"
down_revision = "20260108_add_weekend_config"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create activities table and seed default activities."""
    # Create activities table
    op.create_table(
        "activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("display_abbreviation", sa.String(20), nullable=True),
        sa.Column("activity_category", sa.String(20), nullable=False),
        sa.Column("font_color", sa.String(50), nullable=True),
        sa.Column("background_color", sa.String(50), nullable=True),
        sa.Column(
            "requires_supervision",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "is_protected", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "counts_toward_clinical_hours",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "is_archived", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("archived_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("name", name="uq_activity_name"),
        sa.UniqueConstraint("code", name="uq_activity_code"),
    )

    # Create indexes
    op.create_index("ix_activities_code", "activities", ["code"])
    op.create_index(
        "ix_activities_activity_category", "activities", ["activity_category"]
    )
    op.create_index("ix_activities_is_protected", "activities", ["is_protected"])
    op.create_index("ix_activities_is_archived", "activities", ["is_archived"])

    # Seed default activities
    now = datetime.utcnow().isoformat()
    activities = [
        # Clinical activities
        {
            "id": str(uuid.uuid4()),
            "name": "FM Clinic",
            "code": "fm_clinic",
            "display_abbreviation": "C",
            "activity_category": "clinical",
            "font_color": "white",
            "background_color": "green-500",
            "requires_supervision": True,
            "is_protected": False,
            "counts_toward_clinical_hours": True,
            "display_order": 10,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Specialty",
            "code": "specialty",
            "display_abbreviation": "S",
            "activity_category": "clinical",
            "font_color": "white",
            "background_color": "sky-500",
            "requires_supervision": True,
            "is_protected": False,
            "counts_toward_clinical_hours": True,
            "display_order": 20,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Inpatient",
            "code": "inpatient",
            "display_abbreviation": "INP",
            "activity_category": "clinical",
            "font_color": "white",
            "background_color": "blue-600",
            "requires_supervision": True,
            "is_protected": False,
            "counts_toward_clinical_hours": True,
            "display_order": 30,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Call",
            "code": "call",
            "display_abbreviation": "CALL",
            "activity_category": "clinical",
            "font_color": "white",
            "background_color": "red-600",
            "requires_supervision": True,
            "is_protected": False,
            "counts_toward_clinical_hours": True,
            "display_order": 40,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Procedure",
            "code": "procedure",
            "display_abbreviation": "PROC",
            "activity_category": "clinical",
            "font_color": "black",
            "background_color": "yellow-300",
            "requires_supervision": True,
            "is_protected": False,
            "counts_toward_clinical_hours": True,
            "display_order": 50,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Elective",
            "code": "elective",
            "display_abbreviation": "ELEC",
            "activity_category": "clinical",
            "font_color": "black",
            "background_color": "amber-200",
            "requires_supervision": True,
            "is_protected": False,
            "counts_toward_clinical_hours": True,
            "display_order": 60,
        },
        # Educational activities
        {
            "id": str(uuid.uuid4()),
            "name": "Lecture",
            "code": "lec",
            "display_abbreviation": "LEC",
            "activity_category": "educational",
            "font_color": "white",
            "background_color": "purple-700",
            "requires_supervision": False,
            "is_protected": True,  # Protected - solver cannot move
            "counts_toward_clinical_hours": False,
            "display_order": 100,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Conference",
            "code": "conference",
            "display_abbreviation": "CONF",
            "activity_category": "educational",
            "font_color": "white",
            "background_color": "purple-500",
            "requires_supervision": False,
            "is_protected": True,  # Protected
            "counts_toward_clinical_hours": False,
            "display_order": 110,
        },
        # Time off activities
        {
            "id": str(uuid.uuid4()),
            "name": "Day Off",
            "code": "off",
            "display_abbreviation": "OFF",
            "activity_category": "time_off",
            "font_color": "gray-600",
            "background_color": "gray-200",
            "requires_supervision": False,
            "is_protected": False,
            "counts_toward_clinical_hours": False,
            "display_order": 200,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Recovery",
            "code": "recovery",
            "display_abbreviation": "REC",
            "activity_category": "time_off",
            "font_color": "gray-600",
            "background_color": "amber-100",
            "requires_supervision": False,
            "is_protected": False,
            "counts_toward_clinical_hours": False,
            "display_order": 210,
        },
    ]

    # Build INSERT statement
    activities_table = sa.table(
        "activities",
        sa.column("id", postgresql.UUID),
        sa.column("name", sa.String),
        sa.column("code", sa.String),
        sa.column("display_abbreviation", sa.String),
        sa.column("activity_category", sa.String),
        sa.column("font_color", sa.String),
        sa.column("background_color", sa.String),
        sa.column("requires_supervision", sa.Boolean),
        sa.column("is_protected", sa.Boolean),
        sa.column("counts_toward_clinical_hours", sa.Boolean),
        sa.column("display_order", sa.Integer),
        sa.column("is_archived", sa.Boolean),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )

    for activity in activities:
        op.execute(
            activities_table.insert().values(
                id=activity["id"],
                name=activity["name"],
                code=activity["code"],
                display_abbreviation=activity["display_abbreviation"],
                activity_category=activity["activity_category"],
                font_color=activity["font_color"],
                background_color=activity["background_color"],
                requires_supervision=activity["requires_supervision"],
                is_protected=activity["is_protected"],
                counts_toward_clinical_hours=activity["counts_toward_clinical_hours"],
                display_order=activity["display_order"],
                is_archived=False,
                created_at=now,
                updated_at=now,
            )
        )


def downgrade() -> None:
    """Drop activities table."""
    op.drop_index("ix_activities_is_archived", table_name="activities")
    op.drop_index("ix_activities_is_protected", table_name="activities")
    op.drop_index("ix_activities_activity_category", table_name="activities")
    op.drop_index("ix_activities_code", table_name="activities")
    op.drop_table("activities")
