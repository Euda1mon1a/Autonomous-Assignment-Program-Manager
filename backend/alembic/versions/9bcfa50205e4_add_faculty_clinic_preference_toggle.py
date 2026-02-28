"""add_faculty_clinic_preference_toggle

Revision ID: 9bcfa50205e4
Revises: be2e66649140
Create Date: 2026-02-27 12:26:58.022510

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9bcfa50205e4"
down_revision: str | None = "be2e66649140"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "people",
        sa.Column(
            "prefer_full_days",
            sa.Boolean(),
            server_default="true",
            nullable=False,
            comment="If true, solver prefers AM+PM on the same day for clinics instead of scattering them",
        ),
    )


def downgrade() -> None:
    op.drop_column("people", "prefer_full_days")
