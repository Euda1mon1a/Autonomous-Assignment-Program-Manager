"""Tests for Shapley value service.

Test coverage:
- Basic Shapley value calculation
- Monte Carlo convergence
- Equity gap detection
- Workload adjustment recommendations
- Edge cases (single faculty, equal contributions, zero assignments)
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.services.shapley_values import ShapleyValueService


@pytest.fixture
async def faculty_members(db_session):
    """Create test faculty members."""
    faculty = []
    for i in range(3):
        person = Person(
            id=uuid4(),
            name=f"Dr. Faculty{i + 1}",
            type="faculty",
            email=f"faculty{i + 1}@test.mil",
            performs_procedures=True,
            faculty_role="core",
        )
        db_session.add(person)
        faculty.append(person)

    await db_session.commit()
    for f in faculty:
        await db_session.refresh(f)

    return faculty


@pytest.fixture
async def blocks(db_session):
    """Create test blocks (2-week period = 28 half-day blocks)."""
    start = date(2024, 1, 1)
    blocks = []

    for day_offset in range(14):  # 14 days
        current_date = start + timedelta(days=day_offset)
        for tod in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=tod,
                block_number=1,
                is_weekend=(current_date.weekday() >= 5),
                is_holiday=False,
            )
            db_session.add(block)
            blocks.append(block)

    await db_session.commit()
    for b in blocks:
        await db_session.refresh(b)

    # Filter out weekends for workday-only coverage
    workday_blocks = [b for b in blocks if not b.is_weekend]
    return workday_blocks


class TestShapleyValueCalculation:
    """Test basic Shapley value calculation."""

    async def test_equal_contribution_equal_shapley(
        self, db_session, faculty_members, blocks
    ):
        """Test that equal contributions result in equal Shapley values."""
        # Setup: Each faculty covers equal number of blocks
        blocks_per_faculty = len(blocks) // 3
        for i, faculty in enumerate(faculty_members):
            start_idx = i * blocks_per_faculty
            end_idx = start_idx + blocks_per_faculty
            for block in blocks[start_idx:end_idx]:
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=faculty.id,
                    role="primary",
                    created_by="test",
                )
                db_session.add(assignment)

        await db_session.commit()

        # Test
        service = ShapleyValueService(db_session)
        results = await service.calculate_shapley_values(
            faculty_ids=[f.id for f in faculty_members],
            start_date=blocks[0].date,
            end_date=blocks[-1].date,
            num_samples=1000,
        )

        # Verify: All Shapley values should be approximately equal (within 5%)
        shapley_values = [r.shapley_value for r in results.values()]
        expected = 1.0 / 3  # Three faculty, equal split
        for sv in shapley_values:
            assert abs(sv - expected) < 0.05, (
                f"Shapley value {sv} not close to {expected}"
            )

        # Verify: Sum of Shapley values = 1.0 (efficiency property)
        assert abs(sum(shapley_values) - 1.0) < 0.01

    async def test_unequal_contribution_proportional_shapley(
        self, db_session, faculty_members, blocks
    ):
        """Test that Shapley values reflect different contribution levels."""
        # Setup: Faculty 1 covers 50%, Faculty 2 covers 30%, Faculty 3 covers 20%
        total = len(blocks)
        allocations = [int(total * 0.5), int(total * 0.3), int(total * 0.2)]

        current_idx = 0
        for i, (faculty, count) in enumerate(zip(faculty_members, allocations)):
            for block in blocks[current_idx : current_idx + count]:
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=faculty.id,
                    role="primary",
                    created_by="test",
                )
                db_session.add(assignment)
            current_idx += count

        await db_session.commit()

        # Test
        service = ShapleyValueService(db_session)
        results = await service.calculate_shapley_values(
            faculty_ids=[f.id for f in faculty_members],
            start_date=blocks[0].date,
            end_date=blocks[-1].date,
            num_samples=2000,  # More samples for better accuracy
        )

        # Verify: Shapley values roughly proportional to contributions
        sorted_results = sorted(
            results.values(), key=lambda x: x.shapley_value, reverse=True
        )

        # Faculty 1 should have highest Shapley value (~0.5)
        assert sorted_results[0].shapley_value > 0.4
        # Faculty 2 should have medium Shapley value (~0.3)
        assert 0.2 < sorted_results[1].shapley_value < 0.4
        # Faculty 3 should have lowest Shapley value (~0.2)
        assert sorted_results[2].shapley_value < 0.3

    async def test_zero_contribution_zero_shapley(
        self, db_session, faculty_members, blocks
    ):
        """Test null player property: zero contribution = zero Shapley value."""
        # Setup: Only first two faculty have assignments, third has none
        blocks_per_faculty = len(blocks) // 2
        for i in range(2):
            faculty = faculty_members[i]
            start_idx = i * blocks_per_faculty
            end_idx = start_idx + blocks_per_faculty
            for block in blocks[start_idx:end_idx]:
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=faculty.id,
                    role="primary",
                    created_by="test",
                )
                db_session.add(assignment)

        await db_session.commit()

        # Test
        service = ShapleyValueService(db_session)
        results = await service.calculate_shapley_values(
            faculty_ids=[f.id for f in faculty_members],
            start_date=blocks[0].date,
            end_date=blocks[-1].date,
            num_samples=1000,
        )

        # Verify: Third faculty (no assignments) has near-zero Shapley value
        third_faculty_result = results[faculty_members[2].id]
        assert third_faculty_result.shapley_value < 0.05
        assert third_faculty_result.current_workload == 0.0


class TestEquityGapDetection:
    """Test equity gap calculation and reporting."""

    async def test_equity_gap_calculation(self, db_session, faculty_members, blocks):
        """Test that equity gaps correctly identify over/underworked faculty."""
        # Setup: Faculty 1 works 60%, Faculty 2 works 30%, Faculty 3 works 10%
        total = len(blocks)
        allocations = [int(total * 0.6), int(total * 0.3), int(total * 0.1)]

        current_idx = 0
        for faculty, count in zip(faculty_members, allocations):
            for block in blocks[current_idx : current_idx + count]:
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=faculty.id,
                    role="primary",
                    created_by="test",
                )
                db_session.add(assignment)
            current_idx += count

        await db_session.commit()

        # Test
        service = ShapleyValueService(db_session)
        results = await service.calculate_shapley_values(
            faculty_ids=[f.id for f in faculty_members],
            start_date=blocks[0].date,
            end_date=blocks[-1].date,
        )

        # Verify: Faculty 1 should be overworked (positive equity gap)
        fac1_result = results[faculty_members[0].id]
        assert fac1_result.equity_gap > 0, "Faculty 1 should be overworked"

        # Verify: Faculty 3 should be underworked (negative equity gap)
        fac3_result = results[faculty_members[2].id]
        assert fac3_result.equity_gap < 0, "Faculty 3 should be underworked"

    async def test_equity_report_summary(self, db_session, faculty_members, blocks):
        """Test comprehensive equity report generation."""
        # Setup: Unbalanced workload
        total = len(blocks)
        allocations = [int(total * 0.5), int(total * 0.3), int(total * 0.2)]

        current_idx = 0
        for faculty, count in zip(faculty_members, allocations):
            for block in blocks[current_idx : current_idx + count]:
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=faculty.id,
                    role="primary",
                    created_by="test",
                )
                db_session.add(assignment)
            current_idx += count

        await db_session.commit()

        # Test
        service = ShapleyValueService(db_session)
        report = await service.get_equity_report(
            faculty_ids=[f.id for f in faculty_members],
            start_date=blocks[0].date,
            end_date=blocks[-1].date,
        )

        # Verify
        assert len(report.faculty_results) == 3
        assert report.total_workload > 0
        assert report.overworked_count >= 0
        assert report.underworked_count >= 0
        assert report.overworked_count + report.underworked_count <= 3
        assert report.most_overworked_faculty_id is not None
        assert report.most_underworked_faculty_id is not None


class TestWorkloadAdjustments:
    """Test workload adjustment recommendations."""

    async def test_suggest_adjustments_threshold(
        self, db_session, faculty_members, blocks
    ):
        """Test that adjustment suggestions respect threshold."""
        # Setup: Significant imbalance (70/20/10 split)
        total = len(blocks)
        allocations = [int(total * 0.7), int(total * 0.2), int(total * 0.1)]

        current_idx = 0
        for faculty, count in zip(faculty_members, allocations):
            for block in blocks[current_idx : current_idx + count]:
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=faculty.id,
                    role="primary",
                    created_by="test",
                )
                db_session.add(assignment)
            current_idx += count

        await db_session.commit()

        # Test with high threshold (should get fewer suggestions)
        service = ShapleyValueService(db_session)
        suggestions_high = await service.suggest_workload_adjustments(
            faculty_ids=[f.id for f in faculty_members],
            start_date=blocks[0].date,
            end_date=blocks[-1].date,
            threshold=20.0,  # 20 hours
        )

        # Test with low threshold (should get more suggestions)
        suggestions_low = await service.suggest_workload_adjustments(
            faculty_ids=[f.id for f in faculty_members],
            start_date=blocks[0].date,
            end_date=blocks[-1].date,
            threshold=5.0,  # 5 hours
        )

        # Verify
        assert len(suggestions_low) >= len(suggestions_high)
        assert all("faculty_id" in s for s in suggestions_low)
        assert all("action" in s for s in suggestions_low)
        assert all(s["action"] in ["reduce", "increase"] for s in suggestions_low)

    async def test_adjustment_sorting(self, db_session, faculty_members, blocks):
        """Test that adjustment suggestions are sorted by urgency (magnitude)."""
        # Setup: Varying imbalances
        total = len(blocks)
        allocations = [int(total * 0.6), int(total * 0.25), int(total * 0.15)]

        current_idx = 0
        for faculty, count in zip(faculty_members, allocations):
            for block in blocks[current_idx : current_idx + count]:
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=faculty.id,
                    role="primary",
                    created_by="test",
                )
                db_session.add(assignment)
            current_idx += count

        await db_session.commit()

        # Test
        service = ShapleyValueService(db_session)
        suggestions = await service.suggest_workload_adjustments(
            faculty_ids=[f.id for f in faculty_members],
            start_date=blocks[0].date,
            end_date=blocks[-1].date,
            threshold=1.0,
        )

        # Verify: Sorted by magnitude (most urgent first)
        if len(suggestions) > 1:
            for i in range(len(suggestions) - 1):
                assert suggestions[i]["hours"] >= suggestions[i + 1]["hours"]


class TestEdgeCases:
    """Test edge cases and error conditions."""

    async def test_minimum_faculty_requirement(self, db_session, faculty_members):
        """Test that at least 2 faculty are required."""
        service = ShapleyValueService(db_session)

        with pytest.raises(ValueError, match="at least 2 faculty"):
            await service.calculate_shapley_values(
                faculty_ids=[faculty_members[0].id],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 14),
            )

    async def test_empty_assignments(self, db_session, faculty_members, blocks):
        """Test calculation with no assignments (all zero)."""
        # No assignments created
        service = ShapleyValueService(db_session)
        results = await service.calculate_shapley_values(
            faculty_ids=[f.id for f in faculty_members],
            start_date=blocks[0].date,
            end_date=blocks[-1].date,
        )

        # Verify: All faculty have zero workload and near-equal Shapley values
        for result in results.values():
            assert result.current_workload == 0.0
            assert result.fair_workload_target == 0.0
            # Shapley values should be roughly equal (1/3 each)
            assert 0.2 < result.shapley_value < 0.5

    async def test_monte_carlo_consistency(self, db_session, faculty_members, blocks):
        """Test that increasing samples improves consistency."""
        # Setup: Equal distribution
        blocks_per_faculty = len(blocks) // 3
        for i, faculty in enumerate(faculty_members):
            start_idx = i * blocks_per_faculty
            end_idx = start_idx + blocks_per_faculty
            for block in blocks[start_idx:end_idx]:
                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=faculty.id,
                    role="primary",
                    created_by="test",
                )
                db_session.add(assignment)

        await db_session.commit()

        service = ShapleyValueService(db_session)

        # Run with low samples
        results_low = await service.calculate_shapley_values(
            faculty_ids=[f.id for f in faculty_members],
            start_date=blocks[0].date,
            end_date=blocks[-1].date,
            num_samples=100,
        )

        # Run with high samples
        results_high = await service.calculate_shapley_values(
            faculty_ids=[f.id for f in faculty_members],
            start_date=blocks[0].date,
            end_date=blocks[-1].date,
            num_samples=5000,
        )

        # Verify: Both should converge to ~0.33, but high samples should be closer
        expected = 1.0 / 3
        variance_low = sum(
            (r.shapley_value - expected) ** 2 for r in results_low.values()
        )
        variance_high = sum(
            (r.shapley_value - expected) ** 2 for r in results_high.values()
        )

        # High sample variance should be lower (more consistent)
        assert variance_high <= variance_low * 1.5  # Allow some randomness
