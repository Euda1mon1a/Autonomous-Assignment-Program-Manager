"""Tests for scheduling_catalyst catalyst analysis."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.scheduling_catalyst.catalysts import (
    CatalystAnalyzer,
    CatalystMatch,
    CatalystRecommendation,
    CatalystScorer,
)
from app.scheduling_catalyst.models import (
    BarrierType,
    CatalystMechanism,
    CatalystPerson,
    CatalystType,
    EnergyBarrier,
)


class TestCatalystScorer:
    """Tests for CatalystScorer."""

    def test_score_person_catalyst_available(self):
        """Test scoring an available person catalyst."""
        catalyst = CatalystPerson(
            person_id=uuid4(),
            name="Coordinator",
            catalyst_type=CatalystType.ENZYMATIC,
            catalyst_score=0.9,
            barriers_addressed=[BarrierType.ELECTRONIC],
            reduction_factors={BarrierType.ELECTRONIC: 0.8},
            is_available=True,
            capacity_remaining=1.0,
        )

        barrier = EnergyBarrier(
            barrier_type=BarrierType.ELECTRONIC,
            name="Auth",
            description="Test",
            energy_contribution=0.5,
        )

        score = CatalystScorer.score_person_catalyst(catalyst, barrier)
        # availability(0.3) + capability(0.36) + capacity(0.2) + history(0.05) = 0.91
        assert 0.8 <= score <= 1.0

    def test_score_person_catalyst_unavailable(self):
        """Test scoring an unavailable person catalyst."""
        catalyst = CatalystPerson(
            person_id=uuid4(),
            name="Coordinator",
            catalyst_type=CatalystType.ENZYMATIC,
            catalyst_score=0.9,
            barriers_addressed=[BarrierType.ELECTRONIC],
            reduction_factors={BarrierType.ELECTRONIC: 0.8},
            is_available=False,
        )

        barrier = EnergyBarrier(
            barrier_type=BarrierType.ELECTRONIC,
            name="Auth",
            description="Test",
            energy_contribution=0.5,
        )

        score = CatalystScorer.score_person_catalyst(catalyst, barrier)
        # availability=0, so score is reduced
        assert score < 0.7

    def test_score_person_catalyst_cannot_address(self):
        """Test scoring when catalyst cannot address barrier."""
        catalyst = CatalystPerson(
            person_id=uuid4(),
            name="Hub Faculty",
            catalyst_type=CatalystType.HOMOGENEOUS,
            catalyst_score=0.8,
            barriers_addressed=[BarrierType.THERMODYNAMIC],
            reduction_factors={BarrierType.THERMODYNAMIC: 0.6},
        )

        barrier = EnergyBarrier(
            barrier_type=BarrierType.REGULATORY,
            name="ACGME",
            description="Test",
            energy_contribution=0.8,
        )

        score = CatalystScorer.score_person_catalyst(catalyst, barrier)
        assert score == 0.0

    def test_score_mechanism_catalyst(self):
        """Test scoring a mechanism catalyst."""
        mechanism = CatalystMechanism(
            mechanism_id="auto_matcher",
            name="Auto-Matcher",
            catalyst_type=CatalystType.HETEROGENEOUS,
            barriers_addressed=[BarrierType.THERMODYNAMIC],
            reduction_factors={BarrierType.THERMODYNAMIC: 0.6},
            is_active=True,
        )

        barrier = EnergyBarrier(
            barrier_type=BarrierType.THERMODYNAMIC,
            name="Workload",
            description="Test",
            energy_contribution=0.4,
        )

        score = CatalystScorer.score_mechanism_catalyst(mechanism, barrier)
        assert score == 0.6

    def test_score_inactive_mechanism(self):
        """Test scoring an inactive mechanism."""
        mechanism = CatalystMechanism(
            mechanism_id="emergency",
            name="Emergency Override",
            catalyst_type=CatalystType.ENZYMATIC,
            barriers_addressed=[BarrierType.KINETIC],
            reduction_factors={BarrierType.KINETIC: 0.9},
            is_active=False,
        )

        barrier = EnergyBarrier(
            barrier_type=BarrierType.KINETIC,
            name="Freeze",
            description="Test",
            energy_contribution=0.5,
        )

        score = CatalystScorer.score_mechanism_catalyst(mechanism, barrier)
        assert score == 0.0

    def test_calculate_combined_reduction(self):
        """Test combined reduction from multiple catalysts."""
        catalysts = [
            CatalystPerson(
                person_id=uuid4(),
                name="Catalyst 1",
                catalyst_type=CatalystType.HOMOGENEOUS,
                catalyst_score=0.7,
                barriers_addressed=[BarrierType.KINETIC],
                reduction_factors={BarrierType.KINETIC: 0.4},
                is_available=True,
                capacity_remaining=1.0,
            ),
            CatalystMechanism(
                mechanism_id="mech",
                name="Mechanism",
                catalyst_type=CatalystType.HETEROGENEOUS,
                barriers_addressed=[BarrierType.KINETIC],
                reduction_factors={BarrierType.KINETIC: 0.3},
                is_active=True,
            ),
        ]

        barrier = EnergyBarrier(
            barrier_type=BarrierType.KINETIC,
            name="Freeze",
            description="Test",
            energy_contribution=1.0,
        )

        combined = CatalystScorer.calculate_combined_reduction(catalysts, barrier)
        # First reduces to 0.6, second reduces that to 0.42
        # Total reduction = 1.0 - 0.42 = 0.58
        assert 0.5 <= combined <= 0.6


class TestCatalystMatch:
    """Tests for CatalystMatch dataclass."""

    def test_catalyst_match_creation(self):
        """Test creating a catalyst match."""
        catalyst = CatalystPerson(
            person_id=uuid4(),
            name="Test",
            catalyst_type=CatalystType.ENZYMATIC,
            catalyst_score=0.8,
            barriers_addressed=[BarrierType.ELECTRONIC],
            reduction_factors={BarrierType.ELECTRONIC: 0.7},
        )

        barrier = EnergyBarrier(
            barrier_type=BarrierType.ELECTRONIC,
            name="Auth",
            description="Test",
            energy_contribution=0.5,
        )

        match = CatalystMatch(
            catalyst=catalyst,
            barrier=barrier,
            reduction=0.7,
            confidence=0.85,
        )

        assert match.reduction == 0.7
        assert match.confidence == 0.85


class TestCatalystRecommendation:
    """Tests for CatalystRecommendation dataclass."""

    def test_feasible_recommendation(self):
        """Test creating a feasible recommendation."""
        barriers = [
            EnergyBarrier(
                barrier_type=BarrierType.KINETIC,
                name="Test",
                description="Test",
                energy_contribution=0.5,
            ),
        ]

        recommendation = CatalystRecommendation(
            barriers=barriers,
            recommended_catalysts=[],
            total_reduction=0.4,
            residual_energy=0.1,
            is_feasible=True,
        )

        assert recommendation.is_feasible is True
        assert recommendation.residual_energy == 0.1

    def test_infeasible_recommendation(self):
        """Test creating an infeasible recommendation."""
        barriers = [
            EnergyBarrier(
                barrier_type=BarrierType.REGULATORY,
                name="ACGME",
                description="Test",
                energy_contribution=1.0,
                is_absolute=True,
            ),
        ]

        recommendation = CatalystRecommendation(
            barriers=barriers,
            recommended_catalysts=[],
            total_reduction=0.0,
            residual_energy=1.0,
            is_feasible=False,
        )

        assert recommendation.is_feasible is False


class TestCatalystAnalyzer:
    """Tests for CatalystAnalyzer."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def analyzer(self, mock_db):
        """Create catalyst analyzer."""
        return CatalystAnalyzer(mock_db)

    @pytest.mark.asyncio
    async def test_find_person_catalysts(self, analyzer):
        """Test finding person catalysts."""
        barriers = [
            EnergyBarrier(
                barrier_type=BarrierType.ELECTRONIC,
                name="Auth",
                description="Test",
                energy_contribution=0.5,
            ),
        ]

        catalysts = await analyzer.find_person_catalysts(barriers)
        assert len(catalysts) >= 1
        # Should find coordinators for electronic barriers
        assert any(BarrierType.ELECTRONIC in c.barriers_addressed for c in catalysts)

    @pytest.mark.asyncio
    async def test_find_mechanism_catalysts(self, analyzer):
        """Test finding mechanism catalysts."""
        barriers = [
            EnergyBarrier(
                barrier_type=BarrierType.THERMODYNAMIC,
                name="Workload",
                description="Test",
                energy_contribution=0.4,
            ),
            EnergyBarrier(
                barrier_type=BarrierType.KINETIC,
                name="Freeze",
                description="Test",
                energy_contribution=0.5,
            ),
        ]

        mechanisms = await analyzer.find_mechanism_catalysts(barriers)
        assert len(mechanisms) >= 2  # At least auto-matcher and emergency

        # Should have auto-matcher for thermodynamic
        assert any(m.mechanism_id == "auto_matcher" for m in mechanisms)

        # Should have emergency override for kinetic
        assert any(m.mechanism_id == "emergency_override" for m in mechanisms)

    @pytest.mark.asyncio
    async def test_recommend_catalysts(self, analyzer):
        """Test generating catalyst recommendations."""
        barriers = [
            EnergyBarrier(
                barrier_type=BarrierType.ELECTRONIC,
                name="Auth",
                description="Test",
                energy_contribution=0.5,
            ),
            EnergyBarrier(
                barrier_type=BarrierType.THERMODYNAMIC,
                name="Workload",
                description="Test",
                energy_contribution=0.3,
            ),
        ]

        recommendation = await analyzer.recommend_catalysts(barriers)

        assert recommendation.barriers == barriers
        assert len(recommendation.recommended_catalysts) >= 1
        assert recommendation.total_reduction > 0

    @pytest.mark.asyncio
    async def test_recommend_catalysts_infeasible(self, analyzer):
        """Test recommendations for infeasible barriers."""
        barriers = [
            EnergyBarrier(
                barrier_type=BarrierType.REGULATORY,
                name="ACGME",
                description="Test",
                energy_contribution=1.0,
                is_absolute=True,
            ),
        ]

        recommendation = await analyzer.recommend_catalysts(barriers)

        assert recommendation.is_feasible is False
        # Absolute barriers cannot be catalyzed
        assert len(recommendation.recommended_catalysts) == 0

    @pytest.mark.asyncio
    async def test_get_catalyst_statistics(self, analyzer):
        """Test getting catalyst statistics."""
        stats = await analyzer.get_catalyst_statistics()

        assert "person_catalysts" in stats
        assert "mechanism_catalysts" in stats
        assert "coverage" in stats
        assert stats["person_catalysts"]["total"] >= 0
        assert stats["mechanism_catalysts"]["total"] >= 0
