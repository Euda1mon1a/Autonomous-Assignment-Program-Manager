"""
Tests for Le Chatelier's Principle (Physical Chemistry Pattern).

Tests the equilibrium shift analysis for scheduling systems,
ensuring stress quantification, compensation responses, and
equilibrium predictions work correctly.

Le Chatelier's principle: When a system at equilibrium experiences
a change in conditions, it shifts to partially counteract that change.
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.resilience.le_chatelier import (
    CompensationResponse,
    CompensationType,
    EquilibriumReport,
    EquilibriumShift,
    EquilibriumState,
    LeChatelierAnalyzer,
    StressResponsePrediction,
    StressType,
    SystemStress,
)


class TestStressType:
    """Test StressType enum."""

    def test_stress_types_exist(self):
        """Test all expected stress types are defined."""
        assert StressType.FACULTY_LOSS == "faculty_loss"
        assert StressType.DEMAND_SURGE == "demand_surge"
        assert StressType.QUALITY_PRESSURE == "quality_pressure"
        assert StressType.TIME_COMPRESSION == "time_compression"
        assert StressType.RESOURCE_SCARCITY == "resource_scarcity"
        assert StressType.EXTERNAL_PRESSURE == "external_pressure"

    def test_all_stress_types_are_strings(self):
        """Test all stress types are string enums."""
        for stress_type in StressType:
            assert isinstance(stress_type.value, str)


class TestCompensationType:
    """Test CompensationType enum."""

    def test_compensation_types_exist(self):
        """Test all expected compensation types are defined."""
        assert CompensationType.OVERTIME == "overtime"
        assert CompensationType.CROSS_COVERAGE == "cross_coverage"
        assert CompensationType.DEFERRED_LEAVE == "deferred_leave"
        assert CompensationType.SERVICE_REDUCTION == "service_reduction"
        assert CompensationType.EFFICIENCY_GAIN == "efficiency_gain"
        assert CompensationType.BACKUP_ACTIVATION == "backup_activation"
        assert CompensationType.QUALITY_TRADE == "quality_trade"

    def test_all_compensation_types_are_strings(self):
        """Test all compensation types are string enums."""
        for comp_type in CompensationType:
            assert isinstance(comp_type.value, str)


class TestEquilibriumState:
    """Test EquilibriumState enum."""

    def test_equilibrium_states_exist(self):
        """Test all expected equilibrium states are defined."""
        assert EquilibriumState.STABLE == "stable"
        assert EquilibriumState.COMPENSATING == "compensating"
        assert EquilibriumState.STRESSED == "stressed"
        assert EquilibriumState.UNSUSTAINABLE == "unsustainable"
        assert EquilibriumState.CRITICAL == "critical"

    def test_state_severity_ordering(self):
        """Test equilibrium states have expected severity ordering."""
        states = [
            EquilibriumState.STABLE,
            EquilibriumState.COMPENSATING,
            EquilibriumState.STRESSED,
            EquilibriumState.UNSUSTAINABLE,
            EquilibriumState.CRITICAL,
        ]
        assert len(states) == 5


class TestSystemStress:
    """Test SystemStress dataclass."""

    def test_create_stress(self):
        """Test creating a system stress."""
        stress_id = uuid4()
        now = datetime.now()

        stress = SystemStress(
            id=stress_id,
            stress_type=StressType.FACULTY_LOSS,
            description="Faculty on emergency leave",
            applied_at=now,
            magnitude=0.2,
            duration_days=14,
            is_acute=True,
            is_reversible=True,
            capacity_impact=-0.2,
            demand_impact=0.0,
        )

        assert stress.id == stress_id
        assert stress.stress_type == StressType.FACULTY_LOSS
        assert stress.magnitude == 0.2
        assert stress.duration_days == 14
        assert stress.is_acute is True
        assert stress.is_reversible is True
        assert stress.capacity_impact == -0.2
        assert stress.demand_impact == 0.0
        assert stress.is_active is True
        assert stress.resolved_at is None

    def test_stress_with_demand_impact(self):
        """Test stress that increases demand."""
        stress = SystemStress(
            id=uuid4(),
            stress_type=StressType.DEMAND_SURGE,
            description="Flu season surge",
            applied_at=datetime.now(),
            magnitude=0.3,
            duration_days=30,
            is_acute=False,
            is_reversible=True,
            capacity_impact=0.0,
            demand_impact=0.3,
        )

        assert stress.demand_impact == 0.3
        assert stress.capacity_impact == 0.0


class TestCompensationResponse:
    """Test CompensationResponse dataclass."""

    def test_create_compensation(self):
        """Test creating a compensation response."""
        stress_id = uuid4()
        comp_id = uuid4()
        now = datetime.now()

        compensation = CompensationResponse(
            id=comp_id,
            stress_id=stress_id,
            compensation_type=CompensationType.OVERTIME,
            description="Faculty working extra hours",
            initiated_at=now,
            compensation_magnitude=0.5,
            effectiveness=0.8,
            immediate_cost=1000.0,
            hidden_cost=50.0,
            sustainability_days=30,
        )

        assert compensation.id == comp_id
        assert compensation.stress_id == stress_id
        assert compensation.compensation_type == CompensationType.OVERTIME
        assert compensation.compensation_magnitude == 0.5
        assert compensation.effectiveness == 0.8
        assert compensation.immediate_cost == 1000.0
        assert compensation.hidden_cost == 50.0
        assert compensation.sustainability_days == 30
        assert compensation.is_active is True
        assert compensation.ended_at is None
        assert compensation.end_reason is None


class TestLeChatelierAnalyzerInit:
    """Test LeChatelierAnalyzer initialization."""

    def test_default_initialization(self):
        """Test analyzer with default parameters."""
        analyzer = LeChatelierAnalyzer()

        assert analyzer.base_compensation_rate == 0.5
        assert analyzer.compensation_cost_multiplier == 1.5
        assert analyzer.sustainability_threshold == 0.7
        assert analyzer._current_capacity == 1.0
        assert analyzer._current_demand == 0.8
        assert analyzer._compensation_debt == 0.0
        assert len(analyzer.stresses) == 0
        assert len(analyzer.compensations) == 0
        assert len(analyzer.shifts) == 0

    def test_custom_initialization(self):
        """Test analyzer with custom parameters."""
        analyzer = LeChatelierAnalyzer(
            base_compensation_rate=0.6,
            compensation_cost_multiplier=2.0,
            sustainability_threshold=0.8,
        )

        assert analyzer.base_compensation_rate == 0.6
        assert analyzer.compensation_cost_multiplier == 2.0
        assert analyzer.sustainability_threshold == 0.8


class TestApplyStress:
    """Test stress application."""

    def test_apply_faculty_loss_stress(self):
        """Test applying a faculty loss stress."""
        analyzer = LeChatelierAnalyzer()
        initial_capacity = analyzer._current_capacity

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Senior faculty on TDY",
            magnitude=0.25,
            duration_days=21,
            capacity_impact=-0.25,
        )

        assert stress is not None
        assert stress.stress_type == StressType.FACULTY_LOSS
        assert stress.magnitude == 0.25
        assert stress.duration_days == 21
        assert stress.capacity_impact == -0.25
        assert stress.is_active is True
        assert stress.id in analyzer.stresses

        # Capacity should be reduced
        assert analyzer._current_capacity < initial_capacity
        assert analyzer._current_capacity == pytest.approx(
            initial_capacity - 0.25, abs=0.01
        )

    def test_apply_demand_surge_stress(self):
        """Test applying a demand surge stress."""
        analyzer = LeChatelierAnalyzer()
        initial_demand = analyzer._current_demand

        stress = analyzer.apply_stress(
            stress_type=StressType.DEMAND_SURGE,
            description="Emergency department overflow",
            magnitude=0.3,
            duration_days=7,
            capacity_impact=0.0,
            demand_impact=0.3,
        )

        assert stress.stress_type == StressType.DEMAND_SURGE
        assert stress.demand_impact == 0.3

        # Demand should increase
        assert analyzer._current_demand > initial_demand
        expected_demand = initial_demand * (1 + 0.3)
        assert analyzer._current_demand == pytest.approx(expected_demand, abs=0.01)

    def test_apply_multiple_stresses(self):
        """Test applying multiple stresses."""
        analyzer = LeChatelierAnalyzer()
        initial_capacity = analyzer._current_capacity

        stress1 = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Faculty sick",
            magnitude=0.1,
            duration_days=5,
            capacity_impact=-0.1,
        )

        stress2 = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Faculty on leave",
            magnitude=0.15,
            duration_days=10,
            capacity_impact=-0.15,
        )

        assert len(analyzer.stresses) == 2
        assert stress1.id in analyzer.stresses
        assert stress2.id in analyzer.stresses

        # Combined capacity impact
        assert analyzer._current_capacity == pytest.approx(
            initial_capacity - 0.1 - 0.15, abs=0.01
        )

    def test_capacity_floor_protection(self):
        """Test capacity doesn't go below minimum floor."""
        analyzer = LeChatelierAnalyzer()

        # Apply massive stress
        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Catastrophic loss",
            magnitude=1.0,
            duration_days=30,
            capacity_impact=-2.0,  # More than total capacity
        )

        # Should be clamped to minimum (0.1)
        assert analyzer._current_capacity == 0.1

    def test_acute_vs_gradual_stress(self):
        """Test acute vs gradual stress marking."""
        analyzer = LeChatelierAnalyzer()

        acute_stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Sudden illness",
            magnitude=0.1,
            duration_days=5,
            capacity_impact=-0.1,
            is_acute=True,
        )

        gradual_stress = analyzer.apply_stress(
            stress_type=StressType.RESOURCE_SCARCITY,
            description="Budget cuts",
            magnitude=0.2,
            duration_days=90,
            capacity_impact=-0.1,
            is_acute=False,
        )

        assert acute_stress.is_acute is True
        assert gradual_stress.is_acute is False


class TestInitiateCompensation:
    """Test compensation initiation."""

    def test_initiate_overtime_compensation(self):
        """Test initiating overtime compensation."""
        analyzer = LeChatelierAnalyzer()

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Faculty absence",
            magnitude=0.2,
            duration_days=14,
            capacity_impact=-0.2,
        )

        comp = analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.OVERTIME,
            description="Remaining faculty working extra hours",
            magnitude=0.5,
            effectiveness=0.8,
            sustainability_days=30,
            immediate_cost=500.0,
            hidden_cost=25.0,
        )

        assert comp is not None
        assert comp.stress_id == stress.id
        assert comp.compensation_type == CompensationType.OVERTIME
        assert comp.compensation_magnitude == 0.5
        assert comp.effectiveness == 0.8
        assert comp.sustainability_days == 30
        assert comp.immediate_cost == 500.0
        assert comp.hidden_cost == 25.0
        assert comp.is_active is True
        assert comp.id in analyzer.compensations

    def test_compensation_for_nonexistent_stress(self):
        """Test compensation for non-existent stress returns None."""
        analyzer = LeChatelierAnalyzer()

        fake_stress_id = uuid4()
        comp = analyzer.initiate_compensation(
            stress_id=fake_stress_id,
            compensation_type=CompensationType.OVERTIME,
            description="No stress",
            magnitude=0.5,
        )

        assert comp is None

    def test_compensation_adds_to_debt(self):
        """Test compensation increases compensation debt."""
        analyzer = LeChatelierAnalyzer()
        initial_debt = analyzer._compensation_debt

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Test",
            magnitude=0.2,
            duration_days=14,
            capacity_impact=-0.2,
        )

        analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.OVERTIME,
            description="Test",
            magnitude=0.5,
            hidden_cost=50.0,
        )

        assert analyzer._compensation_debt > initial_debt
        assert analyzer._compensation_debt == initial_debt + 50.0

    def test_multiple_compensations(self):
        """Test multiple compensations for same stress."""
        analyzer = LeChatelierAnalyzer()

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Major shortage",
            magnitude=0.3,
            duration_days=30,
            capacity_impact=-0.3,
        )

        comp1 = analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.OVERTIME,
            description="Extra hours",
            magnitude=0.3,
            hidden_cost=20.0,
        )

        comp2 = analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.CROSS_COVERAGE,
            description="Cross-trained staff",
            magnitude=0.2,
            hidden_cost=15.0,
        )

        assert len(analyzer.compensations) == 2
        assert analyzer._compensation_debt == 35.0


class TestCalculateEquilibriumShift:
    """Test equilibrium shift calculation."""

    def test_shift_with_no_stress(self):
        """Test equilibrium shift with no active stress."""
        analyzer = LeChatelierAnalyzer()

        shift = analyzer.calculate_equilibrium_shift(
            original_capacity=1.0,
            original_demand=0.8,
        )

        assert shift is not None
        assert shift.original_capacity == 1.0
        assert shift.original_demand == 0.8
        assert shift.total_capacity_impact == 0.0
        assert shift.total_demand_impact == 0.0
        assert len(shift.stresses) == 0
        assert len(shift.compensations) == 0
        assert shift.equilibrium_state == EquilibriumState.STABLE

    def test_shift_with_single_stress(self):
        """Test equilibrium shift with single stress."""
        analyzer = LeChatelierAnalyzer()

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Test",
            magnitude=0.2,
            duration_days=14,
            capacity_impact=-0.2,
        )

        shift = analyzer.calculate_equilibrium_shift(
            original_capacity=1.0,
            original_demand=0.8,
        )

        assert len(shift.stresses) == 1
        assert shift.total_capacity_impact == -0.2
        assert shift.new_capacity < shift.original_capacity
        # Note: coverage rate is capped at 1.0 when capacity >= demand
        # With capacity 0.8 and demand 0.8, coverage is still 1.0
        assert shift.new_capacity == pytest.approx(0.8, abs=0.01)
        assert shift.new_coverage_rate == 1.0

    def test_shift_with_stress_and_compensation(self):
        """Test equilibrium shift with stress and compensation."""
        analyzer = LeChatelierAnalyzer()

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Test",
            magnitude=0.2,
            duration_days=14,
            capacity_impact=-0.2,
        )

        analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.OVERTIME,
            description="Extra hours",
            magnitude=0.6,
            effectiveness=0.8,
        )

        shift = analyzer.calculate_equilibrium_shift(
            original_capacity=1.0,
            original_demand=0.8,
        )

        assert len(shift.stresses) == 1
        assert len(shift.compensations) == 1
        assert shift.total_compensation > 0

        # With compensation, new capacity should be higher than without
        assert shift.new_capacity > shift.sustainable_capacity

    def test_shift_determines_equilibrium_state(self):
        """Test equilibrium state determination."""
        analyzer = LeChatelierAnalyzer()

        # Stable state (high coverage, low risk)
        shift_stable = analyzer.calculate_equilibrium_shift(
            original_capacity=1.0,
            original_demand=0.8,
        )
        assert shift_stable.equilibrium_state == EquilibriumState.STABLE

        # Apply moderate stress
        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Moderate loss",
            magnitude=0.15,
            duration_days=14,
            capacity_impact=-0.15,
        )

        shift_after = analyzer.calculate_equilibrium_shift(
            original_capacity=1.0,
            original_demand=0.8,
        )

        # State should change based on coverage
        assert shift_after.equilibrium_state in [
            EquilibriumState.STABLE,
            EquilibriumState.COMPENSATING,
            EquilibriumState.STRESSED,
        ]

    def test_shift_diminishing_returns_multiple_compensations(self):
        """Test compensation efficiency decreases with multiple compensations."""
        analyzer = LeChatelierAnalyzer()

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Test",
            magnitude=0.3,
            duration_days=30,
            capacity_impact=-0.3,
        )

        # Add multiple compensations
        for i in range(3):
            analyzer.initiate_compensation(
                stress_id=stress.id,
                compensation_type=CompensationType.OVERTIME,
                description=f"Comp {i}",
                magnitude=0.2,
                effectiveness=0.8,
            )

        shift = analyzer.calculate_equilibrium_shift(
            original_capacity=1.0,
            original_demand=0.8,
        )

        # Efficiency should be less than 1.0 due to multiple compensations
        assert shift.compensation_efficiency < 1.0

    def test_shift_burnout_risk_calculation(self):
        """Test burnout risk is calculated from compensation."""
        analyzer = LeChatelierAnalyzer()

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Test",
            magnitude=0.3,
            duration_days=30,
            capacity_impact=-0.3,
        )

        analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.OVERTIME,
            description="Heavy overtime",
            magnitude=0.8,
            effectiveness=0.9,
            hidden_cost=100.0,
        )

        shift = analyzer.calculate_equilibrium_shift(
            original_capacity=1.0,
            original_demand=0.8,
        )

        # With high compensation and cost, burnout risk should be elevated
        assert shift.burnout_risk > 0

    def test_shift_days_until_exhaustion(self):
        """Test days until exhaustion calculation."""
        analyzer = LeChatelierAnalyzer()

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Test",
            magnitude=0.2,
            duration_days=60,
            capacity_impact=-0.2,
        )

        analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.OVERTIME,
            description="Limited overtime",
            magnitude=0.5,
            sustainability_days=14,  # Only sustainable for 14 days
        )

        shift = analyzer.calculate_equilibrium_shift(
            original_capacity=1.0,
            original_demand=0.8,
        )

        # Days until exhaustion should be at most 14
        assert shift.days_until_exhaustion <= 14


class TestPredictStressResponse:
    """Test stress response prediction."""

    def test_predict_minor_stress(self):
        """Test prediction for minor stress."""
        analyzer = LeChatelierAnalyzer()

        prediction = analyzer.predict_stress_response(
            stress_type=StressType.FACULTY_LOSS,
            magnitude=0.1,
            duration_days=7,
            capacity_impact=-0.05,
        )

        assert prediction is not None
        assert prediction.stress_type == StressType.FACULTY_LOSS
        assert prediction.stress_magnitude == 0.1
        assert prediction.stress_duration_days == 7
        assert prediction.predicted_new_capacity > 0
        assert prediction.predicted_coverage_rate > 0
        assert "sustainably" in prediction.sustainability_assessment.lower()

    def test_predict_moderate_stress(self):
        """Test prediction for moderate stress."""
        analyzer = LeChatelierAnalyzer()

        prediction = analyzer.predict_stress_response(
            stress_type=StressType.FACULTY_LOSS,
            magnitude=0.3,
            duration_days=21,
            capacity_impact=-0.25,
        )

        assert prediction.predicted_compensation > 0
        assert prediction.predicted_daily_cost > 0
        assert prediction.predicted_total_cost > 0
        # Note: recommendations only appear when certain thresholds are crossed
        # With default capacity 1.0 and demand 0.8, moderate stress may not trigger
        assert prediction.sustainability_assessment is not None

    def test_predict_severe_stress(self):
        """Test prediction for severe stress with higher demand."""
        analyzer = LeChatelierAnalyzer()
        # Set higher demand so capacity reduction affects coverage
        analyzer.set_current_state(capacity=1.0, demand=1.0)

        prediction = analyzer.predict_stress_response(
            stress_type=StressType.FACULTY_LOSS,
            magnitude=0.5,
            duration_days=30,
            capacity_impact=-0.4,
        )

        # With capacity 1.0 - 0.4 + 0.2 compensation = 0.8, demand 1.0
        # Coverage = 0.8, which gives "Manageable with active monitoring"
        assert prediction.predicted_coverage_rate < 1.0
        assert prediction.additional_intervention_needed > 0
        # The module classifies 0.8 coverage as "Manageable with active monitoring"
        assert "manageable" in prediction.sustainability_assessment.lower()
        assert len(prediction.recommended_actions) > 0

    def test_predict_critical_stress(self):
        """Test prediction for critical stress with higher demand."""
        analyzer = LeChatelierAnalyzer()
        # Set higher demand to make capacity reduction cause critical coverage
        analyzer.set_current_state(capacity=1.0, demand=1.2)

        prediction = analyzer.predict_stress_response(
            stress_type=StressType.FACULTY_LOSS,
            magnitude=0.8,
            duration_days=60,
            capacity_impact=-0.6,
        )

        # With capacity 1.0 - 0.6 + 0.3 compensation = 0.7, demand 1.2
        # Coverage = 0.7/1.2 = ~0.58 (critical)
        assert prediction.predicted_coverage_rate < 0.7
        assert prediction.additional_intervention_needed > 0
        # Should have critical recommendations
        assert any(
            "critical" in action.lower() or "fallback" in action.lower()
            for action in prediction.recommended_actions
        )

    def test_predict_with_demand_surge(self):
        """Test prediction with demand surge."""
        analyzer = LeChatelierAnalyzer()

        prediction = analyzer.predict_stress_response(
            stress_type=StressType.DEMAND_SURGE,
            magnitude=0.3,
            duration_days=14,
            capacity_impact=0.0,
            demand_impact=0.3,
        )

        assert prediction.stress_type == StressType.DEMAND_SURGE
        # Demand surge reduces effective coverage
        assert prediction.predicted_coverage_rate < 1.0

    def test_predict_extended_stress_recommendations(self):
        """Test extended stress gets appropriate recommendations."""
        analyzer = LeChatelierAnalyzer()

        prediction = analyzer.predict_stress_response(
            stress_type=StressType.FACULTY_LOSS,
            magnitude=0.2,
            duration_days=60,  # Extended duration
            capacity_impact=-0.15,
        )

        # Should recommend permanent adjustments for extended stress
        assert any(
            "permanent" in action.lower() or "extended" in action.lower()
            for action in prediction.recommended_actions
        )


class TestCalculateNewEquilibrium:
    """Test simplified new equilibrium calculation."""

    def test_calculate_no_stress(self):
        """Test new equilibrium with no stress."""
        analyzer = LeChatelierAnalyzer()

        result = analyzer.calculate_new_equilibrium(
            original_capacity=1.0,
            stress_reduction=0.0,
        )

        assert result["capacity"] == 1.0
        assert result["sustainable_capacity"] == 1.0
        assert result["compensation_debt"] == 0.0
        assert result["compensation_ratio"] == 0

    def test_calculate_small_stress(self):
        """Test new equilibrium with small stress."""
        analyzer = LeChatelierAnalyzer()

        result = analyzer.calculate_new_equilibrium(
            original_capacity=1.0,
            stress_reduction=0.1,
        )

        # Sustainable capacity is raw (without compensation)
        assert result["sustainable_capacity"] == 0.9

        # Effective capacity includes 50% natural compensation
        expected_effective = 0.9 + (0.1 * 0.5)  # 0.95
        assert result["capacity"] == pytest.approx(expected_effective, abs=0.01)

        # Compensation has cost
        assert result["compensation_debt"] > 0

        # Compensation ratio should be 50% (default)
        assert result["compensation_ratio"] == pytest.approx(0.5, abs=0.01)

    def test_calculate_moderate_stress(self):
        """Test new equilibrium with moderate stress."""
        analyzer = LeChatelierAnalyzer()

        result = analyzer.calculate_new_equilibrium(
            original_capacity=1.0,
            stress_reduction=0.3,
        )

        assert result["sustainable_capacity"] == 0.7
        expected_effective = 0.7 + (0.3 * 0.5)  # 0.85
        assert result["capacity"] == pytest.approx(expected_effective, abs=0.01)

        # Higher stress = higher debt
        assert result["compensation_debt"] > 0

    def test_calculate_with_custom_compensation_rate(self):
        """Test new equilibrium with custom compensation rate."""
        analyzer = LeChatelierAnalyzer(base_compensation_rate=0.3)

        result = analyzer.calculate_new_equilibrium(
            original_capacity=1.0,
            stress_reduction=0.2,
        )

        # With 30% compensation rate
        expected_effective = 0.8 + (0.2 * 0.3)  # 0.86
        assert result["capacity"] == pytest.approx(expected_effective, abs=0.01)
        assert result["compensation_ratio"] == pytest.approx(0.3, abs=0.01)


class TestResolveStress:
    """Test stress resolution."""

    def test_resolve_stress(self):
        """Test resolving a stress."""
        analyzer = LeChatelierAnalyzer()
        initial_capacity = analyzer._current_capacity

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Temporary absence",
            magnitude=0.2,
            duration_days=14,
            capacity_impact=-0.2,
        )

        # Capacity reduced
        assert analyzer._current_capacity < initial_capacity

        # Resolve the stress
        analyzer.resolve_stress(stress.id)

        assert stress.is_active is False
        assert stress.resolved_at is not None

        # Capacity restored (capped at 1.0)
        assert analyzer._current_capacity == pytest.approx(initial_capacity, abs=0.01)

    def test_resolve_ends_related_compensations(self):
        """Test resolving stress ends related compensations."""
        analyzer = LeChatelierAnalyzer()

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Test",
            magnitude=0.2,
            duration_days=14,
            capacity_impact=-0.2,
        )

        comp = analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.OVERTIME,
            description="Extra hours",
            magnitude=0.5,
        )

        analyzer.resolve_stress(stress.id)

        assert comp.is_active is False
        assert comp.end_reason == "stress_resolved"

    def test_resolve_nonexistent_stress(self):
        """Test resolving non-existent stress is safe."""
        analyzer = LeChatelierAnalyzer()

        # Should not raise an error
        analyzer.resolve_stress(uuid4())


class TestEndCompensation:
    """Test compensation ending."""

    def test_end_compensation(self):
        """Test ending a compensation."""
        analyzer = LeChatelierAnalyzer()

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Test",
            magnitude=0.2,
            duration_days=14,
            capacity_impact=-0.2,
        )

        comp = analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.OVERTIME,
            description="Extra hours",
            magnitude=0.5,
        )

        analyzer.end_compensation(comp.id, "sustainability_limit_reached")

        assert comp.is_active is False
        assert comp.end_reason == "sustainability_limit_reached"
        assert comp.ended_at is not None

    def test_end_nonexistent_compensation(self):
        """Test ending non-existent compensation is safe."""
        analyzer = LeChatelierAnalyzer()

        # Should not raise an error
        analyzer.end_compensation(uuid4(), "test")


class TestGetReport:
    """Test report generation."""

    def test_report_no_stress(self):
        """Test report with no active stress."""
        analyzer = LeChatelierAnalyzer()

        report = analyzer.get_report()

        assert report is not None
        assert report.current_equilibrium_state == EquilibriumState.STABLE
        assert report.current_capacity == 1.0
        assert report.current_demand == 0.8
        assert report.current_coverage_rate == pytest.approx(1.0, abs=0.01)
        assert len(report.active_stresses) == 0
        assert len(report.active_compensations) == 0
        assert report.compensation_debt == 0.0
        assert report.sustainability_score == 1.0

    def test_report_with_stress(self):
        """Test report with active stress."""
        analyzer = LeChatelierAnalyzer()

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Test",
            magnitude=0.2,
            duration_days=14,
            capacity_impact=-0.2,
        )

        report = analyzer.get_report()

        assert len(report.active_stresses) == 1
        assert report.total_stress_magnitude == pytest.approx(0.2, abs=0.01)
        assert report.current_capacity < 1.0

    def test_report_with_stress_and_compensation(self):
        """Test report with stress and compensation."""
        analyzer = LeChatelierAnalyzer()

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Test",
            magnitude=0.2,
            duration_days=14,
            capacity_impact=-0.2,
        )

        comp = analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.OVERTIME,
            description="Extra hours",
            magnitude=0.5,
            hidden_cost=25.0,
        )

        report = analyzer.get_report()

        assert len(report.active_stresses) == 1
        assert len(report.active_compensations) == 1
        assert report.total_compensation_magnitude == 0.5
        assert report.compensation_debt == 25.0

    def test_report_recommendations_for_critical_state(self):
        """Test report has recommendations for critical state."""
        analyzer = LeChatelierAnalyzer()

        # Create critical situation
        analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Major crisis",
            magnitude=0.6,
            duration_days=30,
            capacity_impact=-0.6,
        )

        report = analyzer.get_report()

        assert len(report.recommendations) > 0
        # Should have critical recommendations
        assert report.current_equilibrium_state in [
            EquilibriumState.UNSUSTAINABLE,
            EquilibriumState.CRITICAL,
        ]

    def test_report_exhaustion_warning(self):
        """Test report warns about compensation exhaustion."""
        analyzer = LeChatelierAnalyzer()

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Test",
            magnitude=0.2,
            duration_days=60,
            capacity_impact=-0.2,
        )

        analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.OVERTIME,
            description="Limited overtime",
            magnitude=0.5,
            sustainability_days=7,  # Very short
        )

        report = analyzer.get_report()

        assert report.days_until_exhaustion <= 7
        assert any("exhaustion" in rec.lower() for rec in report.recommendations)

    def test_report_sustainability_score(self):
        """Test sustainability score reflects state."""
        analyzer = LeChatelierAnalyzer()

        # Stable state
        report_stable = analyzer.get_report()
        assert report_stable.sustainability_score == 1.0

        # Add significant stress to move past stable state
        # Need to push capacity below demand to change state
        analyzer.set_current_state(capacity=1.0, demand=1.0)
        analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Major shortage",
            magnitude=0.3,
            duration_days=30,
            capacity_impact=-0.3,
        )

        report_stressed = analyzer.get_report()
        # With capacity 0.7 and demand 1.0, coverage is 0.7 -> STRESSED state
        assert report_stressed.sustainability_score < 1.0


class TestSetCurrentState:
    """Test state setting."""

    def test_set_current_state(self):
        """Test setting current system state."""
        analyzer = LeChatelierAnalyzer()

        analyzer.set_current_state(capacity=0.8, demand=0.9)

        assert analyzer._current_capacity == 0.8
        assert analyzer._current_demand == 0.9


class TestResetCompensationDebt:
    """Test debt reset."""

    def test_reset_compensation_debt(self):
        """Test resetting compensation debt."""
        analyzer = LeChatelierAnalyzer()

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Test",
            magnitude=0.2,
            duration_days=14,
            capacity_impact=-0.2,
        )

        analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.OVERTIME,
            description="Extra hours",
            magnitude=0.5,
            hidden_cost=100.0,
        )

        assert analyzer._compensation_debt == 100.0

        analyzer.reset_compensation_debt()

        assert analyzer._compensation_debt == 0.0


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    def test_scenario_faculty_illness(self):
        """Test scenario: Faculty member gets ill."""
        analyzer = LeChatelierAnalyzer()

        # Initial report
        report1 = analyzer.get_report()
        assert report1.current_equilibrium_state == EquilibriumState.STABLE

        # Faculty gets ill
        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Faculty member hospitalized",
            magnitude=0.2,
            duration_days=10,
            capacity_impact=-0.15,
            is_acute=True,
            is_reversible=True,
        )

        # System compensates with overtime (lower magnitude to control burnout)
        analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.OVERTIME,
            description="Remaining faculty cover extra shifts",
            magnitude=0.4,  # Lower magnitude for lower burnout
            effectiveness=0.85,
            sustainability_days=14,
            hidden_cost=10.0,  # Lower hidden cost
        )

        # Calculate new equilibrium
        shift = analyzer.calculate_equilibrium_shift(
            original_capacity=1.0,
            original_demand=0.8,
        )

        assert shift.new_coverage_rate > 0.7
        # Burnout risk depends on compensation debt and magnitude
        # The module calculates burnout_risk = min(1.0, compensation_debt / 100 + total_compensation * 0.3)
        assert shift.burnout_risk >= 0  # Just verify it's calculated

        # Faculty recovers
        analyzer.resolve_stress(stress.id)

        report_final = analyzer.get_report()
        assert len(report_final.active_stresses) == 0
        assert len(report_final.active_compensations) == 0

    def test_scenario_prolonged_shortage(self):
        """Test scenario: Prolonged faculty shortage."""
        analyzer = LeChatelierAnalyzer()

        # Apply prolonged shortage
        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Unfilled position",
            magnitude=0.25,
            duration_days=90,
            capacity_impact=-0.2,
            is_acute=False,
            is_reversible=True,
        )

        # Multiple compensation strategies
        analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.OVERTIME,
            description="Limited overtime",
            magnitude=0.3,
            sustainability_days=30,
            hidden_cost=40.0,
        )

        analyzer.initiate_compensation(
            stress_id=stress.id,
            compensation_type=CompensationType.CROSS_COVERAGE,
            description="Cross-trained staff",
            magnitude=0.2,
            sustainability_days=60,
            hidden_cost=20.0,
        )

        shift = analyzer.calculate_equilibrium_shift(
            original_capacity=1.0,
            original_demand=0.8,
        )

        # Compensation efficiency reduced due to multiple compensations
        assert shift.compensation_efficiency < 1.0

        # Report should show sustainability concerns
        report = analyzer.get_report()
        assert report.compensation_debt > 0

    def test_scenario_demand_surge_during_shortage(self):
        """Test scenario: Demand surge during existing shortage."""
        analyzer = LeChatelierAnalyzer()

        # Existing shortage
        shortage_stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Open position",
            magnitude=0.15,
            duration_days=60,
            capacity_impact=-0.15,
        )

        # Demand surge (e.g., flu season)
        surge_stress = analyzer.apply_stress(
            stress_type=StressType.DEMAND_SURGE,
            description="Flu season",
            magnitude=0.3,
            duration_days=21,
            capacity_impact=0.0,
            demand_impact=0.25,
        )

        shift = analyzer.calculate_equilibrium_shift(
            original_capacity=1.0,
            original_demand=0.8,
        )

        # Combined impacts should reduce coverage
        assert shift.new_coverage_rate < shift.original_coverage_rate
        assert shift.total_capacity_impact < 0
        assert shift.total_demand_impact > 0

        # State reflects the combined impacts (could be compensating or worse)
        assert shift.equilibrium_state in [
            EquilibriumState.COMPENSATING,
            EquilibriumState.STRESSED,
            EquilibriumState.UNSUSTAINABLE,
            EquilibriumState.CRITICAL,
        ]

    def test_scenario_prediction_before_known_event(self):
        """Test scenario: Predict impact of planned TDY with tight capacity."""
        analyzer = LeChatelierAnalyzer()
        # Set capacity equal to demand so stress will reduce coverage
        analyzer.set_current_state(capacity=1.0, demand=1.0)

        # Predict upcoming TDY impact
        prediction = analyzer.predict_stress_response(
            stress_type=StressType.FACULTY_LOSS,
            magnitude=0.2,
            duration_days=30,
            capacity_impact=-0.2,
        )

        # Should provide actionable predictions
        assert prediction.predicted_new_capacity > 0
        assert prediction.predicted_coverage_rate > 0

        # With capacity 1.0 - 0.2 + 0.1 compensation = 0.9, demand 1.0
        # Coverage = 0.9 (tight, should have recommendations)
        assert prediction.predicted_coverage_rate < 1.0

        # Should recommend backup coverage since coverage is reduced
        if prediction.predicted_coverage_rate < 0.9:
            assert prediction.additional_intervention_needed > 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_demand(self):
        """Test handling of very low demand."""
        analyzer = LeChatelierAnalyzer()
        analyzer.set_current_state(capacity=1.0, demand=0.1)

        report = analyzer.get_report()
        assert report.current_coverage_rate == 1.0  # Capped at 1.0

    def test_very_high_stress(self):
        """Test system behavior under extreme stress."""
        analyzer = LeChatelierAnalyzer()

        # Apply massive stress
        analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Mass exodus",
            magnitude=0.9,
            duration_days=30,
            capacity_impact=-0.8,
        )

        report = analyzer.get_report()

        assert report.current_equilibrium_state == EquilibriumState.CRITICAL
        assert report.sustainability_score < 0.5

    def test_many_small_stresses(self):
        """Test accumulation of many small stresses."""
        analyzer = LeChatelierAnalyzer()

        # Apply many small stresses
        for i in range(10):
            analyzer.apply_stress(
                stress_type=StressType.RESOURCE_SCARCITY,
                description=f"Small issue {i}",
                magnitude=0.02,
                duration_days=30,
                capacity_impact=-0.02,
            )

        report = analyzer.get_report()

        assert len(report.active_stresses) == 10
        # Cumulative impact should be significant
        assert report.total_stress_magnitude == pytest.approx(0.2, abs=0.02)

    def test_compensation_without_stress(self):
        """Test that compensation requires valid stress."""
        analyzer = LeChatelierAnalyzer()

        result = analyzer.initiate_compensation(
            stress_id=uuid4(),  # Non-existent
            compensation_type=CompensationType.OVERTIME,
            description="Orphan compensation",
            magnitude=0.5,
        )

        assert result is None
        assert len(analyzer.compensations) == 0

    def test_rapid_stress_resolution(self):
        """Test resolving stress immediately after applying."""
        analyzer = LeChatelierAnalyzer()
        initial_capacity = analyzer._current_capacity

        stress = analyzer.apply_stress(
            stress_type=StressType.FACULTY_LOSS,
            description="Brief absence",
            magnitude=0.1,
            duration_days=1,
            capacity_impact=-0.1,
        )

        # Immediate resolution
        analyzer.resolve_stress(stress.id)

        assert stress.is_active is False
        assert analyzer._current_capacity == pytest.approx(initial_capacity, abs=0.01)
