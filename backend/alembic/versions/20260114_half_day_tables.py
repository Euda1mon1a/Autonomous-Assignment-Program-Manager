"""Add half-day assignment tables for TAMC scheduling.

Revision ID: 20260114_half_day_tables
Revises: 20260114_sm_constraints
Create Date: 2026-01-14

This migration creates the unified half-day assignment model:
- half_day_assignments: Persisted daily AM/PM slots with source tracking
- inpatient_preloads: FMIT, NF, PedW, etc. preloaded before solver
- resident_call_preloads: Chief-assigned resident call

Also adds:
- Faculty clinic caps (min/max per week) to people table
- Physical capacity flag to activities table
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260114_half_day_tables"
down_revision = "20260114_sm_constraints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create half_day_assignments table
    op.create_table(
        "half_day_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("time_of_day", sa.String(2), nullable=False),
        sa.Column("activity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("block_assignment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_override", sa.Boolean(), nullable=False, default=False),
        sa.Column("override_reason", sa.Text(), nullable=True),
        sa.Column("overridden_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("overridden_at", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["activity_id"], ["activities.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["block_assignment_id"], ["block_assignments.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["overridden_by"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "time_of_day IN ('AM', 'PM')", name="check_half_day_time_of_day"
        ),
        sa.CheckConstraint(
            "source IN ('preload', 'manual', 'solver', 'template')",
            name="check_half_day_source",
        ),
        sa.UniqueConstraint(
            "person_id",
            "date",
            "time_of_day",
            name="uq_half_day_assignment_person_date_time",
        ),
    )

    # Create indexes for half_day_assignments
    op.create_index("idx_hda_person_id", "half_day_assignments", ["person_id"])
    op.create_index("idx_hda_date", "half_day_assignments", ["date"])
    op.create_index("idx_hda_activity_id", "half_day_assignments", ["activity_id"])
    op.create_index("idx_hda_source", "half_day_assignments", ["source"])
    op.create_index(
        "idx_hda_block_assignment_id", "half_day_assignments", ["block_assignment_id"]
    )
    op.create_index(
        "idx_hda_person_date", "half_day_assignments", ["person_id", "date"]
    )
    op.create_index(
        "idx_hda_date_time", "half_day_assignments", ["date", "time_of_day"]
    )

    # Create inpatient_preloads table
    op.create_table(
        "inpatient_preloads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rotation_type", sa.String(20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("fmit_week_number", sa.Integer(), nullable=True),
        sa.Column("includes_post_call", sa.Boolean(), nullable=False, default=False),
        sa.Column("assigned_by", sa.String(20), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "rotation_type IN ('FMIT', 'NF', 'PedW', 'PedNF', 'KAP', 'IM', 'LDNF')",
            name="check_inpatient_rotation_type",
        ),
        sa.CheckConstraint(
            "fmit_week_number IS NULL OR fmit_week_number BETWEEN 1 AND 4",
            name="check_fmit_week_number",
        ),
        sa.CheckConstraint(
            "assigned_by IS NULL OR assigned_by IN ('chief', 'scheduler', 'coordinator', 'manual')",
            name="check_preload_assigned_by",
        ),
        sa.CheckConstraint("end_date >= start_date", name="check_preload_dates"),
        sa.UniqueConstraint(
            "person_id",
            "start_date",
            "rotation_type",
            name="uq_inpatient_preload_person_start_type",
        ),
    )

    # Create indexes for inpatient_preloads
    op.create_index(
        "idx_inpatient_preload_person_id", "inpatient_preloads", ["person_id"]
    )
    op.create_index(
        "idx_inpatient_preload_rotation_type", "inpatient_preloads", ["rotation_type"]
    )
    op.create_index(
        "idx_inpatient_preload_start_date", "inpatient_preloads", ["start_date"]
    )
    op.create_index(
        "idx_inpatient_preload_dates", "inpatient_preloads", ["start_date", "end_date"]
    )

    # Create resident_call_preloads table
    op.create_table(
        "resident_call_preloads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("call_date", sa.Date(), nullable=False),
        sa.Column("call_type", sa.String(20), nullable=False),
        sa.Column("assigned_by", sa.String(20), nullable=True),
        sa.Column("notes", sa.String(500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "call_type IN ('ld_24hr', 'nf_coverage', 'weekend')",
            name="check_resident_call_type",
        ),
        sa.CheckConstraint(
            "assigned_by IS NULL OR assigned_by IN ('chief', 'scheduler')",
            name="check_resident_call_assigned_by",
        ),
        sa.UniqueConstraint(
            "person_id", "call_date", name="uq_resident_call_person_date"
        ),
    )

    # Create indexes for resident_call_preloads
    op.create_index(
        "idx_resident_call_person_id", "resident_call_preloads", ["person_id"]
    )
    op.create_index("idx_resident_call_date", "resident_call_preloads", ["call_date"])

    # Add faculty clinic caps to people table (if not already present)
    # Note: Some columns may already exist from previous migrations
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    people_cols = {c["name"] for c in inspector.get_columns("people")}
    activities_cols = {c["name"] for c in inspector.get_columns("activities")}

    if "min_clinic_halfdays_per_week" not in people_cols:
        op.add_column(
            "people",
            sa.Column(
                "min_clinic_halfdays_per_week", sa.Integer(), nullable=True, default=0
            ),
        )
    if "max_clinic_halfdays_per_week" not in people_cols:
        op.add_column(
            "people",
            sa.Column(
                "max_clinic_halfdays_per_week", sa.Integer(), nullable=True, default=4
            ),
        )
    if "admin_type" not in people_cols:
        op.add_column(
            "people",
            sa.Column("admin_type", sa.String(20), nullable=True, default="GME"),
        )

    # Add physical capacity flag to activities table (if not already present)
    if "counts_toward_physical_capacity" not in activities_cols:
        op.add_column(
            "activities",
            sa.Column(
                "counts_toward_physical_capacity",
                sa.Boolean(),
                nullable=True,
                default=False,
            ),
        )

    # Set defaults for existing rows - always run these since columns exist now
    op.execute(
        "UPDATE people SET min_clinic_halfdays_per_week = 0 WHERE min_clinic_halfdays_per_week IS NULL"
    )
    op.execute(
        "UPDATE people SET max_clinic_halfdays_per_week = 4 WHERE max_clinic_halfdays_per_week IS NULL"
    )
    op.execute(
        "UPDATE people SET admin_type = 'GME' WHERE admin_type IS NULL AND type = 'faculty'"
    )
    op.execute(
        "UPDATE activities SET counts_toward_physical_capacity = false WHERE counts_toward_physical_capacity IS NULL"
    )

    # Seed faculty caps per TAMC skill roster
    _seed_faculty_caps()

    # Seed activity physical capacity flags
    _seed_activity_capacity_flags()


def _seed_faculty_caps() -> None:
    """Seed faculty MIN/MAX clinic caps per TAMC skill roster."""
    # Format: (name_pattern, min_c, max_c, admin_type)
    faculty_caps = [
        ("%Bevis%", 0, 0, "GME"),  # APD, 100% admin
        ("%Kinkennon%", 2, 4, "GME"),
        ("%LaBounty%", 2, 4, "GME"),
        ("%McGuire%", 1, 1, "DFM"),  # 90% DFM admin
        ("%McRae%", 2, 4, "GME"),
        ("%Tagawa%", 0, 0, "SM"),  # Sports Med faculty, no regular C
        ("%Montgomery%", 2, 2, "GME"),
        ("%Colgan%", 0, 0, "GME"),  # DEP (deployed)
        ("%Chu%", 0, 0, "GME"),  # FMIT weeks
        ("%Napierala%", 0, 0, "GME"),  # FMIT/Call only (adjunct)
        ("%Van Brunt%", 0, 0, "GME"),  # FMIT/Call only (adjunct)
        ("%Lamoureux%", 2, 2, "GME"),
        ("%Dahl%", 0, 0, "GME"),  # OUT Dec-Jun
    ]

    for name_pattern, min_c, max_c, admin in faculty_caps:
        op.execute(f"""
            UPDATE people SET
                min_clinic_halfdays_per_week = {min_c},
                max_clinic_halfdays_per_week = {max_c},
                admin_type = '{admin}'
            WHERE name ILIKE '{name_pattern}' AND type = 'faculty';
        """)


def _seed_activity_capacity_flags() -> None:
    """Seed activity counts_toward_physical_capacity flags."""
    # Clinical activities that count toward physical capacity (max 6/slot)
    clinical_codes = ["C", "CV", "PR", "VAS", "C30", "C40", "C60", "CC"]

    for code in clinical_codes:
        op.execute(f"""
            UPDATE activities SET counts_toward_physical_capacity = true
            WHERE code = '{code}';
        """)

    # AT/supervision activities do NOT count toward physical capacity
    supervision_codes = ["AT", "PCAT", "DO"]
    for code in supervision_codes:
        op.execute(f"""
            UPDATE activities SET counts_toward_physical_capacity = false
            WHERE code = '{code}';
        """)


def downgrade() -> None:
    """Downgrade not supported for data-seeding migration."""
    raise NotImplementedError(
        "Downgrade not supported. This migration seeds faculty caps and activity "
        "capacity flags that cannot be safely reversed. If you need to undo these "
        "changes, restore from a database backup."
    )
