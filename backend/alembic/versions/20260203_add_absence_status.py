"""Add status fields for absence approval workflow.

Revision ID: 20260203_add_absence_status
Revises: 20260202_add_users_version
Create Date: 2026-02-03
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260203_add_absence_status"
down_revision: str | None = "20260202_add_users_version"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "absences",
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="approved"
        ),
    )
    op.add_column("absences", sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    op.add_column(
        "absences",
        sa.Column("reviewed_by_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("absences", sa.Column("review_notes", sa.Text(), nullable=True))

    op.create_foreign_key(
        "fk_absences_reviewed_by_id_users",
        "absences",
        "users",
        ["reviewed_by_id"],
        ["id"],
        ondelete=None,
    )

    op.create_check_constraint(
        "check_absence_status",
        "absences",
        "status IN ('pending', 'approved', 'rejected', 'cancelled')",
    )
    op.create_index("idx_absences_status", "absences", ["status"])

    # Ensure existing rows are approved
    op.execute("UPDATE absences SET status = 'approved' WHERE status IS NULL")

    op.alter_column("absences", "status", server_default=None)


def downgrade() -> None:
    op.drop_index("idx_absences_status", table_name="absences")
    op.drop_constraint("check_absence_status", "absences", type_="check")
    op.drop_constraint(
        "fk_absences_reviewed_by_id_users", "absences", type_="foreignkey"
    )
    op.drop_column("absences", "review_notes")
    op.drop_column("absences", "reviewed_by_id")
    op.drop_column("absences", "reviewed_at")
    op.drop_column("absences", "status")
