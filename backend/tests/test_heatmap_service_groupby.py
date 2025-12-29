"""Tests for heatmap service daily and weekly grouping functionality."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.services.heatmap_service import HeatmapService


class TestHeatmapServiceGroupBy:
    """Test suite for HeatmapService group_by functionality."""

    def test_generate_daily_heatmap(self):
        """Test daily heatmap generation."""
        service = HeatmapService()

        # Create mock database
        db = MagicMock()

        # Create mock assignments
        assignments = []
        for i in range(3):
            assignment = MagicMock()
            assignment.block = MagicMock()
            assignment.block.date = date(2025, 1, i + 1)
            assignments.append(assignment)

        # Add another assignment on day 1
        assignment = MagicMock()
        assignment.block = MagicMock()
        assignment.block.date = date(2025, 1, 1)
        assignments.append(assignment)

        # Mock swap records query
        service._get_swap_records_in_range = MagicMock(return_value=[])

        result = service._generate_daily_heatmap(
            db,
            assignments,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 3),
            include_fmit=False,
        )

        assert result.title == "Daily Assignment Heatmap"
        assert result.data.y_labels == ["Total Assignments"]
        assert result.data.x_labels == ["2025-01-01", "2025-01-02", "2025-01-03"]
        # Should have 2 assignments on day 1, 1 on day 2, 1 on day 3
        assert result.data.z_values == [[2.0, 1.0, 1.0]]
        assert result.metadata["grouping_type"] == "daily"
        assert result.metadata["date_range_days"] == 3
        assert result.metadata["total_assignments"] == 4

    def test_generate_daily_heatmap_with_fmit(self):
        """Test daily heatmap generation includes FMIT data when requested."""
        service = HeatmapService()

        # Create mock database
        db = MagicMock()

        # Create mock assignments
        assignments = []
        assignment = MagicMock()
        assignment.block = MagicMock()
        assignment.block.date = date(2025, 1, 1)
        assignments.append(assignment)

        # Mock swap records query to return 2 swaps
        mock_swaps = [MagicMock(), MagicMock()]
        service._get_swap_records_in_range = MagicMock(return_value=mock_swaps)

        result = service._generate_daily_heatmap(
            db,
            assignments,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            include_fmit=True,
        )

        assert result.metadata["fmit_swaps_count"] == 2
        service._get_swap_records_in_range.assert_called_once()

    def test_generate_weekly_heatmap(self):
        """Test weekly heatmap generation."""
        service = HeatmapService()

        # Create mock database
        db = MagicMock()

        # Create mock assignments
        # Week starting 2024-12-30 (Monday)
        assignments = []
        for i in range(2):
            assignment = MagicMock()
            assignment.block = MagicMock()
            assignment.block.date = date(2024, 12, 30 + i)
            assignments.append(assignment)

        # Week starting 2025-01-06 (Monday)
        for i in range(3):
            assignment = MagicMock()
            assignment.block = MagicMock()
            assignment.block.date = date(2025, 1, 6 + i)
            assignments.append(assignment)

        # Mock swap records query
        service._get_swap_records_in_range = MagicMock(return_value=[])

        result = service._generate_weekly_heatmap(
            db,
            assignments,
            start_date=date(2024, 12, 30),
            end_date=date(2025, 1, 10),
            include_fmit=False,
        )

        assert result.title == "Weekly Assignment Heatmap"
        assert result.data.y_labels == ["Total Assignments"]
        assert len(result.data.x_labels) >= 2
        assert result.metadata["grouping_type"] == "weekly"
        assert result.metadata["total_assignments"] == 5

    def test_generate_weekly_heatmap_with_fmit(self):
        """Test weekly heatmap generation includes FMIT data when requested."""
        service = HeatmapService()

        # Create mock database
        db = MagicMock()

        # Create mock assignments
        assignments = []
        assignment = MagicMock()
        assignment.block = MagicMock()
        assignment.block.date = date(2025, 1, 6)
        assignments.append(assignment)

        # Mock swap records query to return 3 swaps
        mock_swaps = [MagicMock(), MagicMock(), MagicMock()]
        service._get_swap_records_in_range = MagicMock(return_value=mock_swaps)

        result = service._generate_weekly_heatmap(
            db,
            assignments,
            start_date=date(2025, 1, 6),
            end_date=date(2025, 1, 12),
            include_fmit=True,
        )

        assert result.metadata["fmit_swaps_count"] == 3
        service._get_swap_records_in_range.assert_called_once()

    def test_generate_heatmap_with_daily_group_by(self):
        """Test unified heatmap with daily grouping."""
        service = HeatmapService()

        # Create mock database and assignments
        db = MagicMock()
        assignments = []

        # Day 1: 3 assignments
        for i in range(3):
            assignment = MagicMock()
            assignment.block = MagicMock()
            assignment.block.date = date(2025, 1, 1)
            assignment.person_id = f"person-{i}"
            assignment.rotation_template_id = f"rotation-{i}"
            assignments.append(assignment)

        # Day 2: 2 assignments
        for i in range(2):
            assignment = MagicMock()
            assignment.block = MagicMock()
            assignment.block.date = date(2025, 1, 2)
            assignment.person_id = f"person-{i}"
            assignment.rotation_template_id = f"rotation-{i}"
            assignments.append(assignment)

        # Mock the query methods
        service._get_assignments_in_range = MagicMock(return_value=assignments)

        result = service.generate_unified_heatmap(
            db=db,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 2),
            group_by="daily",
        )

        assert result.title == "Daily Assignment Heatmap"
        assert result.data.y_labels == ["Total Assignments"]
        assert result.data.z_values == [[3.0, 2.0]]
        assert result.metadata["grouping_type"] == "daily"

    def test_generate_heatmap_with_weekly_group_by(self):
        """Test unified heatmap with weekly grouping."""
        service = HeatmapService()

        # Create mock database and assignments
        db = MagicMock()
        assignments = []

        # Week 1 (2024-12-30 to 2025-01-05): 4 assignments
        for i in range(4):
            assignment = MagicMock()
            assignment.block = MagicMock()
            assignment.block.date = date(2024, 12, 30 + i)
            assignment.person_id = f"person-{i}"
            assignment.rotation_template_id = f"rotation-{i}"
            assignments.append(assignment)

        # Week 2 (2025-01-06 to 2025-01-12): 3 assignments
        for i in range(3):
            assignment = MagicMock()
            assignment.block = MagicMock()
            assignment.block.date = date(2025, 1, 6 + i)
            assignment.person_id = f"person-{i}"
            assignment.rotation_template_id = f"rotation-{i}"
            assignments.append(assignment)

        # Mock the query methods
        service._get_assignments_in_range = MagicMock(return_value=assignments)

        result = service.generate_unified_heatmap(
            db=db,
            start_date=date(2024, 12, 30),
            end_date=date(2025, 1, 12),
            group_by="weekly",
        )

        assert result.title == "Weekly Assignment Heatmap"
        assert result.data.y_labels == ["Total Assignments"]
        assert len(result.data.x_labels) >= 2
        assert result.data.z_values[0][0] == 4.0  # First week
        assert result.metadata["grouping_type"] == "weekly"

    def test_generate_heatmap_person_grouping_still_works(self):
        """Ensure person grouping still works after adding daily/weekly."""
        service = HeatmapService()

        # Create mock database
        db = MagicMock()

        # Create mock person objects
        person1 = MagicMock()
        person1.id = "person-1"
        person1.name = "Dr. Smith"

        person2 = MagicMock()
        person2.id = "person-2"
        person2.name = "Dr. Johnson"

        # Create mock assignments
        assignments = []
        assignment1 = MagicMock()
        assignment1.block = MagicMock()
        assignment1.block.date = date(2025, 1, 1)
        assignment1.person_id = "person-1"
        assignment1.rotation_template_id = "rotation-1"
        assignments.append(assignment1)

        assignment2 = MagicMock()
        assignment2.block = MagicMock()
        assignment2.block.date = date(2025, 1, 1)
        assignment2.person_id = "person-2"
        assignment2.rotation_template_id = "rotation-2"
        assignments.append(assignment2)

        # Mock query results
        service._get_assignments_in_range = MagicMock(return_value=assignments)
        db.query.return_value.filter.return_value.all.return_value = [person1, person2]

        result = service.generate_unified_heatmap(
            db=db,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            group_by="person",
        )

        assert result.data.y_labels == ["Dr. Smith", "Dr. Johnson"]
        assert len(result.data.z_values) == 2

    def test_generate_heatmap_rotation_grouping_still_works(self):
        """Ensure rotation grouping still works after adding daily/weekly."""
        service = HeatmapService()

        # Create mock database
        db = MagicMock()

        # Create mock rotation objects
        rotation1 = MagicMock()
        rotation1.id = "rotation-1"
        rotation1.name = "Clinic"

        rotation2 = MagicMock()
        rotation2.id = "rotation-2"
        rotation2.name = "Inpatient"

        # Create mock assignments
        assignments = []
        assignment1 = MagicMock()
        assignment1.block = MagicMock()
        assignment1.block.date = date(2025, 1, 1)
        assignment1.person_id = "person-1"
        assignment1.rotation_template_id = "rotation-1"
        assignments.append(assignment1)

        assignment2 = MagicMock()
        assignment2.block = MagicMock()
        assignment2.block.date = date(2025, 1, 1)
        assignment2.person_id = "person-2"
        assignment2.rotation_template_id = "rotation-2"
        assignments.append(assignment2)

        # Mock query results
        service._get_assignments_in_range = MagicMock(return_value=assignments)
        db.query.return_value.filter.return_value.all.return_value = [
            rotation1,
            rotation2,
        ]

        result = service.generate_unified_heatmap(
            db=db,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 1),
            group_by="rotation",
        )

        assert result.data.y_labels == ["Clinic", "Inpatient"]
        assert len(result.data.z_values) == 2
