"""annual_rotation

Create annual_rotation_plans and annual_rotation_assignments tables
for the Annual Rotation Optimizer.

Revision ID: 20260309_annual_rot
Revises: 20260305_learner_tables
Create Date: 2026-03-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.db.types import GUID


# revision identifiers, used by Alembic.
revision: str = "20260309_annual_rot"
down_revision: str | None = "20260305_learner_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "annual_rotation_plans",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("academic_year", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("solver_time_limit", sa.Float(), server_default="30.0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", GUID(), nullable=True),
        sa.Column("objective_value", sa.Integer(), nullable=True),
        sa.Column("solver_status", sa.String(50), nullable=True),
        sa.Column("solve_duration_ms", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_annual_rotation_plans")),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_annual_rotation_plans_created_by_users"),
        ),
    )

    op.create_table(
        "annual_rotation_assignments",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("plan_id", GUID(), nullable=False),
        sa.Column("person_id", GUID(), nullable=False),
        sa.Column("block_number", sa.Integer(), nullable=False),
        sa.Column("rotation_name", sa.String(100), nullable=False),
        sa.Column("is_fixed", sa.Boolean(), server_default="false"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_annual_rotation_assignments")),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["annual_rotation_plans.id"],
            name=op.f("fk_annual_rotation_assignments_plan_id_annual_rotation_plans"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["people.id"],
            name=op.f("fk_annual_rotation_assignments_person_id_people"),
        ),
        sa.UniqueConstraint(
            "plan_id",
            "person_id",
            "block_number",
            name=op.f("uq_annual_rotation_assignments_plan_id"),
        ),
    )


def downgrade() -> None:
    op.drop_table("annual_rotation_assignments")
    op.drop_table("annual_rotation_plans")
