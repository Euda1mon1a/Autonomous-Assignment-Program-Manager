"""Add schema versioning columns to application_settings.

Revision ID: 20251225_schema_ver
Revises: 20251224_merge
Create Date: 2025-12-25

Adds columns to track the current Alembic version in the application settings.
This enables detection of schema mismatches when restoring backups.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20251225_schema_ver"
down_revision: str | None = "20251224_merge"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add schema versioning columns."""
    op.add_column(
        "application_settings",
        sa.Column("alembic_version", sa.String(255), nullable=True),
    )
    op.add_column(
        "application_settings",
        sa.Column("schema_timestamp", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Remove schema versioning columns."""
    op.drop_column("application_settings", "schema_timestamp")
    op.drop_column("application_settings", "alembic_version")
