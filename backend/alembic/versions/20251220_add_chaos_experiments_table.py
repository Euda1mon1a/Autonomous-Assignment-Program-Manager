"""Add chaos_experiments table

Revision ID: 20251220_add_chaos_experiments
Revises: 20251220_add_gateway_auth_tables
Create Date: 2025-12-20 18:35:00.000000

Adds table for chaos engineering experiments tracking:
- chaos_experiments: Chaos engineering experiment execution history
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20251220_add_chaos_experiments"
down_revision: str | None = "20251220_add_gateway_auth_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create chaos_experiments table."""

    # Create chaos_experiments table
    op.create_table(
        "chaos_experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("injector_type", sa.String(50), nullable=False),
        # Blast radius configuration
        sa.Column("blast_radius", sa.Float(), nullable=False, server_default="0.1"),
        sa.Column("blast_radius_scope", sa.String(50), nullable=False),
        sa.Column("target_component", sa.String(200), nullable=True),
        sa.Column("target_zone_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        # Execution tracking
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column(
            "scheduled_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column(
            "max_duration_minutes", sa.Integer(), nullable=False, server_default="15"
        ),
        # Safety configuration
        sa.Column("auto_rollback", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("slo_thresholds", postgresql.JSONB(), nullable=True),
        # Results
        sa.Column("total_injections", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "successful_injections", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "failed_injections", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("slo_breaches", postgresql.JSONB(), nullable=True),
        sa.Column("rollback_reason", sa.String(500), nullable=True),
        # Data
        sa.Column("injector_params", postgresql.JSONB(), nullable=True),
        sa.Column("observations", postgresql.JSONB(), nullable=True),
        sa.Column("metrics_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        # Authorization
        sa.Column("created_by", sa.String(100), nullable=True),
        sa.Column("approved_by", sa.String(100), nullable=True),
    )

    # Create indexes for chaos_experiments
    op.create_index(
        "ix_chaos_experiments_status",
        "chaos_experiments",
        ["status"],
    )

    op.create_index(
        "ix_chaos_experiments_injector_type",
        "chaos_experiments",
        ["injector_type"],
    )

    op.create_index(
        "ix_chaos_experiments_scheduled_at",
        "chaos_experiments",
        ["scheduled_at"],
    )

    op.create_index(
        "ix_chaos_experiments_started_at",
        "chaos_experiments",
        ["started_at"],
    )


def downgrade() -> None:
    """Drop chaos_experiments table."""
    op.drop_index("ix_chaos_experiments_started_at", table_name="chaos_experiments")
    op.drop_index("ix_chaos_experiments_scheduled_at", table_name="chaos_experiments")
    op.drop_index("ix_chaos_experiments_injector_type", table_name="chaos_experiments")
    op.drop_index("ix_chaos_experiments_status", table_name="chaos_experiments")
    op.drop_table("chaos_experiments")
