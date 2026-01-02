"""Populate font_color and background_color from authoritative CSV

Revision ID: 20260102_populate_colors
Revises: b15f4b13e203
Create Date: 2026-01-02

Populates the font_color and background_color columns added in
20251231_rotation_colors using the authoritative rotation_abbreviations_revised.csv
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '20260102_populate_colors'
down_revision: Union[str, None] = 'b15f4b13e203'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Populate font_color and background_color from authoritative CSV mappings."""
    # Color mappings from rotation_abbreviations_revised.csv
    # Format: display_abbreviation -> (font_color, background_color)
    op.execute("""
        UPDATE rotation_templates SET
            font_color = CASE display_abbreviation
                -- Outpatient (green backgrounds)
                WHEN 'C' THEN 'black'
                WHEN 'DFM' THEN 'black'
                WHEN 'HC' THEN 'black'
                WHEN 'PCAT' THEN 'black'
                WHEN 'DO' THEN 'black'

                -- Procedures/Specialty (yellow backgrounds)
                WHEN 'ADV' THEN 'black'
                WHEN 'BTX' THEN 'black'
                WHEN 'COLP' THEN 'black'
                WHEN 'PROC' THEN 'black'
                WHEN 'VAS' THEN 'black'
                WHEN 'SM' THEN 'black'
                WHEN 'aSM' THEN 'black'

                -- Inpatient (sky/blue backgrounds)
                WHEN 'FMIT' THEN 'white'
                WHEN 'ICU' THEN 'white'
                WHEN 'IMW' THEN 'white'
                WHEN 'LND' THEN 'white'
                WHEN 'LDNF' THEN 'white'
                WHEN 'NBN' THEN 'white'
                WHEN 'NICU' THEN 'white'
                WHEN 'NICU+NF' THEN 'white'
                WHEN 'PEDSW' THEN 'white'
                WHEN 'PNF' THEN 'white'

                -- Night Float (black backgrounds)
                WHEN 'NF' THEN 'gray-200'
                WHEN 'NF+' THEN 'gray-200'
                WHEN 'NF-DERM' THEN 'gray-200'
                WHEN 'NF-MED' THEN 'gray-200'
                WHEN 'NF-NICU' THEN 'gray-200'
                WHEN 'NF-I' THEN 'gray-200'
                WHEN 'CARD+NF' THEN 'gray-200'
                WHEN 'DERM+NF' THEN 'gray-200'

                -- Education (purple/gray backgrounds)
                WHEN 'FMO' THEN 'white'
                WHEN 'GME' THEN 'gray-800'
                WHEN 'LEC' THEN 'gray-800'

                -- Absence/Off (blue/gray backgrounds)
                WHEN 'LV' THEN 'black'
                WHEN 'OFF' THEN 'gray-600'
                WHEN 'WKND' THEN 'black'
                WHEN 'PC' THEN 'black'

                -- Off-site (orange backgrounds)
                WHEN 'HILO' THEN 'black'
                WHEN 'KAP' THEN 'black'
                WHEN 'OKI' THEN 'black'

                -- Resident supervision
                WHEN 'AT' THEN 'black'

                ELSE font_color
            END,
            background_color = CASE display_abbreviation
                -- Outpatient (green)
                WHEN 'C' THEN 'green-500'
                WHEN 'DFM' THEN 'green-500'
                WHEN 'HC' THEN 'green-500'
                WHEN 'PCAT' THEN 'green-500'
                WHEN 'DO' THEN 'green-500'

                -- Procedures/Specialty (yellow)
                WHEN 'ADV' THEN 'yellow-300'
                WHEN 'BTX' THEN 'yellow-300'
                WHEN 'COLP' THEN 'yellow-300'
                WHEN 'PROC' THEN 'yellow-300'
                WHEN 'VAS' THEN 'yellow-300'
                WHEN 'SM' THEN 'yellow-300'
                WHEN 'aSM' THEN 'yellow-300'

                -- Inpatient (sky blue)
                WHEN 'FMIT' THEN 'sky-500'
                WHEN 'ICU' THEN 'sky-500'
                WHEN 'IMW' THEN 'sky-500'
                WHEN 'LND' THEN 'sky-500'
                WHEN 'LDNF' THEN 'sky-500'
                WHEN 'NBN' THEN 'sky-500'
                WHEN 'NICU' THEN 'sky-500'
                WHEN 'NICU+NF' THEN 'sky-500'
                WHEN 'PEDSW' THEN 'sky-500'
                WHEN 'PNF' THEN 'sky-500'

                -- Night Float (black)
                WHEN 'NF' THEN 'black'
                WHEN 'NF+' THEN 'black'
                WHEN 'NF-DERM' THEN 'black'
                WHEN 'NF-MED' THEN 'black'
                WHEN 'NF-NICU' THEN 'black'
                WHEN 'NF-I' THEN 'black'
                WHEN 'CARD+NF' THEN 'black'
                WHEN 'DERM+NF' THEN 'black'

                -- Education (purple/gray)
                WHEN 'FMO' THEN 'purple-700'
                WHEN 'GME' THEN 'gray-100'
                WHEN 'LEC' THEN 'gray-100'

                -- Absence/Off (blue/gray)
                WHEN 'LV' THEN 'red-300'
                WHEN 'OFF' THEN 'gray-200'
                WHEN 'WKND' THEN 'blue-300'
                WHEN 'PC' THEN 'amber-200'

                -- Off-site (orange)
                WHEN 'HILO' THEN 'orange-400'
                WHEN 'KAP' THEN 'orange-400'
                WHEN 'OKI' THEN 'orange-400'

                -- Resident supervision (teal)
                WHEN 'AT' THEN 'teal-300'

                ELSE background_color
            END
        WHERE display_abbreviation IS NOT NULL
    """)


def downgrade() -> None:
    """Clear color values (columns remain from previous migration)."""
    op.execute("""
        UPDATE rotation_templates
        SET font_color = NULL, background_color = NULL
    """)
