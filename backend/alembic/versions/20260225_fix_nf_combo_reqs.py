"""Remove unused NF combined rotation_activity_requirements + fix Blk12 assignment

The previous migration (20260224_blk12_act_reqs) inserted Cat 2 requirements
with min=20 NF half-days designed for an AM/PM split pattern. The correct
pattern is half-block (14 days NF + 14 days specialty), and preloaded slots
bypass the solver entirely — making these requirements dead data. This
migration removes them.

Also corrects one Block 12 block_assignment that had the wrong rotation
template (NF-first instead of specialty-first mirror template).

Revision ID: 20260225_fix_nf_combo_reqs
Revises: 20260224_blk12_act_reqs
Create Date: 2026-02-25

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260225_fix_nf_combo_reqs"
down_revision: str = "20260224_blk12_act_reqs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# --- Rotation Template IDs (from previous migration) ---
RT_NF_FMIT = "6dd781d5-41aa-4dd3-a44b-a3c3eea439c5"
RT_NF_CARDS = "691ad20d-cc4a-4d2a-bed4-22b90ad1a903"
RT_NF_DERM = "38d35ac5-bb3c-4161-ace8-9f26ec4e88a6"

# --- Activity IDs (from previous migration) ---
ACTIVITY_NF = "f677382c-390e-4c50-83a0-0153ad55da53"
ACTIVITY_FMIT = "9fd0dca9-f260-478d-80b1-c9ea5d78b6d0"
ACTIVITY_CARDS = "9d993a60-256b-41cd-a657-3fb4d8a10456"
ACTIVITY_DERM = "eac32207-030f-4b44-aba7-1041cc4ede6e"

# --- Block 12 assignment fix ---
RESIDENT_ID = "aef2ee77-7ba3-471a-a688-e9e403ee582c"
RT_D_PLUS_N = "65d3d5f0-604b-4087-b24d-c68be9e11cf1"  # D+N (specialty-first mirror)

NULL_WEEKS_HASH = "5eefc5da-40d2-5afc-af3a-e7b6c2730b0d"

_DELETE_RAR = sa.text("""
    DELETE FROM rotation_activity_requirements
    WHERE rotation_template_id = :rt_id AND activity_id = :act_id
""")

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


def upgrade() -> None:
    conn = op.get_bind()

    # ---------------------------------------------------------------
    # Remove Cat 2 NF combined requirements (preload handles these)
    # ---------------------------------------------------------------
    for rt_id in [RT_NF_FMIT, RT_NF_CARDS, RT_NF_DERM]:
        for act_id in [ACTIVITY_NF, ACTIVITY_FMIT, ACTIVITY_CARDS, ACTIVITY_DERM]:
            conn.execute(_DELETE_RAR, {"rt_id": rt_id, "act_id": act_id})

    # ---------------------------------------------------------------
    # Fix Block 12 assignment: NF-DERM-PG → D+N (mirror template)
    # ---------------------------------------------------------------
    conn.execute(
        sa.text("""
            UPDATE block_assignments
            SET rotation_template_id = :new_rt, updated_at = now()
            WHERE resident_id = :resident_id
              AND block_number = 12
              AND academic_year = 2025
              AND rotation_template_id = :old_rt
        """),
        {
            "new_rt": RT_D_PLUS_N,
            "resident_id": RESIDENT_ID,
            "old_rt": RT_NF_DERM,
        },
    )


def downgrade() -> None:
    conn = op.get_bind()

    # Restore Block 12 assignment: D+N → NF-DERM-PG
    conn.execute(
        sa.text("""
            UPDATE block_assignments
            SET rotation_template_id = :old_rt, updated_at = now()
            WHERE resident_id = :resident_id
              AND block_number = 12
              AND academic_year = 2025
              AND rotation_template_id = :new_rt
        """),
        {
            "old_rt": RT_NF_DERM,
            "resident_id": RESIDENT_ID,
            "new_rt": RT_D_PLUS_N,
        },
    )

    # Re-insert Cat 2 NF combined requirements
    nf_combo_reqs = [
        (RT_NF_FMIT, ACTIVITY_NF, 20, 24, 28, 90),
        (RT_NF_FMIT, ACTIVITY_FMIT, 12, 16, 20, 80),
        (RT_NF_CARDS, ACTIVITY_NF, 20, 24, 28, 90),
        (RT_NF_CARDS, ACTIVITY_CARDS, 10, 14, 18, 80),
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
