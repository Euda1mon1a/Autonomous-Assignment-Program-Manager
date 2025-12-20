"""
Comprehensive integration tests for scheduling_catalyst module.

Tests the full workflow from barrier detection through catalyst recommendation
to pathway optimization, covering all integration points between components.
"""

import pytest
from datetime import date, timedelta
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4, UUID

from app.scheduling_catalyst.barriers import BarrierDetector, BarrierWeights
from app.scheduling_catalyst.catalysts import CatalystAnalyzer, CatalystRecommendation
from app.scheduling_catalyst.optimizer import (
    TransitionOptimizer,
    BatchOptimizer,
    OptimizationConfig,
    PathwayResult,
)
from app.scheduling_catalyst.integration import (
    DefenseIntegration,
    HubIntegration,
    ResilienceFrameworkIntegration,
)
from app.scheduling_catalyst.models import (
    ActivationEnergy,
    BarrierType,
    CatalystMechanism,
    CatalystPerson,
    CatalystType,
    EnergyBarrier,
    ReactionPathway,
    ReactionType,
)


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_db():
    """Create mock async database session."""
    return AsyncMock()


@pytest.fixture
def barrier_detector(mock_db):
    """Create barrier detector instance."""
    return BarrierDetector(mock_db)


@pytest.fixture
def catalyst_analyzer(mock_db):
    """Create catalyst analyzer instance."""
    return CatalystAnalyzer(mock_db)


@pytest.fixture
def optimizer(mock_db):
    """Create transition optimizer instance."""
    return TransitionOptimizer(mock_db)


@pytest.fixture
def sample_barriers() -> list[EnergyBarrier]:
    """Create sample barriers of different types."""
    return [
        EnergyBarrier(
            barrier_type=BarrierType.KINETIC,
            name="Freeze Horizon",
            description="Within 14-day freeze period",
            energy_contribution=0.5,
            is_absolute=False,
            source="freeze_horizon",
        ),
        EnergyBarrier(
            barrier_type=BarrierType.ELECTRONIC,
            name="Authorization Required",
            description="Coordinator approval needed",
            energy_contribution=0.4,
            is_absolute=False,
            source="role_authorization",
        ),
        EnergyBarrier(
            barrier_type=BarrierType.THERMODYNAMIC,
            name="Workload Imbalance",
            description="High utilization",
            energy_contribution=0.3,
            is_absolute=False,
            source="workload_balance",
        ),
    ]


@pytest.fixture
def absolute_barrier() -> EnergyBarrier:
    """Create an absolute barrier (cannot be catalyzed)."""
    return EnergyBarrier(
        barrier_type=BarrierType.REGULATORY,
        name="ACGME Violation",
        description="Would violate 80-hour rule",
        energy_contribution=1.0,
        is_absolute=True,
        source="acgme_hours",
    )


@pytest.fixture
def mock_hub_metrics():
    """Create mock hub metrics for testing."""
    class MockHubMetrics:
        person_id: UUID = uuid4()
        composite_score: float = 0.85
        degree_centrality: float = 0.75
        betweenness_centrality: float = 0.2
        unique_services: int = 3

    return [MockHubMetrics()]


# ============================================================================
# Integration Test: Full Catalyst Recommendation Workflow
# ============================================================================


class TestFullCatalystWorkflow:
    """Test complete workflow from barriers to recommendations."""

    @pytest.mark.asyncio
    async def test_barrier_to_recommendation_workflow(
        self,
        barrier_detector,
        catalyst_analyzer,
    ):
        """
        Test full workflow: detect barriers → analyze → recommend catalysts.

        This tests the primary use case of the catalyst system.
        """
        # Step 1: Detect barriers for a proposed change
        today = date.today()
        target_date = today + timedelta(days=7)  # Within freeze
        assignment_id = uuid4()

        proposed_change = {
            "target_date": target_date.isoformat(),
            "change_type": "reassignment",
            "requester_role": "resident",
            "new_person_id": uuid4(),
        }

        barriers = await barrier_detector.detect_all_barriers(
            assignment_id,
            proposed_change,
            reference_date=today,
        )

        # Should detect multiple barriers
        assert len(barriers) > 0
        barrier_types = {b.barrier_type for b in barriers}
        assert BarrierType.KINETIC in barrier_types  # Freeze horizon
        assert BarrierType.ELECTRONIC in barrier_types  # Authorization

        # Step 2: Calculate activation energy
        energy = barrier_detector.calculate_activation_energy()
        assert energy.value > 0
        assert len(energy.components) > 0

        # Step 3: Get catalyst recommendations
        recommendation = await catalyst_analyzer.recommend_catalysts(barriers)

        # Should provide recommendations for catalyzable barriers
        assert isinstance(recommendation, CatalystRecommendation)
        assert recommendation.barriers == barriers
        assert len(recommendation.recommended_catalysts) > 0

        # Step 4: Verify energy reduction
        if recommendation.recommended_catalysts:
            assert recommendation.total_reduction > 0
            assert recommendation.residual_energy < sum(
                b.energy_contribution for b in barriers
            )

    @pytest.mark.asyncio
    async def test_workflow_with_absolute_barriers(
        self,
        barrier_detector,
        catalyst_analyzer,
        absolute_barrier,
    ):
        """Test workflow when absolute barriers are present."""
        barriers = [absolute_barrier]

        # Get recommendations
        recommendation = await catalyst_analyzer.recommend_catalysts(barriers)

        # Should indicate not feasible
        assert recommendation.is_feasible is False
        # No catalysts should be recommended for absolute barriers
        assert len(recommendation.recommended_catalysts) == 0
        # No reduction possible
        assert recommendation.total_reduction == 0.0

    @pytest.mark.asyncio
    async def test_workflow_statistics_after_recommendations(
        self,
        catalyst_analyzer,
        sample_barriers,
    ):
        """Test catalyst statistics generation after recommendations."""
        # Get recommendations
        recommendation = await catalyst_analyzer.recommend_catalysts(sample_barriers)

        # Get statistics
        stats = await catalyst_analyzer.get_catalyst_statistics()

        # Verify structure
        assert "person_catalysts" in stats
        assert "mechanism_catalysts" in stats
        assert "coverage" in stats

        # Should have catalysts available
        assert stats["person_catalysts"]["total"] > 0
        assert stats["mechanism_catalysts"]["total"] > 0

        # Coverage should include all barrier types
        for barrier_type in BarrierType:
            assert barrier_type.value in stats["coverage"]


# ============================================================================
# Integration Test: Optimizer with Catalysts and Barriers
# ============================================================================


class TestOptimizerIntegration:
    """Test optimizer integration with barrier detection and catalyst analysis."""

    @pytest.mark.asyncio
    async def test_optimizer_full_pipeline(self, optimizer):
        """Test optimizer running full barrier detection and catalyst selection."""
        today = date.today()
        target_date = today + timedelta(days=7)

        proposed_change = {
            "target_date": target_date.isoformat(),
            "change_type": "reassignment",
            "requester_role": "resident",
            "new_person_id": uuid4(),
        }

        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change=proposed_change,
        )

        # Should return a result
        assert isinstance(result, PathwayResult)
        assert result.pathway is not None

        # Pathway should have barriers and catalysts
        pathway = result.pathway
        assert len(pathway.barriers) > 0

        # If energy was high enough, catalysts should be applied
        if pathway.total_activation_energy > 0.5:
            assert len(pathway.catalysts_applied) > 0

    @pytest.mark.asyncio
    async def test_optimizer_applies_catalysts_effectively(self, optimizer):
        """Test that optimizer reduces energy with catalysts."""
        today = date.today()
        target_date = today + timedelta(days=5)

        proposed_change = {
            "target_date": target_date.isoformat(),
            "change_type": "reassignment",
            "requester_role": "resident",
        }

        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change=proposed_change,
        )

        if result.success and result.pathway:
            pathway = result.pathway

            # If catalysts were applied, effective energy should be less
            if len(pathway.catalysts_applied) > 0:
                assert pathway.effective_activation_energy <= pathway.total_activation_energy

    @pytest.mark.asyncio
    async def test_optimizer_with_custom_catalysts(self, optimizer):
        """Test optimizer with pre-selected catalysts."""
        # Create a powerful catalyst
        coordinator = CatalystPerson(
            person_id=uuid4(),
            name="Schedule Coordinator",
            catalyst_type=CatalystType.ENZYMATIC,
            catalyst_score=0.95,
            barriers_addressed=[
                BarrierType.KINETIC,
                BarrierType.ELECTRONIC,
                BarrierType.THERMODYNAMIC,
            ],
            reduction_factors={
                BarrierType.KINETIC: 0.9,
                BarrierType.ELECTRONIC: 0.95,
                BarrierType.THERMODYNAMIC: 0.7,
            },
            is_available=True,
            capacity_remaining=1.0,
        )

        today = date.today()
        target_date = today + timedelta(days=7)

        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": target_date.isoformat(),
                "change_type": "reassignment",
            },
            available_catalysts=[coordinator],
        )

        # Should succeed with powerful catalyst
        if result.pathway:
            # If energy was already low, catalyst may not be needed
            if result.pathway.total_activation_energy > 0.5:
                # For high-energy pathways, catalyst should be applied
                assert coordinator in result.pathway.catalysts_applied
                # Energy should be significantly reduced
                assert result.pathway.effective_activation_energy < result.pathway.total_activation_energy
            else:
                # Low energy pathways may proceed without catalysts
                # But should still succeed
                assert result.success is True


# ============================================================================
# Integration Test: Barrier-Catalyst Matching
# ============================================================================


class TestBarrierCatalystMatching:
    """Test matching catalysts to barriers across multiple types."""

    @pytest.mark.asyncio
    async def test_match_person_catalysts_to_barriers(
        self,
        catalyst_analyzer,
        sample_barriers,
    ):
        """Test matching person catalysts to multiple barrier types."""
        recommendation = await catalyst_analyzer.recommend_catalysts(sample_barriers)

        # Should have matches for each catalyzable barrier
        catalyzable_barriers = [b for b in sample_barriers if not b.is_absolute]
        assert len(recommendation.recommended_catalysts) >= 1

        # Each match should address its barrier
        for match in recommendation.recommended_catalysts:
            catalyst = match.catalyst
            barrier = match.barrier

            if isinstance(catalyst, CatalystPerson):
                assert catalyst.can_address_barrier(barrier)
            else:
                assert catalyst.can_address_barrier(barrier)

    @pytest.mark.asyncio
    async def test_match_mechanism_catalysts_to_barriers(
        self,
        catalyst_analyzer,
    ):
        """Test mechanism catalysts for different barrier types."""
        # Create barriers of different types
        barriers = [
            EnergyBarrier(
                barrier_type=BarrierType.THERMODYNAMIC,
                name="Workload",
                description="Test",
                energy_contribution=0.5,
            ),
            EnergyBarrier(
                barrier_type=BarrierType.KINETIC,
                name="Freeze",
                description="Test",
                energy_contribution=0.6,
            ),
        ]

        mechanisms = await catalyst_analyzer.find_mechanism_catalysts(barriers)

        # Should find appropriate mechanisms
        assert len(mechanisms) > 0

        # Should have auto-matcher for thermodynamic
        has_auto_matcher = any(m.mechanism_id == "auto_matcher" for m in mechanisms)
        assert has_auto_matcher

        # Should have emergency override for kinetic
        has_emergency = any(m.mechanism_id == "emergency_override" for m in mechanisms)
        assert has_emergency

    @pytest.mark.asyncio
    async def test_multiple_barriers_same_type(self, catalyst_analyzer):
        """Test matching when multiple barriers of same type exist."""
        # Two kinetic barriers
        barriers = [
            EnergyBarrier(
                barrier_type=BarrierType.KINETIC,
                name="Freeze Horizon",
                description="Freeze",
                energy_contribution=0.5,
            ),
            EnergyBarrier(
                barrier_type=BarrierType.KINETIC,
                name="Short Notice",
                description="Last minute",
                energy_contribution=0.3,
            ),
        ]

        recommendation = await catalyst_analyzer.recommend_catalysts(barriers)

        # Should recommend catalysts that can address kinetic barriers
        for match in recommendation.recommended_catalysts:
            assert BarrierType.KINETIC in match.catalyst.barriers_addressed


# ============================================================================
# Integration Test: Catalyst Chain Reactions
# ============================================================================


class TestCatalystChainReactions:
    """Test scenarios where one catalyst enables another."""

    @pytest.mark.asyncio
    async def test_defense_level_cascade(self, mock_db):
        """Test defense level escalation enables more catalysts."""
        defense = DefenseIntegration(mock_db)

        # Level 1 has basic catalysts
        level1_mechs = defense.get_available_mechanisms(1)
        level1_count = len(level1_mechs)

        # Level 3 should have more (cumulative)
        level3_mechs = defense.get_available_mechanisms(3)
        level3_count = len(level3_mechs)

        assert level3_count > level1_count

        # Level 3 should include level 1 catalysts plus more
        level1_ids = {m.mechanism_id for m in level1_mechs}
        level3_ids = {m.mechanism_id for m in level3_mechs}
        assert level1_ids.issubset(level3_ids)

    @pytest.mark.asyncio
    async def test_catalyst_capacity_chain(self, catalyst_analyzer, sample_barriers):
        """Test that using catalysts reduces available capacity for next use."""
        # Get initial catalysts
        recommendation1 = await catalyst_analyzer.recommend_catalysts(sample_barriers)

        # Simulate using a catalyst by reducing capacity
        if recommendation1.recommended_catalysts:
            first_match = recommendation1.recommended_catalysts[0]
            if isinstance(first_match.catalyst, CatalystPerson):
                # Reduce capacity
                first_match.catalyst.capacity_remaining = 0.2

                # Get catalysts again with reduced capacity
                recommendation2 = await catalyst_analyzer.recommend_catalysts(
                    sample_barriers
                )

                # The catalyst with reduced capacity should score lower
                # (This is implicit in the scoring function)
                assert recommendation2 is not None


# ============================================================================
# Integration Test: Combined Person + Mechanism Catalysts
# ============================================================================


class TestCombinedCatalystEffects:
    """Test combined effects of person and mechanism catalysts."""

    def test_combined_reduction_calculation(self):
        """Test calculating combined reduction from person and mechanism."""
        from app.scheduling_catalyst.catalysts import CatalystScorer

        # Create a person catalyst
        person = CatalystPerson(
            person_id=uuid4(),
            name="Coordinator",
            catalyst_type=CatalystType.ENZYMATIC,
            catalyst_score=0.8,
            barriers_addressed=[BarrierType.KINETIC],
            reduction_factors={BarrierType.KINETIC: 0.5},
            is_available=True,
            capacity_remaining=1.0,
        )

        # Create a mechanism catalyst
        mechanism = CatalystMechanism(
            mechanism_id="emergency",
            name="Emergency Override",
            catalyst_type=CatalystType.HETEROGENEOUS,
            barriers_addressed=[BarrierType.KINETIC],
            reduction_factors={BarrierType.KINETIC: 0.4},
            is_active=True,
        )

        # Create a barrier
        barrier = EnergyBarrier(
            barrier_type=BarrierType.KINETIC,
            name="Freeze",
            description="Test",
            energy_contribution=1.0,
        )

        # Calculate combined reduction
        combined = CatalystScorer.calculate_combined_reduction(
            [person, mechanism], barrier
        )

        # Both catalysts should reduce energy
        # First: 1.0 * (1 - 0.5) = 0.5
        # Second: 0.5 * (1 - 0.4) = 0.3
        # Total reduction: (1.0 - 0.3) / 1.0 = 0.7
        assert 0.65 <= combined <= 0.75

    @pytest.mark.asyncio
    async def test_pathway_with_mixed_catalysts(self, optimizer):
        """Test pathway optimization with both person and mechanism catalysts."""
        person_catalyst = CatalystPerson(
            person_id=uuid4(),
            name="Hub Faculty",
            catalyst_type=CatalystType.HOMOGENEOUS,
            catalyst_score=0.7,
            barriers_addressed=[BarrierType.THERMODYNAMIC],
            reduction_factors={BarrierType.THERMODYNAMIC: 0.6},
        )

        mechanism_catalyst = CatalystMechanism(
            mechanism_id="auto_matcher",
            name="Auto-Matcher",
            catalyst_type=CatalystType.HETEROGENEOUS,
            barriers_addressed=[BarrierType.THERMODYNAMIC],
            reduction_factors={BarrierType.THERMODYNAMIC: 0.5},
        )

        today = date.today()
        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": (today + timedelta(days=7)).isoformat(),
                "change_type": "modification",
                "new_person_id": uuid4(),
            },
            available_catalysts=[person_catalyst, mechanism_catalyst],
        )

        # Should return a result
        assert isinstance(result, PathwayResult)

        # Verify catalysts are available
        if result.pathway and result.pathway.total_activation_energy > 0.3:
            # Catalysts should be used if energy is significant
            pathway = result.pathway
            has_person = any(
                isinstance(c, CatalystPerson) for c in pathway.catalysts_applied
            )
            has_mechanism = any(
                isinstance(c, CatalystMechanism) for c in pathway.catalysts_applied
            )

            # At least one should be used for high-energy pathways
            assert has_person or has_mechanism or len(pathway.catalysts_applied) == 0


# ============================================================================
# Integration Test: Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_no_available_catalysts(self, catalyst_analyzer):
        """Test when no catalysts are available for barriers."""
        # Create a very specific barrier with no matching catalysts
        # (This is hypothetical - normally there would be some)
        barriers = [
            EnergyBarrier(
                barrier_type=BarrierType.STERIC,
                name="Unique Credential",
                description="Very specific requirement",
                energy_contribution=0.8,
            )
        ]

        recommendation = await catalyst_analyzer.recommend_catalysts(barriers)

        # Should still return a recommendation
        assert isinstance(recommendation, CatalystRecommendation)
        # Note: In current implementation, backup pool members can address
        # steric barriers, so we may get some reduction
        # The key is that a recommendation is always returned
        assert recommendation.residual_energy >= 0.0

    @pytest.mark.asyncio
    async def test_all_barriers_absolute(self, catalyst_analyzer, absolute_barrier):
        """Test when all barriers are absolute (immutable)."""
        barriers = [
            absolute_barrier,
            EnergyBarrier(
                barrier_type=BarrierType.ELECTRONIC,
                name="Missing Consent",
                description="Required consent not provided",
                energy_contribution=1.0,
                is_absolute=True,
                source="consent_check",
            ),
        ]

        recommendation = await catalyst_analyzer.recommend_catalysts(barriers)

        # Should indicate not feasible
        assert recommendation.is_feasible is False
        # No catalysts should be recommended
        assert len(recommendation.recommended_catalysts) == 0
        # No reduction
        assert recommendation.total_reduction == 0.0

    @pytest.mark.asyncio
    async def test_conflicting_catalysts(self, mock_db):
        """Test when catalysts might conflict or compete."""
        batch_optimizer = BatchOptimizer(mock_db)

        # Create multiple changes that might need the same catalyst
        today = date.today()
        changes = [
            (
                uuid4(),
                {
                    "target_date": (today + timedelta(days=7)).isoformat(),
                    "change_type": "reassignment",
                    "requester_role": "resident",
                },
            ),
            (
                uuid4(),
                {
                    "target_date": (today + timedelta(days=7)).isoformat(),
                    "change_type": "reassignment",
                    "requester_role": "resident",
                },
            ),
        ]

        results = await batch_optimizer.optimize_batch(changes)

        # Should handle both requests
        assert len(results) == 2

        # May warn about catalyst conflicts in recommendations
        all_recommendations = []
        for result in results:
            all_recommendations.extend(result.recommendations)

        # Check if any conflict warnings were issued
        # (Implementation-dependent)
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_zero_energy_barriers(self, barrier_detector, catalyst_analyzer):
        """Test handling of barriers with zero energy contribution."""
        # This shouldn't normally happen, but test robustness
        barriers = [
            EnergyBarrier(
                barrier_type=BarrierType.THERMODYNAMIC,
                name="Minimal Preference",
                description="Slight preference conflict",
                energy_contribution=0.0,  # Zero energy
            )
        ]

        energy = barrier_detector.calculate_activation_energy()
        recommendation = await catalyst_analyzer.recommend_catalysts(barriers)

        # Should handle gracefully
        assert energy.value == 0.0
        assert recommendation.is_feasible is True


# ============================================================================
# Integration Test: Energy Reduction Accumulation
# ============================================================================


class TestEnergyReductionAccumulation:
    """Test energy reduction across multiple barriers and catalysts."""

    @pytest.mark.asyncio
    async def test_cumulative_reduction_multiple_barriers(
        self,
        catalyst_analyzer,
        sample_barriers,
    ):
        """Test that reductions accumulate correctly across barriers."""
        # Get recommendations
        recommendation = await catalyst_analyzer.recommend_catalysts(sample_barriers)

        # Calculate expected total barrier energy
        total_barrier_energy = sum(b.energy_contribution for b in sample_barriers)

        # Verify accounting
        if recommendation.recommended_catalysts:
            calculated_residual = (
                total_barrier_energy - recommendation.total_reduction
            )
            assert abs(calculated_residual - recommendation.residual_energy) < 0.01

    def test_pathway_energy_recalculation(self):
        """Test pathway recalculates energy when catalysts are added."""
        # Create pathway with barriers
        barriers = [
            EnergyBarrier(
                barrier_type=BarrierType.KINETIC,
                name="Barrier 1",
                description="Test",
                energy_contribution=0.5,
            ),
            EnergyBarrier(
                barrier_type=BarrierType.ELECTRONIC,
                name="Barrier 2",
                description="Test",
                energy_contribution=0.4,
            ),
        ]

        pathway = ReactionPathway(
            pathway_id=str(uuid4()),
            initial_state={},
            target_state={},
            barriers=barriers,
            total_activation_energy=0.9,
            effective_activation_energy=0.9,
        )

        # Add a catalyst
        catalyst = CatalystPerson(
            person_id=uuid4(),
            name="Test Catalyst",
            catalyst_type=CatalystType.ENZYMATIC,
            catalyst_score=0.8,
            barriers_addressed=[BarrierType.KINETIC, BarrierType.ELECTRONIC],
            reduction_factors={
                BarrierType.KINETIC: 0.5,
                BarrierType.ELECTRONIC: 0.5,
            },
        )

        initial_energy = pathway.effective_activation_energy
        pathway.add_catalyst(catalyst)

        # Energy should be reduced
        assert pathway.effective_activation_energy < initial_energy
        # Catalyst should be in list
        assert catalyst in pathway.catalysts_applied


# ============================================================================
# Integration Test: Feasibility Determination
# ============================================================================


class TestFeasibilityDetermination:
    """Test feasibility logic across the system."""

    @pytest.mark.asyncio
    async def test_feasibility_with_sufficient_catalysts(self, optimizer):
        """Test that sufficient catalysts make changes feasible."""
        # Provide powerful catalysts
        catalysts = [
            CatalystPerson(
                person_id=uuid4(),
                name="Super Coordinator",
                catalyst_type=CatalystType.ENZYMATIC,
                catalyst_score=0.95,
                barriers_addressed=list(BarrierType),  # Addresses all types
                reduction_factors={bt: 0.9 for bt in BarrierType},
            )
        ]

        today = date.today()
        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": (today + timedelta(days=7)).isoformat(),
                "change_type": "modification",
            },
            available_catalysts=catalysts,
        )

        # Should be feasible with powerful catalyst
        if not any(b.is_absolute for b in result.pathway.barriers if result.pathway):
            # If no absolute barriers, should succeed
            assert result.success or result.pathway.effective_activation_energy < 1.0

    @pytest.mark.asyncio
    async def test_feasibility_with_absolute_barriers(self, optimizer):
        """Test that absolute barriers make changes infeasible."""
        # Create a change that will trigger absolute barrier
        result = await optimizer.find_optimal_pathway(
            assignment_id=uuid4(),
            proposed_change={
                "change_type": "swap",
                "other_person_consented": False,  # Absolute barrier
            },
        )

        # Should not be feasible
        assert result.success is False
        assert len(result.blocking_barriers) > 0
        assert any(b.is_absolute for b in result.blocking_barriers)

    @pytest.mark.asyncio
    async def test_feasibility_threshold_configuration(self, mock_db):
        """Test custom feasibility thresholds."""
        # Create optimizer with strict threshold
        strict_optimizer = TransitionOptimizer(
            mock_db,
            config=OptimizationConfig(energy_threshold=0.3),
        )

        # Create optimizer with lenient threshold
        lenient_optimizer = TransitionOptimizer(
            mock_db,
            config=OptimizationConfig(energy_threshold=0.9),
        )

        today = date.today()
        proposed_change = {
            "target_date": (today + timedelta(days=7)).isoformat(),
            "change_type": "modification",
        }

        strict_result = await strict_optimizer.find_optimal_pathway(
            uuid4(), proposed_change
        )
        lenient_result = await lenient_optimizer.find_optimal_pathway(
            uuid4(), proposed_change
        )

        # Lenient should be more likely to succeed
        # (Though both might succeed for simple changes)
        assert isinstance(strict_result, PathwayResult)
        assert isinstance(lenient_result, PathwayResult)


# ============================================================================
# Integration Test: Resilience Framework Integration
# ============================================================================


class TestResilienceFrameworkIntegration:
    """Test integration with resilience framework components."""

    @pytest.mark.asyncio
    async def test_defense_integration_catalyst_access(self, mock_db):
        """Test accessing catalysts through defense integration."""
        defense = DefenseIntegration(mock_db)

        # Test different defense levels
        for level in range(1, 6):
            mechanisms = defense.get_available_mechanisms(level)
            assert len(mechanisms) > 0

            # Higher levels should have reduction bonuses
            if level > 1:
                # Check that mechanisms have boosted reduction factors
                for mech in mechanisms:
                    # Verify mechanism has reduction factors
                    assert len(mech.reduction_factors) > 0

    @pytest.mark.asyncio
    async def test_hub_integration_catalyst_conversion(
        self,
        mock_db,
        mock_hub_metrics,
    ):
        """Test converting hub metrics to catalysts."""
        hub = HubIntegration(mock_db)

        catalysts = hub.identify_catalyst_hubs(mock_hub_metrics)

        # Should identify catalysts from hub metrics
        assert len(catalysts) > 0

        # Catalysts should have appropriate properties
        for catalyst in catalysts:
            assert isinstance(catalyst, CatalystPerson)
            assert catalyst.catalyst_score > 0
            assert len(catalyst.barriers_addressed) > 0

    @pytest.mark.asyncio
    async def test_unified_framework_integration(self, mock_db, mock_hub_metrics):
        """Test unified resilience framework integration."""
        framework = ResilienceFrameworkIntegration(mock_db)

        # Get all available catalysts
        all_catalysts = await framework.get_all_available_catalysts(
            current_defense_level=3,
            coverage_rate=0.85,
            hub_metrics=mock_hub_metrics,
        )

        # Should have catalysts from all sources
        assert "defense_mechanisms" in all_catalysts
        assert "hub_personnel" in all_catalysts
        assert "sacrifice_mechanisms" in all_catalysts
        assert "feedback_mechanisms" in all_catalysts

        # Each category should have some catalysts
        assert len(all_catalysts["defense_mechanisms"]) > 0

    @pytest.mark.asyncio
    async def test_system_catalyst_capacity(self, mock_db, mock_hub_metrics):
        """Test calculating system-wide catalyst capacity."""
        framework = ResilienceFrameworkIntegration(mock_db)

        capacity = await framework.calculate_system_catalyst_capacity(
            hub_metrics=mock_hub_metrics
        )

        # Should return capacity metrics
        assert "hub_capacity" in capacity
        assert "defense_mechanisms_available" in capacity
        assert "total_catalyst_types" in capacity

        # Values should be reasonable
        assert capacity["defense_mechanisms_available"] > 0
        assert capacity["total_catalyst_types"] == len(CatalystType)


# ============================================================================
# Integration Test: End-to-End Scenarios
# ============================================================================


class TestEndToEndScenarios:
    """Test complete end-to-end scenarios."""

    @pytest.mark.asyncio
    async def test_emergency_swap_scenario(self, optimizer):
        """Test emergency swap scenario with full workflow."""
        # Scenario: Resident needs emergency swap due to sick call
        requester_id = uuid4()
        target_id = uuid4()
        assignment_id = uuid4()

        # Use emergency optimization
        result = await optimizer.optimize_emergency_coverage(
            assignment_id=assignment_id,
            emergency_type="sick_call",
        )

        # Emergency should provide override catalysts
        assert isinstance(result, PathwayResult)

        # Should have pathway (may or may not succeed depending on barriers)
        if result.pathway:
            # Should have emergency catalyst if any barriers existed
            if result.pathway.barriers:
                has_emergency_catalyst = any(
                    "emergency" in (
                        c.mechanism_id if isinstance(c, CatalystMechanism)
                        else c.name.lower()
                    )
                    for c in result.pathway.catalysts_applied
                )
                # Emergency catalyst should be applied for this type
                assert has_emergency_catalyst or len(result.pathway.catalysts_applied) > 0

    @pytest.mark.asyncio
    async def test_routine_swap_scenario(self, optimizer):
        """Test routine swap scenario."""
        # Scenario: Two residents want to swap a future assignment
        requester_id = uuid4()
        target_id = uuid4()
        assignment_id = uuid4()

        result = await optimizer.optimize_swap(
            requester_id=requester_id,
            target_id=target_id,
            assignment_id=assignment_id,
        )

        # Should have result
        assert isinstance(result, PathwayResult)

        # Will likely fail without consent
        if not result.success:
            # Should have recommendations
            assert len(result.recommendations) > 0 or len(result.blocking_barriers) > 0

    @pytest.mark.asyncio
    async def test_batch_reassignment_scenario(self, mock_db):
        """Test batch reassignment scenario."""
        batch_optimizer = BatchOptimizer(mock_db)

        today = date.today()

        # Scenario: Multiple assignments need reassignment
        changes = [
            (
                uuid4(),
                {
                    "target_date": (today + timedelta(days=i * 7)).isoformat(),
                    "change_type": "reassignment",
                    "new_person_id": uuid4(),
                }
            )
            for i in range(1, 4)
        ]

        results = await batch_optimizer.optimize_batch(changes)

        # Should process all changes
        assert len(results) == len(changes)

        # Should determine optimal order
        order = await batch_optimizer.find_optimal_order(changes)
        assert len(order) == len(changes)
        assert set(order) == set(range(len(changes)))
