"""Tests for scheduling_catalyst barrier detection."""

from datetime import date, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.scheduling_catalyst.barriers import (
    BarrierClassifier,
    BarrierDetector,
    BarrierWeights,
)
from app.scheduling_catalyst.models import BarrierType, EnergyBarrier


class TestBarrierWeights:
    """Tests for BarrierWeights configuration."""

    def test_default_weights(self):
        """Test default barrier weights."""
        weights = BarrierWeights()
        assert weights.kinetic == 0.3
        assert weights.thermodynamic == 0.2
        assert weights.steric == 0.25
        assert weights.electronic == 0.15
        assert weights.regulatory == 0.4

    def test_get_weight(self):
        """Test getting weight for barrier type."""
        weights = BarrierWeights()
        assert weights.get_weight(BarrierType.KINETIC) == 0.3
        assert weights.get_weight(BarrierType.REGULATORY) == 0.4

    def test_custom_weights(self):
        """Test custom weight configuration."""
        weights = BarrierWeights(kinetic=0.5, regulatory=0.6)
        assert weights.kinetic == 0.5
        assert weights.regulatory == 0.6


class TestBarrierDetector:
    """Tests for BarrierDetector."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def detector(self, mock_db):
        """Create barrier detector with mock db."""
        return BarrierDetector(mock_db)

    @pytest.mark.asyncio
    async def test_detect_kinetic_barriers_within_freeze(self, detector):
        """Test detecting freeze horizon barriers."""
        today = date.today()
        target_date = today + timedelta(days=7)

        barriers = await detector.detect_all_barriers(
            assignment_id=uuid4(),
            proposed_change={"target_date": target_date.isoformat()},
            reference_date=today,
        )

        kinetic_barriers = [
            b for b in barriers if b.barrier_type == BarrierType.KINETIC
        ]
        assert len(kinetic_barriers) >= 1

        freeze_barrier = next(
            (b for b in kinetic_barriers if b.source == "freeze_horizon"),
            None,
        )
        assert freeze_barrier is not None
        assert freeze_barrier.energy_contribution > 0

    @pytest.mark.asyncio
    async def test_detect_short_notice_barrier(self, detector):
        """Test detecting short notice barriers."""
        today = date.today()
        target_date = today + timedelta(days=1)

        barriers = await detector.detect_all_barriers(
            assignment_id=uuid4(),
            proposed_change={"target_date": target_date.isoformat()},
            reference_date=today,
        )

        short_notice = [b for b in barriers if b.source == "short_notice"]
        assert len(short_notice) == 1
        assert short_notice[0].energy_contribution == 0.3

    @pytest.mark.asyncio
    async def test_detect_electronic_barriers_reassignment(self, detector):
        """Test detecting authorization barriers for reassignments."""
        barriers = await detector.detect_all_barriers(
            assignment_id=uuid4(),
            proposed_change={
                "change_type": "reassignment",
                "requester_role": "resident",
            },
        )

        auth_barriers = [
            b
            for b in barriers
            if b.barrier_type == BarrierType.ELECTRONIC
            and b.source == "role_authorization"
        ]
        assert len(auth_barriers) == 1

    @pytest.mark.asyncio
    async def test_detect_consent_barrier_swap(self, detector):
        """Test detecting consent barrier for swaps."""
        barriers = await detector.detect_all_barriers(
            assignment_id=uuid4(),
            proposed_change={
                "change_type": "swap",
                "other_person_consented": False,
            },
        )

        consent_barriers = [b for b in barriers if b.source == "consent_check"]
        assert len(consent_barriers) == 1
        assert consent_barriers[0].is_absolute is True

    @pytest.mark.asyncio
    async def test_no_barriers_outside_freeze(self, detector):
        """Test no freeze barrier when outside freeze horizon."""
        today = date.today()
        target_date = today + timedelta(days=30)

        barriers = await detector.detect_all_barriers(
            assignment_id=uuid4(),
            proposed_change={"target_date": target_date.isoformat()},
            reference_date=today,
        )

        freeze_barriers = [b for b in barriers if b.source == "freeze_horizon"]
        assert len(freeze_barriers) == 0

    @pytest.mark.asyncio
    async def test_calculate_activation_energy(self, detector):
        """Test calculating activation energy from barriers."""
        today = date.today()
        target_date = today + timedelta(days=7)

        await detector.detect_all_barriers(
            assignment_id=uuid4(),
            proposed_change={
                "target_date": target_date.isoformat(),
                "change_type": "reassignment",
                "requester_role": "resident",
            },
            reference_date=today,
        )

        energy = detector.calculate_activation_energy()
        assert 0.0 <= energy.value <= 1.0
        assert len(energy.components) > 0


class TestBarrierClassifier:
    """Tests for BarrierClassifier."""

    def test_classify_severity_critical(self):
        """Test critical severity for absolute barriers."""
        barrier = EnergyBarrier(
            barrier_type=BarrierType.REGULATORY,
            name="ACGME",
            description="Violation",
            energy_contribution=1.0,
            is_absolute=True,
        )
        assert BarrierClassifier.classify_severity(barrier) == "critical"

    def test_classify_severity_high(self):
        """Test high severity for high-energy barriers."""
        barrier = EnergyBarrier(
            barrier_type=BarrierType.STERIC,
            name="Credentials",
            description="Missing",
            energy_contribution=0.8,
        )
        assert BarrierClassifier.classify_severity(barrier) == "high"

    def test_classify_severity_medium(self):
        """Test medium severity."""
        barrier = EnergyBarrier(
            barrier_type=BarrierType.KINETIC,
            name="Freeze",
            description="Within freeze",
            energy_contribution=0.5,
        )
        assert BarrierClassifier.classify_severity(barrier) == "medium"

    def test_classify_severity_low(self):
        """Test low severity."""
        barrier = EnergyBarrier(
            barrier_type=BarrierType.THERMODYNAMIC,
            name="Preference",
            description="Conflicts",
            energy_contribution=0.2,
        )
        assert BarrierClassifier.classify_severity(barrier) == "low"

    def test_classify_actionability_immutable(self):
        """Test immutable actionability for absolute barriers."""
        barrier = EnergyBarrier(
            barrier_type=BarrierType.REGULATORY,
            name="ACGME",
            description="Violation",
            energy_contribution=1.0,
            is_absolute=True,
        )
        assert BarrierClassifier.classify_actionability(barrier) == "immutable"

    def test_classify_actionability_catalyzable(self):
        """Test catalyzable actionability."""
        barrier = EnergyBarrier(
            barrier_type=BarrierType.ELECTRONIC,
            name="Auth",
            description="Needs approval",
            energy_contribution=0.5,
        )
        assert BarrierClassifier.classify_actionability(barrier) == "catalyzable"

    def test_get_recommended_catalysts(self):
        """Test getting recommended catalysts for barrier."""
        barrier = EnergyBarrier(
            barrier_type=BarrierType.KINETIC,
            name="Freeze",
            description="Freeze period",
            energy_contribution=0.5,
        )
        recommendations = BarrierClassifier.get_recommended_catalysts(barrier)
        assert "coordinator_override" in recommendations
        assert "emergency_code" in recommendations

    def test_get_recommended_catalysts_absolute(self):
        """Test no recommendations for absolute barriers."""
        barrier = EnergyBarrier(
            barrier_type=BarrierType.REGULATORY,
            name="ACGME",
            description="Violation",
            energy_contribution=1.0,
            is_absolute=True,
        )
        recommendations = BarrierClassifier.get_recommended_catalysts(barrier)
        assert recommendations == []

    def test_summarize_barriers_empty(self):
        """Test summarizing empty barrier list."""
        summary = BarrierClassifier.summarize_barriers([])
        assert summary["total_count"] == 0
        assert summary["has_absolute"] is False
        assert summary["recommended_approach"] == "proceed"

    def test_summarize_barriers_with_absolute(self):
        """Test summarizing barriers with absolute barrier."""
        barriers = [
            EnergyBarrier(
                barrier_type=BarrierType.KINETIC,
                name="Freeze",
                description="Test",
                energy_contribution=0.3,
            ),
            EnergyBarrier(
                barrier_type=BarrierType.REGULATORY,
                name="ACGME",
                description="Test",
                energy_contribution=1.0,
                is_absolute=True,
            ),
        ]
        summary = BarrierClassifier.summarize_barriers(barriers)
        assert summary["total_count"] == 2
        assert summary["has_absolute"] is True
        assert summary["highest_severity"] == "critical"
        assert summary["recommended_approach"] == "blocked"

    def test_summarize_barriers_seek_catalyst(self):
        """Test summarizing barriers that need catalysts."""
        barriers = [
            EnergyBarrier(
                barrier_type=BarrierType.KINETIC,
                name="Freeze",
                description="Test",
                energy_contribution=0.8,
            ),
        ]
        summary = BarrierClassifier.summarize_barriers(barriers)
        assert summary["recommended_approach"] == "seek_catalyst"
