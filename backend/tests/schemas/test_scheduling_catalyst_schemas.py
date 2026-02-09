"""Tests for scheduling catalyst schemas (enums, Field bounds, defaults, nested models)."""

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.scheduling_catalyst import (
    BarrierTypeEnum,
    CatalystTypeEnum,
    ReactionTypeEnum,
    BarrierDetectionRequest,
    CatalystAnalysisRequest,
    PathwayOptimizationRequest,
    SwapBarrierAnalysisRequest,
    BatchOptimizationRequest,
    EnergyBarrierResponse,
    ActivationEnergyResponse,
    CatalystPersonResponse,
    CatalystMechanismResponse,
    CatalystRecommendationResponse,
    TransitionStateResponse,
    ReactionPathwayResponse,
    PathwayResultResponse,
    BarrierAnalysisResponse,
    SwapBarrierAnalysisResponse,
    BatchOptimizationResponse,
    CatalystCapacityResponse,
)


class TestBarrierTypeEnum:
    def test_values(self):
        assert BarrierTypeEnum.KINETIC == "kinetic"
        assert BarrierTypeEnum.REGULATORY == "regulatory"

    def test_count(self):
        assert len(BarrierTypeEnum) == 5


class TestCatalystTypeEnum:
    def test_count(self):
        assert len(CatalystTypeEnum) == 4


class TestReactionTypeEnum:
    def test_count(self):
        assert len(ReactionTypeEnum) == 5


class TestBarrierDetectionRequest:
    def test_valid(self):
        r = BarrierDetectionRequest(
            assignment_id=uuid4(), proposed_change={"type": "swap"}
        )
        assert r.reference_date is None


class TestCatalystAnalysisRequest:
    def test_defaults(self):
        barrier = EnergyBarrierResponse(
            barrier_type=BarrierTypeEnum.KINETIC,
            name="test",
            description="test",
            energy_contribution=0.5,
            is_absolute=False,
            source="test",
        )
        r = CatalystAnalysisRequest(barriers=[barrier])
        assert r.max_catalysts == 3

    # --- max_catalysts ge=1, le=10 ---

    def test_max_catalysts_below_min(self):
        with pytest.raises(ValidationError):
            CatalystAnalysisRequest(barriers=[], max_catalysts=0)

    def test_max_catalysts_above_max(self):
        with pytest.raises(ValidationError):
            CatalystAnalysisRequest(barriers=[], max_catalysts=11)


class TestPathwayOptimizationRequest:
    def test_defaults(self):
        r = PathwayOptimizationRequest(
            assignment_id=uuid4(), proposed_change={"type": "swap"}
        )
        assert r.energy_threshold == 0.8
        assert r.prefer_mechanisms is True
        assert r.allow_multi_step is True

    # --- energy_threshold ge=0.0, le=1.0 ---

    def test_energy_threshold_below_min(self):
        with pytest.raises(ValidationError):
            PathwayOptimizationRequest(
                assignment_id=uuid4(),
                proposed_change={},
                energy_threshold=-0.1,
            )

    def test_energy_threshold_above_max(self):
        with pytest.raises(ValidationError):
            PathwayOptimizationRequest(
                assignment_id=uuid4(),
                proposed_change={},
                energy_threshold=1.1,
            )


class TestSwapBarrierAnalysisRequest:
    def test_defaults(self):
        r = SwapBarrierAnalysisRequest(
            source_faculty_id=uuid4(),
            source_week=date(2026, 1, 10),
            target_faculty_id=uuid4(),
        )
        assert r.target_week is None
        assert r.swap_type == "one_to_one"


class TestBatchOptimizationRequest:
    def test_valid(self):
        change = PathwayOptimizationRequest(assignment_id=uuid4(), proposed_change={})
        r = BatchOptimizationRequest(changes=[change])
        assert r.find_optimal_order is True

    # --- changes min_length=1 ---

    def test_changes_empty(self):
        with pytest.raises(ValidationError):
            BatchOptimizationRequest(changes=[])


class TestEnergyBarrierResponse:
    def test_valid(self):
        r = EnergyBarrierResponse(
            barrier_type=BarrierTypeEnum.STERIC,
            name="Coverage gap",
            description="No coverage available",
            energy_contribution=0.7,
            is_absolute=False,
            source="validator",
        )
        assert r.metadata == {}

    # --- energy_contribution ge=0.0, le=1.0 ---

    def test_energy_contribution_below_min(self):
        with pytest.raises(ValidationError):
            EnergyBarrierResponse(
                barrier_type=BarrierTypeEnum.KINETIC,
                name="test",
                description="test",
                energy_contribution=-0.1,
                is_absolute=False,
                source="test",
            )

    def test_energy_contribution_above_max(self):
        with pytest.raises(ValidationError):
            EnergyBarrierResponse(
                barrier_type=BarrierTypeEnum.KINETIC,
                name="test",
                description="test",
                energy_contribution=1.1,
                is_absolute=False,
                source="test",
            )


class TestActivationEnergyResponse:
    def test_defaults(self):
        r = ActivationEnergyResponse(
            value=0.5,
            is_feasible=True,
            effective_energy=0.3,
            reduction_percentage=40.0,
        )
        assert r.components == {}
        assert r.catalyzed_value is None
        assert r.catalyst_effect == 0.0

    # --- value ge=0.0, le=1.0 ---

    def test_value_below_min(self):
        with pytest.raises(ValidationError):
            ActivationEnergyResponse(
                value=-0.1,
                is_feasible=True,
                effective_energy=0,
                reduction_percentage=0,
            )

    def test_value_above_max(self):
        with pytest.raises(ValidationError):
            ActivationEnergyResponse(
                value=1.1,
                is_feasible=True,
                effective_energy=0,
                reduction_percentage=0,
            )


class TestCatalystPersonResponse:
    def test_valid(self):
        r = CatalystPersonResponse(
            person_id=uuid4(),
            name="Dr. Smith",
            catalyst_type=CatalystTypeEnum.HOMOGENEOUS,
            availability=0.8,
            capacity=0.6,
        )
        assert r.effectiveness == {}

    # --- availability/capacity ge=0.0, le=1.0 ---

    def test_availability_above_max(self):
        with pytest.raises(ValidationError):
            CatalystPersonResponse(
                person_id=uuid4(),
                name="Dr. Smith",
                catalyst_type=CatalystTypeEnum.HOMOGENEOUS,
                availability=1.1,
                capacity=0.5,
            )

    def test_capacity_below_min(self):
        with pytest.raises(ValidationError):
            CatalystPersonResponse(
                person_id=uuid4(),
                name="Dr. Smith",
                catalyst_type=CatalystTypeEnum.HOMOGENEOUS,
                availability=0.5,
                capacity=-0.1,
            )


class TestCatalystMechanismResponse:
    def test_valid(self):
        r = CatalystMechanismResponse(
            mechanism_id="mech-1",
            name="Auto-swap",
            catalyst_type=CatalystTypeEnum.ENZYMATIC,
            target_barriers=[BarrierTypeEnum.KINETIC],
            reduction_factor=0.5,
            auto_applicable=True,
            requires_authorization=False,
        )
        assert r.reduction_factor == 0.5


class TestCatalystRecommendationResponse:
    def test_valid(self):
        barrier = EnergyBarrierResponse(
            barrier_type=BarrierTypeEnum.KINETIC,
            name="test",
            description="test",
            energy_contribution=0.5,
            is_absolute=False,
            source="test",
        )
        r = CatalystRecommendationResponse(
            barrier=barrier,
            person_catalysts=[],
            mechanism_catalysts=[],
            recommended_catalyst="auto-swap",
            confidence=0.9,
        )
        assert r.confidence == 0.9

    # --- confidence ge=0.0, le=1.0 ---

    def test_confidence_above_max(self):
        barrier = EnergyBarrierResponse(
            barrier_type=BarrierTypeEnum.KINETIC,
            name="t",
            description="t",
            energy_contribution=0.5,
            is_absolute=False,
            source="t",
        )
        with pytest.raises(ValidationError):
            CatalystRecommendationResponse(
                barrier=barrier,
                person_catalysts=[],
                mechanism_catalysts=[],
                recommended_catalyst="x",
                confidence=1.1,
            )


class TestTransitionStateResponse:
    def test_defaults(self):
        r = TransitionStateResponse(
            state_id="s1",
            description="Intermediate",
            energy=0.5,
            is_stable=False,
        )
        assert r.duration_estimate_hours is None

    # --- energy ge=0.0, le=1.0 ---

    def test_energy_above_max(self):
        with pytest.raises(ValidationError):
            TransitionStateResponse(
                state_id="s1", description="test", energy=1.1, is_stable=False
            )


class TestReactionPathwayResponse:
    def test_valid(self):
        r = ReactionPathwayResponse(
            pathway_id="p1",
            total_energy=0.8,
            catalyzed_energy=0.4,
            transition_states=[],
            catalysts_used=[],
            success_probability=0.9,
        )
        assert r.estimated_duration_hours is None

    # --- success_probability ge=0.0, le=1.0 ---

    def test_success_probability_above_max(self):
        with pytest.raises(ValidationError):
            ReactionPathwayResponse(
                pathway_id="p1",
                total_energy=0.8,
                catalyzed_energy=0.4,
                transition_states=[],
                catalysts_used=[],
                success_probability=1.1,
            )


class TestPathwayResultResponse:
    def test_defaults(self):
        r = PathwayResultResponse(success=False)
        assert r.pathway is None
        assert r.alternative_pathways == []
        assert r.blocking_barriers == []
        assert r.recommendations == []


class TestBarrierAnalysisResponse:
    def test_valid(self):
        energy = ActivationEnergyResponse(
            value=0.5,
            is_feasible=True,
            effective_energy=0.3,
            reduction_percentage=40.0,
        )
        r = BarrierAnalysisResponse(
            total_barriers=0,
            barriers=[],
            activation_energy=energy,
            has_absolute_barriers=False,
            summary="No barriers",
        )
        assert r.total_barriers == 0


class TestSwapBarrierAnalysisResponse:
    def test_defaults(self):
        energy = ActivationEnergyResponse(
            value=0.5,
            is_feasible=True,
            effective_energy=0.3,
            reduction_percentage=40.0,
        )
        r = SwapBarrierAnalysisResponse(
            swap_feasible=True,
            barriers=[],
            activation_energy=energy,
        )
        assert r.catalyst_recommendations == []
        assert r.blocking_barriers == []
        assert r.pathway is None
        assert r.recommendations == []


class TestBatchOptimizationResponse:
    def test_defaults(self):
        r = BatchOptimizationResponse(
            total_changes=0,
            successful_pathways=0,
            results=[],
            aggregate_energy=0.0,
        )
        assert r.optimal_order == []
        assert r.catalyst_conflicts == []


class TestCatalystCapacityResponse:
    def test_defaults(self):
        r = CatalystCapacityResponse(
            person_catalysts_available=5,
            mechanism_catalysts_available=3,
            total_capacity=0.8,
        )
        assert r.bottleneck_catalysts == []
        assert r.recommendations == []

    # --- total_capacity ge=0.0 ---

    def test_total_capacity_negative(self):
        with pytest.raises(ValidationError):
            CatalystCapacityResponse(
                person_catalysts_available=0,
                mechanism_catalysts_available=0,
                total_capacity=-0.1,
            )
