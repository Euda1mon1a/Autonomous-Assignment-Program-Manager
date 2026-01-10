"""Add notification tables

Revision ID: 010
Revises: 009b
Create Date: 2025-12-16 00:00:00.000000

Creates tables for notification system:
- notifications: Stores delivered notifications for in-app display
- scheduled_notifications: Queue for future notifications
- notification_preferences: User notification settings
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "010"
down_revision: str | None = "009b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create notification tables."""

    # Table 1: notifications - stores delivered notifications
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Recipient
        sa.Column(
            "recipient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Content
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("data", postgresql.JSONB(), server_default="{}"),
        # Priority and channels
        sa.Column("priority", sa.String(20), server_default="'normal'"),
        sa.Column("channels_delivered", sa.String(200)),
        # Read status
        sa.Column("is_read", sa.Boolean(), server_default="false"),
        sa.Column("read_at", sa.DateTime()),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        # Constraints
        sa.CheckConstraint(
            "priority IN ('high', 'normal', 'low')", name="check_notification_priority"
        ),
    )
    op.create_index("idx_notifications_recipient", "notifications", ["recipient_id"])
    op.create_index("idx_notifications_type", "notifications", ["notification_type"])
    op.create_index("idx_notifications_is_read", "notifications", ["is_read"])
    op.create_index("idx_notifications_created", "notifications", ["created_at"])

    # Table 2: scheduled_notifications - queue for future delivery
    op.create_table(
        "scheduled_notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Recipient
        sa.Column(
            "recipient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Notification details
        sa.Column("notification_type", sa.String(50), nullable=False),
        sa.Column("data", postgresql.JSONB(), server_default="{}"),
        # Scheduling
        sa.Column("send_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(20), server_default="'pending'"),
        # Delivery tracking
        sa.Column("sent_at", sa.DateTime()),
        sa.Column("error_message", sa.Text()),
        sa.Column("retry_count", sa.Integer(), server_default="0"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        # Constraints
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'sent', 'failed', 'cancelled')",
            name="check_scheduled_status",
        ),
    )
    op.create_index(
        "idx_scheduled_recipient", "scheduled_notifications", ["recipient_id"]
    )
    op.create_index("idx_scheduled_send_at", "scheduled_notifications", ["send_at"])
    op.create_index("idx_scheduled_status", "scheduled_notifications", ["status"])

    # Table 3: notification_preferences - user settings
    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # User (unique per user)
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("people.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # Channel preferences
        sa.Column("enabled_channels", sa.String(200), server_default="'in_app,email'"),
        # Type preferences (JSON map)
        sa.Column("notification_types", postgresql.JSONB(), server_default="{}"),
        # Quiet hours
        sa.Column("quiet_hours_start", sa.Integer()),
        sa.Column("quiet_hours_end", sa.Integer()),
        # Digest preferences
        sa.Column("email_digest_enabled", sa.Boolean(), server_default="false"),
        sa.Column("email_digest_frequency", sa.String(20), server_default="'daily'"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        # Constraints
        sa.CheckConstraint(
            "quiet_hours_start IS NULL OR (quiet_hours_start >= 0 AND quiet_hours_start <= 23)",
            name="check_quiet_start",
        ),
        sa.CheckConstraint(
            "quiet_hours_end IS NULL OR (quiet_hours_end >= 0 AND quiet_hours_end <= 23)",
            name="check_quiet_end",
        ),
        sa.CheckConstraint(
            "email_digest_frequency IN ('daily', 'weekly')",
            name="check_digest_frequency",
        ),
    )
    op.create_index("idx_prefs_user", "notification_preferences", ["user_id"])


def downgrade() -> None:
    """Drop notification tables."""
    op.drop_table("notification_preferences")
    op.drop_table("scheduled_notifications")
    op.drop_table("notifications")
