"""Add Tier 3 resilience tables

Revision ID: 006
Revises: 005
Create Date: 2024-01-01 00:00:00.000000

This migration adds tables for Tier 3 resilience features:
- Cognitive Load Management (decisions, sessions)
- Stigmergy (preference trails, signals)
- Hub Analysis (centrality, protection plans, cross-training)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # Cognitive Load Tables
    # =========================================================================

    # Cognitive sessions table
    op.create_table(
        'cognitive_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_decisions_before_break', sa.Integer, nullable=False, default=7),
        sa.Column('total_cognitive_cost', sa.Float, nullable=False, default=0.0),
        sa.Column('decisions_count', sa.Integer, nullable=False, default=0),
        sa.Column('breaks_taken', sa.Integer, nullable=False, default=0),
        sa.Column('final_state', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_cognitive_sessions_user_id', 'cognitive_sessions', ['user_id'])
    op.create_index('ix_cognitive_sessions_started_at', 'cognitive_sessions', ['started_at'])

    # Decisions table
    op.create_table(
        'cognitive_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('complexity', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('options', postgresql.JSONB, nullable=True),
        sa.Column('recommended_option', sa.String(255), nullable=True),
        sa.Column('safe_default', sa.String(255), nullable=True),
        sa.Column('has_safe_default', sa.Boolean, default=False),
        sa.Column('is_urgent', sa.Boolean, default=False),
        sa.Column('can_defer', sa.Boolean, default=True),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('context', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('outcome', sa.String(50), nullable=True),
        sa.Column('chosen_option', sa.String(255), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_by', sa.String(255), nullable=True),
        sa.Column('estimated_cognitive_cost', sa.Float, nullable=False, default=1.0),
        sa.Column('actual_time_seconds', sa.Float, nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['cognitive_sessions.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_cognitive_decisions_session_id', 'cognitive_decisions', ['session_id'])
    op.create_index('ix_cognitive_decisions_category', 'cognitive_decisions', ['category'])
    op.create_index('ix_cognitive_decisions_outcome', 'cognitive_decisions', ['outcome'])
    op.create_index('ix_cognitive_decisions_created_at', 'cognitive_decisions', ['created_at'])

    # =========================================================================
    # Stigmergy Tables
    # =========================================================================

    # Preference trails table
    op.create_table(
        'preference_trails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('faculty_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trail_type', sa.String(50), nullable=False),
        sa.Column('slot_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('slot_type', sa.String(100), nullable=True),
        sa.Column('block_type', sa.String(100), nullable=True),
        sa.Column('service_type', sa.String(100), nullable=True),
        sa.Column('target_faculty_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('strength', sa.Float, nullable=False, default=0.5),
        sa.Column('peak_strength', sa.Float, nullable=False, default=0.5),
        sa.Column('evaporation_rate', sa.Float, nullable=False, default=0.1),
        sa.Column('reinforcement_count', sa.Integer, nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_reinforced', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_evaporated', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_preference_trails_faculty_id', 'preference_trails', ['faculty_id'])
    op.create_index('ix_preference_trails_trail_type', 'preference_trails', ['trail_type'])
    op.create_index('ix_preference_trails_slot_type', 'preference_trails', ['slot_type'])
    op.create_index('ix_preference_trails_strength', 'preference_trails', ['strength'])

    # Trail signals table (history of reinforcements)
    op.create_table(
        'trail_signals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('trail_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('signal_type', sa.String(50), nullable=False),
        sa.Column('strength_change', sa.Float, nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['trail_id'], ['preference_trails.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_trail_signals_trail_id', 'trail_signals', ['trail_id'])
    op.create_index('ix_trail_signals_recorded_at', 'trail_signals', ['recorded_at'])

    # =========================================================================
    # Hub Analysis Tables
    # =========================================================================

    ***REMOVED*** centrality scores table
    op.create_table(
        'faculty_centrality',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('faculty_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('faculty_name', sa.String(255), nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('degree_centrality', sa.Float, nullable=False, default=0.0),
        sa.Column('betweenness_centrality', sa.Float, nullable=False, default=0.0),
        sa.Column('eigenvector_centrality', sa.Float, nullable=False, default=0.0),
        sa.Column('pagerank', sa.Float, nullable=False, default=0.0),
        sa.Column('composite_score', sa.Float, nullable=False, default=0.0),
        sa.Column('services_covered', sa.Integer, nullable=False, default=0),
        sa.Column('unique_services', sa.Integer, nullable=False, default=0),
        sa.Column('total_assignments', sa.Integer, nullable=False, default=0),
        sa.Column('replacement_difficulty', sa.Float, nullable=False, default=0.0),
        sa.Column('risk_level', sa.String(50), nullable=False),
        sa.Column('is_hub', sa.Boolean, nullable=False, default=False),
    )
    op.create_index('ix_faculty_centrality_faculty_id', 'faculty_centrality', ['faculty_id'])
    op.create_index('ix_faculty_centrality_composite_score', 'faculty_centrality', ['composite_score'])
    op.create_index('ix_faculty_centrality_is_hub', 'faculty_centrality', ['is_hub'])

    # Hub protection plans table
    op.create_table(
        'hub_protection_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('hub_faculty_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hub_faculty_name', sa.String(255), nullable=False),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('workload_reduction', sa.Float, nullable=False, default=0.3),
        sa.Column('backup_assigned', sa.Boolean, nullable=False, default=False),
        sa.Column('backup_faculty_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('critical_only', sa.Boolean, nullable=False, default=False),
        sa.Column('status', sa.String(50), nullable=False, default='planned'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deactivated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=True),
    )
    op.create_index('ix_hub_protection_plans_hub_faculty_id', 'hub_protection_plans', ['hub_faculty_id'])
    op.create_index('ix_hub_protection_plans_status', 'hub_protection_plans', ['status'])
    op.create_index('ix_hub_protection_plans_period', 'hub_protection_plans', ['period_start', 'period_end'])

    # Cross-training recommendations table
    op.create_table(
        'cross_training_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('skill', sa.String(255), nullable=False),
        sa.Column('current_holders', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('recommended_trainees', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('priority', sa.String(50), nullable=False),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('estimated_training_hours', sa.Integer, nullable=False, default=20),
        sa.Column('risk_reduction', sa.Float, nullable=False, default=0.0),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', sa.String(255), nullable=True),
    )
    op.create_index('ix_cross_training_priority', 'cross_training_recommendations', ['priority'])
    op.create_index('ix_cross_training_status', 'cross_training_recommendations', ['status'])


def downgrade() -> None:
    # Drop Hub Analysis tables
    op.drop_table('cross_training_recommendations')
    op.drop_table('hub_protection_plans')
    op.drop_table('faculty_centrality')

    # Drop Stigmergy tables
    op.drop_table('trail_signals')
    op.drop_table('preference_trails')

    # Drop Cognitive Load tables
    op.drop_table('cognitive_decisions')
    op.drop_table('cognitive_sessions')
