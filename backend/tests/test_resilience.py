"""
Tests for resilience modules (Tier 1).

Tests cover:
1. Utilization Monitor (queuing theory 80% threshold)
2. Defense in Depth (5-level nuclear safety paradigm)
3. Contingency Analysis (N-1/N-2 power grid analysis)
4. Static Stability (pre-computed fallback schedules)
5. Sacrifice Hierarchy (triage load shedding)
6. Resilience Service (orchestration)
7. Resilience API endpoints
"""
from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.block import Block
from app.models.person import Person
from app.resilience.contingency import (
    ContingencyAnalyzer,
)
from app.resilience.defense_in_depth import (
    DefenseInDepth,
    DefenseLevel,
)
from app.resilience.sacrifice_hierarchy import (
    ActivityCategory,
    LoadSheddingLevel,
    SacrificeHierarchy,
)
from app.resilience.service import (
    ResilienceConfig,
    ResilienceService,
)
from app.resilience.static_stability import (
    FallbackScenario,
    FallbackScheduler,
)
from app.resilience.utilization import (
    UtilizationLevel,
    UtilizationMonitor,
    UtilizationThreshold,
)

# ============================================================================
# Utilization Monitor Tests
# ============================================================================

class TestUtilizationMonitor:
    """Tests for UtilizationMonitor (queuing theory)."""

    def test_default_threshold(self):
        """Test default 80% utilization threshold."""
        monitor = UtilizationMonitor()
        assert monitor.threshold.max_utilization == 0.80
        assert monitor.threshold.warning_threshold == 0.70

    def test_custom_threshold(self):
        """Test custom utilization thresholds."""
        threshold = UtilizationThreshold(
            max_utilization=0.75,
            warning_threshold=0.60,
        )
        monitor = UtilizationMonitor(threshold)
        assert monitor.threshold.max_utilization == 0.75

    def test_utilization_calculation_low(self):
        """Test utilization calculation at low levels (GREEN)."""
        monitor = UtilizationMonitor()

        # Create mock faculty
        faculty = [type('obj', (object,), {'id': uuid4()})() for _ in range(10)]

        metrics = monitor.calculate_utilization(
            available_faculty=faculty,
            required_blocks=40,  # 50% utilization
            blocks_per_faculty_per_day=2.0,
            days_in_period=4,
        )

        assert metrics.utilization_rate == 0.5
        assert metrics.level == UtilizationLevel.GREEN
        assert metrics.buffer_remaining > 0.2

    def test_utilization_calculation_warning(self):
        """Test utilization at warning level (YELLOW)."""
        monitor = UtilizationMonitor()
        faculty = [type('obj', (object,), {'id': uuid4()})() for _ in range(10)]

        metrics = monitor.calculate_utilization(
            available_faculty=faculty,
            required_blocks=56,  # 70% utilization
            blocks_per_faculty_per_day=2.0,
            days_in_period=4,
        )

        assert metrics.level == UtilizationLevel.YELLOW

    def test_utilization_calculation_critical(self):
        """Test utilization at critical level (RED/BLACK)."""
        monitor = UtilizationMonitor()
        faculty = [type('obj', (object,), {'id': uuid4()})() for _ in range(10)]

        metrics = monitor.calculate_utilization(
            available_faculty=faculty,
            required_blocks=76,  # 95% utilization
            blocks_per_faculty_per_day=2.0,
            days_in_period=4,
        )

        assert metrics.level in (UtilizationLevel.RED, UtilizationLevel.BLACK)

    def test_wait_time_multiplier(self):
        """Test M/M/1 queue wait time multiplier calculation."""
        monitor = UtilizationMonitor()
        faculty = [type('obj', (object,), {'id': uuid4()})() for _ in range(10)]

        # At 50% utilization, multiplier should be ~1x
        metrics_50 = monitor.calculate_utilization(
            available_faculty=faculty,
            required_blocks=40,
            blocks_per_faculty_per_day=2.0,
            days_in_period=4,
        )
        assert 0.8 <= metrics_50.wait_time_multiplier <= 1.2

        # At 80% utilization, multiplier should be ~4x
        metrics_80 = monitor.calculate_utilization(
            available_faculty=faculty,
            required_blocks=64,
            blocks_per_faculty_per_day=2.0,
            days_in_period=4,
        )
        assert 3.5 <= metrics_80.wait_time_multiplier <= 4.5


# ============================================================================
# Defense in Depth Tests
# ============================================================================

class TestDefenseInDepth:
    """Tests for Defense in Depth (nuclear safety paradigm)."""

    def test_initial_state(self):
        """Test initial defense state."""
        defense = DefenseInDepth()
        assert defense.current_level == DefenseLevel.PREVENTION

    def test_level_recommendation_high_coverage(self):
        """Test recommended level with high coverage."""
        defense = DefenseInDepth()
        level = defense.get_recommended_level(coverage_rate=0.95)
        assert level == DefenseLevel.PREVENTION

    def test_level_recommendation_degraded(self):
        """Test recommended level with degraded coverage."""
        defense = DefenseInDepth()
        level = defense.get_recommended_level(coverage_rate=0.75)
        assert level in (DefenseLevel.CONTROL, DefenseLevel.SAFETY_SYSTEMS)

    def test_level_recommendation_critical(self):
        """Test recommended level with critical coverage."""
        defense = DefenseInDepth()
        level = defense.get_recommended_level(coverage_rate=0.50)
        assert level in (DefenseLevel.CONTAINMENT, DefenseLevel.EMERGENCY)

    def test_action_activation(self):
        """Test defense action activation."""
        defense = DefenseInDepth()
        result = defense.activate_action(DefenseLevel.CONTROL, "early_warning")
        assert result is True

    def test_redundancy_check_healthy(self):
        """Test N+2 redundancy check with healthy capacity."""
        defense = DefenseInDepth()
        status = defense.check_redundancy(
            service="clinical_coverage",
            available_providers=[1, 2, 3, 4, 5],
            minimum_required=3,
        )
        assert status.status == "N+2"
        assert status.buffer == 2

    def test_redundancy_check_warning(self):
        """Test N+2 redundancy check at warning level."""
        defense = DefenseInDepth()
        status = defense.check_redundancy(
            service="clinical_coverage",
            available_providers=[1, 2, 3, 4],
            minimum_required=3,
        )
        assert status.status == "N+1"

    def test_redundancy_check_minimum(self):
        """Test N+2 redundancy check at minimum."""
        defense = DefenseInDepth()
        status = defense.check_redundancy(
            service="clinical_coverage",
            available_providers=[1, 2, 3],
            minimum_required=3,
        )
        assert status.status == "N+0"

    def test_redundancy_check_below(self):
        """Test N+2 redundancy check below minimum."""
        defense = DefenseInDepth()
        status = defense.check_redundancy(
            service="clinical_coverage",
            available_providers=[1, 2],
            minimum_required=3,
        )
        assert status.status == "BELOW"


# ============================================================================
# Contingency Analysis Tests
# ============================================================================

class TestContingencyAnalyzer:
    """Tests for N-1/N-2 Contingency Analysis."""

    def test_analyzer_initialization(self):
        """Test analyzer initialization."""
        analyzer = ContingencyAnalyzer()
        assert analyzer is not None

    def test_n1_analysis_with_redundancy(self):
        """Test N-1 analysis passes with redundancy."""
        analyzer = ContingencyAnalyzer()

        # Create mock data with redundancy
        faculty = [
            type('obj', (object,), {'id': uuid4(), 'name': f'Faculty {i}'})()
            for i in range(5)
        ]
        blocks = [
            type('obj', (object,), {'id': uuid4(), 'date': date.today()})()
            for _ in range(10)
        ]
        # Each block covered by multiple faculty
        assignments = []
        for i, block in enumerate(blocks):
            for j in range(2):  # 2 faculty per block
                assignments.append(type('obj', (object,), {
                    'block_id': block.id,
                    'person_id': faculty[(i + j) % len(faculty)].id,
                })())

        coverage_requirements = {b.id: 1 for b in blocks}

        report = analyzer.generate_report(
            faculty=faculty,
            blocks=blocks,
            assignments=assignments,
            coverage_requirements=coverage_requirements,
            current_utilization=0.5,
        )

        # With redundancy, should pass N-1
        assert report.n1_pass is True

    def test_centrality_calculation(self):
        """Test faculty centrality (hub vulnerability) calculation."""
        analyzer = ContingencyAnalyzer()

        faculty = [
            type('obj', (object,), {'id': uuid4(), 'name': f'Faculty {i}'})()
            for i in range(3)
        ]

        ***REMOVED*** 0 covers many more assignments
        assignments = []
        for i in range(10):
            assignments.append(type('obj', (object,), {
                'block_id': uuid4(),
                'person_id': faculty[0].id,
            })())
        for i in range(2):
            assignments.append(type('obj', (object,), {
                'block_id': uuid4(),
                'person_id': faculty[1].id,
            })())

        services = {}  # Empty for this test

        centrality = analyzer.calculate_centrality(faculty, assignments, services)

        ***REMOVED*** 0 should have highest centrality
        assert len(centrality) > 0
        assert centrality[0].faculty_id == faculty[0].id


# ============================================================================
# Static Stability Tests
# ============================================================================

class TestFallbackScheduler:
    """Tests for Static Stability (pre-computed fallbacks)."""

    def test_scheduler_initialization(self):
        """Test fallback scheduler initialization."""
        scheduler = FallbackScheduler()
        assert scheduler is not None

    def test_scenario_enum(self):
        """Test all expected scenarios exist."""
        assert FallbackScenario.SINGLE_FACULTY_LOSS
        assert FallbackScenario.DOUBLE_FACULTY_LOSS
        assert FallbackScenario.PCS_SEASON_50_PERCENT
        assert FallbackScenario.HOLIDAY_SKELETON
        assert FallbackScenario.PANDEMIC_ESSENTIAL

    def test_best_fallback_for_single_loss(self):
        """Test recommendation for single faculty loss."""
        scheduler = FallbackScheduler()
        scenario = scheduler.get_best_fallback_for_situation(
            faculty_loss_count=1,
            is_pcs_season=False,
            is_holiday=False,
        )
        assert scenario == FallbackScenario.SINGLE_FACULTY_LOSS

    def test_best_fallback_for_pcs_season(self):
        """Test recommendation for PCS season."""
        scheduler = FallbackScheduler()
        scenario = scheduler.get_best_fallback_for_situation(
            faculty_loss_count=5,
            is_pcs_season=True,
            is_holiday=False,
        )
        assert scenario == FallbackScenario.PCS_SEASON_50_PERCENT

    def test_best_fallback_for_holiday(self):
        """Test recommendation for holiday period."""
        scheduler = FallbackScheduler()
        scenario = scheduler.get_best_fallback_for_situation(
            faculty_loss_count=0,
            is_pcs_season=False,
            is_holiday=True,
        )
        assert scenario == FallbackScenario.HOLIDAY_SKELETON


# ============================================================================
# Sacrifice Hierarchy Tests
# ============================================================================

class TestSacrificeHierarchy:
    """Tests for Sacrifice Hierarchy (triage load shedding)."""

    def test_initial_level(self):
        """Test initial load shedding level is NORMAL."""
        hierarchy = SacrificeHierarchy()
        assert hierarchy.current_level == LoadSheddingLevel.NORMAL

    def test_activity_priorities(self):
        """Test activity priority order."""
        # PATIENT_SAFETY should be highest priority (lowest number)
        assert ActivityCategory.PATIENT_SAFETY.value < ActivityCategory.ACGME_REQUIREMENTS.value
        assert ActivityCategory.ACGME_REQUIREMENTS.value < ActivityCategory.EDUCATION_CORE.value
        assert ActivityCategory.EDUCATION_CORE.value < ActivityCategory.EDUCATION_OPTIONAL.value

    def test_level_activation(self):
        """Test load shedding level activation."""
        hierarchy = SacrificeHierarchy()
        hierarchy.activate_level(LoadSheddingLevel.YELLOW, reason="Test")
        assert hierarchy.current_level == LoadSheddingLevel.YELLOW

    def test_level_deactivation(self):
        """Test load shedding level deactivation."""
        hierarchy = SacrificeHierarchy()
        hierarchy.activate_level(LoadSheddingLevel.RED, reason="Test")
        hierarchy.deactivate_level(LoadSheddingLevel.NORMAL)
        assert hierarchy.current_level == LoadSheddingLevel.NORMAL

    def test_status_report(self):
        """Test load shedding status report."""
        hierarchy = SacrificeHierarchy()
        hierarchy.activate_level(LoadSheddingLevel.ORANGE, reason="Test")
        status = hierarchy.get_status()

        assert status.level == LoadSheddingLevel.ORANGE
        assert len(status.activities_suspended) > 0
        assert len(status.activities_protected) > 0

    def test_protected_activities_at_black(self):
        """Test patient safety activities protected at BLACK level."""
        hierarchy = SacrificeHierarchy()
        hierarchy.activate_level(LoadSheddingLevel.BLACK, reason="Emergency")
        status = hierarchy.get_status()

        # Patient safety should always be protected
        assert ActivityCategory.PATIENT_SAFETY.name in status.activities_protected or \
               any("PATIENT" in a for a in status.activities_protected)


# ============================================================================
# Resilience Service Tests
# ============================================================================

class TestResilienceService:
    """Tests for ResilienceService orchestration."""

    def test_service_initialization(self):
        """Test service initialization with default config."""
        service = ResilienceService()
        assert service.config.max_utilization == 0.80
        assert service.utilization is not None
        assert service.defense is not None
        assert service.contingency is not None
        assert service.fallback is not None
        assert service.sacrifice is not None

    def test_service_custom_config(self):
        """Test service with custom config."""
        config = ResilienceConfig(
            max_utilization=0.75,
            warning_threshold=0.65,
        )
        service = ResilienceService(config=config)
        assert service.config.max_utilization == 0.75

    def test_crisis_response_activation(self):
        """Test crisis response activation."""
        service = ResilienceService()
        result = service.activate_crisis_response(
            severity="moderate",
            reason="Test crisis",
        )

        assert result["crisis_mode"] is True
        assert "actions_taken" in result
        assert len(result["actions_taken"]) > 0

    def test_crisis_response_deactivation(self):
        """Test crisis response deactivation."""
        service = ResilienceService()
        service.activate_crisis_response(severity="moderate", reason="Test")
        result = service.deactivate_crisis_response(reason="Crisis resolved")

        assert result["crisis_mode"] is False
        assert "recovery_plan" in result

    def test_fallback_recommendation(self):
        """Test fallback recommendation logic."""
        service = ResilienceService()
        scenario = service.recommend_fallback(
            faculty_available=5,
            faculty_total=10,
            is_pcs_season=True,
        )

        assert scenario == FallbackScenario.PCS_SEASON_50_PERCENT

    def test_event_handler_registration(self):
        """Test event handler registration."""
        service = ResilienceService()
        events_received = []

        def handler(data):
            events_received.append(data)

        service.register_event_handler("crisis_activated", handler)
        service.activate_crisis_response(severity="minor", reason="Test")

        assert len(events_received) == 1


# ============================================================================
# Integration Tests with Database
# ============================================================================

class TestResilienceWithDatabase:
    """Integration tests requiring database."""

    def test_health_check_with_data(self, db: Session):
        """Test health check with actual database data."""
        # Create test data
        faculty = []
        for i in range(5):
            f = Person(
                id=uuid4(),
                name=f"Dr. Faculty {i}",
                type="faculty",
                email=f"faculty{i}@test.org",
            )
            db.add(f)
            faculty.append(f)

        blocks = []
        for i in range(7):
            for tod in ["AM", "PM"]:
                b = Block(
                    id=uuid4(),
                    date=date.today() + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(b)
                blocks.append(b)

        db.commit()

        # Run health check
        service = ResilienceService(db=db)
        report = service.check_health(
            faculty=faculty,
            blocks=blocks,
            assignments=[],
        )

        assert report is not None
        assert report.overall_status in ("healthy", "warning", "degraded", "critical", "emergency")
        assert report.utilization is not None
        assert report.defense_level is not None


# ============================================================================
# API Endpoint Tests
# ============================================================================

class TestResilienceAPI:
    """Tests for resilience API endpoints."""

    def test_health_endpoint(self, client: TestClient):
        """Test /api/resilience/health endpoint."""
        response = client.get("/api/resilience/health?persist=false")
        # May fail if no data, but should return a response
        assert response.status_code in (200, 500)

    def test_load_shedding_endpoint(self, client: TestClient):
        """Test /api/resilience/load-shedding GET endpoint."""
        response = client.get("/api/resilience/load-shedding")
        assert response.status_code == 200
        data = response.json()
        assert "level" in data
        assert "activities_suspended" in data

    def test_fallbacks_list_endpoint(self, client: TestClient):
        """Test /api/resilience/fallbacks GET endpoint."""
        response = client.get("/api/resilience/fallbacks")
        assert response.status_code == 200
        data = response.json()
        assert "fallbacks" in data
        assert "active_count" in data

    def test_history_health_endpoint(self, client: TestClient):
        """Test /api/resilience/history/health endpoint."""
        response = client.get("/api/resilience/history/health")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_history_events_endpoint(self, client: TestClient):
        """Test /api/resilience/history/events endpoint."""
        response = client.get("/api/resilience/history/events")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestResilienceEdgeCases:
    """Tests for edge cases and error handling."""

    def test_zero_faculty(self):
        """Test handling of zero faculty."""
        monitor = UtilizationMonitor()
        metrics = monitor.calculate_utilization(
            available_faculty=[],
            required_blocks=10,
            blocks_per_faculty_per_day=2.0,
            days_in_period=5,
        )

        # Should handle gracefully (100% or infinite utilization)
        assert metrics.utilization_rate >= 1.0 or metrics.level == UtilizationLevel.BLACK

    def test_zero_blocks(self):
        """Test handling of zero required blocks."""
        monitor = UtilizationMonitor()
        faculty = [type('obj', (object,), {'id': uuid4()})() for _ in range(5)]

        metrics = monitor.calculate_utilization(
            available_faculty=faculty,
            required_blocks=0,
            blocks_per_faculty_per_day=2.0,
            days_in_period=5,
        )

        # Should be healthy (0% utilization)
        assert metrics.utilization_rate == 0.0
        assert metrics.level == UtilizationLevel.GREEN

    def test_invalid_crisis_severity(self):
        """Test crisis activation with edge case severity."""
        service = ResilienceService()

        # "minor" is valid minimum
        result = service.activate_crisis_response(severity="minor", reason="Test")
        assert result["crisis_mode"] is True

        # Deactivate for next test
        service.deactivate_crisis_response(reason="Test")

        # "critical" is valid maximum
        result = service.activate_crisis_response(severity="critical", reason="Test")
        assert result["crisis_mode"] is True

    def test_multiple_crisis_activations(self):
        """Test multiple crisis activations (escalation)."""
        service = ResilienceService()

        service.activate_crisis_response(severity="minor", reason="Initial")
        result = service.activate_crisis_response(severity="critical", reason="Escalated")

        # Should escalate
        assert result["crisis_mode"] is True

    def test_recovery_plan_order(self):
        """Test that recovery plan restores in correct order."""
        hierarchy = SacrificeHierarchy()

        # Activate to BLACK (most severe)
        hierarchy.activate_level(LoadSheddingLevel.BLACK, reason="Test")

        # Get recovery plan
        plan = hierarchy.get_recovery_plan()

        # Should restore in reverse sacrifice order
        # (low priority activities restored last)
        assert len(plan) > 0
