"""Add email notification tables

Revision ID: 016
Revises: 015
Create Date: 2025-12-18 00:00:00.000000

Creates tables for email notification feature:
- email_logs: Tracks all emails sent from the system
- email_templates: Stores reusable email templates with variable substitution

This supports v1.1.0 priority email notification infrastructure.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "016"
down_revision: str | None = "015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create email notification tables."""

    # Table 1: email_logs - tracks all emails sent
    op.create_table(
        "email_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Optional link to notification
        sa.Column(
            "notification_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("notifications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Email details
        sa.Column("recipient_email", sa.String(255), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        # Delivery tracking
        sa.Column(
            "status",
            sa.Enum("queued", "sent", "failed", "bounced", name="emailstatus"),
            nullable=False,
            server_default="queued",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )

    # Indexes for email_logs
    op.create_index("ix_email_logs_notification_id", "email_logs", ["notification_id"])
    op.create_index("ix_email_logs_recipient_email", "email_logs", ["recipient_email"])
    op.create_index("ix_email_logs_status", "email_logs", ["status"])
    op.create_index("ix_email_logs_created_at", "email_logs", ["created_at"])

    # Table 2: email_templates - reusable email templates
    op.create_table(
        "email_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        # Template identification
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column(
            "template_type",
            sa.Enum(
                "schedule_change",
                "swap_notification",
                "certification_expiry",
                "absence_reminder",
                "compliance_alert",
                name="emailtemplatetype",
            ),
            nullable=False,
        ),
        # Template content (supports Jinja2 variable substitution)
        sa.Column("subject_template", sa.String(500), nullable=False),
        sa.Column("body_html_template", sa.Text(), nullable=False),
        sa.Column("body_text_template", sa.Text(), nullable=False),
        # Template status
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        # Audit tracking
        # Note: FK to users added in migration 017 after users table is created
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Timestamps
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
    )

    # Indexes for email_templates
    op.create_index("ix_email_templates_name", "email_templates", ["name"])
    op.create_index(
        "ix_email_templates_template_type", "email_templates", ["template_type"]
    )
    op.create_index("ix_email_templates_is_active", "email_templates", ["is_active"])


def downgrade() -> None:
    """Drop email notification tables."""

    # Drop tables in reverse order
    op.drop_index("ix_email_templates_is_active", table_name="email_templates")
    op.drop_index("ix_email_templates_template_type", table_name="email_templates")
    op.drop_index("ix_email_templates_name", table_name="email_templates")
    op.drop_table("email_templates")

    op.drop_index("ix_email_logs_created_at", table_name="email_logs")
    op.drop_index("ix_email_logs_status", table_name="email_logs")
    op.drop_index("ix_email_logs_recipient_email", table_name="email_logs")
    op.drop_index("ix_email_logs_notification_id", table_name="email_logs")
    op.drop_table("email_logs")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS emailtemplatetype")
    op.execute("DROP TYPE IF EXISTS emailstatus")
