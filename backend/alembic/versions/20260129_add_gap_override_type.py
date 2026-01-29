"""Allow gap override type for schedule overrides.

Revision ID: 20260129_add_gap_override_type
Revises: 2a58a0dc6f40
Create Date: 2026-01-29
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260129_add_gap_override_type"
down_revision = "2a58a0dc6f40"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_schedule_override_type", "schedule_overrides", type_="check")
    op.drop_constraint(
        "ck_schedule_override_replacement", "schedule_overrides", type_="check"
    )

    op.create_check_constraint(
        "ck_schedule_override_type",
        "schedule_overrides",
        "override_type IN ('coverage', 'cancellation', 'gap')",
    )
    op.create_check_constraint(
        "ck_schedule_override_replacement",
        "schedule_overrides",
        "(override_type = 'coverage' AND replacement_person_id IS NOT NULL) "
        "OR (override_type IN ('cancellation', 'gap') AND replacement_person_id IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_schedule_override_type", "schedule_overrides", type_="check")
    op.drop_constraint(
        "ck_schedule_override_replacement", "schedule_overrides", type_="check"
    )

    op.create_check_constraint(
        "ck_schedule_override_type",
        "schedule_overrides",
        "override_type IN ('coverage', 'cancellation')",
    )
    op.create_check_constraint(
        "ck_schedule_override_replacement",
        "schedule_overrides",
        "(override_type = 'coverage' AND replacement_person_id IS NOT NULL) "
        "OR (override_type = 'cancellation' AND replacement_person_id IS NULL)",
    )
