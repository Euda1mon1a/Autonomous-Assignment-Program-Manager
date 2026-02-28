"""Fix activity classification flags for solver correctness.

1. counts_toward_physical_capacity: Many clinic activities had false despite
   being patient-generating. Root cause: seed migration ran UPDATEs before
   the activities existed, so they matched 0 rows.

2. provides_supervision: Ensures AT, PCAT, DO, SM_CLINIC have true.
   Activity.is_supervision now depends on this field (not hardcoded strings),
   so incorrect values would undercount supervision coverage.

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

    # ----- provides_supervision backfill -----
    # Activity.is_supervision now depends on this field (not hardcoded strings).
    # Ensure all supervision activities have it set correctly.
    # SM_CLINIC is the special case: both supervision AND physical capacity.
    supervision_codes = [
        "at",  # Attending (core supervision)
        "pcat",  # Post-Call Attending (AM after overnight)
        "do",  # Direct Observation (supervision during clinic)
        "sm_clinic",  # Sports Medicine — supervises AND generates patient load
    ]
    for code in supervision_codes:
        op.execute(
            sa.text(
                "UPDATE activities SET provides_supervision = true "
                "WHERE code = :code AND provides_supervision = false"
            ).bindparams(code=code)
        )


def downgrade() -> None:
    """Revert capacity flags (only rows this migration touched).

    The upgrade only flips rows where counts_toward_physical_capacity was
    false, so the downgrade mirrors that by only reverting rows that are
    currently true for these codes.
    """
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
                "WHERE code = :code AND counts_toward_physical_capacity = true"
            ).bindparams(code=code)
        )

    # Revert provides_supervision (only rows this migration touched)
    supervision_codes = ["at", "pcat", "do", "sm_clinic"]
    for code in supervision_codes:
        op.execute(
            sa.text(
                "UPDATE activities SET provides_supervision = false "
                "WHERE code = :code AND provides_supervision = true"
            ).bindparams(code=code)
        )
