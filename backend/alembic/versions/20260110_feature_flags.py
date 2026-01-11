"""Add feature_flags tables

Revision ID: 20260110_feature_flags
Revises: 20260109_faculty_weekly
Create Date: 2026-01-11

Creates 3 tables for feature flag system:
- feature_flags: Main configuration table
- feature_flag_evaluations: Analytics/evaluation history
- feature_flag_audit: Change audit trail
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260110_feature_flags"
down_revision: str | None = "20260109_faculty_weekly"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # feature_flags - main configuration table
    op.create_table(
        "feature_flags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("flag_type", sa.String(20), nullable=False, server_default="boolean"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("rollout_percentage", sa.Float(), nullable=True),
        sa.Column("environments", sa.JSON(), nullable=True),
        sa.Column("target_user_ids", sa.JSON(), nullable=True),
        sa.Column("target_roles", sa.JSON(), nullable=True),
        sa.Column("variants", sa.JSON(), nullable=True),
        sa.Column("dependencies", sa.JSON(), nullable=True),
        sa.Column("custom_attributes", sa.JSON(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "flag_type IN ('boolean', 'percentage', 'variant')", name="check_flag_type"
        ),
        sa.CheckConstraint(
            "rollout_percentage IS NULL OR (rollout_percentage >= 0.0 AND rollout_percentage <= 1.0)",
            name="check_rollout_percentage_range",
        ),
    )
    op.create_index("idx_feature_flag_enabled", "feature_flags", ["enabled"])
    op.create_index("idx_feature_flag_type", "feature_flags", ["flag_type"])

    # feature_flag_evaluations - analytics/evaluation history
    op.create_table(
        "feature_flag_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "flag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("feature_flags.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("user_role", sa.String(50), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("variant", sa.String(50), nullable=True),
        sa.Column("environment", sa.String(50), nullable=True),
        sa.Column("rollout_percentage", sa.Float(), nullable=True),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column(
            "evaluated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
    )
    op.create_index(
        "idx_flag_eval_flag_user", "feature_flag_evaluations", ["flag_id", "user_id"]
    )
    op.create_index(
        "idx_flag_eval_timestamp", "feature_flag_evaluations", ["evaluated_at"]
    )

    # feature_flag_audit - change audit trail
    op.create_table(
        "feature_flag_audit",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "flag_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("feature_flags.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("changes", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
        sa.CheckConstraint(
            "action IN ('created', 'updated', 'deleted', 'enabled', 'disabled')",
            name="check_audit_action",
        ),
    )
    op.create_index("idx_flag_audit_timestamp", "feature_flag_audit", ["created_at"])
    op.create_index("idx_flag_audit_user", "feature_flag_audit", ["user_id"])


def downgrade() -> None:
    op.drop_table("feature_flag_audit")
    op.drop_table("feature_flag_evaluations")
    op.drop_table("feature_flags")
