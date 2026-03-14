"""Add preload classification columns to rotation_templates.

Moves hardcoded Python sets (OFFSITE_ROTATIONS, LEC_EXEMPT_ROTATIONS, etc.)
and simple preload activity codes into the rotation_templates table so
coordinators can manage them from the admin UI.

Revision ID: 20260314_rt_preload_cols
Revises: 20260313_rename_legacy_cstr
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa

revision = "20260314_rt_preload_cols"
down_revision = "20260313_rename_legacy_cstr"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add classification columns
    op.add_column(
        "rotation_templates",
        sa.Column("is_offsite", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "rotation_templates",
        sa.Column(
            "is_lec_exempt", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "rotation_templates",
        sa.Column(
            "is_continuity_exempt", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "rotation_templates",
        sa.Column(
            "is_saturday_off", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "rotation_templates",
        sa.Column("preload_activity_code", sa.String(20), nullable=True),
    )

    # Seed from current Python constants

    # Offsite rotations
    op.execute(
        "UPDATE rotation_templates SET is_offsite = TRUE "
        "WHERE abbreviation IN ('TDY','HILO','OKI','JAPAN','PEDS-EM','MILITARY')"
    )

    # LEC exempt (offsite + NF variants)
    op.execute(
        "UPDATE rotation_templates SET is_lec_exempt = TRUE "
        "WHERE abbreviation IN ('TDY','HILO','OKI','JAPAN','PEDS-EM','MILITARY',"
        "'NF','PEDNF','LDNF') OR abbreviation LIKE 'NF-%'"
    )

    # Continuity exempt (lec_exempt + KAP)
    op.execute(
        "UPDATE rotation_templates SET is_continuity_exempt = TRUE "
        "WHERE is_lec_exempt = TRUE OR abbreviation LIKE 'KAP%'"
    )

    # Saturday off (inpatient + offsite + NF)
    op.execute(
        "UPDATE rotation_templates SET is_saturday_off = TRUE "
        "WHERE abbreviation IN ('IM','IMW','PEDW','PEDNF','ICU','CCU','NICU','NIC',"
        "'NBN','LAD','LND','LD','KAP','HILO','OKI','TDY','JAPAN','PEDS-EM',"
        "'MILITARY','NF') OR abbreviation LIKE 'NF-%'"
    )

    # Simple preload activity codes
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'MUC' "
        "WHERE abbreviation = 'MILITARY'"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'TDY' "
        "WHERE abbreviation IN ('TDY','JAPAN')"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'TDY' "
        "WHERE abbreviation LIKE 'HILO%' OR abbreviation LIKE 'OKI%'"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'PEM' "
        "WHERE abbreviation = 'PEDS-EM'"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'FMIT' "
        "WHERE abbreviation LIKE 'FMIT-PGY%'"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'NBN' "
        "WHERE abbreviation = 'NBN'"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'PEDW' "
        "WHERE abbreviation = 'PEDW'"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'KAP' "
        "WHERE abbreviation LIKE 'KAP%'"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'NF' "
        "WHERE abbreviation IN ('NF','NF-PM','NF-AM')"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'LDNF' "
        "WHERE abbreviation = 'LDNF'"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'PedNF' "
        "WHERE abbreviation = 'PEDNF'"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'NEURO' "
        "WHERE abbreviation = 'NEURO'"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'ICU' "
        "WHERE abbreviation = 'ICU'"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'IM' "
        "WHERE abbreviation IN ('IM','IMW')"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'DERM' "
        "WHERE abbreviation = 'DERM'"
    )
    op.execute(
        "UPDATE rotation_templates SET preload_activity_code = 'EM' "
        "WHERE abbreviation = 'EM'"
    )


def downgrade() -> None:
    op.drop_column("rotation_templates", "preload_activity_code")
    op.drop_column("rotation_templates", "is_saturday_off")
    op.drop_column("rotation_templates", "is_continuity_exempt")
    op.drop_column("rotation_templates", "is_lec_exempt")
    op.drop_column("rotation_templates", "is_offsite")
