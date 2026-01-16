"""Add gamified wellness platform tables.

Revision ID: 20260116_wellness_tables
Revises: ae892630526b
Create Date: 2026-01-16

This migration creates 7 tables for the gamified wellness survey platform:
- surveys: Survey instrument definitions (MBI-2, PSS-4, PSQI-1, GSE-4, etc.)
- survey_responses: Individual survey responses with privacy-preserving linkage
- survey_availability: Tracks survey cooldowns and availability per person
- wellness_accounts: Gamification points, streaks, and achievements
- wellness_point_transactions: Ledger of point transactions
- wellness_leaderboard_snapshots: Periodic leaderboard snapshots
- hopfield_positions: User-positioned state on Hopfield energy landscape

Research Correlation:
    - Burnout Rt -> MBI-2 scores
    - Fire Danger Index -> PSS-4 + MBI-2
    - FRMS Fatigue -> PSQI-1
    - Hopfield Energy -> User-positioned basin depth
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260116_wellness_tables"
down_revision = "ae892630526b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # 1. Create surveys table
    # =========================================================================
    op.create_table(
        "surveys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("survey_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("questions_json", postgresql.JSON(), nullable=False),
        sa.Column("scoring_json", postgresql.JSON(), nullable=True),
        sa.Column("points_value", sa.Integer(), nullable=False, default=50),
        sa.Column("estimated_seconds", sa.Integer(), nullable=True, default=60),
        sa.Column("frequency", sa.String(20), nullable=False, default="weekly"),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("target_roles_json", postgresql.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_survey_name"),
        sa.CheckConstraint(
            "survey_type IN ('burnout', 'stress', 'sleep', 'efficacy', 'pulse', 'hopfield', 'custom')",
            name="check_survey_type",
        ),
        sa.CheckConstraint(
            "frequency IN ('daily', 'weekly', 'biweekly', 'block', 'annual')",
            name="check_survey_frequency",
        ),
        sa.CheckConstraint("points_value >= 0", name="check_points_non_negative"),
    )

    op.create_index("idx_survey_name", "surveys", ["name"])
    op.create_index("idx_survey_type", "surveys", ["survey_type"])
    op.create_index("idx_survey_is_active", "surveys", ["is_active"])

    # =========================================================================
    # 2. Create survey_responses table
    # =========================================================================
    op.create_table(
        "survey_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("block_number", sa.Integer(), nullable=True),
        sa.Column("academic_year", sa.Integer(), nullable=True),
        sa.Column("response_data", postgresql.JSON(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("score_interpretation", sa.String(100), nullable=True),
        sa.Column(
            "submitted_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("algorithm_snapshot_json", postgresql.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "block_number IS NULL OR (block_number >= 0 AND block_number <= 13)",
            name="check_block_number_range",
        ),
        sa.CheckConstraint(
            "academic_year IS NULL OR (academic_year >= 2000 AND academic_year <= 2100)",
            name="check_academic_year_range",
        ),
    )

    op.create_index("idx_survey_response_survey_id", "survey_responses", ["survey_id"])
    op.create_index("idx_survey_response_person_id", "survey_responses", ["person_id"])
    op.create_index(
        "idx_survey_response_submitted", "survey_responses", ["submitted_at"]
    )
    op.create_index(
        "ix_survey_responses_temporal",
        "survey_responses",
        ["survey_id", "block_number", "academic_year"],
    )

    # =========================================================================
    # 3. Create wellness_accounts table
    # =========================================================================
    op.create_table(
        "wellness_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("points_balance", sa.Integer(), nullable=False, default=0),
        sa.Column("points_lifetime", sa.Integer(), nullable=False, default=0),
        sa.Column("points_spent", sa.Integer(), nullable=False, default=0),
        sa.Column("current_streak_weeks", sa.Integer(), nullable=False, default=0),
        sa.Column("longest_streak_weeks", sa.Integer(), nullable=False, default=0),
        sa.Column("last_activity_date", sa.Date(), nullable=True),
        sa.Column("streak_start_date", sa.Date(), nullable=True),
        sa.Column("achievements_json", postgresql.JSON(), nullable=True),
        sa.Column("achievements_earned_at_json", postgresql.JSON(), nullable=True),
        sa.Column("leaderboard_opt_in", sa.Boolean(), nullable=False, default=False),
        sa.Column("display_name", sa.String(50), nullable=True),
        sa.Column("research_consent", sa.Boolean(), nullable=False, default=False),
        sa.Column("consent_date", sa.DateTime(), nullable=True),
        sa.Column("consent_version", sa.String(20), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("person_id", name="uq_wellness_account_person"),
        sa.CheckConstraint(
            "points_balance >= 0", name="check_wellness_points_non_negative"
        ),
        sa.CheckConstraint(
            "points_lifetime >= 0", name="check_wellness_lifetime_non_negative"
        ),
        sa.CheckConstraint(
            "current_streak_weeks >= 0", name="check_streak_non_negative"
        ),
    )

    op.create_index("idx_wellness_account_person", "wellness_accounts", ["person_id"])

    # =========================================================================
    # 4. Create wellness_point_transactions table
    # =========================================================================
    op.create_table(
        "wellness_point_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(50), nullable=False),
        sa.Column("source", sa.String(200), nullable=False),
        sa.Column("survey_response_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["account_id"], ["wellness_accounts.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["survey_response_id"], ["survey_responses.id"], ondelete="SET NULL"
        ),
        sa.CheckConstraint(
            "transaction_type IN ('survey', 'streak', 'achievement', 'block_bonus', 'admin', 'redemption')",
            name="check_transaction_type",
        ),
    )

    op.create_index(
        "idx_wellness_txn_account", "wellness_point_transactions", ["account_id"]
    )
    op.create_index(
        "idx_wellness_txn_created", "wellness_point_transactions", ["created_at"]
    )

    # =========================================================================
    # 5. Create wellness_leaderboard_snapshots table
    # =========================================================================
    op.create_table(
        "wellness_leaderboard_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("snapshot_type", sa.String(20), nullable=False, default="weekly"),
        sa.Column("rankings_json", postgresql.JSON(), nullable=False),
        sa.Column("total_participants", sa.Integer(), nullable=False),
        sa.Column("average_points", sa.Float(), nullable=True),
        sa.Column("median_points", sa.Float(), nullable=True),
        sa.Column("top_10_cutoff", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "snapshot_type IN ('daily', 'weekly', 'block')",
            name="check_snapshot_type",
        ),
        sa.UniqueConstraint(
            "snapshot_date", "snapshot_type", name="uq_leaderboard_snapshot"
        ),
    )

    op.create_index(
        "idx_leaderboard_snapshot_date",
        "wellness_leaderboard_snapshots",
        ["snapshot_date"],
    )

    # =========================================================================
    # 6. Create hopfield_positions table
    # =========================================================================
    op.create_table(
        "hopfield_positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("x_position", sa.Float(), nullable=False),
        sa.Column("y_position", sa.Float(), nullable=False),
        sa.Column("z_position", sa.Float(), nullable=True),
        sa.Column("basin_depth", sa.Float(), nullable=True),
        sa.Column("energy_value", sa.Float(), nullable=True),
        sa.Column("stability_score", sa.Float(), nullable=True),
        sa.Column("nearest_attractor_id", sa.String(100), nullable=True),
        sa.Column("nearest_attractor_type", sa.String(50), nullable=True),
        sa.Column("hamming_distance", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("block_number", sa.Integer(), nullable=True),
        sa.Column("academic_year", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "x_position >= 0 AND x_position <= 1",
            name="check_x_position_range",
        ),
        sa.CheckConstraint(
            "y_position >= 0 AND y_position <= 1",
            name="check_y_position_range",
        ),
        sa.CheckConstraint(
            "z_position IS NULL OR (z_position >= 0 AND z_position <= 1)",
            name="check_z_position_range",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 1 AND confidence <= 5)",
            name="check_confidence_range",
        ),
        sa.CheckConstraint(
            "block_number IS NULL OR (block_number >= 0 AND block_number <= 13)",
            name="check_hopfield_block_range",
        ),
    )

    op.create_index("idx_hopfield_person", "hopfield_positions", ["person_id"])
    op.create_index("idx_hopfield_created", "hopfield_positions", ["created_at"])
    op.create_index(
        "ix_hopfield_positions_temporal",
        "hopfield_positions",
        ["person_id", "block_number", "academic_year"],
    )

    # =========================================================================
    # 7. Create survey_availability table
    # =========================================================================
    op.create_table(
        "survey_availability",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("last_completed_at", sa.DateTime(), nullable=True),
        sa.Column("next_available_at", sa.DateTime(), nullable=True),
        sa.Column("completions_this_block", sa.Integer(), nullable=True, default=0),
        sa.Column("completions_this_year", sa.Integer(), nullable=True, default=0),
        sa.Column("current_block_number", sa.Integer(), nullable=True),
        sa.Column("current_academic_year", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["survey_id"], ["surveys.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "person_id", "survey_id", name="uq_survey_availability_person_survey"
        ),
    )

    op.create_index("idx_survey_avail_person", "survey_availability", ["person_id"])
    op.create_index("idx_survey_avail_survey", "survey_availability", ["survey_id"])
    op.create_index(
        "ix_survey_availability_next", "survey_availability", ["next_available_at"]
    )


def downgrade() -> None:
    """Downgrade: drop all wellness tables."""
    op.drop_table("survey_availability")
    op.drop_table("hopfield_positions")
    op.drop_table("wellness_leaderboard_snapshots")
    op.drop_table("wellness_point_transactions")
    op.drop_table("wellness_accounts")
    op.drop_table("survey_responses")
    op.drop_table("surveys")
