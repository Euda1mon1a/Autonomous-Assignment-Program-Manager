"""Block 12 activity requirements: PEM activity, NF combo reqs, clinic mins

Fixes 277 null-activity half-day assignments in Block 12 by:
1. Creating PEM (Pediatric Emergency Medicine) activity for off-site preload
2. Adding NF + specialty activity requirements for combined NF rotations
3. Setting non-zero min_halfdays on MSK Selective and FM Clinic primary activities

Revision ID: 20260224_blk12_act_reqs
Revises: 20260219_add_gt_tables
Create Date: 2026-02-24

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260224_blk12_act_reqs"
down_revision: str = "20260219_add_gt_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# --- Activity IDs (from production DB) ---
ACTIVITY_NF = "f677382c-390e-4c50-83a0-0153ad55da53"
ACTIVITY_FMIT = "9fd0dca9-f260-478d-80b1-c9ea5d78b6d0"
ACTIVITY_CARDS = "9d993a60-256b-41cd-a657-3fb4d8a10456"
ACTIVITY_DERM = "eac32207-030f-4b44-aba7-1041cc4ede6e"

# --- Rotation Template IDs ---
RT_NF_FMIT = "6dd781d5-41aa-4dd3-a44b-a3c3eea439c5"
RT_NF_CARDS = "691ad20d-cc4a-4d2a-bed4-22b90ad1a903"
RT_NF_DERM = "38d35ac5-bb3c-4161-ace8-9f26ec4e88a6"

# --- Existing rotation_activity_requirements IDs to UPDATE (Cat 3) ---
RAR_MSK_SM_CLINIC = "c7c437d2-9228-4a52-bec9-4534ed7fefe1"
RAR_MSK_RADIOLOGY = "2e6523a5-4dac-4224-b865-8d991e421437"
RAR_MSK_CASTING = "31fe1b2b-f401-412d-8cba-1d838a5073c5"
RAR_MSK_ASM = "c9d4477b-401b-403d-a7f4-28a7c077e15d"
RAR_FMC_CLINIC = "980fffdb-2823-494f-9691-b08594411106"
RAR_FMC_PROCEDURES = "ab1e16f2-e02b-43e0-ba83-85c1cb32cef2"

# uuid5(NAMESPACE_DNS, "all") — hash for applicable_weeks=NULL (matches existing rows)
NULL_WEEKS_HASH = "5eefc5da-40d2-5afc-af3a-e7b6c2730b0d"

_INSERT_RAR = sa.text("""
    INSERT INTO rotation_activity_requirements (
        id, rotation_template_id, activity_id,
        min_halfdays, max_halfdays, target_halfdays,
        applicable_weeks, applicable_weeks_hash,
        prefer_full_days, priority, created_at, updated_at
    ) VALUES (
        gen_random_uuid(), :rt_id, :act_id,
        :min_hd, :max_hd, :target_hd,
        NULL, :null_hash,
        true, :priority, now(), now()
    )
    ON CONFLICT (rotation_template_id, activity_id, applicable_weeks_hash)
    DO NOTHING
""")

_UPDATE_MIN = sa.text("""
    UPDATE rotation_activity_requirements
    SET min_halfdays = :new_min, updated_at = now()
    WHERE id = :rar_id
""")

_DELETE_RAR = sa.text("""
    DELETE FROM rotation_activity_requirements
    WHERE rotation_template_id = :rt_id AND activity_id = :act_id
""")


def upgrade() -> None:
    conn = op.get_bind()

    # ---------------------------------------------------------------
    # Category 1: Create PEM activity for off-site Peds EM preload
    # ---------------------------------------------------------------
    conn.execute(
        sa.text("""
        INSERT INTO activities (
            id, name, code, display_abbreviation, activity_category,
            requires_supervision, is_protected, counts_toward_clinical_hours,
            display_order, is_archived, provides_supervision,
            counts_toward_physical_capacity, created_at, updated_at
        ) VALUES (
            gen_random_uuid(), 'Pediatric Emergency Medicine', 'PEM', 'PEM',
            'clinical', true, false, true, 0, false, false, false, now(), now()
        )
        ON CONFLICT DO NOTHING
    """)
    )

    # ---------------------------------------------------------------
    # Category 2: NF combined rotation activity requirements
    # ---------------------------------------------------------------
    nf_combo_reqs = [
        # NF + FMIT Intern
        (RT_NF_FMIT, ACTIVITY_NF, 20, 24, 28, 90),
        (RT_NF_FMIT, ACTIVITY_FMIT, 12, 16, 20, 80),
        # NF + Cardiology
        (RT_NF_CARDS, ACTIVITY_NF, 20, 24, 28, 90),
        (RT_NF_CARDS, ACTIVITY_CARDS, 10, 14, 18, 80),
        # NF + Dermatology PGY-2
        (RT_NF_DERM, ACTIVITY_NF, 20, 24, 28, 90),
        (RT_NF_DERM, ACTIVITY_DERM, 10, 14, 18, 80),
    ]

    for rt_id, act_id, min_hd, target_hd, max_hd, priority in nf_combo_reqs:
        conn.execute(
            _INSERT_RAR,
            {
                "rt_id": rt_id,
                "act_id": act_id,
                "min_hd": min_hd,
                "max_hd": max_hd,
                "target_hd": target_hd,
                "priority": priority,
                "null_hash": NULL_WEEKS_HASH,
            },
        )

    # ---------------------------------------------------------------
    # Category 3: Set non-zero min_halfdays on clinic/selective
    # ---------------------------------------------------------------
    min_updates = [
        # MSK Selective
        (RAR_MSK_SM_CLINIC, 4),  # Sports Medicine Clinic: 0 → 4
        (RAR_MSK_RADIOLOGY, 2),  # Radiology: 0 → 2
        (RAR_MSK_CASTING, 2),  # Casting Clinic: 0 → 2
        (RAR_MSK_ASM, 1),  # Academic Sports Medicine: 0 → 1
        # FM Clinic
        (RAR_FMC_CLINIC, 4),  # FM Clinic: 0 → 4
        (RAR_FMC_PROCEDURES, 1),  # Procedures: 0 → 1
    ]

    for rar_id, new_min in min_updates:
        conn.execute(_UPDATE_MIN, {"rar_id": rar_id, "new_min": new_min})


def downgrade() -> None:
    conn = op.get_bind()

    # Category 3: Restore min_halfdays to 0
    restore_mins = [
        RAR_MSK_SM_CLINIC,
        RAR_MSK_RADIOLOGY,
        RAR_MSK_CASTING,
        RAR_MSK_ASM,
        RAR_FMC_CLINIC,
        RAR_FMC_PROCEDURES,
    ]
    for rar_id in restore_mins:
        conn.execute(_UPDATE_MIN, {"rar_id": rar_id, "new_min": 0})

    # Category 2: Remove NF combo requirements (keep Lecture)
    for rt_id in [RT_NF_FMIT, RT_NF_CARDS, RT_NF_DERM]:
        for act_id in [ACTIVITY_NF, ACTIVITY_FMIT, ACTIVITY_CARDS, ACTIVITY_DERM]:
            conn.execute(_DELETE_RAR, {"rt_id": rt_id, "act_id": act_id})

    # Category 1: Remove PEM activity
    conn.execute(sa.text("DELETE FROM activities WHERE code = 'PEM'"))
