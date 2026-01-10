"""Add idempotency requests table

Revision ID: 014
Revises: 013
Create Date: 2025-12-17 00:00:00.000000

Creates table for idempotency key tracking to prevent duplicate
schedule generation requests and enable request replay.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "014"
down_revision: str | None = "013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create idempotency requests table."""

    op.create_table(
        "idempotency_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Idempotency key provided by client
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        # SHA-256 hash of request body
        sa.Column("body_hash", sa.String(64), nullable=False),
        # Request parameters for audit
        sa.Column("request_params", postgresql.JSONB(), nullable=True),
        # Processing status: pending, completed, failed
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        # Reference to result (schedule_run_id)
        sa.Column("result_ref", postgresql.UUID(as_uuid=True), nullable=True),
        # Error message if failed
        sa.Column("error_message", sa.Text(), nullable=True),
        # Cached response for replay
        sa.Column("response_body", postgresql.JSONB(), nullable=True),
        sa.Column("response_status_code", sa.String(3), nullable=True),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )

    # Composite unique index for idempotency lookup
    op.create_index(
        "idx_idempotency_key_hash",
        "idempotency_requests",
        ["idempotency_key", "body_hash"],
        unique=True,
    )

    # Index for cleanup of expired entries
    op.create_index("idx_idempotency_expires", "idempotency_requests", ["expires_at"])

    # Index for status lookups
    op.create_index("idx_idempotency_status", "idempotency_requests", ["status"])


def downgrade() -> None:
    """Drop idempotency requests table."""
    op.drop_index("idx_idempotency_status", "idempotency_requests")
    op.drop_index("idx_idempotency_expires", "idempotency_requests")
    op.drop_index("idx_idempotency_key_hash", "idempotency_requests")
    op.drop_table("idempotency_requests")
