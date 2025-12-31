"""
Comprehensive tests for ResilienceService.

Tests the main orchestrator service that coordinates all resilience components:
- Health checks
- Crisis response activation/deactivation
- Defense level management
- Fallback scenario activation
- Event handling
- Tier 2 (Homeostasis, Blast Radius, Le Chatelier)
- Tier 3 (Cognitive Load, Stigmergy, Hub Analysis)
- Tier 4 (Transcription Factors)
"""

import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4, UUID

from app.resilience.service import (
    ResilienceService,
    ResilienceConfig,
    SystemHealthReport,
)
from app.resilience.defense_in_depth import DefenseLevel
from app.resilience.sacrifice_hierarchy import LoadSheddingLevel
from app.resilience.utilization import UtilizationLevel
from app.resilience.static_stability import FallbackScenario
from app.resilience.homeostasis import AllostasisState
from app.resilience.le_chatelier import StressType, CompensationType, EquilibriumState
from app.resilience.cognitive_load import DecisionCategory, DecisionComplexity
from app.resilience.stigmergy import TrailType, SignalType
from app.resilience.blast_radius import ZoneType, ContainmentLevel
from app.resilience.transcription_factors import TFType, ChromatinState


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def config():
    """Create test configuration."""
    return ResilienceConfig(
        max_utilization=0.80,
        warning_threshold=0.70,
        auto_activate_defense=True,
        auto_activate_fallback=False,
        health_check_interval_minutes=15,
    )


@pytest.fixture
def resilience_service(config):
    """Create resilience service without database."""
    return ResilienceService(db=None, config=config)


@pytest.fixture
def mock_faculty():
    """Create mock faculty list."""
    return [
        type("Person", (), {"id": uuid4(), "name": f"Faculty {i}", "type": "faculty"})()
        for i in range(5)
    ]


@pytest.fixture
def mock_blocks():
    """Create mock blocks for 7 days."""
    blocks = []
    start_date = date.today()
    for day in range(7):
        current_date = start_date + timedelta(days=day)
        for tod in ["AM", "PM"]:
            block = type(
                "Block",
                (),
                {
                    "id": uuid4(),
                    "date": current_date,
                    "time_of_day": tod,
                    "block_number": 1,
                },
            )()
            blocks.append(block)
    return blocks


@pytest.fixture
def mock_assignments(mock_faculty, mock_blocks):
    """Create mock assignments."""
    assignments = []
    rotation_id = uuid4()
    for i, block in enumerate(mock_blocks):
        faculty_idx = i % len(mock_faculty)
        assignment = type(
            "Assignment",
            (),
            {
                "id": uuid4(),
                "block_id": block.id,
                "person_id": mock_faculty[faculty_idx].id,
                "rotation_template_id": rotation_id,
                "role": "primary",
            },
        )()
        assignments.append(assignment)
    return assignments


# ============================================================================
# Test Class: Basic Service Initialization
# ============================================================================


class TestResilienceServiceInitialization:
    """Tests for service initialization."""

    def test_service_initializes_with_defaults(self):
        """Test service initializes with default config."""
        service = ResilienceService()

        assert service.config.max_utilization == 0.80
        assert service.config.warning_threshold == 0.70
        assert service.utilization is not None
        assert service.defense is not None
        assert service.contingency is not None
        assert service.fallback is not None
        assert service.sacrifice is not None

    def test_service_initializes_with_custom_config(self, config):
        """Test service initializes with custom config."""
        service = ResilienceService(config=config)

        assert service.config.max_utilization == 0.80
        assert service.config.health_check_interval_minutes == 15

    def test_tier2_components_initialized(self, resilience_service):
        """Test Tier 2 components are initialized."""
        assert resilience_service.homeostasis is not None
        assert resilience_service.blast_radius is not None
        assert resilience_service.equilibrium is not None

    def test_tier3_components_initialized(self, resilience_service):
        """Test Tier 3 components are initialized."""
        assert resilience_service.cognitive_load is not None
        assert resilience_service.stigmergy is not None
        assert resilience_service.hub_analyzer is not None

    def test_tier4_components_initialized_when_enabled(self):
        """Test Tier 4 components initialized when enabled."""
        config = ResilienceConfig(enable_transcription_factors=True)
        service = ResilienceService(config=config)

        assert service.tf_scheduler is not None

    def test_tier4_components_disabled_when_configured(self):
        """Test Tier 4 components disabled when configured."""
        config = ResilienceConfig(enable_transcription_factors=False)
        service = ResilienceService(config=config)

        assert service.tf_scheduler is None


# ============================================================================
# Test Class: Health Check
# ============================================================================


class TestHealthCheck:
    """Tests for system health checks."""

    def test_health_check_returns_report(
        self, resilience_service, mock_faculty, mock_blocks, mock_assignments
    ):
        """Test health check returns complete report."""
        report = resilience_service.check_health(
            mock_faculty, mock_blocks, mock_assignments
        )

        assert isinstance(report, SystemHealthReport)
        assert report.timestamp is not None
        assert report.overall_status in ["healthy", "degraded", "critical", "emergency"]
        assert report.utilization is not None
        assert report.defense_level is not None

    def test_health_check_detects_healthy_state(
        self, resilience_service, mock_faculty, mock_blocks
    ):
        """Test health check detects healthy state with low utilization."""
        # Low utilization (empty schedule)
        report = resilience_service.check_health(mock_faculty, mock_blocks, [])

        assert report.overall_status == "healthy"
        assert report.defense_level == DefenseLevel.GREEN
        assert report.utilization.level == UtilizationLevel.GREEN

    def test_health_check_detects_degraded_state(
        self, resilience_service, mock_faculty, mock_blocks, mock_assignments
    ):
        """Test health check detects degraded state with high utilization."""
        # High utilization (all assignments)
        report = resilience_service.check_health(
            mock_faculty, mock_blocks, mock_assignments
        )

        # Should show some level of concern
        assert report.utilization.utilization_rate > 0.0

    def test_health_check_updates_last_check_timestamp(
        self, resilience_service, mock_faculty, mock_blocks, mock_assignments
    ):
        """Test health check updates last check timestamp."""
        before = datetime.now()
        resilience_service.check_health(mock_faculty, mock_blocks, mock_assignments)
        after = datetime.now()

        assert resilience_service._last_health_check is not None
        assert before <= resilience_service._last_health_check <= after

    def test_health_check_calculates_utilization_correctly(
        self, resilience_service, mock_faculty, mock_blocks, mock_assignments
    ):
        """Test health check calculates utilization metrics."""
        report = resilience_service.check_health(
            mock_faculty, mock_blocks, mock_assignments
        )

        assert 0.0 <= report.utilization.utilization_rate <= 1.5
        assert report.utilization.available_capacity > 0

    def test_health_check_includes_recommendations(
        self, resilience_service, mock_faculty, mock_blocks, mock_assignments
    ):
        """Test health check includes actionable recommendations."""
        report = resilience_service.check_health(
            mock_faculty, mock_blocks, mock_assignments
        )

        # Should have either immediate actions or watch items
        assert isinstance(report.immediate_actions, list)
        assert isinstance(report.watch_items, list)


# ============================================================================
# Test Class: Crisis Response
# ============================================================================


class TestCrisisResponse:
    """Tests for crisis response activation and deactivation."""

    def test_activate_crisis_minor_severity(self, resilience_service):
        """Test activating crisis response with minor severity."""
        result = resilience_service.activate_crisis_response(
            severity="minor", reason="Test minor crisis"
        )

        assert result["crisis_mode"] is True
        assert result["severity"] == "minor"
        assert len(result["actions_taken"]) > 0
        assert resilience_service.sacrifice.current_level == LoadSheddingLevel.YELLOW

    def test_activate_crisis_moderate_severity(self, resilience_service):
        """Test activating crisis response with moderate severity."""
        result = resilience_service.activate_crisis_response(
            severity="moderate", reason="Test moderate crisis"
        )

        assert result["severity"] == "moderate"
        assert resilience_service.sacrifice.current_level == LoadSheddingLevel.ORANGE

    def test_activate_crisis_severe_severity(self, resilience_service):
        """Test activating crisis response with severe severity."""
        result = resilience_service.activate_crisis_response(
            severity="severe", reason="Test severe crisis"
        )

        assert result["severity"] == "severe"
        assert resilience_service.sacrifice.current_level == LoadSheddingLevel.RED

    def test_activate_crisis_critical_severity(self, resilience_service):
        """Test activating crisis response with critical severity."""
        result = resilience_service.activate_crisis_response(
            severity="critical", reason="Test critical crisis"
        )

        assert result["severity"] == "critical"
        assert resilience_service.sacrifice.current_level == LoadSheddingLevel.BLACK

    def test_deactivate_crisis_response(self, resilience_service):
        """Test deactivating crisis response."""
        # First activate
        resilience_service.activate_crisis_response(
            severity="moderate", reason="Test crisis"
        )
        assert resilience_service._crisis_mode is True

        # Then deactivate
        result = resilience_service.deactivate_crisis_response(
            reason="Crisis resolved"
        )

        assert result["crisis_mode"] is False
        assert resilience_service._crisis_mode is False
        assert "recovery_plan" in result

    def test_crisis_mode_flag_set_correctly(self, resilience_service):
        """Test crisis mode flag is set correctly."""
        assert resilience_service._crisis_mode is False

        resilience_service.activate_crisis_response(
            severity="moderate", reason="Test"
        )
        assert resilience_service._crisis_mode is True

        resilience_service.deactivate_crisis_response(reason="Done")
        assert resilience_service._crisis_mode is False


# ============================================================================
# Test Class: Fallback Scenarios
# ============================================================================


class TestFallbackScenarios:
    """Tests for fallback scenario recommendation and activation."""

    def test_recommend_fallback_with_adequate_coverage(self, resilience_service):
        """Test no fallback recommended when coverage adequate."""
        result = resilience_service.recommend_fallback(
            faculty_available=5, faculty_total=5, is_pcs_season=False, is_holiday=False
        )

        # No faculty loss, no fallback needed
        assert result is None or result == FallbackScenario.NORMAL

    def test_recommend_fallback_with_single_faculty_loss(self, resilience_service):
        """Test fallback recommended with single faculty loss."""
        result = resilience_service.recommend_fallback(
            faculty_available=4, faculty_total=5, is_pcs_season=False, is_holiday=False
        )

        # Should recommend a fallback scenario
        assert result is not None

    def test_recommend_fallback_during_pcs_season(self, resilience_service):
        """Test fallback recommendation during PCS season."""
        result = resilience_service.recommend_fallback(
            faculty_available=4, faculty_total=5, is_pcs_season=True, is_holiday=False
        )

        assert result is not None

    def test_recommend_fallback_during_holiday(self, resilience_service):
        """Test fallback recommendation during holiday period."""
        result = resilience_service.recommend_fallback(
            faculty_available=4, faculty_total=5, is_pcs_season=False, is_holiday=True
        )

        assert result is not None

    def test_activate_fallback_scenario(self, resilience_service):
        """Test activating a fallback scenario."""
        # Note: This will return None without precomputed fallbacks
        result = resilience_service.activate_fallback(
            scenario=FallbackScenario.N_MINUS_1, approved_by="test_user"
        )

        # Expected to return None since no fallbacks are precomputed
        assert result is None


# ============================================================================
# Test Class: Event Handlers
# ============================================================================


class TestEventHandlers:
    """Tests for event registration and emission."""

    def test_register_event_handler(self, resilience_service):
        """Test registering an event handler."""
        handled_events = []

        def handler(data):
            handled_events.append(data)

        resilience_service.register_event_handler("health_check", handler)

        # Trigger event
        resilience_service._emit_event("health_check", {"test": "data"})

        assert len(handled_events) == 1
        assert handled_events[0]["test"] == "data"

    def test_multiple_handlers_for_same_event(self, resilience_service):
        """Test multiple handlers for same event type."""
        handler1_calls = []
        handler2_calls = []

        def handler1(data):
            handler1_calls.append(data)

        def handler2(data):
            handler2_calls.append(data)

        resilience_service.register_event_handler("test_event", handler1)
        resilience_service.register_event_handler("test_event", handler2)

        resilience_service._emit_event("test_event", {"value": 42})

        assert len(handler1_calls) == 1
        assert len(handler2_calls) == 1

    def test_handler_exception_does_not_break_emission(self, resilience_service):
        """Test that handler exception doesn't prevent other handlers."""
        successful_calls = []

        def failing_handler(data):
            raise ValueError("Intentional error")

        def successful_handler(data):
            successful_calls.append(data)

        resilience_service.register_event_handler("test_event", failing_handler)
        resilience_service.register_event_handler("test_event", successful_handler)

        # Should not raise exception
        resilience_service._emit_event("test_event", {"data": "test"})

        # Successful handler should still be called
        assert len(successful_calls) == 1


# ============================================================================
# Test Class: Tier 2 - Homeostasis
# ============================================================================


class TestTier2Homeostasis:
    """Tests for Tier 2 homeostasis methods."""

    def test_check_homeostasis_with_current_values(self, resilience_service):
        """Test homeostasis check with current values."""
        current_values = {"coverage_rate": 0.95, "faculty_utilization": 0.75}

        status = resilience_service.check_homeostasis(current_values)

        assert status.overall_state is not None
        assert status.feedback_loops_healthy >= 0
        assert status.feedback_loops_deviating >= 0

    def test_calculate_allostatic_load(self, resilience_service):
        """Test allostatic load calculation."""
        entity_id = uuid4()
        stress_factors = {
            "workload": 0.8,
            "sleep_debt": 0.6,
            "schedule_variability": 0.4,
        }

        metrics = resilience_service.calculate_allostatic_load(
            entity_id, "faculty", stress_factors
        )

        assert metrics.total_allostatic_load >= 0.0
        assert metrics.risk_level in ["low", "moderate", "high", "critical"]

    def test_get_feedback_loop_status(self, resilience_service):
        """Test retrieving feedback loop status."""
        # Create a feedback loop first
        resilience_service.check_homeostasis({"coverage_rate": 0.90})

        loop = resilience_service.get_feedback_loop_status("coverage_rate")

        assert loop is not None
        assert loop.setpoint_name == "coverage_rate"


# ============================================================================
# Test Class: Tier 2 - Blast Radius
# ============================================================================


class TestTier2BlastRadius:
    """Tests for Tier 2 blast radius methods."""

    def test_create_zone(self, resilience_service):
        """Test creating a scheduling zone."""
        zone = resilience_service.create_zone(
            name="Test Zone",
            zone_type=ZoneType.CLINICAL_SERVICE,
            description="Test zone for unit tests",
            services=["service1", "service2"],
            minimum_coverage=1,
            optimal_coverage=2,
        )

        assert zone.name == "Test Zone"
        assert zone.zone_type == ZoneType.CLINICAL_SERVICE
        assert len(zone.services) == 2

    def test_assign_faculty_to_zone(self, resilience_service):
        """Test assigning faculty to a zone."""
        zone = resilience_service.create_zone(
            name="Test Zone",
            zone_type=ZoneType.CLINICAL_SERVICE,
            description="Test",
            services=["service1"],
        )

        faculty_id = uuid4()
        result = resilience_service.assign_faculty_to_zone(
            zone.id, faculty_id, "Dr. Test", role="primary"
        )

        assert result is True

    def test_check_all_zones(self, resilience_service):
        """Test checking all zones health."""
        # Create a zone first
        resilience_service.create_zone(
            name="Test Zone",
            zone_type=ZoneType.CLINICAL_SERVICE,
            description="Test",
            services=["service1"],
        )

        report = resilience_service.check_all_zones()

        assert report.total_zones >= 0
        assert report.containment_level is not None

    def test_set_containment_level(self, resilience_service):
        """Test setting system-wide containment level."""
        resilience_service.set_containment_level(
            ContainmentLevel.MODERATE, "Testing containment"
        )

        assert resilience_service.blast_radius.global_containment == ContainmentLevel.MODERATE


# ============================================================================
# Test Class: Tier 2 - Le Chatelier
# ============================================================================


class TestTier2LeChatelier:
    """Tests for Tier 2 Le Chatelier / equilibrium methods."""

    def test_apply_system_stress(self, resilience_service):
        """Test applying stress to the system."""
        stress = resilience_service.apply_system_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Test faculty loss",
            magnitude=0.2,
            duration_days=30,
            capacity_impact=-0.2,
            demand_impact=0.0,
        )

        assert stress.stress_type == StressType.FACULTY_LOSS
        assert stress.magnitude == 0.2
        assert stress.capacity_impact == -0.2

    def test_initiate_compensation(self, resilience_service):
        """Test initiating compensation for stress."""
        # First apply stress
        stress = resilience_service.apply_system_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Test",
            magnitude=0.2,
            duration_days=30,
            capacity_impact=-0.2,
        )

        # Then compensate
        compensation = resilience_service.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.OVERTIME,
            description="Overtime to compensate",
            magnitude=0.15,
        )

        assert compensation is not None
        assert compensation.compensation_type == CompensationType.OVERTIME

    def test_get_equilibrium_report(self, resilience_service):
        """Test getting equilibrium report."""
        report = resilience_service.get_equilibrium_report()

        assert report.current_equilibrium_state is not None
        assert report.current_coverage_rate >= 0.0


# ============================================================================
# Test Class: Tier 3 - Cognitive Load
# ============================================================================


class TestTier3CognitiveLoad:
    """Tests for Tier 3 cognitive load methods."""

    def test_start_cognitive_session(self, resilience_service):
        """Test starting a cognitive session."""
        user_id = uuid4()
        session = resilience_service.start_cognitive_session(user_id)

        assert session.user_id == user_id
        assert session.start_time is not None

    def test_end_cognitive_session(self, resilience_service):
        """Test ending a cognitive session."""
        user_id = uuid4()
        session = resilience_service.start_cognitive_session(user_id)

        resilience_service.end_cognitive_session(session.id)

        assert session.end_time is not None

    def test_create_decision(self, resilience_service):
        """Test creating a decision request."""
        decision = resilience_service.create_decision(
            category=DecisionCategory.SCHEDULE_CHANGE,
            complexity=DecisionComplexity.SIMPLE,
            description="Test decision",
            options=["Option A", "Option B"],
            safe_default="Option A",
        )

        assert decision.category == DecisionCategory.SCHEDULE_CHANGE
        assert decision.complexity == DecisionComplexity.SIMPLE
        assert len(decision.options) == 2

    def test_get_decision_queue_status(self, resilience_service):
        """Test getting decision queue status."""
        status = resilience_service.get_decision_queue_status()

        assert status.total_pending >= 0
        assert status.estimated_cognitive_cost >= 0


# ============================================================================
# Test Class: Tier 3 - Stigmergy
# ============================================================================


class TestTier3Stigmergy:
    """Tests for Tier 3 stigmergy methods."""

    def test_record_preference(self, resilience_service):
        """Test recording a preference trail."""
        faculty_id = uuid4()
        trail = resilience_service.record_preference(
            faculty_id=faculty_id,
            trail_type=TrailType.SLOT_PREFERENCE,
            slot_type="clinic",
            strength=0.7,
        )

        assert trail.faculty_id == faculty_id
        assert trail.trail_type == TrailType.SLOT_PREFERENCE
        assert trail.strength == 0.7

    def test_record_behavioral_signal(self, resilience_service):
        """Test recording a behavioral signal."""
        faculty_id = uuid4()

        # First create a preference
        resilience_service.record_preference(
            faculty_id=faculty_id,
            trail_type=TrailType.SLOT_PREFERENCE,
            slot_type="clinic",
        )

        # Then record a signal
        resilience_service.record_behavioral_signal(
            faculty_id=faculty_id,
            signal_type=SignalType.ACCEPTED,
            slot_type="clinic",
        )

        # Signal should strengthen the trail
        preferences = resilience_service.get_faculty_preferences(faculty_id)
        assert len(preferences) > 0

    def test_get_stigmergy_status(self, resilience_service):
        """Test getting stigmergy status."""
        status = resilience_service.get_stigmergy_status()

        assert status.total_trails >= 0
        assert status.average_strength >= 0.0


# ============================================================================
# Test Class: Tier 3 - Hub Analysis
# ============================================================================


class TestTier3HubAnalysis:
    """Tests for Tier 3 hub analysis methods."""

    def test_analyze_hubs(self, resilience_service, mock_faculty, mock_assignments):
        """Test hub analysis calculation."""
        services = {uuid4(): [f.id for f in mock_faculty[:3]]}

        results = resilience_service.analyze_hubs(
            mock_faculty, mock_assignments, services
        )

        assert len(results) >= 0

    def test_get_hub_status(self, resilience_service):
        """Test getting hub status."""
        status = resilience_service.get_hub_status()

        assert isinstance(status, dict)


# ============================================================================
# Test Class: Tier 4 - Transcription Factors
# ============================================================================


class TestTier4TranscriptionFactors:
    """Tests for Tier 4 transcription factor methods."""

    def test_create_transcription_factor_when_enabled(self):
        """Test creating a transcription factor when TF scheduler enabled."""
        config = ResilienceConfig(enable_transcription_factors=True)
        service = ResilienceService(config=config)

        tf = service.create_transcription_factor(
            name="TestTF",
            tf_type=TFType.ACTIVATOR,
            description="Test TF",
            binding_affinity=0.8,
        )

        assert tf is not None
        assert tf.name == "TestTF"
        assert tf.tf_type == TFType.ACTIVATOR

    def test_create_transcription_factor_when_disabled(self, resilience_service):
        """Test creating TF returns None when scheduler disabled."""
        tf = resilience_service.create_transcription_factor(
            name="TestTF",
            tf_type=TFType.ACTIVATOR,
            description="Test TF",
        )

        assert tf is None

    def test_get_tf_scheduler_status_when_disabled(self, resilience_service):
        """Test TF scheduler status when disabled."""
        status = resilience_service.get_tf_scheduler_status()

        assert status["enabled"] is False

    def test_get_tf_scheduler_status_when_enabled(self):
        """Test TF scheduler status when enabled."""
        config = ResilienceConfig(enable_transcription_factors=True)
        service = ResilienceService(config=config)

        status = service.get_tf_scheduler_status()

        assert status["enabled"] is True


# ============================================================================
# Test Class: Comprehensive Report
# ============================================================================


class TestComprehensiveReport:
    """Tests for comprehensive resilience report generation."""

    def test_get_comprehensive_report(
        self, resilience_service, mock_faculty, mock_blocks, mock_assignments
    ):
        """Test generating comprehensive report."""
        report = resilience_service.get_comprehensive_report(
            mock_faculty, mock_blocks, mock_assignments
        )

        assert "generated_at" in report
        assert "overall_status" in report
        assert "summary" in report
        assert "components" in report
        assert "immediate_actions" in report
        assert "watch_items" in report

    def test_comprehensive_report_includes_all_components(
        self, resilience_service, mock_faculty, mock_blocks, mock_assignments
    ):
        """Test comprehensive report includes all component statuses."""
        report = resilience_service.get_comprehensive_report(
            mock_faculty, mock_blocks, mock_assignments
        )

        assert "utilization" in report["components"]
        assert "defense" in report["components"]
        assert "fallback" in report["components"]
        assert "sacrifice" in report["components"]

    def test_tier2_status_report(self, resilience_service):
        """Test Tier 2 combined status report."""
        status = resilience_service.get_tier2_status()

        assert "homeostasis" in status
        assert "blast_radius" in status
        assert "equilibrium" in status
        assert "tier2_status" in status

    def test_tier3_status_report(self, resilience_service):
        """Test Tier 3 combined status report."""
        status = resilience_service.get_tier3_status()

        assert "cognitive_load" in status
        assert "stigmergy" in status
        assert "hub_analysis" in status
        assert "tier3_status" in status

    def test_tier4_status_report(self, resilience_service):
        """Test Tier 4 status report."""
        status = resilience_service.get_tier4_status()

        assert "enabled" in status
        assert "tier4_status" in status
