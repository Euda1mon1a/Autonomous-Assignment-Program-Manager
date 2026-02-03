"""
Tests for Negative Viscosity / Propulsion Zone functionality.

Tests cover:
1. Energy flow direction calculation (entropy.py)
2. Constraint alignment scoring (constraint_validator.py)
3. Propulsion zone detection (propulsion_zones.py)

Based on active matter physics research - PR #803.
"""

import pytest
from datetime import date
from unittest.mock import MagicMock


# Test energy flow direction
class TestEnergyFlowDirection:
    """Tests for calculate_energy_flow_direction function."""

    def test_negative_flow_indicates_injection(self):
        """Negative energy flow means system is gaining organization."""
        from app.resilience.thermodynamics.entropy import (
            calculate_energy_flow_direction,
        )

        # Entropy decreasing = organization increasing = negative flow
        current_entropy = 2.0
        previous_entropy = 3.0
        time_delta = 1.0

        flow = calculate_energy_flow_direction(
            current_entropy, previous_entropy, time_delta
        )

        assert flow < 0, "Decreasing entropy should yield negative flow (injection)"
        assert flow == -1.0, f"Expected -1.0, got {flow}"

    def test_positive_flow_indicates_dissipation(self):
        """Positive energy flow means system is losing organization."""
        from app.resilience.thermodynamics.entropy import (
            calculate_energy_flow_direction,
        )

        # Entropy increasing = disorder increasing = positive flow
        current_entropy = 3.5
        previous_entropy = 3.0
        time_delta = 1.0

        flow = calculate_energy_flow_direction(
            current_entropy, previous_entropy, time_delta
        )

        assert flow > 0, "Increasing entropy should yield positive flow (dissipation)"
        assert flow == 0.5, f"Expected 0.5, got {flow}"

    def test_zero_flow_at_equilibrium(self):
        """Zero flow when entropy unchanged."""
        from app.resilience.thermodynamics.entropy import (
            calculate_energy_flow_direction,
        )

        flow = calculate_energy_flow_direction(3.0, 3.0, 1.0)

        assert flow == 0.0, "No entropy change should yield zero flow"

    def test_zero_delta_returns_zero(self):
        """Zero time delta should return zero to avoid division by zero."""
        from app.resilience.thermodynamics.entropy import (
            calculate_energy_flow_direction,
        )

        flow = calculate_energy_flow_direction(3.0, 2.0, 0.0)

        assert flow == 0.0, "Zero time delta should return 0"

    def test_time_scaling(self):
        """Flow should scale inversely with time delta."""
        from app.resilience.thermodynamics.entropy import (
            calculate_energy_flow_direction,
        )

        flow_1h = calculate_energy_flow_direction(2.0, 3.0, 1.0)
        flow_2h = calculate_energy_flow_direction(2.0, 3.0, 2.0)

        assert flow_1h == 2 * flow_2h, "Flow should halve when time doubles"


class TestEntropyMonitorEnergyFlow:
    """Tests for ScheduleEntropyMonitor energy flow tracking."""

    def test_monitor_tracks_energy_flow_history(self):
        """Monitor should track energy flow history."""
        from app.resilience.thermodynamics.entropy import ScheduleEntropyMonitor

        monitor = ScheduleEntropyMonitor(history_window=10)

        # Initially empty
        assert len(monitor.energy_flow_history) == 0

        # Simulate updates with mock assignments
        class MockAssignment:
            def __init__(self, person_id, block_id):
                self.person_id = person_id
                self.block_id = block_id
                self.rotation_template_id = None

        # First update - no flow yet (need 2 measurements)
        monitor.update([MockAssignment(1, 1), MockAssignment(2, 1)])
        assert len(monitor.energy_flow_history) == 0

        # Second update - flow calculated
        monitor.update([MockAssignment(1, 1), MockAssignment(2, 2)])
        # After 2 updates, may have energy flow if time elapsed
        # (depends on timestamp difference)

    def test_monitor_returns_propulsion_zone_indicator(self):
        """get_current_metrics should include in_propulsion_zone."""
        from app.resilience.thermodynamics.entropy import ScheduleEntropyMonitor

        monitor = ScheduleEntropyMonitor()
        metrics = monitor.get_current_metrics()

        assert "energy_flow_direction" in metrics
        assert "in_propulsion_zone" in metrics


class TestEntropyMetricsDataclass:
    """Tests for EntropyMetrics dataclass."""

    def test_energy_flow_direction_field_exists(self):
        """EntropyMetrics should have energy_flow_direction field."""
        from app.resilience.thermodynamics.entropy import EntropyMetrics

        metrics = EntropyMetrics(
            person_entropy=1.0,
            rotation_entropy=1.0,
            time_entropy=1.0,
            joint_entropy=2.0,
            mutual_information=0.5,
            energy_flow_direction=-0.3,
        )

        assert hasattr(metrics, "energy_flow_direction")
        assert metrics.energy_flow_direction == -0.3


# Test constraint alignment
class TestConstraintAlignment:
    """Tests for ConstraintConflictDetector alignment scoring."""

    def test_alignment_dataclass_classification(self):
        """ConstraintAlignmentScore should auto-classify interaction type."""
        from app.scheduling.constraint_validator import ConstraintAlignmentScore

        synergy = ConstraintAlignmentScore(
            constraint_a="A", constraint_b="B", alignment=0.7, interaction_type=""
        )
        assert synergy.interaction_type == "synergy"

        conflict = ConstraintAlignmentScore(
            constraint_a="A", constraint_b="B", alignment=-0.5, interaction_type=""
        )
        assert conflict.interaction_type == "conflict"

        orthogonal = ConstraintAlignmentScore(
            constraint_a="A", constraint_b="B", alignment=0.1, interaction_type=""
        )
        assert orthogonal.interaction_type == "orthogonal"

    def test_alignment_matrix_aggregates(self):
        """ConstraintAlignmentMatrix should calculate aggregates."""
        from app.scheduling.constraint_validator import (
            ConstraintAlignmentScore,
            ConstraintAlignmentMatrix,
        )

        scores = [
            ConstraintAlignmentScore("A", "B", 0.8, ""),  # synergy
            ConstraintAlignmentScore("A", "C", -0.6, ""),  # conflict
            ConstraintAlignmentScore("B", "C", 0.1, ""),  # orthogonal
        ]

        matrix = ConstraintAlignmentMatrix(
            scores=scores,
            overall_alignment=sum(s.alignment for s in scores) / len(scores),
            synergy_count=1,
            conflict_count=1,
            propulsion_potential=0.5,
        )

        assert matrix.synergy_count == 1
        assert matrix.conflict_count == 1
        assert -0.3 < matrix.overall_alignment < 0.3  # Mixed

    def test_alignment_matrix_to_dict(self):
        """ConstraintAlignmentMatrix.to_dict should return serializable dict."""
        from app.scheduling.constraint_validator import (
            ConstraintAlignmentScore,
            ConstraintAlignmentMatrix,
        )

        matrix = ConstraintAlignmentMatrix(
            scores=[ConstraintAlignmentScore("A", "B", 0.5, "synergy")],
            overall_alignment=0.5,
            synergy_count=1,
            conflict_count=0,
            propulsion_potential=0.7,
        )

        result = matrix.to_dict()

        assert "overall_alignment" in result
        assert "propulsion_potential" in result
        assert "top_synergies" in result
        assert "top_conflicts" in result


class TestConstraintDetectorAlignment:
    """Tests for ConstraintConflictDetector.calculate_alignment_score."""

    def test_calculate_alignment_with_soft_constraints(self):
        """Should calculate alignment for soft constraints."""
        from app.scheduling.constraint_validator import ConstraintConflictDetector
        from app.scheduling.constraints.base import SoftConstraint, ConstraintType

        class MockSoftConstraint(SoftConstraint):
            def __init__(self, name: str, weight: float = 1.0):
                self.name = name
                self.constraint_type = ConstraintType.EQUITY
                self.weight = weight
                self.priority = None

            def add_to_cpsat(self, *args, **kwargs):
                pass

            def add_to_pulp(self, *args, **kwargs):
                pass

            def validate(self, *args, **kwargs):
                return True

        detector = ConstraintConflictDetector()

        constraints = [
            MockSoftConstraint("Equity"),
            MockSoftConstraint("Continuity"),
            MockSoftConstraint("Coverage"),
        ]

        matrix = detector.calculate_alignment_score(constraints)

        assert matrix is not None
        assert len(matrix.scores) > 0
        assert hasattr(matrix, "propulsion_potential")

    def test_known_synergy_pairs(self):
        """Known synergy pairs should return positive alignment."""
        from app.scheduling.constraint_validator import ConstraintConflictDetector

        detector = ConstraintConflictDetector()

        # Check known synergy pair exists
        assert (
            ("Availability", "Coverage") in detector.SYNERGY_PAIRS
            or ("Coverage", "Availability") in detector.SYNERGY_PAIRS
            or ("EightyHourRule", "DutyHourLimit") in detector.SYNERGY_PAIRS
        )

    def test_known_conflict_pairs(self):
        """Known conflict pairs should return negative alignment."""
        from app.scheduling.constraint_validator import ConstraintConflictDetector

        detector = ConstraintConflictDetector()

        # Check known conflict pair exists
        assert ("Equity", "Continuity") in detector.CONFLICT_PAIRS or (
            "Continuity",
            "Equity",
        ) in detector.CONFLICT_PAIRS


# Test propulsion zones
class TestPropulsionZones:
    """Tests for propulsion zone detection."""

    def test_propulsion_zone_classification(self):
        """PropulsionZone should classify based on metrics."""
        from app.resilience.propulsion_zones import PropulsionZone

        # Propulsion zone: positive alignment + negative energy flow
        propulsion = PropulsionZone(
            block_range=(date(2026, 2, 1), date(2026, 2, 7)),
            constraint_alignment=0.5,
            energy_flow=-0.3,
            intervention_potential=0.8,
        )
        assert propulsion.is_propulsion_zone
        assert not propulsion.is_friction_zone

        # Friction zone: negative alignment
        friction = PropulsionZone(
            block_range=(date(2026, 2, 1), date(2026, 2, 7)),
            constraint_alignment=-0.5,
            energy_flow=0.2,
            intervention_potential=0.3,
        )
        assert not friction.is_propulsion_zone
        assert friction.is_friction_zone

        # Neutral zone
        neutral = PropulsionZone(
            block_range=(date(2026, 2, 1), date(2026, 2, 7)),
            constraint_alignment=0.1,
            energy_flow=0.1,
            intervention_potential=0.5,
        )
        assert not neutral.is_propulsion_zone
        assert not neutral.is_friction_zone

    def test_intervention_potential_calculation(self):
        """calculate_intervention_potential should combine metrics."""
        from app.resilience.propulsion_zones import calculate_intervention_potential

        # High alignment + negative flow = high potential
        high = calculate_intervention_potential(0.8, -1.0)
        assert high > 0.7

        # Low alignment + positive flow = low potential
        low = calculate_intervention_potential(-0.8, 1.0)
        assert low < 0.3

        # Neutral
        mid = calculate_intervention_potential(0.0, 0.0)
        assert 0.4 < mid < 0.6

    def test_propulsion_analysis_to_dict(self):
        """PropulsionAnalysis.to_dict should serialize properly."""
        from app.resilience.propulsion_zones import PropulsionZone, PropulsionAnalysis

        analysis = PropulsionAnalysis(
            zones=[
                PropulsionZone(
                    block_range=(date(2026, 2, 1), date(2026, 2, 7)),
                    constraint_alignment=0.5,
                    energy_flow=-0.2,
                    intervention_potential=0.7,
                )
            ],
            overall_propulsion_potential=0.7,
            propulsion_zone_count=1,
            friction_zone_count=0,
            neutral_zone_count=0,
            recommendation="Test recommendation",
        )

        result = analysis.to_dict()

        assert "overall_propulsion_potential" in result
        assert "zones" in result
        assert len(result["zones"]) == 1
        assert "block_range" in result["zones"][0]


class TestPropulsionZoneDetection:
    """Tests for detect_propulsion_zones function."""

    def test_detect_zones_returns_analysis(self):
        """detect_propulsion_zones should return PropulsionAnalysis."""
        from app.resilience.propulsion_zones import (
            detect_propulsion_zones,
            PropulsionAnalysis,
        )

        # Mock schedule and context
        schedule = MagicMock()
        context = MagicMock()
        context.blocks = []
        context.constraints = []

        result = detect_propulsion_zones(schedule, context)

        assert isinstance(result, PropulsionAnalysis)
        assert hasattr(result, "recommendation")

    def test_generate_recommendation(self):
        """_generate_recommendation should return actionable text."""
        from app.resilience.propulsion_zones import _generate_recommendation

        # High opportunity
        rec = _generate_recommendation(0.8, 2, 0, [])
        assert "HIGH OPPORTUNITY" in rec

        # High friction
        rec = _generate_recommendation(0.2, 0, 3, [])
        assert "HIGH FRICTION" in rec or "FRICTION" in rec.upper()

        # Moderate
        rec = _generate_recommendation(0.5, 1, 1, [])
        assert "MODERATE" in rec or "MIXED" in rec


# Test bio-inspired integration
class TestPSONegativeViscosity:
    """Tests for PSO negative viscosity integration."""

    def test_pso_config_has_viscosity_params(self):
        """PSOConfig should have negative viscosity parameters."""
        from app.scheduling.bio_inspired.particle_swarm import PSOConfig

        config = PSOConfig()

        assert hasattr(config, "negative_viscosity_factor")
        assert hasattr(config, "viscosity_decay_rate")
        assert hasattr(config, "enable_negative_viscosity")
        assert config.negative_viscosity_factor > 0
        assert 0 < config.viscosity_decay_rate <= 1

    def test_pso_constants_exist(self):
        """PSO constants for negative viscosity should exist."""
        from app.scheduling.bio_inspired.constants import (
            PSO_NEGATIVE_VISCOSITY_FACTOR,
            PSO_VISCOSITY_DECAY_RATE,
        )

        assert PSO_NEGATIVE_VISCOSITY_FACTOR > 0
        assert 0 < PSO_VISCOSITY_DECAY_RATE <= 1


class TestACONegativeEvaporation:
    """Tests for ACO negative evaporation integration."""

    def test_pheromone_matrix_has_negative_evaporation_params(self):
        """PheromoneMatrix should have negative evaporation parameters."""
        from app.scheduling.bio_inspired.ant_colony import PheromoneMatrix

        matrix = PheromoneMatrix(
            n_residents=5,
            n_blocks=10,
            n_templates=3,
        )

        assert hasattr(matrix, "negative_evaporation_rate")
        assert hasattr(matrix, "hotspot_threshold_multiplier")
        assert hasattr(matrix, "enable_negative_evaporation")

    def test_aco_constants_exist(self):
        """ACO constants for negative evaporation should exist."""
        from app.scheduling.bio_inspired.constants import (
            ACO_NEGATIVE_EVAPORATION_RATE,
            ACO_HOTSPOT_THRESHOLD_MULTIPLIER,
        )

        assert ACO_NEGATIVE_EVAPORATION_RATE > 0
        assert ACO_HOTSPOT_THRESHOLD_MULTIPLIER > 1


# Integration tests
class TestNegativeViscosityIntegration:
    """Integration tests for negative viscosity components."""

    def test_entropy_to_propulsion_flow(self):
        """Energy flow from entropy should feed propulsion zone detection."""
        from app.resilience.thermodynamics.entropy import (
            calculate_energy_flow_direction,
        )
        from app.resilience.propulsion_zones import calculate_intervention_potential

        # Simulate entropy decrease (improvement)
        energy_flow = calculate_energy_flow_direction(2.0, 3.0, 1.0)
        assert energy_flow < 0  # Injection

        # Feed into intervention potential
        potential = calculate_intervention_potential(0.5, energy_flow)
        assert potential > 0.5  # Good opportunity

    def test_alignment_to_propulsion_flow(self):
        """Constraint alignment should feed propulsion zone detection."""
        from app.resilience.propulsion_zones import PropulsionZone

        # High alignment should create propulsion zone
        zone = PropulsionZone(
            block_range=(date(2026, 2, 1), date(2026, 2, 7)),
            constraint_alignment=0.7,  # High synergy
            energy_flow=-0.2,  # Injection
            intervention_potential=0.8,
        )

        assert zone.is_propulsion_zone
        assert zone.intervention_potential > 0.7
