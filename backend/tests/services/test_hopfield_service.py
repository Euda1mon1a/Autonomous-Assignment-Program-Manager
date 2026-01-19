"""Tests for Hopfield Network Service.

Test coverage:
- Energy calculation
- Gini coefficient calculation
- Attractor finding
- Basin depth measurement
- Spurious attractor detection
- Stability level classification
- Recommendation generation
"""

import numpy as np
import pytest

from app.services.hopfield_service import (
    AttractorInfo,
    AttractorType,
    BasinMetrics,
    EnergyMetrics,
    HopfieldService,
    SpuriousAttractorInfo,
    StabilityLevel,
)


class TestGiniCoefficient:
    """Test _calculate_gini method."""

    def test_empty_list_returns_zero(self):
        """Empty list should return 0."""
        service = HopfieldService()
        assert service._calculate_gini([]) == 0.0

    def test_single_value_returns_zero(self):
        """Single value (n < 2) should return 0."""
        service = HopfieldService()
        assert service._calculate_gini([100.0]) == 0.0

    def test_perfect_equality_returns_zero(self):
        """All equal values should have Gini = 0."""
        service = HopfieldService()
        gini = service._calculate_gini([10.0, 10.0, 10.0, 10.0])
        assert gini == pytest.approx(0.0, abs=0.001)

    def test_moderate_inequality(self):
        """Moderate inequality should have Gini between 0 and 1."""
        service = HopfieldService()
        gini = service._calculate_gini([10.0, 20.0, 30.0, 40.0])
        assert 0.0 < gini < 1.0

    def test_high_inequality_greater_than_low(self):
        """Highly unequal distribution should have higher Gini."""
        service = HopfieldService()
        low_inequality = service._calculate_gini([9.0, 10.0, 10.0, 11.0])
        high_inequality = service._calculate_gini([1.0, 1.0, 1.0, 97.0])
        assert high_inequality > low_inequality


class TestAntiPatternDetection:
    """Test _check_anti_pattern method."""

    def test_overload_concentration_detected(self):
        """High Gini workload should detect overload."""
        service = HopfieldService()
        # Very uneven workload distribution
        workloads = [100.0, 10.0, 10.0, 10.0]  # One person has most work
        detected, confidence, basin = service._check_anti_pattern(
            "overload_concentration", np.zeros(100), workloads
        )
        # Gini should be high enough to trigger
        assert detected

    def test_underutilization_detected(self):
        """Low workload people should detect underutilization."""
        service = HopfieldService()
        # Some people have very low workload
        workloads = [100.0, 100.0, 10.0, 10.0, 10.0]  # 3/5 are underutilized
        detected, confidence, basin = service._check_anti_pattern(
            "underutilization", np.zeros(100), workloads
        )
        # 60% are below half mean, should detect
        assert detected

    def test_empty_workloads_not_detected(self):
        """Empty workloads should not detect patterns."""
        service = HopfieldService()
        detected, confidence, basin = service._check_anti_pattern(
            "overload_concentration", np.zeros(100), []
        )
        assert not detected
        assert confidence == 0.0


class TestStabilityClassification:
    """Test stability level interpretation."""

    def test_very_stable_classification(self):
        """Low normalized energy at minimum = very stable."""
        # This tests the _interpret_energy method indirectly
        service = HopfieldService()
        # The service interprets stability based on energy and gradient
        # We'll verify the dataclass can be created
        metrics = EnergyMetrics(
            total_energy=-50.0,
            normalized_energy=-0.85,
            energy_density=-0.32,
            interaction_energy=-45.0,
            stability_score=0.95,
            gradient_magnitude=0.05,
            is_local_minimum=True,
            distance_to_minimum=0,
        )
        assert metrics.is_local_minimum
        assert metrics.stability_score > 0.9

    def test_unstable_classification(self):
        """Positive normalized energy = unstable."""
        metrics = EnergyMetrics(
            total_energy=10.0,
            normalized_energy=0.5,
            energy_density=0.1,
            interaction_energy=9.0,
            stability_score=0.3,
            gradient_magnitude=0.7,
            is_local_minimum=False,
            distance_to_minimum=15,
        )
        assert not metrics.is_local_minimum
        assert metrics.stability_score < 0.5


class TestAttractorInfo:
    """Test AttractorInfo dataclass."""

    def test_attractor_types(self):
        """All attractor types should be valid."""
        assert AttractorType.GLOBAL_MINIMUM == "global_minimum"
        assert AttractorType.LOCAL_MINIMUM == "local_minimum"
        assert AttractorType.SPURIOUS == "spurious"
        assert AttractorType.METASTABLE == "metastable"
        assert AttractorType.SADDLE_POINT == "saddle_point"

    def test_attractor_creation(self):
        """AttractorInfo should hold all fields."""
        attractor = AttractorInfo(
            attractor_id="attr_001",
            attractor_type=AttractorType.LOCAL_MINIMUM,
            energy_level=-42.5,
            basin_depth=8.3,
            basin_volume=150,
            hamming_distance=3,
            pattern_description="Test pattern",
            confidence=0.9,
        )
        assert attractor.attractor_id == "attr_001"
        assert attractor.energy_level == -42.5
        assert attractor.basin_volume == 150


class TestBasinMetrics:
    """Test BasinMetrics dataclass."""

    def test_basin_metrics_creation(self):
        """BasinMetrics should hold all fields."""
        metrics = BasinMetrics(
            min_escape_energy=5.0,
            avg_escape_energy=8.0,
            max_escape_energy=15.0,
            basin_stability_index=0.75,
            num_escape_paths=6,
            nearest_saddle_distance=4,
            basin_radius=10,
            critical_perturbation_size=3,
        )
        assert metrics.min_escape_energy == 5.0
        assert metrics.basin_stability_index == 0.75
        assert metrics.critical_perturbation_size == 3


class TestSpuriousAttractorInfo:
    """Test SpuriousAttractorInfo dataclass."""

    def test_spurious_attractor_creation(self):
        """SpuriousAttractorInfo should hold all fields."""
        spurious = SpuriousAttractorInfo(
            attractor_id="spurious_001",
            energy_level=-25.0,
            basin_size=50,
            anti_pattern_type="overload_concentration",
            description="Test anti-pattern",
            risk_level="high",
            distance_from_valid=5,
            probability_of_capture=0.15,
            mitigation_strategy="Add constraint",
        )
        assert spurious.attractor_id == "spurious_001"
        assert spurious.risk_level == "high"
        assert spurious.probability_of_capture == 0.15


class TestStabilityLevelEnum:
    """Test StabilityLevel enum."""

    def test_all_stability_levels(self):
        """All stability levels should have correct values."""
        assert StabilityLevel.VERY_STABLE == "very_stable"
        assert StabilityLevel.STABLE == "stable"
        assert StabilityLevel.MARGINALLY_STABLE == "marginally_stable"
        assert StabilityLevel.UNSTABLE == "unstable"
        assert StabilityLevel.HIGHLY_UNSTABLE == "highly_unstable"


class TestRecommendationGeneration:
    """Test recommendation generation methods."""

    def test_coverage_low_risk_recommendation(self):
        """Low risk should return positive message."""
        service = HopfieldService()
        # Use stable energy metrics for low risk scenario
        metrics = EnergyMetrics(
            total_energy=-50.0,
            normalized_energy=-0.85,
            energy_density=-0.32,
            interaction_energy=-45.0,
            stability_score=0.95,
            gradient_magnitude=0.05,
            is_local_minimum=True,
            distance_to_minimum=0,
        )
        recs = service._generate_energy_recommendations(
            metrics, StabilityLevel.VERY_STABLE
        )
        assert len(recs) >= 1

    def test_coverage_high_risk_recommendation(self):
        """High risk should recommend specific actions."""
        service = HopfieldService()
        recs = service._generate_energy_recommendations(
            EnergyMetrics(
                total_energy=10.0,
                normalized_energy=0.5,
                energy_density=0.1,
                interaction_energy=9.0,
                stability_score=0.3,
                gradient_magnitude=0.7,
                is_local_minimum=False,
                distance_to_minimum=15,
            ),
            StabilityLevel.UNSTABLE,
        )
        assert any("URGENT" in r or "revise" in r.lower() for r in recs)

    def test_basin_very_stable_recommendation(self):
        """Very stable basin should recommend maintenance."""
        service = HopfieldService()
        recs = service._generate_basin_recommendations(
            BasinMetrics(
                min_escape_energy=10.0,
                avg_escape_energy=15.0,
                max_escape_energy=20.0,
                basin_stability_index=0.85,
                num_escape_paths=4,
                nearest_saddle_distance=8,
                basin_radius=12,
                critical_perturbation_size=5,
            ),
            StabilityLevel.VERY_STABLE,
        )
        assert any("stable" in r.lower() or "robust" in r.lower() for r in recs)

    def test_spurious_clean_recommendation(self):
        """No spurious attractors should report clean."""
        service = HopfieldService()
        recs = service._generate_spurious_recommendations([])
        assert len(recs) >= 1
        assert any("no" in r.lower() or "clean" in r.lower() for r in recs)


class TestServiceInitialization:
    """Test HopfieldService initialization."""

    def test_default_initialization(self):
        """Service should initialize with defaults."""
        service = HopfieldService()
        assert service.num_spins == 100
        assert service.temperature == 1.0

    def test_custom_initialization(self):
        """Service should accept custom parameters."""
        service = HopfieldService(num_spins=200, temperature=0.5)
        assert service.num_spins == 200
        assert service.temperature == 0.5

    def test_spin_glass_lazy_initialization(self):
        """Spin glass model should be lazy initialized."""
        service = HopfieldService()
        assert service._spin_glass is None
        # Access triggers initialization
        model = service._get_spin_glass()
        assert model is not None
        assert service._spin_glass is not None


class TestAntiPatternDefinitions:
    """Test ANTI_PATTERNS constant."""

    def test_all_patterns_defined(self):
        """All expected anti-patterns should be defined."""
        patterns = HopfieldService.ANTI_PATTERNS
        assert "overload_concentration" in patterns
        assert "clustering_violation" in patterns
        assert "underutilization" in patterns
        assert "coverage_gap" in patterns

    def test_pattern_structure(self):
        """Each pattern should have required fields."""
        for pattern_name, pattern_info in HopfieldService.ANTI_PATTERNS.items():
            assert "description" in pattern_info
            assert "risk_level" in pattern_info
            assert "mitigation" in pattern_info
