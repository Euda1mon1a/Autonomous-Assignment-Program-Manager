"""Tests for HeatmapService."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.schemas.visualization import HeatmapData, TimeRangeType
from app.services.heatmap_service import HeatmapService


class TestHeatmapService:
    """Test suite for HeatmapService."""

    # ========================================================================
    # calculate_date_range Tests
    # ========================================================================

    def test_calculate_date_range_week(self):
        """Test date range calculation for week type."""
        service = HeatmapService()
        # Reference date: Wednesday, Jan 10, 2024
        reference = date(2024, 1, 10)
        time_range = TimeRangeType(range_type="week", reference_date=reference)

        start, end = service.calculate_date_range(time_range)

        # Should start on Monday (Jan 8) and end on Sunday (Jan 14)
        assert start == date(2024, 1, 8)
        assert end == date(2024, 1, 14)
        assert (end - start).days == 6  # 7 days total

    def test_calculate_date_range_week_default_reference(self):
        """Test week range with no reference date (uses today)."""
        service = HeatmapService()
        time_range = TimeRangeType(range_type="week")

        start, end = service.calculate_date_range(time_range)

        # Should be Monday to Sunday of current week
        today = date.today()
        expected_start = today - timedelta(days=today.weekday())
        assert start == expected_start
        assert (end - start).days == 6

    def test_calculate_date_range_month(self):
        """Test date range calculation for month type."""
        service = HeatmapService()
        reference = date(2024, 1, 15)
        time_range = TimeRangeType(range_type="month", reference_date=reference)

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 1, 1)
        assert end == date(2024, 1, 31)

    def test_calculate_date_range_month_february(self):
        """Test month range for February (leap year)."""
        service = HeatmapService()
        reference = date(2024, 2, 15)  # 2024 is a leap year
        time_range = TimeRangeType(range_type="month", reference_date=reference)

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)

    def test_calculate_date_range_month_december(self):
        """Test month range for December (year boundary)."""
        service = HeatmapService()
        reference = date(2024, 12, 15)
        time_range = TimeRangeType(range_type="month", reference_date=reference)

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 12, 1)
        assert end == date(2024, 12, 31)

    def test_calculate_date_range_quarter_q1(self):
        """Test date range calculation for Q1."""
        service = HeatmapService()
        reference = date(2024, 2, 15)  # Q1
        time_range = TimeRangeType(range_type="quarter", reference_date=reference)

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 1, 1)
        assert end == date(2024, 3, 31)

    def test_calculate_date_range_quarter_q2(self):
        """Test date range calculation for Q2."""
        service = HeatmapService()
        reference = date(2024, 5, 15)  # Q2
        time_range = TimeRangeType(range_type="quarter", reference_date=reference)

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 4, 1)
        assert end == date(2024, 6, 30)

    def test_calculate_date_range_quarter_q3(self):
        """Test date range calculation for Q3."""
        service = HeatmapService()
        reference = date(2024, 8, 15)  # Q3
        time_range = TimeRangeType(range_type="quarter", reference_date=reference)

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 7, 1)
        assert end == date(2024, 9, 30)

    def test_calculate_date_range_quarter_q4(self):
        """Test date range calculation for Q4."""
        service = HeatmapService()
        reference = date(2024, 11, 15)  # Q4
        time_range = TimeRangeType(range_type="quarter", reference_date=reference)

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 10, 1)
        assert end == date(2024, 12, 31)

    def test_calculate_date_range_custom(self):
        """Test custom date range."""
        service = HeatmapService()
        time_range = TimeRangeType(
            range_type="custom",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31),
        )

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 1, 1)
        assert end == date(2024, 1, 31)

    def test_calculate_date_range_custom_missing_start(self):
        """Test custom range fails without start_date."""
        service = HeatmapService()
        time_range = TimeRangeType(range_type="custom", end_date=date(2024, 1, 31))

        with pytest.raises(
            ValueError, match="start_date and end_date required for custom range"
        ):
            service.calculate_date_range(time_range)

    def test_calculate_date_range_custom_missing_end(self):
        """Test custom range fails without end_date."""
        service = HeatmapService()
        time_range = TimeRangeType(range_type="custom", start_date=date(2024, 1, 1))

        with pytest.raises(
            ValueError, match="start_date and end_date required for custom range"
        ):
            service.calculate_date_range(time_range)

    def test_calculate_date_range_invalid_type(self):
        """Test invalid range_type raises error."""
        service = HeatmapService()
        time_range = TimeRangeType(range_type="invalid")

        with pytest.raises(ValueError, match="Invalid range_type"):
            service.calculate_date_range(time_range)

    # ========================================================================
    # _get_date_range Tests
    # ========================================================================

    def test_get_date_range_single_day(self):
        """Test date range for a single day."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 1)

        dates = service._get_date_range(start, end)

        assert len(dates) == 1
        assert dates[0] == start

    def test_get_date_range_multiple_days(self):
        """Test date range for multiple days."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 7)

        dates = service._get_date_range(start, end)

        assert len(dates) == 7
        assert dates[0] == date(2024, 1, 1)
        assert dates[-1] == date(2024, 1, 7)

    def test_get_date_range_month(self):
        """Test date range for a full month."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)

        dates = service._get_date_range(start, end)

        assert len(dates) == 31
        assert dates[0] == date(2024, 1, 1)
        assert dates[-1] == date(2024, 1, 31)

    # ========================================================================
    # _get_blocks_in_range Tests
    # ========================================================================

    def test_get_blocks_in_range_with_blocks(self, db):
        """Test getting blocks in date range."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)

        # Create blocks
        for i in range(3):
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start + timedelta(days=i),
                    time_of_day=time_of_day,
                    block_number=1,
                )
                db.add(block)
        db.commit()

        blocks = service._get_blocks_in_range(db, start, end)

        assert len(blocks) == 6  # 3 days × 2 time periods

    def test_get_blocks_in_range_no_blocks(self, db):
        """Test getting blocks when none exist."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)

        blocks = service._get_blocks_in_range(db, start, end)

        assert len(blocks) == 0

    def test_get_blocks_in_range_partial_overlap(self, db):
        """Test getting blocks with partial date overlap."""
        service = HeatmapService()
        query_start = date(2024, 1, 2)
        query_end = date(2024, 1, 4)

        # Create blocks from Jan 1-5
        for i in range(5):
            block = Block(
                id=uuid4(),
                date=date(2024, 1, 1) + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
        db.commit()

        blocks = service._get_blocks_in_range(db, query_start, query_end)

        # Should get Jan 2, 3, 4 (3 blocks)
        assert len(blocks) == 3
        assert all(query_start <= b.date <= query_end for b in blocks)

    # ========================================================================
    # _get_assignments_in_range Tests
    # ========================================================================

    def test_get_assignments_in_range_no_filters(self, db, sample_residents):
        """Test getting assignments without filters."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)

        # Create blocks and assignments
        for i in range(3):
            block = Block(
                id=uuid4(),
                date=start + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_residents[0].id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        assignments = service._get_assignments_in_range(db, start, end)

        assert len(assignments) == 3

    def test_get_assignments_in_range_filter_by_person(
        self, db, sample_residents, sample_blocks
    ):
        """Test filtering assignments by person_id."""
        service = HeatmapService()
        start = date.today()
        end = date.today() + timedelta(days=6)

        # Create assignments for different people
        for i, resident in enumerate(sample_residents[:2]):
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_blocks[i].id,
                person_id=resident.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        # Filter by first resident
        assignments = service._get_assignments_in_range(
            db, start, end, person_ids=[sample_residents[0].id]
        )

        assert len(assignments) == 1
        assert assignments[0].person_id == sample_residents[0].id

    def test_get_assignments_in_range_filter_by_rotation(
        self, db, sample_resident, sample_blocks
    ):
        """Test filtering assignments by rotation_template_id."""
        service = HeatmapService()
        start = date.today()
        end = date.today() + timedelta(days=6)

        # Create rotation templates
        rotation1 = RotationTemplate(
            id=uuid4(), name="Clinic", activity_type="clinic", abbreviation="CL"
        )
        rotation2 = RotationTemplate(
            id=uuid4(), name="Procedures", activity_type="procedures", abbreviation="PR"
        )
        db.add_all([rotation1, rotation2])
        db.commit()

        # Create assignments with different rotations
        assignment1 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=rotation1.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[1].id,
            person_id=sample_resident.id,
            rotation_template_id=rotation2.id,
            role="primary",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        # Filter by rotation1
        assignments = service._get_assignments_in_range(
            db, start, end, rotation_ids=[rotation1.id]
        )

        assert len(assignments) == 1
        assert assignments[0].rotation_template_id == rotation1.id

    def test_get_assignments_in_range_both_filters(
        self, db, sample_residents, sample_blocks
    ):
        """Test filtering by both person and rotation."""
        service = HeatmapService()
        start = date.today()
        end = date.today() + timedelta(days=6)

        rotation = RotationTemplate(
            id=uuid4(), name="Clinic", activity_type="clinic", abbreviation="CL"
        )
        db.add(rotation)
        db.commit()

        # Create assignments
        assignment1 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_residents[0].id,
            rotation_template_id=rotation.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=sample_blocks[1].id,
            person_id=sample_residents[1].id,
            rotation_template_id=rotation.id,
            role="primary",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        # Filter by both
        assignments = service._get_assignments_in_range(
            db,
            start,
            end,
            person_ids=[sample_residents[0].id],
            rotation_ids=[rotation.id],
        )

        assert len(assignments) == 1
        assert assignments[0].person_id == sample_residents[0].id
        assert assignments[0].rotation_template_id == rotation.id

    # ========================================================================
    # _get_swap_records_in_range Tests
    # ========================================================================

    def test_get_swap_records_in_range_approved(self, db, sample_faculty_members):
        """Test getting approved swap records."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)

        # Create approved swap
        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=sample_faculty_members[0].id,
            source_week=date(2024, 1, 15),
            target_faculty_id=sample_faculty_members[1].id,
            target_week=date(2024, 1, 22),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.APPROVED,
        )
        db.add(swap)
        db.commit()

        swaps = service._get_swap_records_in_range(db, start, end)

        assert len(swaps) == 1
        assert swaps[0].status == SwapStatus.APPROVED

    def test_get_swap_records_in_range_executed(self, db, sample_faculty_members):
        """Test getting executed swap records."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)

        # Create executed swap
        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=sample_faculty_members[0].id,
            source_week=date(2024, 1, 15),
            target_faculty_id=sample_faculty_members[1].id,
            target_week=date(2024, 1, 22),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.EXECUTED,
        )
        db.add(swap)
        db.commit()

        swaps = service._get_swap_records_in_range(db, start, end)

        assert len(swaps) == 1
        assert swaps[0].status == SwapStatus.EXECUTED

    def test_get_swap_records_in_range_excludes_pending(self, db, sample_faculty_members):
        """Test that pending swaps are excluded."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)

        # Create pending swap (should be excluded)
        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=sample_faculty_members[0].id,
            source_week=date(2024, 1, 15),
            target_faculty_id=sample_faculty_members[1].id,
            target_week=date(2024, 1, 22),
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.PENDING,
        )
        db.add(swap)
        db.commit()

        swaps = service._get_swap_records_in_range(db, start, end)

        assert len(swaps) == 0

    def test_get_swap_records_in_range_date_filtering(self, db, sample_faculty_members):
        """Test date range filtering for swaps."""
        service = HeatmapService()
        query_start = date(2024, 1, 15)
        query_end = date(2024, 1, 31)

        # Create swaps with different dates
        swap_in_range = SwapRecord(
            id=uuid4(),
            source_faculty_id=sample_faculty_members[0].id,
            source_week=date(2024, 1, 20),
            target_faculty_id=sample_faculty_members[1].id,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.APPROVED,
        )
        swap_before_range = SwapRecord(
            id=uuid4(),
            source_faculty_id=sample_faculty_members[0].id,
            source_week=date(2024, 1, 1),
            target_faculty_id=sample_faculty_members[1].id,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.APPROVED,
        )
        db.add_all([swap_in_range, swap_before_range])
        db.commit()

        swaps = service._get_swap_records_in_range(db, query_start, query_end)

        assert len(swaps) == 1
        assert swaps[0].source_week == date(2024, 1, 20)

    # ========================================================================
    # generate_unified_heatmap Tests - Daily Grouping
    # ========================================================================

    def test_generate_unified_heatmap_daily(self, db, sample_resident, sample_blocks):
        """Test daily heatmap generation."""
        service = HeatmapService()
        start = date.today()
        end = date.today() + timedelta(days=2)

        # Create assignments for 3 days
        for i in range(3):
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_blocks[i * 2].id,  # AM blocks
                person_id=sample_resident.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        result = service.generate_unified_heatmap(
            db, start, end, group_by="daily", include_fmit=False
        )

        assert result.title == "Daily Assignment Heatmap"
        assert len(result.data.x_labels) == 3  # 3 days
        assert result.data.y_labels == ["Total Assignments"]
        assert len(result.data.z_values) == 1  # Single row
        assert result.metadata["total_assignments"] == 3
        assert result.metadata["grouping_type"] == "daily"

    def test_generate_unified_heatmap_daily_with_fmit(
        self, db, sample_resident, sample_blocks, sample_faculty_members
    ):
        """Test daily heatmap includes FMIT metadata."""
        service = HeatmapService()
        start = date.today()
        end = date.today() + timedelta(days=2)

        # Create assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_blocks[0].id,
            person_id=sample_resident.id,
            role="primary",
        )
        db.add(assignment)

        # Create swap in range
        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=sample_faculty_members[0].id,
            source_week=date.today() + timedelta(days=1),
            target_faculty_id=sample_faculty_members[1].id,
            swap_type=SwapType.ONE_TO_ONE,
            status=SwapStatus.APPROVED,
        )
        db.add(swap)
        db.commit()

        result = service.generate_unified_heatmap(
            db, start, end, group_by="daily", include_fmit=True
        )

        assert "fmit_swaps_count" in result.metadata
        assert result.metadata["fmit_swaps_count"] == 1

    # ========================================================================
    # generate_unified_heatmap Tests - Weekly Grouping
    # ========================================================================

    def test_generate_unified_heatmap_weekly(self, db, sample_resident):
        """Test weekly heatmap generation."""
        service = HeatmapService()
        start = date(2024, 1, 1)  # Monday
        end = date(2024, 1, 21)  # 3 weeks

        # Create blocks and assignments across 3 weeks
        for i in range(21):
            block = Block(
                id=uuid4(),
                date=start + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        result = service.generate_unified_heatmap(
            db, start, end, group_by="weekly", include_fmit=False
        )

        assert result.title == "Weekly Assignment Heatmap"
        assert len(result.data.x_labels) == 3  # 3 weeks
        assert result.data.y_labels == ["Total Assignments"]
        assert result.metadata["grouping_type"] == "weekly"
        assert result.metadata["weeks_count"] == 3

    # ========================================================================
    # generate_unified_heatmap Tests - Person Grouping
    # ========================================================================

    def test_generate_unified_heatmap_by_person(self, db, sample_residents):
        """Test heatmap grouped by person."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)

        # Create blocks
        blocks = []
        for i in range(3):
            block = Block(
                id=uuid4(),
                date=start + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Create assignments for each resident
        for i, resident in enumerate(sample_residents):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i].id,
                person_id=resident.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        result = service.generate_unified_heatmap(
            db, start, end, group_by="person", include_fmit=False
        )

        assert result.title == "Person Schedule Heatmap"
        assert len(result.data.y_labels) == 3  # 3 residents
        assert len(result.data.x_labels) == 3  # 3 days
        assert len(result.data.z_values) == 3  # 3 rows (one per person)
        assert all(len(row) == 3 for row in result.data.z_values)

    def test_generate_unified_heatmap_by_person_filter(self, db, sample_residents):
        """Test person heatmap with person filter."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)

        # Create blocks
        blocks = []
        for i in range(3):
            block = Block(
                id=uuid4(),
                date=start + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Create assignments for each resident
        for i, resident in enumerate(sample_residents):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i].id,
                person_id=resident.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        # Filter to only first resident
        result = service.generate_unified_heatmap(
            db,
            start,
            end,
            person_ids=[sample_residents[0].id],
            group_by="person",
            include_fmit=False,
        )

        assert len(result.data.y_labels) == 1
        assert result.metadata["entities_count"] == 1

    def test_generate_unified_heatmap_by_person_empty(self, db):
        """Test person heatmap with no assignments."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)

        result = service.generate_unified_heatmap(
            db, start, end, group_by="person", include_fmit=False
        )

        assert result.data.y_labels == []
        assert result.data.z_values == []
        assert result.metadata["entities_count"] == 0

    # ========================================================================
    # generate_unified_heatmap Tests - Rotation Grouping
    # ========================================================================

    def test_generate_unified_heatmap_by_rotation(self, db, sample_resident):
        """Test heatmap grouped by rotation."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)

        # Create rotations
        rotation1 = RotationTemplate(
            id=uuid4(), name="Clinic", activity_type="clinic", abbreviation="CL"
        )
        rotation2 = RotationTemplate(
            id=uuid4(), name="Procedures", activity_type="procedures", abbreviation="PR"
        )
        db.add_all([rotation1, rotation2])
        db.commit()

        # Create blocks and assignments
        blocks = []
        for i in range(3):
            block = Block(
                id=uuid4(),
                date=start + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Assign to different rotations
        assignment1 = Assignment(
            id=uuid4(),
            block_id=blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=rotation1.id,
            role="primary",
        )
        assignment2 = Assignment(
            id=uuid4(),
            block_id=blocks[1].id,
            person_id=sample_resident.id,
            rotation_template_id=rotation2.id,
            role="primary",
        )
        db.add_all([assignment1, assignment2])
        db.commit()

        result = service.generate_unified_heatmap(
            db, start, end, group_by="rotation", include_fmit=False
        )

        assert result.title == "Rotation Schedule Heatmap"
        assert len(result.data.y_labels) == 2  # 2 rotations
        assert len(result.data.x_labels) == 3  # 3 days
        assert len(result.data.z_values) == 2  # 2 rows (one per rotation)

    # ========================================================================
    # generate_coverage_heatmap Tests
    # ========================================================================

    def test_generate_coverage_heatmap_full_coverage(self, db, sample_resident):
        """Test coverage heatmap with full coverage."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)

        # Create rotation
        rotation = RotationTemplate(
            id=uuid4(), name="Clinic", activity_type="clinic", abbreviation="CL"
        )
        db.add(rotation)
        db.commit()

        # Create blocks and assignments (full coverage)
        for i in range(3):
            block = Block(
                id=uuid4(),
                date=start + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                rotation_template_id=rotation.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        result = service.generate_coverage_heatmap(db, start, end)

        assert result.title == "Rotation Coverage Heatmap"
        assert result.coverage_percentage == 100.0
        assert len(result.gaps) == 0
        assert result.data.color_scale == "RdYlGn"

    def test_generate_coverage_heatmap_partial_coverage(self, db, sample_resident):
        """Test coverage heatmap with gaps."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)

        # Create rotation
        rotation = RotationTemplate(
            id=uuid4(), name="Clinic", activity_type="clinic", abbreviation="CL"
        )
        db.add(rotation)
        db.commit()

        # Create blocks
        blocks = []
        for i in range(3):
            block = Block(
                id=uuid4(),
                date=start + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Only assign first day (2 days uncovered)
        assignment = Assignment(
            id=uuid4(),
            block_id=blocks[0].id,
            person_id=sample_resident.id,
            rotation_template_id=rotation.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        result = service.generate_coverage_heatmap(db, start, end)

        assert result.coverage_percentage < 100.0
        assert len(result.gaps) > 0
        # Check that gaps have correct structure
        for gap in result.gaps:
            assert gap.date in [date(2024, 1, 2), date(2024, 1, 3)]
            assert gap.rotation == "Clinic"
            assert gap.severity in ["high", "medium"]

    def test_generate_coverage_heatmap_no_rotations(self, db):
        """Test coverage heatmap with no rotations."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)

        result = service.generate_coverage_heatmap(db, start, end)

        assert result.coverage_percentage == 0.0
        assert len(result.data.y_labels) == 0
        assert len(result.data.z_values) == 0

    # ========================================================================
    # generate_person_workload_heatmap Tests
    # ========================================================================

    def test_generate_person_workload_heatmap_basic(self, db, sample_residents):
        """Test basic workload heatmap generation."""
        service = HeatmapService()
        start = date(2024, 1, 1)  # Monday
        end = date(2024, 1, 5)  # Friday (5 weekdays)

        # Create blocks and assignments
        for i in range(5):
            for time_of_day in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start + timedelta(days=i),
                    time_of_day=time_of_day,
                    block_number=1,
                )
                db.add(block)
                db.commit()

                assignment = Assignment(
                    id=uuid4(),
                    block_id=block.id,
                    person_id=sample_residents[0].id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        result = service.generate_person_workload_heatmap(
            db, [sample_residents[0].id], start, end, include_weekends=False
        )

        assert result.title == "Person Workload Heatmap"
        assert len(result.data.y_labels) == 1  # 1 person
        assert len(result.data.x_labels) == 5  # 5 weekdays
        assert result.metadata["total_blocks"] == 10  # 5 days × 2 blocks
        assert result.metadata["include_weekends"] is False
        assert result.data.color_scale == "Blues"

    def test_generate_person_workload_heatmap_with_weekends(self, db, sample_resident):
        """Test workload heatmap including weekends."""
        service = HeatmapService()
        start = date(2024, 1, 1)  # Monday
        end = date(2024, 1, 7)  # Sunday (7 days)

        # Create blocks for all 7 days
        for i in range(7):
            block = Block(
                id=uuid4(),
                date=start + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            db.commit()

            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=sample_resident.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        result = service.generate_person_workload_heatmap(
            db, [sample_resident.id], start, end, include_weekends=True
        )

        assert len(result.data.x_labels) == 7  # All 7 days
        assert result.metadata["include_weekends"] is True

    def test_generate_person_workload_heatmap_exclude_weekends(self, db, sample_resident):
        """Test workload heatmap excluding weekends."""
        service = HeatmapService()
        start = date(2024, 1, 1)  # Monday
        end = date(2024, 1, 7)  # Sunday (7 days)

        # Create blocks for all 7 days
        for i in range(7):
            block = Block(
                id=uuid4(),
                date=start + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
        db.commit()

        result = service.generate_person_workload_heatmap(
            db, [sample_resident.id], start, end, include_weekends=False
        )

        # Should only have 5 weekdays (Mon-Fri)
        assert len(result.data.x_labels) == 5
        # Verify no weekend dates
        dates = [date.fromisoformat(label) for label in result.data.x_labels]
        assert all(d.weekday() < 5 for d in dates)

    def test_generate_person_workload_heatmap_multiple_people(
        self, db, sample_residents
    ):
        """Test workload heatmap with multiple people."""
        service = HeatmapService()
        start = date(2024, 1, 1)
        end = date(2024, 1, 3)

        # Create blocks
        blocks = []
        for i in range(3):
            block = Block(
                id=uuid4(),
                date=start + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)
        db.commit()

        # Create assignments for different people
        for i, resident in enumerate(sample_residents):
            assignment = Assignment(
                id=uuid4(),
                block_id=blocks[i].id,
                person_id=resident.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        person_ids = [r.id for r in sample_residents]
        result = service.generate_person_workload_heatmap(
            db, person_ids, start, end, include_weekends=True
        )

        assert len(result.data.y_labels) == 3  # 3 people
        assert result.metadata["people_count"] == 3
        assert result.metadata["avg_blocks_per_person"] == 1.0  # 3 blocks / 3 people

    # ========================================================================
    # export_heatmap_image Tests
    # ========================================================================

    @patch("app.services.heatmap_service.pio.to_image")
    def test_export_heatmap_image_png(self, mock_to_image):
        """Test exporting heatmap as PNG."""
        service = HeatmapService()
        mock_to_image.return_value = b"fake_png_data"

        data = HeatmapData(
            x_labels=["2024-01-01", "2024-01-02"],
            y_labels=["Person 1", "Person 2"],
            z_values=[[1.0, 0.0], [0.0, 1.0]],
            color_scale="Viridis",
        )

        result = service.export_heatmap_image(data, "Test Heatmap", format="png")

        assert result == b"fake_png_data"
        mock_to_image.assert_called_once()
        call_kwargs = mock_to_image.call_args[1]
        assert call_kwargs["format"] == "png"
        assert call_kwargs["width"] == 1200
        assert call_kwargs["height"] == 800

    @patch("app.services.heatmap_service.pio.to_image")
    def test_export_heatmap_image_pdf(self, mock_to_image):
        """Test exporting heatmap as PDF."""
        service = HeatmapService()
        mock_to_image.return_value = b"fake_pdf_data"

        data = HeatmapData(
            x_labels=["2024-01-01"],
            y_labels=["Person 1"],
            z_values=[[1.0]],
            color_scale="Viridis",
        )

        result = service.export_heatmap_image(
            data, "Test", format="pdf", width=800, height=600
        )

        assert result == b"fake_pdf_data"
        call_kwargs = mock_to_image.call_args[1]
        assert call_kwargs["format"] == "pdf"
        assert call_kwargs["width"] == 800
        assert call_kwargs["height"] == 600

    @patch("app.services.heatmap_service.pio.to_image")
    def test_export_heatmap_image_svg(self, mock_to_image):
        """Test exporting heatmap as SVG."""
        service = HeatmapService()
        mock_to_image.return_value = b"fake_svg_data"

        data = HeatmapData(
            x_labels=["2024-01-01"],
            y_labels=["Person 1"],
            z_values=[[1.0]],
            color_scale="Viridis",
        )

        result = service.export_heatmap_image(data, "Test", format="svg")

        assert result == b"fake_svg_data"
        call_kwargs = mock_to_image.call_args[1]
        assert call_kwargs["format"] == "svg"

    def test_export_heatmap_image_invalid_format(self):
        """Test export fails with invalid format."""
        service = HeatmapService()

        data = HeatmapData(
            x_labels=["2024-01-01"],
            y_labels=["Person 1"],
            z_values=[[1.0]],
            color_scale="Viridis",
        )

        with pytest.raises(ValueError, match="Unsupported format"):
            service.export_heatmap_image(data, "Test", format="invalid")

    # ========================================================================
    # create_plotly_figure Tests
    # ========================================================================

    def test_create_plotly_figure(self):
        """Test creating Plotly figure configuration."""
        service = HeatmapService()

        data = HeatmapData(
            x_labels=["2024-01-01", "2024-01-02"],
            y_labels=["Person 1", "Person 2"],
            z_values=[[1.0, 0.0], [0.0, 1.0]],
            color_scale="Viridis",
        )

        result = service.create_plotly_figure(data, "Test Heatmap")

        assert isinstance(result, dict)
        assert "data" in result
        assert "layout" in result
        assert result["layout"]["title"]["text"] == "Test Heatmap"
        assert result["layout"]["xaxis"]["title"]["text"] == "Date"

    def test_create_plotly_figure_with_custom_colorscale(self):
        """Test creating figure with custom color scale."""
        service = HeatmapService()

        data = HeatmapData(
            x_labels=["2024-01-01"],
            y_labels=["Rotation 1"],
            z_values=[[0.5]],
            color_scale="RdYlGn",
        )

        result = service.create_plotly_figure(data, "Coverage")

        assert result["data"][0]["colorscale"] == "RdYlGn"
