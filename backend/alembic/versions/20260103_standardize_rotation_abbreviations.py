"""Standardize rotation abbreviations to match domain standards

Revision ID: 20260103_standardize_abbrevs
Revises: 20260101_import_staging
Create Date: 2026-01-03

This migration standardizes the abbreviation and display_abbreviation columns
in rotation_templates to match the domain standards defined in
docs/reference/SCHEDULE_ABBREVIATIONS.md.

Changes:
- abbreviation column: CLI-AM -> C-AM, CLI-PM -> C-PM, PRO-AM -> PR-AM, etc.
- display_abbreviation column: Updated to short GUI codes (C, FMIT, NF, PR, etc.)

Reference: docs/reference/SCHEDULE_ABBREVIATIONS.md
"""

from typing import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260103_standardize_abbrevs"
down_revision: str | None = "20260101_import_staging"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ==========================================================================
    # 1. Standardize abbreviation column values
    # ==========================================================================
    # Map old CLI-* pattern to C-* (Clinic)
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'CLI-AM' THEN 'C-AM'
            WHEN abbreviation = 'CLI-PM' THEN 'C-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('CLI-AM', 'CLI-PM')
    """)

    # Map old PRO-* pattern to PR-* (Procedures)
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'PRO-AM' THEN 'PR-AM'
            WHEN abbreviation = 'PRO-PM' THEN 'PR-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('PRO-AM', 'PRO-PM')
    """)

    # Map old SPM-* pattern to SM-* (Sports Medicine)
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'SPM-AM' THEN 'SM-AM'
            WHEN abbreviation = 'SPM-PM' THEN 'SM-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('SPM-AM', 'SPM-PM')
    """)

    # Map old BOT-* pattern to BTX-* (Botox)
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'BOT-AM' THEN 'BTX-AM'
            WHEN abbreviation = 'BOT-PM' THEN 'BTX-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('BOT-AM', 'BOT-PM')
    """)

    # Map old COL-* pattern to COLP-* (Colposcopy)
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'COL-AM' THEN 'COLP-AM'
            WHEN abbreviation = 'COL-PM' THEN 'COLP-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('COL-AM', 'COL-PM')
    """)

    # Map old DEO-* pattern to DFM-* (Department of Family Medicine)
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'DEO-AM' THEN 'DFM-AM'
            WHEN abbreviation = 'DEO-PM' THEN 'DFM-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('DEO-AM', 'DEO-PM')
    """)

    # Map old DIO-* pattern to DO-* (Direct Observation)
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'DIO-PM' THEN 'DO-PM'
            WHEN abbreviation = 'DIO-AM' THEN 'DO-AM'
            ELSE abbreviation
        END
        WHERE abbreviation LIKE 'DIO-%'
    """)

    # Map old GRM-* pattern to GME-* (Graduate Medical Education)
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'GRM-AM' THEN 'GME-AM'
            WHEN abbreviation = 'GRM-PM' THEN 'GME-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('GRM-AM', 'GRM-PM')
    """)

    # Map old HOC-* pattern to HC-* (Houseless Clinic)
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'HOC-AM' THEN 'HC-AM'
            WHEN abbreviation = 'HOC-PM' THEN 'HC-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('HOC-AM', 'HOC-PM')
    """)

    # Map old LEA-* pattern to LV-* (Leave)
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'LEA-AM' THEN 'LV-AM'
            WHEN abbreviation = 'LEA-PM' THEN 'LV-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('LEA-AM', 'LEA-PM')
    """)

    # Map old WEE-* pattern to W-* (Weekend)
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'WEE-AM' THEN 'W-AM'
            WHEN abbreviation = 'WEE-PM' THEN 'W-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('WEE-AM', 'WEE-PM')
    """)

    # Map old RES-* pattern to AT-* (Attending Time / Resident Supervision)
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'RES-AM' THEN 'AT-AM'
            WHEN abbreviation = 'RES-PM' THEN 'AT-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('RES-AM', 'RES-PM')
    """)

    # Map old PCA-* pattern to PCAT-* (PCAT)
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'PCA-AM' THEN 'PCAT-AM'
            WHEN abbreviation = 'PCA-PM' THEN 'PCAT-PM'
            ELSE abbreviation
        END
        WHERE abbreviation LIKE 'PCA-%'
    """)

    # ==========================================================================
    # 2. Update display_abbreviation based on standardized abbreviations
    # ==========================================================================
    op.execute("""
        UPDATE rotation_templates
        SET display_abbreviation = CASE
            -- Clinic (C-AM, C-PM -> C)
            WHEN abbreviation IN ('C', 'C-AM', 'C-PM') THEN 'C'

            -- Continuity Clinic
            WHEN abbreviation IN ('CC', 'CC-AM', 'CC-PM') THEN 'CC'

            -- Clinic Nursing Home
            WHEN abbreviation IN ('CLC', 'CLC-AM', 'CLC-PM') THEN 'CLC'

            -- PGY-3 FMIT Clinic
            WHEN abbreviation IN ('C-I', 'C-I-AM', 'C-I-PM') THEN 'C-I'

            -- 30-minute clinic
            WHEN abbreviation IN ('C30', 'C30-AM', 'C30-PM') THEN 'C30'

            -- Virtual Clinic
            WHEN abbreviation IN ('CV', 'CV-AM', 'CV-PM') THEN 'CV'

            -- FMIT (Family Medicine Inpatient Team)
            WHEN abbreviation IN ('FMIT', 'FMIT-AM', 'FMIT-PM', 'FMI', 'FMIT-R', 'FMIT-PA') THEN 'FMIT'

            -- Night Float
            WHEN abbreviation IN ('NF', 'NF-AM', 'NF-PM') THEN 'NF'

            -- Night Float variants
            WHEN abbreviation IN ('NF+', 'NF+C', 'NF+-AM', 'NF+-PM') THEN 'NF+'
            WHEN abbreviation IN ('NF-I', 'NFI', 'NF-I-AM', 'NF-I-PM') THEN 'NF-I'
            WHEN abbreviation IN ('NF-DERM', 'NF-DERM-AM', 'NF-DERM-PM') THEN 'NF-DERM'
            WHEN abbreviation IN ('NF-MED', 'NF-MED-AM', 'NF-MED-PM') THEN 'NF-MED'
            WHEN abbreviation IN ('NF-NICU', 'NF-NICU-AM', 'NF-NICU-PM') THEN 'NF-NICU'

            -- Procedures
            WHEN abbreviation IN ('PR', 'PR-AM', 'PR-PM', 'PROC') THEN 'PR'

            -- Lecture
            WHEN abbreviation IN ('LEC', 'LEC-AM', 'LEC-PM') THEN 'LEC'

            -- OFF
            WHEN abbreviation IN ('OFF', 'OFF-AM', 'OFF-PM') THEN 'OFF'

            -- Weekend
            WHEN abbreviation IN ('W', 'W-AM', 'W-PM', 'WKND') THEN 'W'

            -- Leave
            WHEN abbreviation IN ('LV', 'LV-AM', 'LV-PM') THEN 'LV'

            -- Post-Call
            WHEN abbreviation = 'PC' THEN 'PC'

            -- Holiday
            WHEN abbreviation IN ('HOL', 'HOL-AM', 'HOL-PM', 'FED') THEN 'HOL'

            -- Sports Medicine
            WHEN abbreviation IN ('SM', 'SM-AM', 'SM-PM') THEN 'SM'
            WHEN abbreviation = 'aSM' THEN 'aSM'

            -- Botox
            WHEN abbreviation IN ('BTX', 'BTX-AM', 'BTX-PM') THEN 'BTX'

            -- Colposcopy
            WHEN abbreviation IN ('COLP', 'COLP-AM', 'COLP-PM') THEN 'COLP'

            -- Department of Family Medicine
            WHEN abbreviation IN ('DFM', 'DFM-AM', 'DFM-PM') THEN 'DFM'

            -- Direct Observation
            WHEN abbreviation IN ('DO', 'DO-AM', 'DO-PM') THEN 'DO'

            -- Graduate Medical Education
            WHEN abbreviation IN ('GME', 'GME-AM', 'GME-PM') THEN 'GME'

            -- Houseless Clinic
            WHEN abbreviation IN ('HC', 'HC-AM', 'HC-PM') THEN 'HC'

            -- Vasectomy
            WHEN abbreviation IN ('VAS', 'VAS-AM', 'VAS-PM') THEN 'VAS'

            -- Vasectomy Counseling
            WHEN abbreviation IN ('VasC', 'VasC-AM', 'VasC-PM') THEN 'VasC'

            -- Walk-In Contraceptive Services
            WHEN abbreviation IN ('WICS', 'WICS-AM', 'WICS-PM') THEN 'WICS'

            -- Home Visit
            WHEN abbreviation IN ('HV', 'HV-AM', 'HV-PM') THEN 'HV'

            -- Video Clinics
            WHEN abbreviation IN ('V1', 'V1-AM', 'V1-PM') THEN 'V1'
            WHEN abbreviation IN ('V2', 'V2-AM', 'V2-PM') THEN 'V2'
            WHEN abbreviation IN ('V3', 'V3-AM', 'V3-PM') THEN 'V3'

            -- Simulation
            WHEN abbreviation IN ('SIM', 'SIM-AM', 'SIM-PM') THEN 'SIM'

            -- Administrative
            WHEN abbreviation IN ('ADM', 'ADM-AM', 'ADM-PM') THEN 'ADM'

            -- Process Improvement
            WHEN abbreviation IN ('PI', 'PI-AM', 'PI-PM') THEN 'PI'

            -- Research
            WHEN abbreviation IN ('RSH', 'RSH-AM', 'RSH-PM') THEN 'RSH'

            -- Flex Time
            WHEN abbreviation IN ('FLX', 'FLX-AM', 'FLX-PM') THEN 'FLX'

            -- NICU
            WHEN abbreviation IN ('NICU', 'NICU-AM', 'NICU-PM') THEN 'NICU'
            WHEN abbreviation IN ('NICU+NF', 'NIC') THEN 'NICU+NF'

            -- Emergency Room
            WHEN abbreviation IN ('ER', 'ER-AM', 'ER-PM') THEN 'ER'

            -- Internal Medicine Ward
            WHEN abbreviation IN ('IMW', 'IMW-AM', 'IMW-PM', 'IM-INT') THEN 'IMW'

            -- Pediatrics
            WHEN abbreviation IN ('PEDSW', 'PEDS-W', 'PedW') THEN 'PEDSW'
            WHEN abbreviation IN ('PedC', 'PedC-AM', 'PedC-PM') THEN 'PedC'
            WHEN abbreviation IN ('PedSP', 'PedSP-AM', 'PedSP-PM') THEN 'PedSP'
            WHEN abbreviation = 'PNF' THEN 'PNF'

            -- Attending Time
            WHEN abbreviation IN ('AT', 'AT-AM', 'AT-PM') THEN 'AT'

            -- Advising
            WHEN abbreviation IN ('ADV', 'ADV-AM', 'ADV-PM') THEN 'ADV'

            -- PCAT
            WHEN abbreviation IN ('PCAT', 'PCAT-AM', 'PCAT-PM') THEN 'PCAT'

            -- ICU
            WHEN abbreviation IN ('ICU', 'ICU-AM', 'ICU-PM') THEN 'ICU'

            -- Labor and Delivery
            WHEN abbreviation IN ('LND', 'LND-AM', 'LND-PM', 'LAD') THEN 'LND'
            WHEN abbreviation IN ('LDNF', 'LDNF-AM', 'LDNF-PM') THEN 'LDNF'

            -- Newborn Nursery
            WHEN abbreviation IN ('NBN', 'NBN-AM', 'NBN-PM') THEN 'NBN'

            -- Off-site locations
            WHEN abbreviation IN ('KAP', 'KAPI', 'KAP-AM', 'KAP-PM') THEN 'KAP'
            WHEN abbreviation IN ('HILO', 'HILO-AM', 'HILO-PM') THEN 'HILO'
            WHEN abbreviation IN ('OKI', 'OKI-AM', 'OKI-PM') THEN 'OKI'
            WHEN abbreviation IN ('STRAUB', 'STRAUB-AM', 'STRAUB-PM') THEN 'STRAUB'

            -- Military-Specific
            WHEN abbreviation IN ('MUC', 'MUC-AM', 'MUC-PM') THEN 'MUC'
            WHEN abbreviation IN ('C4', 'C4-AM', 'C4-PM') THEN 'C4'
            WHEN abbreviation IN ('TDY', 'TDY-AM', 'TDY-PM') THEN 'TDY'

            -- EPIC Training
            WHEN abbreviation IN ('EPIC', 'EPIC-AM', 'EPIC-PM') THEN 'EPIC'

            -- Family Medicine Orientation
            WHEN abbreviation IN ('FMO', 'FMO-AM', 'FMO-PM') THEN 'FMO'

            -- Ophthalmology
            WHEN abbreviation IN ('Ophtho', 'Optho', 'Ophtho-AM', 'Ophtho-PM') THEN 'Ophtho'

            -- Urology
            WHEN abbreviation IN ('URO', 'Uro', 'URO-AM', 'URO-PM') THEN 'URO'

            -- ENT
            WHEN abbreviation IN ('ENT', 'ENT-AM', 'ENT-PM') THEN 'ENT'

            -- Cardiology + Night Float combo
            WHEN abbreviation IN ('CARD+NF', 'C+N') THEN 'CARD+NF'

            -- Dermatology + Night Float combo
            WHEN abbreviation IN ('DERM+NF', 'D+N') THEN 'DERM+NF'

            -- Default: use abbreviation without -AM/-PM suffix
            ELSE REGEXP_REPLACE(abbreviation, '-(AM|PM)$', '')
        END
    """)


def downgrade() -> None:
    # ==========================================================================
    # Reverse the abbreviation standardization
    # ==========================================================================
    # Map C-* back to CLI-*
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'C-AM' THEN 'CLI-AM'
            WHEN abbreviation = 'C-PM' THEN 'CLI-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('C-AM', 'C-PM')
    """)

    # Map PR-* back to PRO-*
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'PR-AM' THEN 'PRO-AM'
            WHEN abbreviation = 'PR-PM' THEN 'PRO-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('PR-AM', 'PR-PM')
    """)

    # Map SM-* back to SPM-*
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'SM-AM' THEN 'SPM-AM'
            WHEN abbreviation = 'SM-PM' THEN 'SPM-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('SM-AM', 'SM-PM')
    """)

    # Map BTX-* back to BOT-*
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'BTX-AM' THEN 'BOT-AM'
            WHEN abbreviation = 'BTX-PM' THEN 'BOT-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('BTX-AM', 'BTX-PM')
    """)

    # Map COLP-* back to COL-*
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'COLP-AM' THEN 'COL-AM'
            WHEN abbreviation = 'COLP-PM' THEN 'COL-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('COLP-AM', 'COLP-PM')
    """)

    # Map DFM-* back to DEO-*
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'DFM-AM' THEN 'DEO-AM'
            WHEN abbreviation = 'DFM-PM' THEN 'DEO-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('DFM-AM', 'DFM-PM')
    """)

    # Map DO-* back to DIO-*
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'DO-AM' THEN 'DIO-AM'
            WHEN abbreviation = 'DO-PM' THEN 'DIO-PM'
            ELSE abbreviation
        END
        WHERE abbreviation LIKE 'DO-%'
    """)

    # Map GME-* back to GRM-*
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'GME-AM' THEN 'GRM-AM'
            WHEN abbreviation = 'GME-PM' THEN 'GRM-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('GME-AM', 'GME-PM')
    """)

    # Map HC-* back to HOC-*
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'HC-AM' THEN 'HOC-AM'
            WHEN abbreviation = 'HC-PM' THEN 'HOC-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('HC-AM', 'HC-PM')
    """)

    # Map LV-* back to LEA-*
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'LV-AM' THEN 'LEA-AM'
            WHEN abbreviation = 'LV-PM' THEN 'LEA-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('LV-AM', 'LV-PM')
    """)

    # Map W-* back to WEE-*
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'W-AM' THEN 'WEE-AM'
            WHEN abbreviation = 'W-PM' THEN 'WEE-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('W-AM', 'W-PM')
    """)

    # Map AT-* back to RES-*
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'AT-AM' THEN 'RES-AM'
            WHEN abbreviation = 'AT-PM' THEN 'RES-PM'
            ELSE abbreviation
        END
        WHERE abbreviation IN ('AT-AM', 'AT-PM')
    """)

    # Map PCAT-* back to PCA-*
    op.execute("""
        UPDATE rotation_templates
        SET abbreviation = CASE
            WHEN abbreviation = 'PCAT-AM' THEN 'PCA-AM'
            WHEN abbreviation = 'PCAT-PM' THEN 'PCA-PM'
            ELSE abbreviation
        END
        WHERE abbreviation LIKE 'PCAT-%'
    """)

    # Note: display_abbreviation will need to be re-run through the previous
    # migration (b15f4b13e203) logic if a full rollback is needed
