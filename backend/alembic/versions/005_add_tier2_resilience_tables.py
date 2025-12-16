"""Add Tier 2 resilience framework tables

Revision ID: 005
Revises: 004
Create Date: 2025-12-16 00:00:00.000000

Creates tables for Tier 2 strategic resilience implementation:
- Homeostasis: feedback_loop_states, allostasis_records, positive_feedback_alerts
- Blast Radius: scheduling_zones, zone_faculty_assignments, zone_borrowing_records, zone_incidents
- Le Chatelier: equilibrium_shifts, system_stress_records, compensation_records
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Tier 2 resilience framework tables."""

    # ==========================================================================
    # HOMEOSTASIS TABLES
    # ==========================================================================

    # Table 1: feedback_loop_states
    # Tracks state of homeostasis feedback loops for monitoring and corrections
    op.create_table(
        'feedback_loop_states',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('loop_name', sa.String(100), nullable=False),
        sa.Column('setpoint_name', sa.String(100), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Setpoint configuration
        sa.Column('target_value', sa.Float(), nullable=False),
        sa.Column('tolerance', sa.Float(), nullable=False),
        sa.Column('is_critical', sa.Boolean(), default=False),

        # Current state
        sa.Column('current_value', sa.Float()),
        sa.Column('deviation', sa.Float()),
        sa.Column('deviation_severity', sa.String(20)),  # none, minor, moderate, major, critical
        sa.Column('consecutive_deviations', sa.Integer(), default=0),

        # Trend analysis
        sa.Column('trend_direction', sa.String(20)),  # stable, increasing, decreasing
        sa.Column('is_improving', sa.Boolean()),

        # Action tracking
        sa.Column('correction_triggered', sa.Boolean(), default=False),
        sa.Column('correction_type', sa.String(50)),
        sa.Column('correction_effective', sa.Boolean()),

        # Constraints
        sa.CheckConstraint(
            "deviation_severity IS NULL OR deviation_severity IN ('none', 'minor', 'moderate', 'major', 'critical')",
            name='check_deviation_severity'
        ),
    )
    op.create_index('idx_feedback_loop_timestamp', 'feedback_loop_states', ['timestamp'])
    op.create_index('idx_feedback_loop_name', 'feedback_loop_states', ['loop_name'])
    op.create_index('idx_feedback_loop_severity', 'feedback_loop_states', ['deviation_severity'])

    # Table 2: allostasis_records
    # Tracks allostatic load (cumulative stress) for faculty and system
    op.create_table(
        'allostasis_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(20), nullable=False),  # faculty, system
        sa.Column('calculated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Stress factors
        sa.Column('consecutive_weekend_calls', sa.Integer(), default=0),
        sa.Column('nights_past_month', sa.Integer(), default=0),
        sa.Column('schedule_changes_absorbed', sa.Integer(), default=0),
        sa.Column('holidays_worked_this_year', sa.Integer(), default=0),
        sa.Column('overtime_hours_month', sa.Float(), default=0.0),
        sa.Column('coverage_gap_responses', sa.Integer(), default=0),
        sa.Column('cross_coverage_events', sa.Integer(), default=0),

        # Calculated scores
        sa.Column('acute_stress_score', sa.Float(), default=0.0),
        sa.Column('chronic_stress_score', sa.Float(), default=0.0),
        sa.Column('total_allostatic_load', sa.Float(), default=0.0),

        # State
        sa.Column('allostasis_state', sa.String(30)),
        sa.Column('risk_level', sa.String(20)),  # low, moderate, high, critical

        # Constraints
        sa.CheckConstraint(
            "entity_type IN ('faculty', 'system')",
            name='check_entity_type'
        ),
        sa.CheckConstraint(
            "allostasis_state IS NULL OR allostasis_state IN ('homeostasis', 'allostasis', 'allostatic_load', 'allostatic_overload')",
            name='check_allostasis_state'
        ),
    )
    op.create_index('idx_allostasis_entity', 'allostasis_records', ['entity_id', 'entity_type'])
    op.create_index('idx_allostasis_calculated', 'allostasis_records', ['calculated_at'])
    op.create_index('idx_allostasis_risk', 'allostasis_records', ['risk_level'])

    # Table 3: positive_feedback_alerts
    # Alerts for detected positive feedback loops that amplify problems
    op.create_table(
        'positive_feedback_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('detected_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Loop pattern
        sa.Column('trigger', sa.String(200)),
        sa.Column('amplification', sa.String(200)),
        sa.Column('consequence', sa.String(200)),

        # Detection
        sa.Column('evidence', postgresql.JSONB()),
        sa.Column('confidence', sa.Float()),
        sa.Column('severity', sa.String(20)),

        # Intervention
        sa.Column('intervention_recommended', sa.String(500)),
        sa.Column('urgency', sa.String(20)),  # immediate, soon, monitor

        # Resolution
        sa.Column('resolved_at', sa.DateTime()),
        sa.Column('resolution_notes', sa.String(500)),
        sa.Column('intervention_effective', sa.Boolean()),

        # Constraints
        sa.CheckConstraint(
            "urgency IS NULL OR urgency IN ('immediate', 'soon', 'monitor')",
            name='check_urgency'
        ),
    )
    op.create_index('idx_positive_feedback_detected', 'positive_feedback_alerts', ['detected_at'])
    op.create_index('idx_positive_feedback_urgency', 'positive_feedback_alerts', ['urgency'])
    op.create_index('idx_positive_feedback_resolved', 'positive_feedback_alerts', ['resolved_at'])

    # ==========================================================================
    # BLAST RADIUS / ZONE TABLES
    # ==========================================================================

    # Table 4: scheduling_zones
    # Configuration and state for scheduling zones (blast radius isolation)
    op.create_table(
        'scheduling_zones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('zone_type', sa.String(50), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Services
        sa.Column('services', postgresql.ARRAY(sa.String())),

        # Capacity requirements
        sa.Column('minimum_coverage', sa.Integer(), default=1),
        sa.Column('optimal_coverage', sa.Integer(), default=2),
        sa.Column('maximum_coverage', sa.Integer(), default=5),

        # Current status
        sa.Column('status', sa.String(20), default='green'),
        sa.Column('containment_level', sa.String(20), default='none'),
        sa.Column('last_status_change', sa.DateTime()),

        # Borrowing configuration
        sa.Column('borrowing_limit', sa.Integer(), default=2),
        sa.Column('lending_limit', sa.Integer(), default=1),
        sa.Column('priority', sa.Integer(), default=5),

        # Zone relationships
        sa.Column('can_borrow_from_zones', postgresql.ARRAY(sa.String())),
        sa.Column('can_lend_to_zones', postgresql.ARRAY(sa.String())),

        # Metrics
        sa.Column('total_borrowing_requests', sa.Integer(), default=0),
        sa.Column('total_lending_events', sa.Integer(), default=0),

        # Active status
        sa.Column('is_active', sa.Boolean(), default=True),

        # Constraints
        sa.CheckConstraint(
            "zone_type IN ('inpatient', 'outpatient', 'education', 'research', 'admin', 'on_call')",
            name='check_zone_type'
        ),
        sa.CheckConstraint(
            "status IN ('green', 'yellow', 'orange', 'red', 'black')",
            name='check_zone_status'
        ),
        sa.CheckConstraint(
            "containment_level IN ('none', 'soft', 'moderate', 'strict', 'lockdown')",
            name='check_containment_level'
        ),
    )
    op.create_index('idx_zones_name', 'scheduling_zones', ['name'], unique=True)
    op.create_index('idx_zones_type', 'scheduling_zones', ['zone_type'])
    op.create_index('idx_zones_status', 'scheduling_zones', ['status'])

    # Table 5: zone_faculty_assignments
    # Records faculty assignments to zones
    op.create_table(
        'zone_faculty_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'zone_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('scheduling_zones.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column('faculty_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('faculty_name', sa.String(200)),
        sa.Column('role', sa.String(20), nullable=False),  # primary, secondary, backup
        sa.Column('assigned_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('is_available', sa.Boolean(), default=True),
        sa.Column('removed_at', sa.DateTime()),

        # Constraints
        sa.CheckConstraint(
            "role IN ('primary', 'secondary', 'backup')",
            name='check_faculty_role'
        ),
    )
    op.create_index('idx_zone_faculty_zone', 'zone_faculty_assignments', ['zone_id'])
    op.create_index('idx_zone_faculty_faculty', 'zone_faculty_assignments', ['faculty_id'])
    op.create_index('idx_zone_faculty_available', 'zone_faculty_assignments', ['is_available'])

    # Table 6: zone_borrowing_records
    # Records cross-zone faculty borrowing requests
    op.create_table(
        'zone_borrowing_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'requesting_zone_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('scheduling_zones.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column(
            'lending_zone_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('scheduling_zones.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column('faculty_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Request details
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('reason', sa.String(500)),
        sa.Column('duration_hours', sa.Integer()),
        sa.Column('requested_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Approval
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('approved_by', sa.String(100)),
        sa.Column('approved_at', sa.DateTime()),
        sa.Column('denial_reason', sa.String(500)),

        # Execution
        sa.Column('started_at', sa.DateTime()),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('was_effective', sa.Boolean()),

        # Constraints
        sa.CheckConstraint(
            "priority IN ('critical', 'high', 'medium', 'low')",
            name='check_borrowing_priority'
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'denied', 'completed')",
            name='check_borrowing_status'
        ),
    )
    op.create_index('idx_borrowing_requesting', 'zone_borrowing_records', ['requesting_zone_id'])
    op.create_index('idx_borrowing_lending', 'zone_borrowing_records', ['lending_zone_id'])
    op.create_index('idx_borrowing_status', 'zone_borrowing_records', ['status'])
    op.create_index('idx_borrowing_requested_at', 'zone_borrowing_records', ['requested_at'])

    # Table 7: zone_incidents
    # Records incidents affecting scheduling zones
    op.create_table(
        'zone_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'zone_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('scheduling_zones.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column('incident_type', sa.String(50), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('severity', sa.String(20), nullable=False),

        # Impact
        sa.Column('faculty_affected', postgresql.ARRAY(sa.String())),
        sa.Column('capacity_lost', sa.Float(), default=0.0),
        sa.Column('services_affected', postgresql.ARRAY(sa.String())),

        # Resolution
        sa.Column('resolved_at', sa.DateTime()),
        sa.Column('resolution_notes', sa.String(500)),
        sa.Column('containment_successful', sa.Boolean(), default=True),

        # Constraints
        sa.CheckConstraint(
            "severity IN ('minor', 'moderate', 'severe', 'critical')",
            name='check_incident_severity'
        ),
    )
    op.create_index('idx_incidents_zone', 'zone_incidents', ['zone_id'])
    op.create_index('idx_incidents_started', 'zone_incidents', ['started_at'])
    op.create_index('idx_incidents_severity', 'zone_incidents', ['severity'])
    op.create_index('idx_incidents_resolved', 'zone_incidents', ['resolved_at'])

    # ==========================================================================
    # LE CHATELIER / EQUILIBRIUM TABLES
    # ==========================================================================

    # Table 8: system_stress_records
    # Records stresses applied to the system
    op.create_table(
        'system_stress_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('stress_type', sa.String(50), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('applied_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Quantification
        sa.Column('magnitude', sa.Float(), nullable=False),
        sa.Column('duration_days', sa.Integer()),
        sa.Column('is_acute', sa.Boolean(), default=True),
        sa.Column('is_reversible', sa.Boolean(), default=True),

        # Impact
        sa.Column('capacity_impact', sa.Float()),
        sa.Column('demand_impact', sa.Float()),

        # Status
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('resolved_at', sa.DateTime()),
        sa.Column('resolution_notes', sa.String(500)),

        # Constraints
        sa.CheckConstraint(
            "stress_type IN ('faculty_loss', 'demand_surge', 'quality_pressure', 'time_compression', 'resource_scarcity', 'external_pressure')",
            name='check_stress_type'
        ),
    )
    op.create_index('idx_stress_applied', 'system_stress_records', ['applied_at'])
    op.create_index('idx_stress_type', 'system_stress_records', ['stress_type'])
    op.create_index('idx_stress_active', 'system_stress_records', ['is_active'])

    # Table 9: compensation_records
    # Records compensation responses to system stress
    op.create_table(
        'compensation_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'stress_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('system_stress_records.id', ondelete='CASCADE'),
            nullable=False
        ),
        sa.Column('compensation_type', sa.String(50), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('initiated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Quantification
        sa.Column('compensation_magnitude', sa.Float(), nullable=False),
        sa.Column('effectiveness', sa.Float(), default=0.8),

        # Costs
        sa.Column('immediate_cost', sa.Float(), default=0.0),
        sa.Column('hidden_cost', sa.Float(), default=0.0),
        sa.Column('sustainability_days', sa.Integer()),

        # Status
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('ended_at', sa.DateTime()),
        sa.Column('end_reason', sa.String(200)),

        # Constraints
        sa.CheckConstraint(
            "compensation_type IN ('overtime', 'cross_coverage', 'deferred_leave', 'service_reduction', 'efficiency_gain', 'backup_activation', 'quality_trade')",
            name='check_compensation_type'
        ),
    )
    op.create_index('idx_compensation_stress', 'compensation_records', ['stress_id'])
    op.create_index('idx_compensation_initiated', 'compensation_records', ['initiated_at'])
    op.create_index('idx_compensation_active', 'compensation_records', ['is_active'])

    # Table 10: equilibrium_shifts
    # Records equilibrium shifts per Le Chatelier's principle
    op.create_table(
        'equilibrium_shifts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),

        # Original state
        sa.Column('original_capacity', sa.Float(), nullable=False),
        sa.Column('original_demand', sa.Float(), nullable=False),
        sa.Column('original_coverage_rate', sa.Float(), nullable=False),

        # Stress applied
        sa.Column('stress_types', postgresql.ARRAY(sa.String())),
        sa.Column('total_capacity_impact', sa.Float()),
        sa.Column('total_demand_impact', sa.Float()),

        # Compensation
        sa.Column('compensation_types', postgresql.ARRAY(sa.String())),
        sa.Column('total_compensation', sa.Float()),
        sa.Column('compensation_efficiency', sa.Float()),

        # New equilibrium
        sa.Column('new_capacity', sa.Float(), nullable=False),
        sa.Column('new_demand', sa.Float(), nullable=False),
        sa.Column('new_coverage_rate', sa.Float(), nullable=False),
        sa.Column('sustainable_capacity', sa.Float()),

        # Costs
        sa.Column('compensation_debt', sa.Float(), default=0.0),
        sa.Column('daily_debt_rate', sa.Float(), default=0.0),
        sa.Column('burnout_risk', sa.Float(), default=0.0),
        sa.Column('days_until_exhaustion', sa.Integer()),

        # State
        sa.Column('equilibrium_state', sa.String(30)),
        sa.Column('is_sustainable', sa.Boolean()),

        # Constraints
        sa.CheckConstraint(
            "equilibrium_state IS NULL OR equilibrium_state IN ('stable', 'compensating', 'stressed', 'unsustainable', 'critical')",
            name='check_equilibrium_state'
        ),
    )
    op.create_index('idx_equilibrium_calculated', 'equilibrium_shifts', ['calculated_at'])
    op.create_index('idx_equilibrium_state', 'equilibrium_shifts', ['equilibrium_state'])
    op.create_index('idx_equilibrium_sustainable', 'equilibrium_shifts', ['is_sustainable'])


def downgrade() -> None:
    """Drop Tier 2 resilience framework tables in reverse order."""
    # Le Chatelier tables
    op.drop_table('equilibrium_shifts')
    op.drop_table('compensation_records')
    op.drop_table('system_stress_records')

    # Blast radius tables
    op.drop_table('zone_incidents')
    op.drop_table('zone_borrowing_records')
    op.drop_table('zone_faculty_assignments')
    op.drop_table('scheduling_zones')

    # Homeostasis tables
    op.drop_table('positive_feedback_alerts')
    op.drop_table('allostasis_records')
    op.drop_table('feedback_loop_states')
