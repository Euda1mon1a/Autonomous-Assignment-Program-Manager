"""canonicalize_combined_rotations

Revision ID: 07e395bd6a1f
Revises: a32138fd921a
Create Date: 2026-03-10 22:34:10.886937

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "07e395bd6a1f"
down_revision: str | None = "a32138fd921a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


import uuid
from sqlalchemy import text


def upgrade() -> None:
    conn = op.get_bind()

    # Mapping of canonical abbreviation to aliases
    canonical_mapping = {
        "DERM/NF": {
            "name": "Dermatology/Night Float",
            "aliases": ["NF-DERM", "D+N", "DERMATOLOGY NF", "DERM NF", "NF DERM"],
        },
        "ENDO/NF": {
            "name": "Endocrinology/Night Float",
            "aliases": ["NF-ENDO", "ENDOCRINOLOGY NF", "ENDO NF", "NF ENDO"],
        },
        "CARDIO/NF": {
            "name": "Cardiology/Night Float",
            "aliases": ["NF+", "C+N", "CARDIOLOGY NF", "CARDIO NF", "NF CARDIO"],
        },
        "MED/NF": {
            "name": "Medical Selective/Night Float",
            "aliases": ["NF-MED", "MED SEL NF", "MED NF"],
        },
        "NICU/NF": {
            "name": "NICU/Night Float",
            "aliases": ["NF-NICU", "NICU NF", "NIC"],
        },
        "NEURO/NF": {
            "name": "Neurology/Night Float",
            "aliases": ["NEURO-NF", "NEURO NF", "NF NEURO"],
        },
        "PEDSW/NF": {
            "name": "Pediatrics Ward/Night Float",
            "aliases": ["PEDS-W", "PNF", "PEDS WARD NF", "PEDS NF", "PEDIATRICS NF"],
        },
        "L&D/NF": {
            "name": "L&D/Night Float",
            "aliases": ["LDNF", "L&D NF", "L AND D NF", "L AND D NIGHT FLOAT"],
        },
    }

    for canonical_abbrev, info in canonical_mapping.items():
        canonical_name = info["name"]
        aliases = info["aliases"]

        # Check if canonical exists by exact abbreviation
        res = conn.execute(
            text("SELECT id FROM rotation_templates WHERE abbreviation = :abbrev"),
            {"abbrev": canonical_abbrev},
        ).fetchone()
        if not res:
            new_id = str(uuid.uuid4())
            conn.execute(
                text("""
                INSERT INTO rotation_templates (id, name, rotation_type, template_category, abbreviation, display_abbreviation, leave_eligible, is_block_half_rotation, includes_weekend_work, is_archived, created_at)
                VALUES (:id, :name, 'inpatient', 'rotation', :abbrev, :abbrev, false, false, true, false, NOW())
            """),
                {"id": new_id, "name": canonical_name, "abbrev": canonical_abbrev},
            )
            canonical_id = new_id
        else:
            canonical_id = res[0]
            conn.execute(
                text(
                    "UPDATE rotation_templates SET is_block_half_rotation = false, is_archived = false WHERE id = :id"
                ),
                {"id": canonical_id},
            )

        # Find duplicates by exact abbreviation or name match (case-insensitive)
        for alias in aliases:
            dups = conn.execute(
                text("""
                SELECT id FROM rotation_templates
                WHERE (UPPER(abbreviation) = UPPER(:alias) OR UPPER(name) = UPPER(:alias))
                  AND id != :canonical_id
            """),
                {"alias": alias, "canonical_id": canonical_id},
            ).fetchall()

            for dup in dups:
                dup_id = dup[0]
                # Re-map primary assignments
                conn.execute(
                    text("""
                    UPDATE block_assignments
                    SET rotation_template_id = :canonical_id, secondary_rotation_template_id = NULL
                    WHERE rotation_template_id = :dup_id
                """),
                    {"canonical_id": canonical_id, "dup_id": dup_id},
                )
                # Re-map secondary assignments
                conn.execute(
                    text("""
                    UPDATE block_assignments
                    SET rotation_template_id = :canonical_id, secondary_rotation_template_id = NULL
                    WHERE secondary_rotation_template_id = :dup_id
                """),
                    {"canonical_id": canonical_id, "dup_id": dup_id},
                )
                # Archive
                conn.execute(
                    text(
                        "UPDATE rotation_templates SET is_archived = true WHERE id = :dup_id"
                    ),
                    {"dup_id": dup_id},
                )

    # Fallback: ensure generic NF is not a half-block
    conn.execute(
        text(
            "UPDATE rotation_templates SET is_block_half_rotation = false WHERE abbreviation IN ('NF', 'NIGHT FLOAT')"
        )
    )

    # Re-map split combinations that were actually concurrent
    split_mappings = [
        (["DERM", "DERMATOLOGY"], ["NF", "NIGHT FLOAT", "NF-PM"], "DERM/NF"),
        (["ENDO", "ENDOCRINOLOGY"], ["NF", "NIGHT FLOAT", "NF-PM"], "ENDO/NF"),
        (["CARDIO", "CARDIOLOGY"], ["NF", "NIGHT FLOAT", "NF-PM"], "CARDIO/NF"),
        (["MED SEL", "MEDICAL SELECTIVE"], ["NF", "NIGHT FLOAT", "NF-PM"], "MED/NF"),
        (["NICU"], ["NF", "NIGHT FLOAT", "NF-PM"], "NICU/NF"),
        (["NEURO", "NEUROLOGY"], ["NF", "NIGHT FLOAT", "NF-PM"], "NEURO/NF"),
        (
            ["PEDS WARD", "PEDIATRICS WARD", "PEDS-W", "PEDSW"],
            ["PEDS NF", "PEDIATRICS NIGHT FLOAT", "PNF"],
            "PEDSW/NF",
        ),
        (["L&D", "L AND D"], ["NF", "NIGHT FLOAT", "NF-PM"], "L&D/NF"),
    ]

    for primary_names, secondary_names, canonical_abbrev in split_mappings:
        # Get canonical ID
        res = conn.execute(
            text("SELECT id FROM rotation_templates WHERE abbreviation = :abbrev"),
            {"abbrev": canonical_abbrev},
        ).fetchone()
        if not res:
            continue
        canonical_id = res[0]

        # Get all rotation IDs matching primary
        prim_ids = []
        for p in primary_names:
            rows = conn.execute(
                text(
                    "SELECT id FROM rotation_templates WHERE UPPER(abbreviation) = UPPER(:p) OR UPPER(name) = UPPER(:p)"
                ),
                {"p": p},
            ).fetchall()
            prim_ids.extend([r[0] for r in rows])

        # Get all rotation IDs matching secondary
        sec_ids = []
        for s in secondary_names:
            rows = conn.execute(
                text(
                    "SELECT id FROM rotation_templates WHERE UPPER(abbreviation) = UPPER(:s) OR UPPER(name) = UPPER(:s)"
                ),
                {"s": s},
            ).fetchall()
            sec_ids.extend([r[0] for r in rows])

        if prim_ids and sec_ids:
            prim_tuple = tuple(prim_ids)
            sec_tuple = tuple(sec_ids)

            # Primary = Base, Secondary = NF
            if len(prim_tuple) == 1:
                p_condition = "= :prim_id"
                p_params = {"prim_id": prim_tuple[0]}
            else:
                p_condition = "IN :prim_ids"
                p_params = {"prim_ids": prim_tuple}

            if len(sec_tuple) == 1:
                s_condition = "= :sec_id"
                s_params = {"sec_id": sec_tuple[0]}
            else:
                s_condition = "IN :sec_ids"
                s_params = {"sec_ids": sec_tuple}

            params1 = {"canonical_id": canonical_id, **p_params, **s_params}

            conn.execute(
                text(
                    f"""
                UPDATE block_assignments
                SET rotation_template_id = :canonical_id, secondary_rotation_template_id = NULL
                WHERE rotation_template_id {p_condition} AND secondary_rotation_template_id {s_condition}
            """
                ),
                params1,
            )

            # Primary = NF, Secondary = Base
            conn.execute(
                text(
                    f"""
                UPDATE block_assignments
                SET rotation_template_id = :canonical_id, secondary_rotation_template_id = NULL
                WHERE rotation_template_id {s_condition} AND secondary_rotation_template_id {p_condition}
            """
                ),
                params1,
            )


def downgrade() -> None:
    pass
