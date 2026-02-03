"""Add users_version table for SQLAlchemy-Continuum.

Revision ID: 20260202_add_users_version
Revises: 20260130_add_institutional_events
Create Date: 2026-02-02

Fixes: User model has __versioned__ = {} but table was missing.
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260202_add_users_version"
down_revision: str | None = "20260130_add_faculty_schedule_preferences"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users_version",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(100)),
        sa.Column("email", sa.String(255)),
        sa.Column("hashed_password", sa.String(255)),
        sa.Column("role", sa.String(50)),
        sa.Column("is_active", sa.Boolean()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
        sa.Column("last_login", sa.DateTime()),
        # Continuum _mod columns (track which fields changed)
        sa.Column("username_mod", sa.Boolean()),
        sa.Column("email_mod", sa.Boolean()),
        sa.Column("hashed_password_mod", sa.Boolean()),
        sa.Column("role_mod", sa.Boolean()),
        sa.Column("is_active_mod", sa.Boolean()),
        sa.Column("created_at_mod", sa.Boolean()),
        sa.Column("updated_at_mod", sa.Boolean()),
        sa.Column("last_login_mod", sa.Boolean()),
        # Version tracking
        sa.Column(
            "transaction_id",
            sa.BigInteger(),
            sa.ForeignKey("transaction.id"),
            nullable=False,
        ),
        sa.Column("operation_type", sa.SmallInteger(), nullable=False),
        sa.Column(
            "end_transaction_id", sa.BigInteger(), sa.ForeignKey("transaction.id")
        ),
        sa.PrimaryKeyConstraint("id", "transaction_id"),
    )
    op.create_index("idx_users_version_txn", "users_version", ["transaction_id"])
    op.create_index(
        "idx_users_version_end_txn", "users_version", ["end_transaction_id"]
    )
    op.create_index("idx_users_version_op", "users_version", ["operation_type"])


def downgrade() -> None:
    op.drop_table("users_version")
