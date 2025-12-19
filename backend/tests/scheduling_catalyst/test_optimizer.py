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

        if result.pathway:
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

        # Emergency should have catalyst applied
        if result.success:
            assert result.pathway is not None

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
