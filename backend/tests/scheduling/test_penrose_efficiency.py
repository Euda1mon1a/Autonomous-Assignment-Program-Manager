"""
Tests for Penrose Process efficiency extraction.

Tests cover:
- Ergosphere identification
- Phase decomposition
- Negative-energy swap detection
- Energy tracking and limits
- Cascade optimization
- Visualization generation
"""

import uuid
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.rotation_template import RotationTemplate
from app.scheduling.penrose_efficiency import (
    ErgospherePeriod,
    PenroseEfficiencyExtractor,
    PenroseSwap,
    PhaseComponent,
    RotationEnergyTracker,
)
from app.scheduling.penrose_visualization import PenroseVisualizer, VisualizationConfig


class TestErgospherePeriod:
    """Test suite for ErgospherePeriod dataclass."""

    def test_create_valid_ergosphere(self):
        """Test creating valid ergosphere period."""
        start = datetime(2024, 1, 1, 0, 0)
        end = datetime(2024, 1, 2, 0, 0)

        ergosphere = ErgospherePeriod(
            start_time=start,
            end_time=end,
            rotation_velocity=2.5,
            extraction_potential=0.15,
            boundary_type="week_end",
        )

        assert ergosphere.start_time == start
        assert ergosphere.end_time == end
        assert ergosphere.rotation_velocity == 2.5
        assert ergosphere.extraction_potential == 0.15
        assert ergosphere.boundary_type == "week_end"
        assert ergosphere.affected_assignments == []

    def test_ergosphere_duration_hours(self):
        """Test duration calculation in hours."""
        start = datetime(2024, 1, 1, 12, 0)
        end = datetime(2024, 1, 2, 18, 0)

        ergosphere = ErgospherePeriod(
            start_time=start,
            end_time=end,
            rotation_velocity=1.0,
            extraction_potential=0.1,
            boundary_type="block_transition",
        )

        assert ergosphere.duration_hours == 30.0  # 1.5 days

    def test_ergosphere_high_potential(self):
        """Test high potential detection."""
        ergosphere_high = ErgospherePeriod(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            rotation_velocity=2.0,
            extraction_potential=0.20,  # 20% > 15% threshold
            boundary_type="week_end",
        )

        ergosphere_low = ErgospherePeriod(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            rotation_velocity=1.0,
            extraction_potential=0.10,  # 10% < 15% threshold
            boundary_type="week_end",
        )

        assert ergosphere_high.is_high_potential
        assert not ergosphere_low.is_high_potential

    def test_ergosphere_invalid_time_order(self):
        """Test validation of time ordering."""
        with pytest.raises(ValueError, match="start_time must be before end_time"):
            ErgospherePeriod(
                start_time=datetime(2024, 1, 2),
                end_time=datetime(2024, 1, 1),  # End before start
                rotation_velocity=1.0,
                extraction_potential=0.1,
                boundary_type="week_end",
            )

    def test_ergosphere_extraction_potential_warning(self, caplog):
        """Test warning when exceeding Penrose limit."""
        ergosphere = ErgospherePeriod(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            rotation_velocity=5.0,
            extraction_potential=0.35,  # Exceeds 29% limit
            boundary_type="week_end",
        )

        assert "exceeds Penrose limit" in caplog.text
        assert ergosphere.extraction_potential == 0.35  # Still created


class TestPhaseComponent:
    """Test suite for PhaseComponent dataclass."""

    def test_create_valid_phase(self):
        """Test creating valid phase component."""
        assignment_id = uuid.uuid4()
        phase_start = datetime(2024, 1, 1, 8, 0)
        phase_end = datetime(2024, 1, 1, 12, 0)

        phase = PhaseComponent(
            assignment_id=assignment_id,
            phase_type="transition",
            energy_state="negative",
            phase_start=phase_start,
            phase_end=phase_end,
            conflict_score=2,
            flexibility_score=0.7,
        )

        assert phase.assignment_id == assignment_id
        assert phase.phase_type == "transition"
        assert phase.energy_state == "negative"
        assert phase.is_negative_energy

    def test_phase_invalid_type(self):
        """Test validation of phase type."""
        with pytest.raises(ValueError, match="phase_type must be one of"):
            PhaseComponent(
                assignment_id=uuid.uuid4(),
                phase_type="invalid_phase",
                energy_state="positive",
                phase_start=datetime(2024, 1, 1),
                phase_end=datetime(2024, 1, 2),
                conflict_score=0,
                flexibility_score=0.5,
            )

    def test_phase_invalid_energy_state(self):
        """Test validation of energy state."""
        with pytest.raises(ValueError, match="energy_state must be one of"):
            PhaseComponent(
                assignment_id=uuid.uuid4(),
                phase_type="transition",
                energy_state="invalid_state",
                phase_start=datetime(2024, 1, 1),
                phase_end=datetime(2024, 1, 2),
                conflict_score=0,
                flexibility_score=0.5,
            )


class TestPenroseSwap:
    """Test suite for PenroseSwap dataclass."""

    def test_create_valid_swap(self):
        """Test creating valid Penrose swap."""
        ergosphere = ErgospherePeriod(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            rotation_velocity=2.0,
            extraction_potential=0.15,
            boundary_type="week_end",
        )

        swap = PenroseSwap(
            swap_id=uuid.uuid4(),
            assignment_a=uuid.uuid4(),
            assignment_b=uuid.uuid4(),
            local_cost=2.0,
            global_benefit=5.0,
            ergosphere_period=ergosphere,
        )

        assert swap.local_cost == 2.0
        assert swap.global_benefit == 5.0
        assert swap.net_extraction == 3.0  # 5.0 - 2.0
        assert swap.is_beneficial
        assert not swap.executed

    def test_swap_net_extraction(self):
        """Test net extraction calculation."""
        ergosphere = ErgospherePeriod(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            rotation_velocity=1.0,
            extraction_potential=0.1,
            boundary_type="week_end",
        )

        swap = PenroseSwap(
            swap_id=uuid.uuid4(),
            assignment_a=uuid.uuid4(),
            assignment_b=uuid.uuid4(),
            local_cost=3.0,
            global_benefit=8.0,
            ergosphere_period=ergosphere,
        )

        assert swap.net_extraction == 5.0

    def test_swap_extraction_ratio(self):
        """Test extraction efficiency ratio."""
        ergosphere = ErgospherePeriod(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            rotation_velocity=1.0,
            extraction_potential=0.1,
            boundary_type="week_end",
        )

        swap = PenroseSwap(
            swap_id=uuid.uuid4(),
            assignment_a=uuid.uuid4(),
            assignment_b=uuid.uuid4(),
            local_cost=2.0,
            global_benefit=6.0,
            ergosphere_period=ergosphere,
        )

        assert swap.extraction_ratio == 3.0  # 6.0 / 2.0

    def test_swap_zero_cost_extraction_ratio(self):
        """Test extraction ratio with near-zero cost."""
        ergosphere = ErgospherePeriod(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            rotation_velocity=1.0,
            extraction_potential=0.1,
            boundary_type="week_end",
        )

        swap = PenroseSwap(
            swap_id=uuid.uuid4(),
            assignment_a=uuid.uuid4(),
            assignment_b=uuid.uuid4(),
            local_cost=0.0001,
            global_benefit=5.0,
            ergosphere_period=ergosphere,
        )

        assert swap.extraction_ratio == float("inf")

    def test_swap_not_beneficial(self):
        """Test swap that is not beneficial."""
        ergosphere = ErgospherePeriod(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            rotation_velocity=1.0,
            extraction_potential=0.1,
            boundary_type="week_end",
        )

        swap = PenroseSwap(
            swap_id=uuid.uuid4(),
            assignment_a=uuid.uuid4(),
            assignment_b=uuid.uuid4(),
            local_cost=5.0,
            global_benefit=2.0,
            ergosphere_period=ergosphere,
        )

        assert swap.net_extraction == -3.0
        assert not swap.is_beneficial


class TestRotationEnergyTracker:
    """Test suite for RotationEnergyTracker."""

    def test_tracker_initialization(self):
        """Test tracker initialization."""
        tracker = RotationEnergyTracker(initial_rotation_energy=100.0)

        assert tracker.initial_rotation_energy == 100.0
        assert tracker.extracted_energy == 0.0
        assert tracker.remaining_energy == 100.0
        assert tracker.extraction_fraction == 0.0
        assert not tracker.is_exhausted

    def test_tracker_extraction_budget(self):
        """Test extraction budget calculation."""
        tracker = RotationEnergyTracker(initial_rotation_energy=100.0)

        # Max extractable = 100 * 0.29 = 29
        assert tracker.extraction_budget == 29.0

    def test_tracker_record_extraction(self):
        """Test recording an extraction."""
        tracker = RotationEnergyTracker(initial_rotation_energy=100.0)

        ergosphere = ErgospherePeriod(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            rotation_velocity=1.0,
            extraction_potential=0.1,
            boundary_type="week_end",
        )

        swap = PenroseSwap(
            swap_id=uuid.uuid4(),
            assignment_a=uuid.uuid4(),
            assignment_b=uuid.uuid4(),
            local_cost=2.0,
            global_benefit=5.0,
            ergosphere_period=ergosphere,
        )

        success = tracker.record_extraction(swap)

        assert success
        assert tracker.extracted_energy == 3.0
        assert tracker.extraction_fraction == 0.03  # 3/100
        assert len(tracker.extraction_history) == 1

    def test_tracker_exhaustion(self):
        """Test tracker exhaustion detection."""
        tracker = RotationEnergyTracker(initial_rotation_energy=100.0)

        # Extract up to the limit
        tracker.extracted_energy = 29.0  # 29% extracted

        assert tracker.is_exhausted
        assert tracker.extraction_budget == 0.0

    def test_tracker_reject_non_beneficial_swap(self):
        """Test rejection of non-beneficial swaps."""
        tracker = RotationEnergyTracker(initial_rotation_energy=100.0)

        ergosphere = ErgospherePeriod(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            rotation_velocity=1.0,
            extraction_potential=0.1,
            boundary_type="week_end",
        )

        swap = PenroseSwap(
            swap_id=uuid.uuid4(),
            assignment_a=uuid.uuid4(),
            assignment_b=uuid.uuid4(),
            local_cost=5.0,
            global_benefit=2.0,  # Not beneficial
            ergosphere_period=ergosphere,
        )

        success = tracker.record_extraction(swap)

        assert not success
        assert tracker.extracted_energy == 0.0


@pytest.mark.asyncio
class TestPenroseEfficiencyExtractor:
    """Test suite for PenroseEfficiencyExtractor."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock(spec=AsyncSession)
        return db

    @pytest.fixture
    def extractor(self, mock_db):
        """Create extractor instance."""
        return PenroseEfficiencyExtractor(mock_db)

    @pytest.fixture
    def sample_blocks(self):
        """Create sample blocks for testing."""
        blocks = []
        start_date = date(2024, 1, 1)  # Monday

        for i in range(14):  # Two weeks
            current_date = start_date + timedelta(days=i)
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid.uuid4(),
                    date=current_date,
                    time_of_day=time_of_day,
                    block_number=1,
                    is_weekend=(current_date.weekday() >= 5),
                    is_holiday=False,
                )
                blocks.append(block)

        return blocks

    async def test_identify_ergosphere_periods(self, extractor, mock_db, sample_blocks):
        """Test identification of ergosphere periods."""
        # Mock database query to return sample blocks
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_blocks
        mock_db.execute = AsyncMock(return_value=mock_result)

        # Mock _get_assignments_in_period
        extractor._get_assignments_in_period = AsyncMock(return_value=[])

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 14)

        ergospheres = await extractor.identify_ergosphere_periods(start_date, end_date)

        assert len(ergospheres) > 0
        # Should find at least one week-end ergosphere
        week_end_ergospheres = [e for e in ergospheres if e.boundary_type == "week_end"]
        assert len(week_end_ergospheres) > 0

    async def test_decompose_into_phases(self, extractor):
        """Test phase decomposition of assignment."""
        # Create test assignment with block
        block = Block(
            id=uuid.uuid4(),
            date=date(2024, 1, 1),
            time_of_day="AM",
            block_number=1,
        )

        assignment = Assignment(
            id=uuid.uuid4(),
            block_id=block.id,
            person_id=uuid.uuid4(),
            role="primary",
        )
        assignment.block = block

        phases = await extractor.decompose_into_phases(assignment)

        assert len(phases) == 3  # Pre, transition, post
        phase_types = {p.phase_type for p in phases}
        assert phase_types == {"pre_transition", "transition", "post_transition"}

    async def test_decompose_assignment_without_block(self, extractor):
        """Test phase decomposition of assignment without block."""
        assignment = Assignment(
            id=uuid.uuid4(),
            block_id=uuid.uuid4(),
            person_id=uuid.uuid4(),
            role="primary",
        )
        # No block relationship

        phases = await extractor.decompose_into_phases(assignment)

        assert len(phases) == 0

    async def test_find_negative_energy_swaps(self, extractor, mock_db):
        """Test finding negative-energy swaps."""
        schedule_id = uuid.uuid4()

        # Create test ergosphere
        ergosphere = ErgospherePeriod(
            start_time=datetime(2024, 1, 5, 12, 0),  # Friday PM
            end_time=datetime(2024, 1, 8, 8, 0),  # Monday AM
            rotation_velocity=2.0,
            extraction_potential=0.15,
            boundary_type="week_end",
            affected_assignments=[uuid.uuid4(), uuid.uuid4()],
        )

        # Create test assignments
        assignment_a = Assignment(
            id=ergosphere.affected_assignments[0],
            block_id=uuid.uuid4(),
            person_id=uuid.uuid4(),
            role="primary",
            rotation_template_id=uuid.uuid4(),
        )

        assignment_b = Assignment(
            id=ergosphere.affected_assignments[1],
            block_id=uuid.uuid4(),
            person_id=uuid.uuid4(),
            role="primary",
            rotation_template_id=uuid.uuid4(),
        )

        # Mock database query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [assignment_a, assignment_b]
        mock_db.execute = AsyncMock(return_value=mock_result)

        swaps = await extractor.find_negative_energy_swaps(schedule_id, ergosphere)

        assert isinstance(swaps, list)
        # May or may not find beneficial swaps depending on heuristics
        for swap in swaps:
            assert swap.is_beneficial
            assert swap.net_extraction > 0

    async def test_compute_extraction_efficiency(self, extractor):
        """Test computation of extraction efficiency."""
        ergosphere = ErgospherePeriod(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            rotation_velocity=1.0,
            extraction_potential=0.1,
            boundary_type="week_end",
        )

        # Create test swaps
        swaps = [
            PenroseSwap(
                swap_id=uuid.uuid4(),
                assignment_a=uuid.uuid4(),
                assignment_b=uuid.uuid4(),
                local_cost=2.0,
                global_benefit=5.0,
                ergosphere_period=ergosphere,
                executed=True,
            ),
            PenroseSwap(
                swap_id=uuid.uuid4(),
                assignment_a=uuid.uuid4(),
                assignment_b=uuid.uuid4(),
                local_cost=1.0,
                global_benefit=4.0,
                ergosphere_period=ergosphere,
                executed=True,
            ),
        ]

        # Initialize tracker
        extractor.energy_tracker = RotationEnergyTracker(100.0)

        efficiency = extractor.compute_extraction_efficiency(swaps)

        assert efficiency > 0
        assert efficiency <= 0.29  # Should not exceed Penrose limit

    async def test_execute_penrose_cascade(self, extractor, mock_db):
        """Test execution of Penrose cascade optimization."""
        schedule_id = uuid.uuid4()

        # Mock the identify_ergosphere_periods method
        extractor.identify_ergosphere_periods = AsyncMock(
            return_value=[
                ErgospherePeriod(
                    start_time=datetime(2024, 1, 1),
                    end_time=datetime(2024, 1, 2),
                    rotation_velocity=2.0,
                    extraction_potential=0.20,  # High potential
                    boundary_type="week_end",
                    affected_assignments=[uuid.uuid4()],
                )
            ]
        )

        # Mock find_negative_energy_swaps
        extractor.find_negative_energy_swaps = AsyncMock(return_value=[])

        result = await extractor.execute_penrose_cascade(schedule_id, max_iterations=2)

        assert "swaps_executed" in result
        assert "efficiency_extracted" in result
        assert "iterations" in result
        assert result["iterations"] <= 2


class TestPenroseVisualizer:
    """Test suite for PenroseVisualizer."""

    @pytest.fixture
    def visualizer(self):
        """Create visualizer instance."""
        return PenroseVisualizer()

    @pytest.fixture
    def sample_ergospheres(self):
        """Create sample ergospheres."""
        return [
            ErgospherePeriod(
                start_time=datetime(2024, 1, 5, 12, 0),
                end_time=datetime(2024, 1, 8, 8, 0),
                rotation_velocity=2.5,
                extraction_potential=0.18,
                boundary_type="week_end",
            ),
            ErgospherePeriod(
                start_time=datetime(2024, 1, 29, 12, 0),
                end_time=datetime(2024, 1, 30, 8, 0),
                rotation_velocity=3.0,
                extraction_potential=0.22,
                boundary_type="block_transition",
            ),
        ]

    @pytest.fixture
    def sample_swaps(self):
        """Create sample swaps."""
        ergosphere = ErgospherePeriod(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 1, 2),
            rotation_velocity=1.0,
            extraction_potential=0.1,
            boundary_type="week_end",
        )

        return [
            PenroseSwap(
                swap_id=uuid.uuid4(),
                assignment_a=uuid.uuid4(),
                assignment_b=uuid.uuid4(),
                local_cost=2.0,
                global_benefit=5.0,
                ergosphere_period=ergosphere,
                executed=True,
            ),
            PenroseSwap(
                swap_id=uuid.uuid4(),
                assignment_a=uuid.uuid4(),
                assignment_b=uuid.uuid4(),
                local_cost=1.5,
                global_benefit=4.0,
                ergosphere_period=ergosphere,
                executed=True,
            ),
        ]

    def test_visualizer_initialization(self, visualizer):
        """Test visualizer initialization."""
        assert visualizer.config is not None
        assert isinstance(visualizer.config, VisualizationConfig)

    def test_plot_ergosphere_timeline(self, visualizer, sample_ergospheres):
        """Test ergosphere timeline plotting."""
        fig = visualizer.plot_ergosphere_timeline(sample_ergospheres)

        assert fig is not None
        # Clean up
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_plot_extraction_efficiency(self, visualizer, sample_swaps):
        """Test extraction efficiency plotting."""
        fig = visualizer.plot_extraction_efficiency(sample_swaps)

        assert fig is not None
        # Clean up
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_plot_swap_network(self, visualizer, sample_swaps):
        """Test swap network plotting."""
        fig = visualizer.plot_swap_network(sample_swaps)

        assert fig is not None
        # Clean up
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_generate_summary_report(
        self, visualizer, sample_ergospheres, sample_swaps
    ):
        """Test summary report generation."""
        efficiency = 0.15

        report = visualizer.generate_summary_report(
            sample_ergospheres, sample_swaps, efficiency
        )

        assert "summary" in report
        assert "ergosphere_breakdown" in report
        assert "top_extractions" in report
        assert "recommendations" in report

        assert report["summary"]["total_ergospheres"] == 2
        assert report["summary"]["total_swaps_executed"] == 2
