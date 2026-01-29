"""Link activities to procedures for credentialed scheduling.

Revision ID: 20260129_link_activities_to_procedures
Revises: 20260129_add_vasc_activity
Create Date: 2026-01-29
"""

import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260129_link_activities_to_procedures"
down_revision = "20260129_add_vasc_activity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "activities",
        sa.Column("procedure_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "idx_activities_procedure_id", "activities", ["procedure_id"], unique=False
    )
    op.create_foreign_key(
        "fk_activities_procedure_id",
        "activities",
        "procedures",
        ["procedure_id"],
        ["id"],
        ondelete="SET NULL",
    )

    conn = op.get_bind()
    now = datetime.utcnow()

    def ensure_procedure(
        name: str,
        category: str,
        specialty: str,
        requires_certification: bool = True,
        complexity_level: str = "standard",
        min_pgy_level: int = 1,
    ) -> str:
        existing = conn.execute(
            sa.text("SELECT id FROM procedures WHERE name = :name"),
            {"name": name},
        ).scalar()
        if existing:
            return str(existing)
        proc_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                """
                INSERT INTO procedures (
                    id,
                    name,
                    category,
                    specialty,
                    requires_certification,
                    supervision_ratio,
                    complexity_level,
                    min_pgy_level,
                    created_at,
                    updated_at
                ) VALUES (
                    :id,
                    :name,
                    :category,
                    :specialty,
                    :requires_certification,
                    :supervision_ratio,
                    :complexity_level,
                    :min_pgy_level,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "id": proc_id,
                "name": name,
                "category": category,
                "specialty": specialty,
                "requires_certification": requires_certification,
                "supervision_ratio": 1,
                "complexity_level": complexity_level,
                "min_pgy_level": min_pgy_level,
                "created_at": now,
                "updated_at": now,
            },
        )
        return proc_id

    vas_proc_id = ensure_procedure("Vasectomy", "office", "Family Medicine")
    sm_proc_id = ensure_procedure("Sports Medicine Clinic", "clinic", "Sports Medicine")
    ensure_procedure("Botox Clinic", "office", "Dermatology")
    ensure_procedure("Colposcopy Clinic", "clinic", "OB/GYN")

    conn.execute(
        sa.text(
            """
            UPDATE activities
            SET procedure_id = :proc_id
            WHERE UPPER(code) IN ('VAS', 'VASC')
               OR UPPER(display_abbreviation) IN ('VAS', 'VASC')
            """
        ),
        {"proc_id": vas_proc_id},
    )
    conn.execute(
        sa.text(
            """
            UPDATE activities
            SET procedure_id = :proc_id
            WHERE UPPER(code) IN ('SM', 'SM_CLINIC')
               OR UPPER(display_abbreviation) IN ('SM', 'SM_CLINIC')
            """
        ),
        {"proc_id": sm_proc_id},
    )

    def seed_credential(procedure_id: str, name_fragment: str, competency: str) -> None:
        rows = conn.execute(
            sa.text(
                """
                SELECT id
                FROM people
                WHERE UPPER(name) LIKE :pattern
                """
            ),
            {"pattern": f"%{name_fragment.upper()}%"},
        ).fetchall()
        for row in rows:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO procedure_credentials (
                        id,
                        person_id,
                        procedure_id,
                        status,
                        competency_level,
                        created_at,
                        updated_at
                    ) VALUES (
                        :id,
                        :person_id,
                        :procedure_id,
                        'active',
                        :competency_level,
                        :created_at,
                        :updated_at
                    )
                    ON CONFLICT (person_id, procedure_id) DO NOTHING
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "person_id": str(row[0]),
                    "procedure_id": procedure_id,
                    "competency_level": competency,
                    "created_at": now,
                    "updated_at": now,
                },
            )

    seed_credential(vas_proc_id, "KINKENNON", "expert")
    seed_credential(vas_proc_id, "LABOUNTY", "expert")
    seed_credential(vas_proc_id, "TAGAWA", "qualified")

    sm_rows = conn.execute(
        sa.text(
            """
            SELECT id
            FROM people
            WHERE faculty_role = 'sports_med'
               OR admin_type = 'SM'
            """
        )
    ).fetchall()
    for row in sm_rows:
        conn.execute(
            sa.text(
                """
                INSERT INTO procedure_credentials (
                    id,
                    person_id,
                    procedure_id,
                    status,
                    competency_level,
                    created_at,
                    updated_at
                ) VALUES (
                    :id,
                    :person_id,
                    :procedure_id,
                    'active',
                    :competency_level,
                    :created_at,
                    :updated_at
                )
                ON CONFLICT (person_id, procedure_id) DO NOTHING
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "person_id": str(row[0]),
                "procedure_id": sm_proc_id,
                "competency_level": "qualified",
                "created_at": now,
                "updated_at": now,
            },
        )


def downgrade() -> None:
    op.drop_constraint("fk_activities_procedure_id", "activities", type_="foreignkey")
    op.drop_index("idx_activities_procedure_id", table_name="activities")
    op.drop_column("activities", "procedure_id")
