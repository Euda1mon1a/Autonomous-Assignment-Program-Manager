"""add_display_abbreviation_to_rotation_templates

Revision ID: b15f4b13e203
Revises: 20251231_rotation_colors
Create Date: 2026-01-02 04:25:17.328758

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b15f4b13e203"
down_revision: str | None = "20251231_rotation_colors"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add display_abbreviation column
    op.add_column(
        "rotation_templates",
        sa.Column("display_abbreviation", sa.String(20), nullable=True),
    )

    # Populate display_abbreviation based on rotation_abbreviations_revised.csv mappings
    # This maps from internal abbreviation to user-facing display code
    op.execute("""
        UPDATE rotation_templates SET display_abbreviation = CASE
            -- Sports Medicine
            WHEN abbreviation = 'aSM' THEN 'aSM'
            WHEN abbreviation IN ('SM', 'SPM-AM', 'SPM-PM') THEN 'SM'

            -- Clinic
            WHEN abbreviation IN ('C', 'CLI-AM', 'CLI-PM') THEN 'C'

            -- Botox
            WHEN abbreviation IN ('BTX', 'BOT-AM', 'BOT-PM') THEN 'BTX'

            -- Colposcopy
            WHEN abbreviation IN ('COLP', 'COL-AM', 'COL-PM') THEN 'COLP'

            -- Department of Family Medicine
            WHEN abbreviation IN ('DFM', 'DEO-AM', 'DEO-PM') THEN 'DFM'

            -- Direct Observation
            WHEN abbreviation IN ('DO', 'DIO-PM') THEN 'DO'

            -- FMIT variants
            WHEN abbreviation IN ('FMIT', 'FMIT-AM', 'FMIT-PM', 'FMI', 'FMIT-R', 'FMIT-PA') THEN 'FMIT'

            -- Family Medicine Orientation
            WHEN abbreviation = 'FMO' THEN 'FMO'

            -- Graduate Medical Education
            WHEN abbreviation IN ('GME', 'GRM-AM', 'GRM-PM') THEN 'GME'

            -- Houseless Clinic
            WHEN abbreviation IN ('HC', 'HOC-AM', 'HOC-PM') THEN 'HC'

            -- Off-site locations
            WHEN abbreviation = 'HILO' THEN 'HILO'
            WHEN abbreviation IN ('KAP', 'KAPI') THEN 'KAP'
            WHEN abbreviation = 'OKI' THEN 'OKI'

            -- ICU
            WHEN abbreviation = 'ICU' THEN 'ICU'

            -- Internal Medicine
            WHEN abbreviation IN ('IMW', 'IM-INT') THEN 'IMW'

            -- Labor and Delivery
            WHEN abbreviation IN ('LND', 'LAD') THEN 'LND'
            WHEN abbreviation = 'LDNF' THEN 'LDNF'

            -- Leave
            WHEN abbreviation IN ('LV', 'LEA-AM', 'LEA-PM') THEN 'LV'

            -- Lecture
            WHEN abbreviation IN ('LEC', 'LEC-AM', 'LEC-PM') THEN 'LEC'

            -- Newborn Nursery
            WHEN abbreviation = 'NBN' THEN 'NBN'

            -- Night Float variants
            WHEN abbreviation IN ('NF', 'NF-AM', 'NF-PM') THEN 'NF'
            WHEN abbreviation IN ('NF+', 'NF+C') THEN 'NF+'
            WHEN abbreviation = 'NF-DERM' THEN 'NF-DERM'
            WHEN abbreviation = 'NF-MED' THEN 'NF-MED'
            WHEN abbreviation = 'NF-NICU' THEN 'NF-NICU'
            WHEN abbreviation IN ('NF-I', 'NFI') THEN 'NF-I'
            WHEN abbreviation IN ('CARD+NF', 'C+N') THEN 'CARD+NF'
            WHEN abbreviation IN ('DERM+NF', 'D+N') THEN 'DERM+NF'

            -- NICU
            WHEN abbreviation = 'NICU' THEN 'NICU'
            WHEN abbreviation IN ('NICU+NF', 'NIC') THEN 'NICU+NF'

            -- OFF
            WHEN abbreviation IN ('OFF', 'OFF-AM', 'OFF-PM') THEN 'OFF'

            -- Post-Call
            WHEN abbreviation = 'PC' THEN 'PC'

            -- PCAT
            WHEN abbreviation IN ('PCAT', 'PCA-AM') THEN 'PCAT'

            -- Pediatrics
            WHEN abbreviation IN ('PEDSW', 'PEDS-W') THEN 'PEDSW'
            WHEN abbreviation = 'PNF' THEN 'PNF'

            -- Procedure
            WHEN abbreviation IN ('PROC', 'PRO-AM', 'PRO-PM') THEN 'PROC'

            -- Resident Supervision (Attending time)
            WHEN abbreviation IN ('AT', 'RES-AM', 'RES-PM') THEN 'AT'

            -- Advising
            WHEN abbreviation IN ('ADV', 'ADV-PM') THEN 'ADV'

            -- Vasectomy
            WHEN abbreviation IN ('VAS', 'VAS-AM', 'VAS-PM') THEN 'VAS'

            -- Weekend
            WHEN abbreviation IN ('WKND', 'WEE-AM', 'WEE-PM') THEN 'WKND'

            -- Default: use the abbreviation as-is
            ELSE abbreviation
        END
    """)


def downgrade() -> None:
    op.drop_column("rotation_templates", "display_abbreviation")
