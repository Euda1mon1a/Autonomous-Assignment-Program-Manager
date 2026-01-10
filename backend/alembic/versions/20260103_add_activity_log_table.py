"""Add activity_log table for admin audit trail

Revision ID: 20260103_add_activity_log
Revises: 20260103_standardize_abbrevs
Create Date: 2026-01-03

This migration adds the activity_log table for tracking all administrative
actions in the system. Supports:
- User authentication events (login, logout, password change)
- CRUD operations on entities (create, update, delete)
- Schedule modifications
- Configuration changes
- Swap approvals/rejections

Table Design:
- id: Primary key (UUID)
- user_id: Foreign key to users table (who performed the action)
- action_type: Type of action (LOGIN, CREATE, UPDATE, DELETE, APPROVE, etc.)
- target_entity: Entity type affected (Person, Assignment, SwapRequest, etc.)
- target_id: ID of the affected entity (UUID as string)
- details: JSONB for additional context (old values, new values, metadata)
- ip_address: Client IP address for security audit
- user_agent: Client user agent string for security audit
- created_at: Timestamp of the action (immutable)

Indexes:
- user_id: For querying actions by user
- action_type: For filtering by action type
- target_entity + target_id: For finding all actions on a specific entity
- created_at: For time-range queries and cleanup

Security:
- No cascade delete from users (preserve audit trail even if user deleted)
- Read-only after creation (no UPDATE triggers)
- Retention policy: 2 years minimum for compliance
"""

from typing import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260103_add_activity_log"
down_revision: str | None = "20260103_standardize_abbrevs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the activity_log table for admin audit trail."""
    op.create_table(
        "activity_log",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("target_entity", sa.String(100), nullable=True),
        sa.Column("target_id", sa.String(100), nullable=True),
        sa.Column(
            "details", JSONB, nullable=True, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("ip_address", sa.String(45), nullable=True),  # IPv6 max length
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Index for querying by user
    op.create_index("ix_activity_log_user_id", "activity_log", ["user_id"])

    # Index for filtering by action type
    op.create_index("ix_activity_log_action_type", "activity_log", ["action_type"])

    # Composite index for entity lookups
    op.create_index(
        "ix_activity_log_target", "activity_log", ["target_entity", "target_id"]
    )

    # Index for time-range queries (descending for recent-first)
    op.create_index(
        "ix_activity_log_created_at", "activity_log", [sa.text("created_at DESC")]
    )

    # Partial index for failed actions (useful for security monitoring)
    op.execute("""
        CREATE INDEX ix_activity_log_failed_actions
        ON activity_log (created_at DESC)
        WHERE details->>'success' = 'false' OR action_type LIKE '%_FAILED'
    """)


def downgrade() -> None:
    """Drop the activity_log table."""
    op.execute("DROP INDEX IF EXISTS ix_activity_log_failed_actions")
    op.drop_index("ix_activity_log_created_at", table_name="activity_log")
    op.drop_index("ix_activity_log_target", table_name="activity_log")
    op.drop_index("ix_activity_log_action_type", table_name="activity_log")
    op.drop_index("ix_activity_log_user_id", table_name="activity_log")
    op.drop_table("activity_log")
