"""Tests for scheduling_catalyst models."""

from uuid import uuid4

import pytest

from app.scheduling_catalyst.models import (
    ActivationEnergy,
    BarrierType,
    CatalystMechanism,
    CatalystPerson,
    CatalystType,
    EnergyBarrier,
    ReactionPathway,
    ReactionType,
    ScheduleReaction,
    TransitionState,
)


class TestActivationEnergy:
    """Tests for ActivationEnergy dataclass."""

    def test_valid_energy_creation(self):
        """Test creating activation energy with valid values."""
        energy = ActivationEnergy(value=0.5)
        assert energy.value == 0.5
        assert energy.effective_energy == 0.5
        assert energy.is_feasible is True

    def test_energy_with_catalysis(self):
        """Test activation energy with catalyst reduction."""
        energy = ActivationEnergy(
            value=0.8,
            catalyzed_value=0.4,
            catalyst_effect=0.4,
        )
        assert energy.effective_energy == 0.4
        assert energy.reduction_percentage == 50.0
        assert energy.is_feasible is True

    def test_infeasible_energy(self):
        """Test energy at maximum (infeasible)."""
        energy = ActivationEnergy(value=1.0)
        assert energy.is_feasible is False

    def test_invalid_energy_raises(self):
        """Test that invalid energy values raise ValueError."""
        with pytest.raises(ValueError, match="must be 0.0-1.0"):
            ActivationEnergy(value=1.5)

        with pytest.raises(ValueError, match="must be 0.0-1.0"):
            ActivationEnergy(value=-0.1)

    def test_energy_components(self):
        """Test energy with component breakdown."""
        energy = ActivationEnergy(
            value=0.6,
            components={
                BarrierType.KINETIC: 0.3,
                BarrierType.ELECTRONIC: 0.3,
            },
        )
        assert sum(energy.components.values()) == 0.6


class TestEnergyBarrier:
    """Tests for EnergyBarrier dataclass."""

    def test_barrier_creation(self):
        """Test creating an energy barrier."""
        barrier = EnergyBarrier(
            barrier_type=BarrierType.KINETIC,
            name="Freeze Horizon",
            description="Within freeze period",
            energy_contribution=0.5,
        )
        assert barrier.barrier_type == BarrierType.KINETIC
        assert barrier.can_be_catalyzed is True

    def test_absolute_barrier(self):
        """Test absolute barrier that cannot be catalyzed."""
        barrier = EnergyBarrier(
            barrier_type=BarrierType.REGULATORY,
            name="ACGME Violation",
            description="Would violate 80-hour rule",
            energy_contribution=1.0,
            is_absolute=True,
        )
        assert barrier.can_be_catalyzed is False

    def test_invalid_contribution_raises(self):
        """Test that invalid energy contribution raises ValueError."""
        with pytest.raises(ValueError, match="must be 0.0-1.0"):
            EnergyBarrier(
                barrier_type=BarrierType.KINETIC,
                name="Test",
                description="Test",
                energy_contribution=1.5,
            )


class TestCatalystPerson:
    """Tests for CatalystPerson dataclass."""

    def test_catalyst_person_creation(self):
        """Test creating a catalyst person."""
        catalyst = CatalystPerson(
            person_id=uuid4(),
            name="Test Coordinator",
            catalyst_type=CatalystType.ENZYMATIC,
            catalyst_score=0.8,
            barriers_addressed=[BarrierType.ELECTRONIC, BarrierType.KINETIC],
            reduction_factors={
                BarrierType.ELECTRONIC: 0.9,
                BarrierType.KINETIC: 0.6,
            },
        )
        assert catalyst.catalyst_score == 0.8
        assert catalyst.is_available is True
        assert catalyst.capacity_remaining == 1.0

    def test_catalyst_can_address_barrier(self):
        """Test checking if catalyst can address a barrier."""
        catalyst = CatalystPerson(
            person_id=uuid4(),
            name="Test",
            catalyst_type=CatalystType.HOMOGENEOUS,
            catalyst_score=0.7,
            barriers_addressed=[BarrierType.THERMODYNAMIC],
            reduction_factors={BarrierType.THERMODYNAMIC: 0.5},
        )

        addressable_barrier = EnergyBarrier(
            barrier_type=BarrierType.THERMODYNAMIC,
            name="Workload",
            description="High workload",
            energy_contribution=0.3,
        )
        assert catalyst.can_address_barrier(addressable_barrier) is True

        unaddressable_barrier = EnergyBarrier(
            barrier_type=BarrierType.REGULATORY,
            name="ACGME",
            description="Compliance",
            energy_contribution=0.5,
        )
        assert catalyst.can_address_barrier(unaddressable_barrier) is False

    def test_catalyst_cannot_address_absolute_barrier(self):
        """Test that catalysts cannot address absolute barriers."""
        catalyst = CatalystPerson(
            person_id=uuid4(),
            name="Test",
            catalyst_type=CatalystType.ENZYMATIC,
            catalyst_score=0.9,
            barriers_addressed=[BarrierType.REGULATORY],
            reduction_factors={BarrierType.REGULATORY: 0.8},
        )

        absolute_barrier = EnergyBarrier(
            barrier_type=BarrierType.REGULATORY,
            name="Absolute",
            description="Cannot override",
            energy_contribution=1.0,
            is_absolute=True,
        )
        assert catalyst.can_address_barrier(absolute_barrier) is False

    def test_reduction_for_barrier(self):
        """Test calculating reduction for a barrier."""
        catalyst = CatalystPerson(
            person_id=uuid4(),
            name="Test",
            catalyst_type=CatalystType.HOMOGENEOUS,
            catalyst_score=0.7,
            barriers_addressed=[BarrierType.KINETIC],
            reduction_factors={BarrierType.KINETIC: 0.6},
            is_available=True,
            capacity_remaining=0.8,
        )

        barrier = EnergyBarrier(
            barrier_type=BarrierType.KINETIC,
            name="Freeze",
            description="Freeze period",
            energy_contribution=0.5,
        )

        # Reduction scaled by capacity
        expected_reduction = 0.6 * 0.8  # reduction * capacity
        assert catalyst.reduction_for_barrier(barrier) == expected_reduction

    def test_unavailable_catalyst_no_reduction(self):
        """Test that unavailable catalysts provide no reduction."""
        catalyst = CatalystPerson(
            person_id=uuid4(),
            name="Test",
            catalyst_type=CatalystType.HOMOGENEOUS,
            catalyst_score=0.7,
            barriers_addressed=[BarrierType.KINETIC],
            reduction_factors={BarrierType.KINETIC: 0.6},
            is_available=False,
        )

        barrier = EnergyBarrier(
            barrier_type=BarrierType.KINETIC,
            name="Freeze",
            description="Freeze period",
            energy_contribution=0.5,
        )

        assert catalyst.reduction_for_barrier(barrier) == 0.0


class TestCatalystMechanism:
    """Tests for CatalystMechanism dataclass."""

    def test_mechanism_creation(self):
        """Test creating a catalyst mechanism."""
        mechanism = CatalystMechanism(
            mechanism_id="auto_matcher",
            name="Swap Auto-Matcher",
            catalyst_type=CatalystType.HETEROGENEOUS,
            barriers_addressed=[BarrierType.THERMODYNAMIC],
            reduction_factors={BarrierType.THERMODYNAMIC: 0.6},
            is_active=True,
        )
        assert mechanism.mechanism_id == "auto_matcher"
        assert mechanism.is_active is True

    def test_mechanism_with_trigger(self):
        """Test mechanism that requires a trigger."""
        mechanism = CatalystMechanism(
            mechanism_id="emergency_override",
            name="Emergency Override",
            catalyst_type=CatalystType.ENZYMATIC,
            barriers_addressed=[BarrierType.KINETIC],
            reduction_factors={BarrierType.KINETIC: 0.8},
            requires_trigger="emergency_code",
        )
        assert mechanism.requires_trigger == "emergency_code"


class TestReactionPathway:
    """Tests for ReactionPathway dataclass."""

    def test_pathway_creation(self):
        """Test creating a reaction pathway."""
        pathway = ReactionPathway(
            pathway_id="test-pathway",
            initial_state={"assignment_id": "123"},
            target_state={"new_person_id": "456"},
            total_activation_energy=0.6,
            effective_activation_energy=0.4,
        )
        assert pathway.is_feasible is True
        assert pathway.catalyst_efficiency == pytest.approx(0.333, rel=0.01)

    def test_infeasible_pathway(self):
        """Test pathway with energy >= 1.0."""
        pathway = ReactionPathway(
            pathway_id="test",
            initial_state={},
            target_state={},
            total_activation_energy=1.0,
            effective_activation_energy=1.0,
        )
        assert pathway.is_feasible is False

    def test_add_catalyst_recalculates_energy(self):
        """Test that adding a catalyst recalculates effective energy."""
        barriers = [
            EnergyBarrier(
                barrier_type=BarrierType.KINETIC,
                name="Test",
                description="Test",
                energy_contribution=0.5,
            ),
        ]

        pathway = ReactionPathway(
            pathway_id="test",
            initial_state={},
            target_state={},
            barriers=barriers,
            total_activation_energy=0.5,
            effective_activation_energy=0.5,
        )

        catalyst = CatalystPerson(
            person_id=uuid4(),
            name="Test",
            catalyst_type=CatalystType.ENZYMATIC,
            catalyst_score=0.9,
            barriers_addressed=[BarrierType.KINETIC],
            reduction_factors={BarrierType.KINETIC: 0.6},
        )

        pathway.add_catalyst(catalyst)

        assert len(pathway.catalysts_applied) == 1
        # Energy should be reduced by 60%
        assert pathway.effective_activation_energy == pytest.approx(0.2, rel=0.01)


class TestTransitionState:
    """Tests for TransitionState dataclass."""

    def test_transition_state_creation(self):
        """Test creating a transition state."""
        state = TransitionState(
            state_id="state-1",
            description="Intermediate state",
            assignments={"cleared": True},
            energy_level=0.6,
            is_stable=False,
        )
        assert state.is_transition is True

    def test_metastable_state(self):
        """Test metastable (stable) intermediate state."""
        state = TransitionState(
            state_id="rollback",
            description="Rollback window",
            assignments={},
            energy_level=0.1,
            is_stable=True,
            duration=1440,
        )
        assert state.is_transition is False
        assert state.duration == 1440


class TestScheduleReaction:
    """Tests for ScheduleReaction dataclass."""

    def test_reaction_creation(self):
        """Test creating a schedule reaction."""
        pathway = ReactionPathway(
            pathway_id="test",
            initial_state={},
            target_state={},
            total_activation_energy=0.4,
            effective_activation_energy=0.3,
        )

        reaction = ScheduleReaction(
            reaction_id="reaction-1",
            reaction_type=ReactionType.SWAP,
            reactants=[{"assignment": "A"}],
            products=[{"assignment": "B"}],
            pathway=pathway,
            rate_constant=0.8,
            is_reversible=True,
            reversal_window=1440,
        )

        assert reaction.is_reversible is True
        assert reaction.reversal_window == 1440

    def test_gibbs_free_energy(self):
        """Test Gibbs free energy calculation."""
        pathway = ReactionPathway(
            pathway_id="test",
            initial_state={},
            target_state={},
            effective_activation_energy=0.3,
        )

        reaction = ScheduleReaction(
            reaction_id="test",
            reaction_type=ReactionType.SWAP,
            reactants=[],
            products=[],
            pathway=pathway,
        )

        # Gibbs = effective_energy - 0.5 = 0.3 - 0.5 = -0.2
        assert reaction.gibbs_free_energy == pytest.approx(-0.2, rel=0.01)
        assert reaction.is_spontaneous is True
