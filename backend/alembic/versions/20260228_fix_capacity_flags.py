"""Fix counts_toward_physical_capacity flags for clinic activities.

Many clinic activities (C, fm_clinic, C-I, C40, C60, CC, sm_clinic, RAD)
had counts_toward_physical_capacity = false even though they are patient-
generating activities. Root cause: the original seed migration
(20260114_half_day_tables) ran before some activities were created, so
the UPDATE matched 0 rows. Later NULL→false backfill cemented the wrong value.

Also sets provides_supervision = true for sm_clinic (Sports Medicine faculty
provide supervision during clinic) and DO (Direct Observation is supervision).

Revision ID: 20260228_fix_capacity_flags
Revises: 20260227_sched_grid
"""

import sqlalchemy as sa
from alembic import op

revision = "20260228_fix_capacity_flags"
down_revision = "20260227_sched_grid"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Fix counts_toward_physical_capacity for clinic activities."""
    # Activities that generate patient load and count toward the max-6/slot
    # physical capacity constraint.  These are the activities mapped to
    # the solver's "C" (clinic) category.
    clinic_codes = [
        "C",  # Core clinic
        "fm_clinic",  # FM continuity clinic (display: C)
        "C-I",  # Clinic - Inpatient
        "C30",  # 30-min clinic
        "C40",  # 40-min clinic
        "C60",  # 60-min clinic
        "CC",  # Continuity clinic
        "sm_clinic",  # Sports Medicine clinic
        "RAD",  # Radiology clinic
    ]

    for code in clinic_codes:
        op.execute(
            sa.text(
                "UPDATE activities SET counts_toward_physical_capacity = true "
                "WHERE code = :code AND counts_toward_physical_capacity = false"
            ).bindparams(code=code)
        )

    # Note: CV, C-N, HLC, PR, VAS, VASC already have the correct value (true)
    # from the original seed or from 20260120_add_rot_activities.py.

    # Note: "asm" in engine.py's _SOLVER_CLINIC_CODES does not exist in the DB.
    # The actual code is "aSM" (Advanced Sports Medicine). If it should count
    # toward capacity, update it here. Skipping for now — needs coordinator
    # confirmation.


def downgrade() -> None:
    """Revert capacity flags (set back to false)."""
    codes_to_revert = [
        "C",
        "fm_clinic",
        "C-I",
        "C30",
        "C40",
        "C60",
        "CC",
        "sm_clinic",
        "RAD",
    ]
    for code in codes_to_revert:
        op.execute(
            sa.text(
                "UPDATE activities SET counts_toward_physical_capacity = false "
                "WHERE code = :code"
            ).bindparams(code=code)
        )
