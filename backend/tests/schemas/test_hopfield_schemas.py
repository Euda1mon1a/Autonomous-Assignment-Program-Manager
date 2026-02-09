"""Tests for Hopfield network schemas (Pydantic validation and Field coverage)."""

import pytest
from pydantic import ValidationError

from app.schemas.hopfield_schemas import (
    AttractorType,
    StabilityLevel,
    HopfieldEnergyRequest,
    EnergyMetricsResponse,
    HopfieldEnergyResponse,
    NearbyAttractorsRequest,
    AttractorInfoResponse,
    NearbyAttractorsResponse,
    BasinDepthRequest,
    BasinMetricsResponse,
    BasinDepthResponse,
    SpuriousAttractorsRequest,
    SpuriousAttractorInfoResponse,
    SpuriousAttractorsResponse,
)


# ===========================================================================
# Enum Tests
# ===========================================================================


class TestAttractorType:
    def test_values(self):
        assert AttractorType.GLOBAL_MINIMUM.value == "global_minimum"
        assert AttractorType.LOCAL_MINIMUM.value == "local_minimum"
        assert AttractorType.SPURIOUS.value == "spurious"
        assert AttractorType.METASTABLE.value == "metastable"
        assert AttractorType.SADDLE_POINT.value == "saddle_point"

    def test_count(self):
        assert len(AttractorType) == 5

    def test_is_str(self):
        assert isinstance(AttractorType.GLOBAL_MINIMUM, str)


class TestStabilityLevel:
    def test_values(self):
        assert StabilityLevel.VERY_STABLE.value == "very_stable"
        assert StabilityLevel.STABLE.value == "stable"
        assert StabilityLevel.MARGINALLY_STABLE.value == "marginally_stable"
        assert StabilityLevel.UNSTABLE.value == "unstable"
        assert StabilityLevel.HIGHLY_UNSTABLE.value == "highly_unstable"

    def test_count(self):
        assert len(StabilityLevel) == 5

    def test_is_str(self):
        assert isinstance(StabilityLevel.VERY_STABLE, str)


# ===========================================================================
# HopfieldEnergyRequest Tests
# ===========================================================================


class TestHopfieldEnergyRequest:
    def test_valid(self):
        r = HopfieldEnergyRequest(start_date="2026-03-01", end_date="2026-03-31")
        assert r.schedule_id is None

    def test_with_schedule_id(self):
        r = HopfieldEnergyRequest(
            start_date="2026-03-01",
            end_date="2026-03-31",
            schedule_id="sched-42",
        )
        assert r.schedule_id == "sched-42"


# ===========================================================================
# EnergyMetricsResponse Tests
# ===========================================================================


class TestEnergyMetricsResponse:
    def _valid_kwargs(self):
        return {
            "total_energy": -5.0,
            "normalized_energy": 0.5,
            "energy_density": 0.1,
            "interaction_energy": -2.0,
            "stability_score": 0.8,
            "gradient_magnitude": 0.01,
            "is_local_minimum": True,
            "distance_to_minimum": 0,
        }

    def test_valid(self):
        r = EnergyMetricsResponse(**self._valid_kwargs())
        assert r.stability_score == 0.8
        assert r.is_local_minimum is True

    # --- normalized_energy ge=-1.0, le=1.0 ---

    def test_normalized_energy_boundaries(self):
        kw = self._valid_kwargs()
        kw["normalized_energy"] = -1.0
        r = EnergyMetricsResponse(**kw)
        assert r.normalized_energy == -1.0

        kw["normalized_energy"] = 1.0
        r = EnergyMetricsResponse(**kw)
        assert r.normalized_energy == 1.0

    def test_normalized_energy_below_min(self):
        kw = self._valid_kwargs()
        kw["normalized_energy"] = -1.1
        with pytest.raises(ValidationError):
            EnergyMetricsResponse(**kw)

    def test_normalized_energy_above_max(self):
        kw = self._valid_kwargs()
        kw["normalized_energy"] = 1.1
        with pytest.raises(ValidationError):
            EnergyMetricsResponse(**kw)

    # --- stability_score ge=0.0, le=1.0 ---

    def test_stability_score_boundaries(self):
        kw = self._valid_kwargs()
        kw["stability_score"] = 0.0
        r = EnergyMetricsResponse(**kw)
        assert r.stability_score == 0.0

        kw["stability_score"] = 1.0
        r = EnergyMetricsResponse(**kw)
        assert r.stability_score == 1.0

    def test_stability_score_negative(self):
        kw = self._valid_kwargs()
        kw["stability_score"] = -0.1
        with pytest.raises(ValidationError):
            EnergyMetricsResponse(**kw)

    def test_stability_score_above_one(self):
        kw = self._valid_kwargs()
        kw["stability_score"] = 1.1
        with pytest.raises(ValidationError):
            EnergyMetricsResponse(**kw)

    # --- gradient_magnitude ge=0.0 ---

    def test_gradient_magnitude_zero(self):
        kw = self._valid_kwargs()
        kw["gradient_magnitude"] = 0.0
        r = EnergyMetricsResponse(**kw)
        assert r.gradient_magnitude == 0.0

    def test_gradient_magnitude_negative(self):
        kw = self._valid_kwargs()
        kw["gradient_magnitude"] = -0.1
        with pytest.raises(ValidationError):
            EnergyMetricsResponse(**kw)

    # --- distance_to_minimum ge=0 ---

    def test_distance_to_minimum_zero(self):
        kw = self._valid_kwargs()
        kw["distance_to_minimum"] = 0
        r = EnergyMetricsResponse(**kw)
        assert r.distance_to_minimum == 0

    def test_distance_to_minimum_negative(self):
        kw = self._valid_kwargs()
        kw["distance_to_minimum"] = -1
        with pytest.raises(ValidationError):
            EnergyMetricsResponse(**kw)


# ===========================================================================
# HopfieldEnergyResponse Tests
# ===========================================================================


class TestHopfieldEnergyResponse:
    def _make_metrics(self):
        return EnergyMetricsResponse(
            total_energy=-5.0,
            normalized_energy=0.5,
            energy_density=0.1,
            interaction_energy=-2.0,
            stability_score=0.8,
            gradient_magnitude=0.01,
            is_local_minimum=True,
            distance_to_minimum=0,
        )

    def test_valid(self):
        r = HopfieldEnergyResponse(
            analyzed_at="2026-03-01T12:00:00Z",
            period_start="2026-03-01",
            period_end="2026-03-31",
            assignments_analyzed=100,
            metrics=self._make_metrics(),
            stability_level=StabilityLevel.STABLE,
            interpretation="Schedule is stable",
        )
        assert r.recommendations == []
        assert r.source == "backend"
        assert r.schedule_id is None

    def test_assignments_analyzed_zero(self):
        r = HopfieldEnergyResponse(
            analyzed_at="2026-03-01T12:00:00Z",
            period_start="2026-03-01",
            period_end="2026-03-31",
            assignments_analyzed=0,
            metrics=self._make_metrics(),
            stability_level=StabilityLevel.UNSTABLE,
            interpretation="No assignments",
        )
        assert r.assignments_analyzed == 0

    def test_assignments_analyzed_negative(self):
        with pytest.raises(ValidationError):
            HopfieldEnergyResponse(
                analyzed_at="2026-03-01T12:00:00Z",
                period_start="2026-03-01",
                period_end="2026-03-31",
                assignments_analyzed=-1,
                metrics=self._make_metrics(),
                stability_level=StabilityLevel.STABLE,
                interpretation="Test",
            )


# ===========================================================================
# NearbyAttractorsRequest Tests
# ===========================================================================


class TestNearbyAttractorsRequest:
    def test_defaults(self):
        r = NearbyAttractorsRequest(start_date="2026-03-01", end_date="2026-03-31")
        assert r.max_distance == 10

    def test_max_distance_boundaries(self):
        r = NearbyAttractorsRequest(
            start_date="2026-03-01", end_date="2026-03-31", max_distance=1
        )
        assert r.max_distance == 1
        r = NearbyAttractorsRequest(
            start_date="2026-03-01", end_date="2026-03-31", max_distance=50
        )
        assert r.max_distance == 50

    def test_max_distance_zero(self):
        with pytest.raises(ValidationError):
            NearbyAttractorsRequest(
                start_date="2026-03-01", end_date="2026-03-31", max_distance=0
            )

    def test_max_distance_above_max(self):
        with pytest.raises(ValidationError):
            NearbyAttractorsRequest(
                start_date="2026-03-01", end_date="2026-03-31", max_distance=51
            )


# ===========================================================================
# AttractorInfoResponse Tests
# ===========================================================================


class TestAttractorInfoResponse:
    def _valid_kwargs(self):
        return {
            "attractor_id": "att-1",
            "attractor_type": AttractorType.LOCAL_MINIMUM,
            "energy_level": -3.5,
            "basin_depth": 1.2,
            "basin_volume": 50,
            "hamming_distance": 3,
            "pattern_description": "Clustered assignments",
            "confidence": 0.85,
        }

    def test_valid(self):
        r = AttractorInfoResponse(**self._valid_kwargs())
        assert r.confidence == 0.85

    # --- basin_depth ge=0.0 ---

    def test_basin_depth_zero(self):
        kw = self._valid_kwargs()
        kw["basin_depth"] = 0.0
        r = AttractorInfoResponse(**kw)
        assert r.basin_depth == 0.0

    def test_basin_depth_negative(self):
        kw = self._valid_kwargs()
        kw["basin_depth"] = -0.1
        with pytest.raises(ValidationError):
            AttractorInfoResponse(**kw)

    # --- basin_volume ge=0 ---

    def test_basin_volume_zero(self):
        kw = self._valid_kwargs()
        kw["basin_volume"] = 0
        r = AttractorInfoResponse(**kw)
        assert r.basin_volume == 0

    def test_basin_volume_negative(self):
        kw = self._valid_kwargs()
        kw["basin_volume"] = -1
        with pytest.raises(ValidationError):
            AttractorInfoResponse(**kw)

    # --- hamming_distance ge=0 ---

    def test_hamming_distance_zero(self):
        kw = self._valid_kwargs()
        kw["hamming_distance"] = 0
        r = AttractorInfoResponse(**kw)
        assert r.hamming_distance == 0

    def test_hamming_distance_negative(self):
        kw = self._valid_kwargs()
        kw["hamming_distance"] = -1
        with pytest.raises(ValidationError):
            AttractorInfoResponse(**kw)

    # --- confidence ge=0.0, le=1.0 ---

    def test_confidence_boundaries(self):
        kw = self._valid_kwargs()
        kw["confidence"] = 0.0
        r = AttractorInfoResponse(**kw)
        assert r.confidence == 0.0

        kw["confidence"] = 1.0
        r = AttractorInfoResponse(**kw)
        assert r.confidence == 1.0

    def test_confidence_negative(self):
        kw = self._valid_kwargs()
        kw["confidence"] = -0.1
        with pytest.raises(ValidationError):
            AttractorInfoResponse(**kw)

    def test_confidence_above_one(self):
        kw = self._valid_kwargs()
        kw["confidence"] = 1.1
        with pytest.raises(ValidationError):
            AttractorInfoResponse(**kw)


# ===========================================================================
# NearbyAttractorsResponse Tests
# ===========================================================================


class TestNearbyAttractorsResponse:
    def test_valid(self):
        r = NearbyAttractorsResponse(
            analyzed_at="2026-03-01T12:00:00Z",
            current_state_energy=-5.0,
            attractors_found=0,
            global_minimum_identified=False,
            interpretation="No nearby attractors",
        )
        assert r.attractors == []
        assert r.recommendations == []
        assert r.source == "backend"
        assert r.current_basin_id is None

    def test_attractors_found_negative(self):
        with pytest.raises(ValidationError):
            NearbyAttractorsResponse(
                analyzed_at="2026-03-01T12:00:00Z",
                current_state_energy=-5.0,
                attractors_found=-1,
                global_minimum_identified=False,
                interpretation="Test",
            )


# ===========================================================================
# BasinDepthRequest Tests
# ===========================================================================


class TestBasinDepthRequest:
    def test_defaults(self):
        r = BasinDepthRequest(start_date="2026-03-01", end_date="2026-03-31")
        assert r.num_perturbations == 100

    def test_num_perturbations_boundaries(self):
        r = BasinDepthRequest(
            start_date="2026-03-01", end_date="2026-03-31", num_perturbations=10
        )
        assert r.num_perturbations == 10
        r = BasinDepthRequest(
            start_date="2026-03-01", end_date="2026-03-31", num_perturbations=1000
        )
        assert r.num_perturbations == 1000

    def test_num_perturbations_below_min(self):
        with pytest.raises(ValidationError):
            BasinDepthRequest(
                start_date="2026-03-01", end_date="2026-03-31", num_perturbations=9
            )

    def test_num_perturbations_above_max(self):
        with pytest.raises(ValidationError):
            BasinDepthRequest(
                start_date="2026-03-01", end_date="2026-03-31", num_perturbations=1001
            )


# ===========================================================================
# BasinMetricsResponse Tests
# ===========================================================================


class TestBasinMetricsResponse:
    def _valid_kwargs(self):
        return {
            "min_escape_energy": 0.5,
            "avg_escape_energy": 1.2,
            "max_escape_energy": 2.5,
            "basin_stability_index": 0.85,
            "num_escape_paths": 3,
            "nearest_saddle_distance": 5,
            "basin_radius": 8,
            "critical_perturbation_size": 4,
        }

    def test_valid(self):
        r = BasinMetricsResponse(**self._valid_kwargs())
        assert r.basin_stability_index == 0.85

    # --- escape energy fields ge=0.0 ---

    def test_escape_energy_zero(self):
        for field in ["min_escape_energy", "avg_escape_energy", "max_escape_energy"]:
            kw = self._valid_kwargs()
            kw[field] = 0.0
            r = BasinMetricsResponse(**kw)
            assert getattr(r, field) == 0.0

    def test_escape_energy_negative(self):
        for field in ["min_escape_energy", "avg_escape_energy", "max_escape_energy"]:
            kw = self._valid_kwargs()
            kw[field] = -0.1
            with pytest.raises(ValidationError):
                BasinMetricsResponse(**kw)

    # --- basin_stability_index ge=0.0, le=1.0 ---

    def test_basin_stability_index_boundaries(self):
        kw = self._valid_kwargs()
        kw["basin_stability_index"] = 0.0
        r = BasinMetricsResponse(**kw)
        assert r.basin_stability_index == 0.0

        kw["basin_stability_index"] = 1.0
        r = BasinMetricsResponse(**kw)
        assert r.basin_stability_index == 1.0

    def test_basin_stability_index_negative(self):
        kw = self._valid_kwargs()
        kw["basin_stability_index"] = -0.1
        with pytest.raises(ValidationError):
            BasinMetricsResponse(**kw)

    def test_basin_stability_index_above_one(self):
        kw = self._valid_kwargs()
        kw["basin_stability_index"] = 1.1
        with pytest.raises(ValidationError):
            BasinMetricsResponse(**kw)

    # --- integer fields ge=0 ---

    def test_integer_fields_zero(self):
        for field in [
            "num_escape_paths",
            "nearest_saddle_distance",
            "basin_radius",
            "critical_perturbation_size",
        ]:
            kw = self._valid_kwargs()
            kw[field] = 0
            r = BasinMetricsResponse(**kw)
            assert getattr(r, field) == 0

    def test_integer_fields_negative(self):
        for field in [
            "num_escape_paths",
            "nearest_saddle_distance",
            "basin_radius",
            "critical_perturbation_size",
        ]:
            kw = self._valid_kwargs()
            kw[field] = -1
            with pytest.raises(ValidationError):
                BasinMetricsResponse(**kw)


# ===========================================================================
# BasinDepthResponse Tests
# ===========================================================================


class TestBasinDepthResponse:
    def _make_metrics(self):
        return BasinMetricsResponse(
            min_escape_energy=0.5,
            avg_escape_energy=1.2,
            max_escape_energy=2.5,
            basin_stability_index=0.85,
            num_escape_paths=3,
            nearest_saddle_distance=5,
            basin_radius=8,
            critical_perturbation_size=4,
        )

    def test_valid(self):
        r = BasinDepthResponse(
            analyzed_at="2026-03-01T12:00:00Z",
            attractor_id="att-1",
            metrics=self._make_metrics(),
            stability_level=StabilityLevel.VERY_STABLE,
            is_robust=True,
            robustness_threshold=4,
            interpretation="Very robust schedule",
        )
        assert r.recommendations == []
        assert r.source == "backend"
        assert r.schedule_id is None

    def test_robustness_threshold_zero(self):
        r = BasinDepthResponse(
            analyzed_at="2026-03-01T12:00:00Z",
            attractor_id="att-1",
            metrics=self._make_metrics(),
            stability_level=StabilityLevel.HIGHLY_UNSTABLE,
            is_robust=False,
            robustness_threshold=0,
            interpretation="Not robust",
        )
        assert r.robustness_threshold == 0

    def test_robustness_threshold_negative(self):
        with pytest.raises(ValidationError):
            BasinDepthResponse(
                analyzed_at="2026-03-01T12:00:00Z",
                attractor_id="att-1",
                metrics=self._make_metrics(),
                stability_level=StabilityLevel.STABLE,
                is_robust=False,
                robustness_threshold=-1,
                interpretation="Test",
            )


# ===========================================================================
# SpuriousAttractorsRequest Tests
# ===========================================================================


class TestSpuriousAttractorsRequest:
    def test_defaults(self):
        r = SpuriousAttractorsRequest(start_date="2026-03-01", end_date="2026-03-31")
        assert r.search_radius == 20

    def test_search_radius_boundaries(self):
        r = SpuriousAttractorsRequest(
            start_date="2026-03-01", end_date="2026-03-31", search_radius=5
        )
        assert r.search_radius == 5
        r = SpuriousAttractorsRequest(
            start_date="2026-03-01", end_date="2026-03-31", search_radius=50
        )
        assert r.search_radius == 50

    def test_search_radius_below_min(self):
        with pytest.raises(ValidationError):
            SpuriousAttractorsRequest(
                start_date="2026-03-01", end_date="2026-03-31", search_radius=4
            )

    def test_search_radius_above_max(self):
        with pytest.raises(ValidationError):
            SpuriousAttractorsRequest(
                start_date="2026-03-01", end_date="2026-03-31", search_radius=51
            )


# ===========================================================================
# SpuriousAttractorInfoResponse Tests
# ===========================================================================


class TestSpuriousAttractorInfoResponse:
    def _valid_kwargs(self):
        return {
            "attractor_id": "spur-1",
            "energy_level": -1.0,
            "basin_size": 10,
            "anti_pattern_type": "clustering",
            "description": "Over-clustered assignments",
            "risk_level": "high",
            "distance_from_valid": 5,
            "probability_of_capture": 0.3,
            "mitigation_strategy": "Redistribute assignments",
        }

    def test_valid(self):
        r = SpuriousAttractorInfoResponse(**self._valid_kwargs())
        assert r.probability_of_capture == 0.3

    # --- basin_size ge=0 ---

    def test_basin_size_zero(self):
        kw = self._valid_kwargs()
        kw["basin_size"] = 0
        r = SpuriousAttractorInfoResponse(**kw)
        assert r.basin_size == 0

    def test_basin_size_negative(self):
        kw = self._valid_kwargs()
        kw["basin_size"] = -1
        with pytest.raises(ValidationError):
            SpuriousAttractorInfoResponse(**kw)

    # --- distance_from_valid ge=0 ---

    def test_distance_from_valid_zero(self):
        kw = self._valid_kwargs()
        kw["distance_from_valid"] = 0
        r = SpuriousAttractorInfoResponse(**kw)
        assert r.distance_from_valid == 0

    def test_distance_from_valid_negative(self):
        kw = self._valid_kwargs()
        kw["distance_from_valid"] = -1
        with pytest.raises(ValidationError):
            SpuriousAttractorInfoResponse(**kw)

    # --- probability_of_capture ge=0.0, le=1.0 ---

    def test_probability_of_capture_boundaries(self):
        kw = self._valid_kwargs()
        kw["probability_of_capture"] = 0.0
        r = SpuriousAttractorInfoResponse(**kw)
        assert r.probability_of_capture == 0.0

        kw["probability_of_capture"] = 1.0
        r = SpuriousAttractorInfoResponse(**kw)
        assert r.probability_of_capture == 1.0

    def test_probability_of_capture_negative(self):
        kw = self._valid_kwargs()
        kw["probability_of_capture"] = -0.1
        with pytest.raises(ValidationError):
            SpuriousAttractorInfoResponse(**kw)

    def test_probability_of_capture_above_one(self):
        kw = self._valid_kwargs()
        kw["probability_of_capture"] = 1.1
        with pytest.raises(ValidationError):
            SpuriousAttractorInfoResponse(**kw)


# ===========================================================================
# SpuriousAttractorsResponse Tests
# ===========================================================================


class TestSpuriousAttractorsResponse:
    def test_valid(self):
        r = SpuriousAttractorsResponse(
            analyzed_at="2026-03-01T12:00:00Z",
            spurious_attractors_found=0,
            total_basin_coverage=0.0,
            is_current_state_spurious=False,
            interpretation="No spurious attractors detected",
        )
        assert r.spurious_attractors == []
        assert r.recommendations == []
        assert r.source == "backend"
        assert r.highest_risk_attractor is None

    # --- spurious_attractors_found ge=0 ---

    def test_spurious_attractors_found_negative(self):
        with pytest.raises(ValidationError):
            SpuriousAttractorsResponse(
                analyzed_at="2026-03-01T12:00:00Z",
                spurious_attractors_found=-1,
                total_basin_coverage=0.0,
                is_current_state_spurious=False,
                interpretation="Test",
            )

    # --- total_basin_coverage ge=0.0, le=1.0 ---

    def test_total_basin_coverage_boundaries(self):
        r = SpuriousAttractorsResponse(
            analyzed_at="2026-03-01T12:00:00Z",
            spurious_attractors_found=0,
            total_basin_coverage=0.0,
            is_current_state_spurious=False,
            interpretation="Test",
        )
        assert r.total_basin_coverage == 0.0

        r = SpuriousAttractorsResponse(
            analyzed_at="2026-03-01T12:00:00Z",
            spurious_attractors_found=5,
            total_basin_coverage=1.0,
            is_current_state_spurious=True,
            interpretation="Test",
        )
        assert r.total_basin_coverage == 1.0

    def test_total_basin_coverage_negative(self):
        with pytest.raises(ValidationError):
            SpuriousAttractorsResponse(
                analyzed_at="2026-03-01T12:00:00Z",
                spurious_attractors_found=0,
                total_basin_coverage=-0.1,
                is_current_state_spurious=False,
                interpretation="Test",
            )

    def test_total_basin_coverage_above_one(self):
        with pytest.raises(ValidationError):
            SpuriousAttractorsResponse(
                analyzed_at="2026-03-01T12:00:00Z",
                spurious_attractors_found=0,
                total_basin_coverage=1.1,
                is_current_state_spurious=False,
                interpretation="Test",
            )
