"""Add resilience framework tables

Revision ID: 004
Revises: 003
Create Date: 2025-12-16 00:00:00.000000

Creates tables for Tier 1 resilience framework:
- resilience_health_checks: Periodic system health assessments
- resilience_events: Audit log for resilience state changes
- sacrifice_decisions: Load shedding decision audit trail
- fallback_activations: Fallback schedule activation records
- vulnerability_records: N-1/N-2 vulnerability analysis results
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create resilience framework tables."""

    # Table 1: resilience_health_checks
    # Stores periodic system health check results for trend analysis and alerting
    op.create_table(
        'resilience_health_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Overall status
        sa.Column('overall_status', sa.String(20), nullable=False),

        # Utilization metrics (queuing theory)
        sa.Column('utilization_rate', sa.Float(), nullable=False),
        sa.Column('utilization_level', sa.String(20), nullable=False),  # GREEN, YELLOW, ORANGE, RED, BLACK
        sa.Column('buffer_remaining', sa.Float()),

        # Defense status (nuclear safety paradigm)
        sa.Column('defense_level', sa.String(30)),  # PREVENTION, CONTROL, SAFETY_SYSTEMS, CONTAINMENT, EMERGENCY
        sa.Column('load_shedding_level', sa.String(20)),  # NORMAL, YELLOW, ORANGE, RED, BLACK, CRITICAL

        # Contingency compliance (N-1/N-2)
        sa.Column('n1_pass', sa.Boolean(), default=True),
        sa.Column('n2_pass', sa.Boolean(), default=True),
        sa.Column('phase_transition_risk', sa.String(20)),  # low, medium, high, critical

        # Active responses
        sa.Column('active_fallbacks', postgresql.ARRAY(sa.String())),
        sa.Column('crisis_mode', sa.Boolean(), default=False),

        # Recommendations captured
        sa.Column('immediate_actions', postgresql.JSONB()),
        sa.Column('watch_items', postgresql.JSONB()),

        # Full metrics snapshot for deep analysis
        sa.Column('metrics_snapshot', postgresql.JSONB()),

        # Constraints
        sa.CheckConstraint(
            "overall_status IN ('healthy', 'warning', 'degraded', 'critical', 'emergency')",
            name='check_health_status'
        ),
        sa.CheckConstraint(
            "utilization_level IN ('GREEN', 'YELLOW', 'ORANGE', 'RED', 'BLACK')",
            name='check_utilization_level'
        ),
    )
    op.create_index('idx_health_checks_timestamp', 'resilience_health_checks', ['timestamp'])
    op.create_index('idx_health_checks_status', 'resilience_health_checks', ['overall_status'])

    # Table 2: resilience_events
    # Audit log for all resilience system state changes
    op.create_table(
        'resilience_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('event_type', sa.String(50), nullable=False),

        # Event context
        sa.Column('severity', sa.String(20)),  # minor, moderate, severe, critical
        sa.Column('reason', sa.String(500)),
        sa.Column('triggered_by', sa.String(100)),  # 'system', 'user:<id>', 'scheduled_task'

        # State before/after for audit trail
        sa.Column('previous_state', postgresql.JSONB()),
        sa.Column('new_state', postgresql.JSONB()),

        # Related entities
        sa.Column(
            'related_health_check_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('resilience_health_checks.id', ondelete='SET NULL'),
        ),

        # Additional context
        sa.Column('metadata', postgresql.JSONB()),

        # Constraints
        sa.CheckConstraint(
            "event_type IN ('health_check', 'crisis_activated', 'crisis_deactivated', "
            "'fallback_activated', 'fallback_deactivated', 'load_shedding_activated', "
            "'load_shedding_deactivated', 'defense_level_changed', 'threshold_exceeded', "
            "'n1_violation', 'n2_violation')",
            name='check_event_type'
        ),
    )
    op.create_index('idx_events_timestamp', 'resilience_events', ['timestamp'])
    op.create_index('idx_events_type', 'resilience_events', ['event_type'])
    op.create_index('idx_events_severity', 'resilience_events', ['severity'])

    # Table 3: sacrifice_decisions
    # Audit trail for load shedding (sacrifice) decisions
    op.create_table(
        'sacrifice_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Decision details
        sa.Column('from_level', sa.String(20), nullable=False),  # Previous load shedding level
        sa.Column('to_level', sa.String(20), nullable=False),  # New load shedding level
        sa.Column('reason', sa.String(500), nullable=False),

        # What was affected
        sa.Column('activities_suspended', postgresql.ARRAY(sa.String())),
        sa.Column('activities_protected', postgresql.ARRAY(sa.String())),

        # Authorization
        sa.Column('approved_by', sa.String(100)),  # User ID or 'auto' for automatic
        sa.Column('approval_method', sa.String(50)),  # 'automatic', 'manual', 'emergency_override'

        # Context at decision time
        sa.Column('utilization_at_decision', sa.Float()),
        sa.Column('coverage_at_decision', sa.Float()),
        sa.Column(
            'related_event_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('resilience_events.id', ondelete='SET NULL'),
        ),

        # Recovery tracking
        sa.Column('recovered_at', sa.DateTime()),
        sa.Column('recovery_reason', sa.String(500)),

        # Constraints
        sa.CheckConstraint(
            "from_level IN ('NORMAL', 'YELLOW', 'ORANGE', 'RED', 'BLACK', 'CRITICAL')",
            name='check_from_level'
        ),
        sa.CheckConstraint(
            "to_level IN ('NORMAL', 'YELLOW', 'ORANGE', 'RED', 'BLACK', 'CRITICAL')",
            name='check_to_level'
        ),
    )
    op.create_index('idx_sacrifice_timestamp', 'sacrifice_decisions', ['timestamp'])
    op.create_index('idx_sacrifice_active', 'sacrifice_decisions', ['recovered_at'])

    # Table 4: fallback_activations
    # Tracks fallback schedule activations for audit and effectiveness tracking
    op.create_table(
        'fallback_activations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('activated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Fallback details
        sa.Column('scenario', sa.String(50), nullable=False),
        sa.Column('scenario_description', sa.String(500)),

        # Authorization
        sa.Column('activated_by', sa.String(100)),  # User ID or 'auto'
        sa.Column('activation_reason', sa.String(500)),

        # Schedule details
        sa.Column('assignments_count', sa.Integer()),
        sa.Column('coverage_rate', sa.Float()),
        sa.Column('services_reduced', postgresql.ARRAY(sa.String())),
        sa.Column('assumptions', postgresql.ARRAY(sa.String())),

        # Deactivation
        sa.Column('deactivated_at', sa.DateTime()),
        sa.Column('deactivated_by', sa.String(100)),
        sa.Column('deactivation_reason', sa.String(500)),

        # Related event
        sa.Column(
            'related_event_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('resilience_events.id', ondelete='SET NULL'),
        ),

        # Constraints
        sa.CheckConstraint(
            "scenario IN ('single_faculty_loss', 'double_faculty_loss', 'pcs_season_50_percent', "
            "'holiday_skeleton', 'pandemic_essential', 'mass_casualty', 'weather_emergency')",
            name='check_fallback_scenario'
        ),
    )
    op.create_index('idx_fallback_activated_at', 'fallback_activations', ['activated_at'])
    op.create_index('idx_fallback_scenario', 'fallback_activations', ['scenario'])
    op.create_index('idx_fallback_active', 'fallback_activations', ['deactivated_at'])

    # Table 5: vulnerability_records
    # Stores N-1/N-2 vulnerability analysis results for trend tracking
    op.create_table(
        'vulnerability_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('analyzed_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Analysis scope
        sa.Column('period_start', sa.DateTime()),
        sa.Column('period_end', sa.DateTime()),
        sa.Column('faculty_count', sa.Integer()),
        sa.Column('block_count', sa.Integer()),

        # Results
        sa.Column('n1_pass', sa.Boolean(), nullable=False),
        sa.Column('n2_pass', sa.Boolean(), nullable=False),
        sa.Column('phase_transition_risk', sa.String(20)),

        # Vulnerability details
        sa.Column('n1_vulnerabilities', postgresql.JSONB()),  # List of single-loss vulnerabilities
        sa.Column('n2_fatal_pairs', postgresql.JSONB()),  # List of fatal faculty pairs
        sa.Column('most_critical_faculty', postgresql.JSONB()),  ***REMOVED*** IDs with highest centrality

        # Recommendations generated
        sa.Column('recommended_actions', postgresql.ARRAY(sa.String())),

        # Related health check
        sa.Column(
            'related_health_check_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('resilience_health_checks.id', ondelete='SET NULL'),
        ),

        # Constraints
        sa.CheckConstraint(
            "phase_transition_risk IN ('low', 'medium', 'high', 'critical')",
            name='check_phase_risk'
        ),
    )
    op.create_index('idx_vulnerability_analyzed_at', 'vulnerability_records', ['analyzed_at'])
    op.create_index('idx_vulnerability_n1_pass', 'vulnerability_records', ['n1_pass'])
    op.create_index('idx_vulnerability_n2_pass', 'vulnerability_records', ['n2_pass'])


def downgrade() -> None:
    """Drop resilience framework tables in reverse order."""
    op.drop_table('vulnerability_records')
    op.drop_table('fallback_activations')
    op.drop_table('sacrifice_decisions')
    op.drop_table('resilience_events')
    op.drop_table('resilience_health_checks')
