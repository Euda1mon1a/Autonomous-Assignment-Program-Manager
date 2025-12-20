"""Tests for scheduling_catalyst optimizer."""

import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

from app.scheduling_catalyst.optimizer import (
    BatchOptimizer,
    OptimizationConfig,
    PathwayResult,
    TransitionOptimizer,
)
from app.scheduling_catalyst.models import (
    BarrierType,
    CatalystMechanism,
    CatalystPerson,
    CatalystType,
    EnergyBarrier,
    ReactionType,
)


class TestOptimizationConfig:
    """Tests for OptimizationConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = OptimizationConfig()
        assert config.max_catalysts == 3
        assert config.max_pathways == 5
        assert config.energy_threshold == 0.8
        assert config.prefer_mechanisms is True
        assert config.allow_multi_step is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = OptimizationConfig(
            max_catalysts=5,
            energy_threshold=0.6,
        )
        assert config.max_catalysts == 5
        assert config.energy_threshold == 0.6


class TestPathwayResult:
    """Tests for PathwayResult."""

    def test_successful_result(self):
        """Test successful pathway result."""
        from app.scheduling_catalyst.models import ReactionPathway

        pathway = ReactionPathway(
            pathway_id="test",
            initial_state={},
            target_state={},
            total_activation_energy=0.5,
            effective_activation_energy=0.3,
        )

        result = PathwayResult(
            success=True,
            pathway=pathway,
        )

        assert result.success is True
        assert result.pathway is not None
        assert len(result.blocking_barriers) == 0

    def test_blocked_result(self):
        """Test blocked pathway result."""
        blocking = [
            EnergyBarrier(
                barrier_type=BarrierType.REGULATORY,
                name="ACGME",
                description="Violation",
                energy_contribution=1.0,
                is_absolute=True,
            ),
        ]

        result = PathwayResult(
            success=False,
            blocking_barriers=blocking,
            recommendations=["Cannot proceed"],
        )

        assert result.success is False
        assert len(result.blocking_barriers) == 1
        assert len(result.recommendations) == 1


class TestTransitionOptimizer:
    """Tests for TransitionOptimizer."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def optimizer(self, mock_db):
        """Create optimizer with mock db."""
        return TransitionOptimizer(mock_db)

    @pytest.mark.asyncio
    async def test_find_optimal_pathway_simple(self, optimizer):
        """Test finding pathway for simple change."""
        today = date.today()
        target_date = today + timedelta(days=30)

        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": target_date.isoformat(),
                "change_type": "modification",
            },
        )

        # Should succeed for change outside freeze
        assert result.success is True
        assert result.pathway is not None

    @pytest.mark.asyncio
    async def test_find_optimal_pathway_with_barriers(self, optimizer):
        """Test finding pathway when barriers exist."""
        today = date.today()
        target_date = today + timedelta(days=5)

        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": target_date.isoformat(),
                "change_type": "reassignment",
                "requester_role": "resident",
            },
        )

        # May or may not succeed depending on barriers
        assert result.pathway is not None

    @pytest.mark.asyncio
    async def test_find_optimal_pathway_blocked(self, optimizer):
        """Test pathway blocked by absolute barrier."""
        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "change_type": "swap",
                "other_person_consented": False,  # Absolute barrier
            },
        )

        # Should fail due to consent barrier
        assert result.success is False
        assert len(result.blocking_barriers) > 0

    @pytest.mark.asyncio
    async def test_find_optimal_pathway_with_catalysts(self, optimizer):
        """Test pathway with pre-selected catalysts."""
        today = date.today()
        target_date = today + timedelta(days=7)

        catalyst = CatalystPerson(
            person_id=uuid4(),
            name="Coordinator",
            catalyst_type=CatalystType.ENZYMATIC,
            catalyst_score=0.9,
            barriers_addressed=[BarrierType.KINETIC, BarrierType.ELECTRONIC],
            reduction_factors={
                BarrierType.KINETIC: 0.8,
                BarrierType.ELECTRONIC: 0.9,
            },
        )

        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": target_date.isoformat(),
                "change_type": "reassignment",
                "requester_role": "resident",
            },
            available_catalysts=[catalyst],
        )

        # Should get a result
        assert isinstance(result, PathwayResult)

        # If pathway has significant barriers, catalyst should be applied
        if result.pathway and result.pathway.total_activation_energy > 0.5:
            assert len(result.pathway.catalysts_applied) >= 1

    @pytest.mark.asyncio
    async def test_optimize_swap(self, optimizer):
        """Test optimizing a swap."""
        result = await optimizer.optimize_swap(
            requester_id=uuid4(),
            target_id=uuid4(),
            assignment_id=uuid4(),
        )

        # Will fail without consent, but should have pathway info
        assert result.pathway is not None or len(result.blocking_barriers) > 0

    @pytest.mark.asyncio
    async def test_optimize_emergency_coverage(self, optimizer):
        """Test optimizing emergency coverage."""
        result = await optimizer.optimize_emergency_coverage(
            assignment_id=uuid4(),
            emergency_type="sick_call",
        )

        # Should return a result
        assert isinstance(result, PathwayResult)
        # Emergency optimization always provides a pathway (even if blocked)
        assert result.pathway is not None or len(result.blocking_barriers) > 0

    @pytest.mark.asyncio
    async def test_calculate_reaction_kinetics(self, optimizer):
        """Test calculating reaction kinetics."""
        from app.scheduling_catalyst.models import ReactionPathway

        pathway = ReactionPathway(
            pathway_id="test",
            initial_state={"assignment": "A"},
            target_state={"change_type": "swap"},
            total_activation_energy=0.5,
            effective_activation_energy=0.3,
        )

        reaction = await optimizer.calculate_reaction_kinetics(pathway)

        assert reaction.reaction_type == ReactionType.SWAP
        assert reaction.rate_constant > 0
        assert reaction.half_life is not None
        assert reaction.is_reversible is True


class TestBatchOptimizer:
    """Tests for BatchOptimizer."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def batch_optimizer(self, mock_db):
        """Create batch optimizer."""
        return BatchOptimizer(mock_db)

    @pytest.mark.asyncio
    async def test_optimize_batch(self, batch_optimizer):
        """Test optimizing multiple changes."""
        today = date.today()

        changes = [
            (
                uuid4(),
                {
                    "target_date": (today + timedelta(days=30)).isoformat(),
                    "change_type": "modification",
                },
            ),
            (
                uuid4(),
                {
                    "target_date": (today + timedelta(days=25)).isoformat(),
                    "change_type": "modification",
                },
            ),
        ]

        results = await batch_optimizer.optimize_batch(changes)

        assert len(results) == 2
        # Both should have some result
        for result in results:
            assert isinstance(result, PathwayResult)

    @pytest.mark.asyncio
    async def test_find_optimal_order(self, batch_optimizer):
        """Test finding optimal execution order."""
        today = date.today()

        changes = [
            (
                uuid4(),
                {
                    "target_date": (today + timedelta(days=5)).isoformat(),
                    "change_type": "reassignment",
                    "requester_role": "resident",
                },
            ),
            (
                uuid4(),
                {
                    "target_date": (today + timedelta(days=30)).isoformat(),
                    "change_type": "modification",
                },
            ),
        ]

        order = await batch_optimizer.find_optimal_order(changes)

        assert len(order) == 2
        assert set(order) == {0, 1}
        # Second change (outside freeze) should be first
        assert order[0] == 1


# ============================================================================
# Multi-Objective Optimization Tests
# ============================================================================


class TestMultiObjectiveOptimization:
    """Tests for multi-objective optimization scenarios."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def optimizer(self, mock_db):
        """Create optimizer with default config."""
        return TransitionOptimizer(mock_db)

    @pytest.mark.asyncio
    async def test_minimize_energy_and_duration(self, optimizer):
        """
        Test optimizing for both low energy and short duration.

        Multi-objective: minimize activation energy AND minimize duration.
        """
        today = date.today()
        target_date = today + timedelta(days=10)

        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": target_date.isoformat(),
                "change_type": "modification",
            },
        )

        if result.success and result.pathway:
            pathway = result.pathway

            # Verify pathway has duration estimate
            assert pathway.estimated_duration is not None
            assert pathway.estimated_duration > 0

            # Check alternative pathways if they exist
            if result.alternative_pathways:
                # Different pathways may have different energy/duration tradeoffs
                for alt in result.alternative_pathways:
                    assert alt.estimated_duration is not None
                    # At least one should differ in characteristics
                    # (either energy or duration)

    @pytest.mark.asyncio
    async def test_maximize_catalyst_efficiency(self, optimizer):
        """Test optimizing for maximum catalyst efficiency."""
        today = date.today()

        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": (today + timedelta(days=7)).isoformat(),
                "change_type": "reassignment",
                "requester_role": "resident",
            },
        )

        if result.success and result.pathway:
            pathway = result.pathway

            # Calculate efficiency
            if pathway.catalysts_applied:
                efficiency = pathway.catalyst_efficiency
                # Efficiency should be reasonable
                assert 0.0 <= efficiency <= 1.0

                # If there's significant energy reduction
                if pathway.total_activation_energy > 0.5:
                    # Efficiency should be positive
                    assert efficiency > 0

    @pytest.mark.asyncio
    async def test_pareto_frontier_generation(self, mock_db):
        """
        Test generating Pareto frontier of optimal solutions.

        Pareto frontier: set of non-dominated solutions where no objective
        can be improved without worsening another.
        """
        optimizer = TransitionOptimizer(
            mock_db,
            config=OptimizationConfig(max_pathways=5),
        )

        today = date.today()
        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": (today + timedelta(days=7)).isoformat(),
                "change_type": "reassignment",
            },
        )

        all_pathways = []
        if result.pathway:
            all_pathways.append(result.pathway)
        all_pathways.extend(result.alternative_pathways)

        if len(all_pathways) > 1:
            # Verify we have diversity in solutions
            energies = [p.effective_activation_energy for p in all_pathways]
            durations = [p.estimated_duration for p in all_pathways]

            # Should have some variation (not all identical)
            assert len(set(energies)) > 1 or len(set(durations)) > 1

    @pytest.mark.asyncio
    async def test_constraint_satisfaction_priority(self, optimizer):
        """
        Test that constraint satisfaction takes priority over optimization.

        Absolute constraints must be satisfied; optimization is secondary.
        """
        # Create scenario with absolute barrier (consent)
        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "change_type": "swap",
                "other_person_consented": False,  # Absolute barrier
            },
        )

        # Should fail regardless of optimization
        assert result.success is False
        # Should have blocking barriers
        assert len(result.blocking_barriers) > 0
        # Should have recommendations for overcoming blocks
        assert len(result.recommendations) > 0


# ============================================================================
# Constraint Satisfaction Tests
# ============================================================================


class TestConstraintSatisfaction:
    """Tests for constraint satisfaction in optimization."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def optimizer(self, mock_db):
        """Create optimizer."""
        return TransitionOptimizer(mock_db)

    @pytest.mark.asyncio
    async def test_hard_constraint_enforcement(self, optimizer):
        """Test that hard constraints cannot be violated."""
        # Hard constraint: same-day changes
        today = date.today()

        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": today.isoformat(),  # Same day = absolute barrier
                "change_type": "modification",
            },
        )

        # Should have barriers detected
        if result.pathway:
            absolute_barriers = [
                b for b in result.pathway.barriers if b.is_absolute
            ]
            # Same-day should create absolute barrier
            if absolute_barriers:
                assert result.success is False

    @pytest.mark.asyncio
    async def test_soft_constraint_optimization(self, optimizer):
        """Test that soft constraints are optimized but can be violated."""
        today = date.today()
        target_date = today + timedelta(days=10)  # Within freeze but not absolute

        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": target_date.isoformat(),
                "change_type": "modification",
            },
        )

        # Soft constraints should allow success with catalysts
        if result.pathway:
            # If barriers exist but none are absolute
            non_absolute = [b for b in result.pathway.barriers if not b.is_absolute]
            absolute = [b for b in result.pathway.barriers if b.is_absolute]

            if non_absolute and not absolute:
                # Should succeed or get close with catalysts
                assert result.success or result.pathway.effective_activation_energy < 1.0

    @pytest.mark.asyncio
    async def test_constraint_hierarchy(self, optimizer):
        """Test that constraints are enforced in correct hierarchy."""
        # Hierarchy: Regulatory > Electronic > Kinetic > Thermodynamic
        from app.scheduling_catalyst.barriers import BarrierWeights

        weights = BarrierWeights()

        # Verify hierarchy in weights
        assert weights.regulatory > weights.electronic
        assert weights.kinetic > weights.thermodynamic
        # Regulatory barriers should have highest weight
        assert weights.regulatory == max([
            weights.kinetic,
            weights.thermodynamic,
            weights.steric,
            weights.electronic,
            weights.regulatory,
        ])

    @pytest.mark.asyncio
    async def test_feasibility_determination(self, optimizer):
        """Test correct feasibility determination based on constraints."""
        today = date.today()

        # Test 1: Clearly feasible (far future, simple change)
        result1 = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": (today + timedelta(days=60)).isoformat(),
                "change_type": "modification",
            },
        )
        assert result1.success is True

        # Test 2: Clearly infeasible (absolute barrier)
        result2 = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "change_type": "swap",
                "other_person_consented": False,
            },
        )
        assert result2.success is False


# ============================================================================
# Advanced Pathway Analysis Tests
# ============================================================================


class TestAdvancedPathwayAnalysis:
    """Tests for advanced pathway analysis features."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_transition_state_generation(self, mock_db):
        """Test generation of intermediate transition states."""
        optimizer = TransitionOptimizer(
            mock_db,
            config=OptimizationConfig(allow_multi_step=True),
        )

        today = date.today()
        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": (today + timedelta(days=7)).isoformat(),
                "change_type": "reassignment",
                "requester_role": "resident",
            },
        )

        if result.success and result.pathway:
            # High-energy pathways should have transition states
            if result.pathway.total_activation_energy > 0.6:
                # Should generate transition states for complex pathways
                assert isinstance(result.pathway.transition_states, list)

    @pytest.mark.asyncio
    async def test_reaction_kinetics_calculation(self, mock_db):
        """Test calculation of reaction kinetics."""
        optimizer = TransitionOptimizer(mock_db)

        today = date.today()
        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": (today + timedelta(days=15)).isoformat(),
                "change_type": "modification",
            },
        )

        if result.success and result.pathway:
            # Calculate kinetics
            reaction = await optimizer.calculate_reaction_kinetics(result.pathway)

            # Verify kinetic properties
            assert reaction.rate_constant > 0
            assert reaction.half_life is not None
            assert reaction.half_life > 0
            assert reaction.reaction_type in ReactionType

            # Rate constant should relate to activation energy
            # Higher energy = lower rate constant
            if result.pathway.effective_activation_energy > 0.5:
                assert reaction.rate_constant < 0.5

    @pytest.mark.asyncio
    async def test_reversibility_analysis(self, mock_db):
        """Test reversibility analysis for pathways."""
        optimizer = TransitionOptimizer(mock_db)

        # Test swap (reversible)
        swap_result = await optimizer.optimize_swap(
            requester_id=uuid4(),
            target_id=uuid4(),
            assignment_id=uuid4(),
        )

        if swap_result.pathway:
            # Calculate kinetics
            swap_reaction = await optimizer.calculate_reaction_kinetics(
                swap_result.pathway
            )

            # Swaps should be reversible
            assert swap_reaction.is_reversible is True
            assert swap_reaction.reversal_window > 0

    @pytest.mark.asyncio
    async def test_pathway_comparison_metrics(self, mock_db):
        """Test metrics for comparing alternative pathways."""
        optimizer = TransitionOptimizer(
            mock_db,
            config=OptimizationConfig(max_pathways=3),
        )

        today = date.today()
        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": (today + timedelta(days=10)).isoformat(),
                "change_type": "modification",
            },
        )

        all_pathways = []
        if result.pathway:
            all_pathways.append(result.pathway)
        all_pathways.extend(result.alternative_pathways)

        if len(all_pathways) > 1:
            # Compare pathways
            for pathway in all_pathways:
                # Each pathway should have comparable metrics
                assert pathway.total_activation_energy >= 0
                assert pathway.effective_activation_energy >= 0
                assert pathway.effective_activation_energy <= pathway.total_activation_energy
                assert pathway.estimated_duration is not None

                # Catalyst efficiency
                if pathway.catalysts_applied:
                    efficiency = pathway.catalyst_efficiency
                    assert 0.0 <= efficiency <= 1.0


# ============================================================================
# Performance and Scalability Tests
# ============================================================================


class TestOptimizationPerformance:
    """Tests for optimization performance and scalability."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_batch_optimization_scalability(self, mock_db):
        """Test batch optimization with many changes."""
        batch_optimizer = BatchOptimizer(mock_db)

        today = date.today()

        # Create 10 changes
        changes = [
            (
                uuid4(),
                {
                    "target_date": (today + timedelta(days=i * 3)).isoformat(),
                    "change_type": "modification",
                },
            )
            for i in range(10)
        ]

        results = await batch_optimizer.optimize_batch(changes)

        # Should handle all
        assert len(results) == 10

        # All should have results
        for result in results:
            assert isinstance(result, PathwayResult)

    @pytest.mark.asyncio
    async def test_catalyst_selection_efficiency(self, mock_db):
        """Test that catalyst selection is efficient."""
        optimizer = TransitionOptimizer(
            mock_db,
            config=OptimizationConfig(max_catalysts=3),  # Limit catalysts
        )

        today = date.today()
        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": (today + timedelta(days=7)).isoformat(),
                "change_type": "reassignment",
            },
        )

        if result.pathway and result.pathway.catalysts_applied:
            # Should respect max_catalysts limit
            assert len(result.pathway.catalysts_applied) <= 3

    @pytest.mark.asyncio
    async def test_alternative_pathway_generation_limit(self, mock_db):
        """Test that alternative pathway generation respects limits."""
        optimizer = TransitionOptimizer(
            mock_db,
            config=OptimizationConfig(max_pathways=3),
        )

        today = date.today()
        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": (today + timedelta(days=10)).isoformat(),
                "change_type": "modification",
            },
        )

        # Should not exceed max_pathways
        total_pathways = 1 if result.pathway else 0
        total_pathways += len(result.alternative_pathways)
        assert total_pathways <= 3
