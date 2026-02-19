"""Add AI usage budget tables for budget-aware cron manager.

Creates tables for tracking Opus API usage costs and budget configuration.
The budget-aware cron manager uses these tables for persistent storage of
usage history and budget limits, while Redis handles real-time tracking.

Revision ID: 20260219_ai_budget_tables
Revises: 20260218_drafts_ver_tbl
Create Date: 2026-02-19
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260219_ai_budget_tables"
down_revision = "20260218_drafts_ver_tbl"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add AI usage log and budget config tables."""

    # ── ai_usage_log ─────────────────────────────────────────────────
    op.create_table(
        "ai_usage_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("task_name", sa.String(255), nullable=False),
        sa.Column("model_id", sa.String(100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("job_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="success"),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_usage_log")),
    )

    op.create_index(
        op.f("ix_ai_usage_log_created_at"),
        "ai_usage_log",
        ["created_at"],
    )
    op.create_index(
        op.f("ix_ai_usage_log_task_name"),
        "ai_usage_log",
        ["task_name"],
    )
    op.create_index(
        op.f("ix_ai_usage_log_model_id"),
        "ai_usage_log",
        ["model_id"],
    )
    op.create_index(
        op.f("ix_ai_usage_log_status"),
        "ai_usage_log",
        ["status"],
    )

    # ── ai_budget_config ─────────────────────────────────────────────
    op.create_table(
        "ai_budget_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("budget_period", sa.String(50), nullable=False),
        sa.Column("budget_limit_usd", sa.Float(), nullable=False),
        sa.Column(
            "warning_threshold_pct",
            sa.Float(),
            nullable=False,
            server_default="0.80",
        ),
        sa.Column(
            "critical_threshold_pct",
            sa.Float(),
            nullable=False,
            server_default="0.95",
        ),
        sa.Column("hard_stop", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("priority_tasks", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_budget_config")),
    )

    op.create_index(
        op.f("ix_ai_budget_config_budget_period"),
        "ai_budget_config",
        ["budget_period"],
    )


def downgrade() -> None:
    """Remove AI usage budget tables."""
    op.drop_table("ai_budget_config")
    op.drop_table("ai_usage_log")
