"""Add rotation-specific activities for preload assignments.

Adds 29 missing activities needed by SyncPreloadService to assign
proper activity_id to inpatient rotations, electives, and schedule codes.

Revision ID: 20260120_add_rot_activities
Revises: 20260119_res_wkly_reqs
Create Date: 2026-01-20

"""

import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260120_add_rot_activities"
down_revision = "20260118_assignment_backups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add 29 missing activities for rotation types."""

    # All activities to add with their properties
    # Format: (code, display_abbrev, name, category, requires_supervision,
    #          is_protected, counts_clinical, provides_supervision, counts_physical)
    activities = [
        # Inpatient rotations
        ("FMIT", "FMIT", "FM Inpatient Team", "clinical", True, True, True, False, False),
        ("NF", "NF", "Night Float", "clinical", True, True, True, False, False),
        ("PedW", "PedW", "Pediatrics Ward", "clinical", True, True, True, False, False),
        ("PedNF", "PedNF", "Peds Night Float", "clinical", True, True, True, False, False),
        ("KAP", "KAP", "Kapiolani L&D", "clinical", True, True, True, False, False),
        ("IM", "IM", "Internal Medicine", "clinical", True, True, True, False, False),
        ("LDNF", "LDNF", "L&D Night Float", "clinical", True, True, True, False, False),
        ("TDY", "TDY", "Temporary Duty", "clinical", False, True, False, False, False),
        # Schedule codes
        ("W", "W", "Weekend", "time_off", False, True, False, False, False),
        ("HOL", "HOL", "Holiday", "time_off", False, True, False, False, False),
        ("DEP", "DEP", "Deployed", "administrative", False, True, False, False, False),
        ("C-N", "C-N", "Night Float Clinic", "clinical", True, False, True, False, True),
        ("CV", "CV", "Virtual Clinic", "clinical", True, False, True, False, True),
        ("FLX", "FLX", "Flex Time", "administrative", False, False, False, False, False),
        ("ADM", "ADM", "Admin", "administrative", False, False, False, False, False),
        # Education/Protected time
        ("SIM", "SIM", "Simulation", "educational", True, True, False, False, False),
        ("PI", "PI", "Process Improvement", "educational", False, True, False, False, False),
        ("MM", "MM", "M&M Conference", "educational", False, True, False, False, False),
        ("CLC", "CLC", "Continuity Learning", "educational", False, True, False, False, False),
        ("HLC", "HLC", "Houseless Clinic", "clinical", True, False, True, False, True),
        ("HAFP", "HAFP", "Hawaii AFP", "educational", False, True, False, False, False),
        ("USAFP", "USAFP", "USAFP Conference", "educational", False, True, False, False, False),
        ("BLS", "BLS", "BLS Training", "educational", False, True, False, False, False),
        # Electives
        ("NEURO", "NEURO", "Neurology", "clinical", True, False, True, False, False),
        ("US", "US", "Ultrasound/POCUS", "clinical", True, False, True, False, False),
        ("GYN", "GYN", "Gynecology", "clinical", True, False, True, False, False),
        ("SURG", "SURG", "Surgery", "clinical", True, False, True, False, False),
        ("PR", "PR", "Procedures", "clinical", True, False, True, False, True),
        ("VAS", "VAS", "Vascular", "clinical", True, False, True, False, True),
    ]

    now = datetime.utcnow().isoformat()

    for (
        code,
        abbrev,
        name,
        category,
        req_supervision,
        is_protected,
        counts_clinical,
        provides_supervision,
        counts_physical,
    ) in activities:
        activity_id = str(uuid.uuid4())
        op.execute(
            sa.text(
                """
            INSERT INTO activities (
                id, code, display_abbreviation, name, activity_category,
                requires_supervision, is_protected, counts_toward_clinical_hours,
                provides_supervision, counts_toward_physical_capacity,
                display_order, is_archived, created_at, updated_at
            ) VALUES (
                :id, :code, :abbrev, :name, :category,
                :req_supervision, :is_protected, :counts_clinical,
                :provides_supervision, :counts_physical,
                0, false, :now, :now
            )
            ON CONFLICT (code) DO NOTHING
            """
            ).bindparams(
                id=activity_id,
                code=code,
                abbrev=abbrev,
                name=name,
                category=category,
                req_supervision=req_supervision,
                is_protected=is_protected,
                counts_clinical=counts_clinical,
                provides_supervision=provides_supervision,
                counts_physical=counts_physical,
                now=now,
            )
        )


def downgrade() -> None:
    """Remove the added activities."""
    codes_to_remove = [
        "FMIT", "NF", "PedW", "PedNF", "KAP", "IM", "LDNF", "TDY",
        "W", "HOL", "DEP", "C-N", "CV", "FLX", "ADM",
        "SIM", "PI", "MM", "CLC", "HLC", "HAFP", "USAFP", "BLS",
        "NEURO", "US", "GYN", "SURG", "PR", "VAS",
    ]
    for code in codes_to_remove:
        op.execute(
            sa.text("DELETE FROM activities WHERE code = :code").bindparams(code=code)
        )
