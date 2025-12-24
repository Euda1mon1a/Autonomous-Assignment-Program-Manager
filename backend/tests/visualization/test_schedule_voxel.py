"""Tests for 3D Voxel Schedule Visualization module."""

import pytest
from datetime import date
from uuid import uuid4

from app.visualization.schedule_voxel import (
    ActivityLayer,
    VoxelColor,
    ScheduleVoxel,
    ScheduleVoxelGrid,
    ScheduleVoxelTransformer,
    VoxelGridDimensions,
    transform_schedule_to_voxels,
    ACTIVITY_COLORS,
)


class TestActivityLayer:
    """Tests for ActivityLayer enum."""

    def test_from_activity_type_clinic(self):
        """Test mapping clinic activity type."""
        layer = ActivityLayer.from_activity_type("clinic")
        assert layer == ActivityLayer.CLINIC

    def test_from_activity_type_inpatient(self):
        """Test mapping inpatient activity type."""
        layer = ActivityLayer.from_activity_type("inpatient")
        assert layer == ActivityLayer.INPATIENT

    def test_from_activity_type_case_insensitive(self):
        """Test case insensitivity of activity type mapping."""
        layer = ActivityLayer.from_activity_type("CLINIC")
        assert layer == ActivityLayer.CLINIC

        layer = ActivityLayer.from_activity_type("Inpatient")
        assert layer == ActivityLayer.INPATIENT

    def test_from_activity_type_unknown_returns_admin(self):
        """Test unknown activity types default to ADMIN."""
        layer = ActivityLayer.from_activity_type("unknown_type")
        assert layer == ActivityLayer.ADMIN


class TestVoxelColor:
    """Tests for VoxelColor dataclass."""

    def test_to_hex(self):
        """Test conversion to hex string."""
        color = VoxelColor(1.0, 0.0, 0.0)
        assert color.to_hex() == "#ff0000"

        color = VoxelColor(0.0, 1.0, 0.0)
        assert color.to_hex() == "#00ff00"

        color = VoxelColor(0.0, 0.0, 1.0)
        assert color.to_hex() == "#0000ff"

    def test_from_hex(self):
        """Test creation from hex string."""
        color = VoxelColor.from_hex("#ff0000")
        assert color.r == 1.0
        assert color.g == 0.0
        assert color.b == 0.0

    def test_from_hex_with_hash(self):
        """Test creation from hex string with hash prefix."""
        color = VoxelColor.from_hex("#3B82F6")
        assert color.to_hex() == "#3b82f6"

    def test_to_rgba_tuple(self):
        """Test conversion to RGBA tuple."""
        color = VoxelColor(0.5, 0.5, 0.5, 0.8)
        rgba = color.to_rgba_tuple()
        assert rgba == (0.5, 0.5, 0.5, 0.8)


class TestScheduleVoxel:
    """Tests for ScheduleVoxel dataclass."""

    def test_basic_creation(self):
        """Test creating a basic voxel."""
        voxel = ScheduleVoxel(x=1, y=2, z=3)
        assert voxel.x == 1
        assert voxel.y == 2
        assert voxel.z == 3
        assert voxel.is_occupied is True
        assert voxel.is_conflict is False

    def test_to_dict(self):
        """Test serialization to dictionary."""
        voxel = ScheduleVoxel(
            x=1,
            y=2,
            z=0,
            assignment_id="test-id",
            person_name="Dr. Smith",
            block_date=date(2024, 1, 15),
            activity_type="clinic",
        )
        result = voxel.to_dict()

        assert result["position"] == {"x": 1, "y": 2, "z": 0}
        assert result["identity"]["assignment_id"] == "test-id"
        assert result["identity"]["person_name"] == "Dr. Smith"
        assert result["identity"]["block_date"] == "2024-01-15"
        assert result["state"]["is_occupied"] is True

    def test_conflict_state(self):
        """Test voxel with conflict state."""
        voxel = ScheduleVoxel(x=1, y=2, z=0, is_conflict=True)
        result = voxel.to_dict()
        assert result["state"]["is_conflict"] is True


class TestScheduleVoxelGrid:
    """Tests for ScheduleVoxelGrid."""

    @pytest.fixture
    def sample_dimensions(self):
        """Create sample grid dimensions."""
        return VoxelGridDimensions(
            x_size=10,
            y_size=5,
            z_size=3,
            x_labels=[f"Day {i}" for i in range(10)],
            y_labels=[f"Person {i}" for i in range(5)],
            z_labels=["clinic", "inpatient", "procedures"],
        )

    def test_create_empty_grid(self, sample_dimensions):
        """Test creating an empty grid."""
        grid = ScheduleVoxelGrid(dimensions=sample_dimensions)
        assert grid.total_assignments == 0
        assert len(grid.voxels) == 0

    def test_add_voxel(self, sample_dimensions):
        """Test adding a voxel to the grid."""
        grid = ScheduleVoxelGrid(dimensions=sample_dimensions)
        voxel = ScheduleVoxel(x=1, y=2, z=0)
        grid.add_voxel(voxel)

        assert grid.total_assignments == 1
        assert len(grid.voxels) == 1

    def test_get_voxel_at(self, sample_dimensions):
        """Test retrieving a voxel at specific coordinates."""
        grid = ScheduleVoxelGrid(dimensions=sample_dimensions)
        voxel = ScheduleVoxel(x=1, y=2, z=0, assignment_id="test")
        grid.add_voxel(voxel)

        found = grid.get_voxel_at(1, 2, 0)
        assert found is not None
        assert found.assignment_id == "test"

        not_found = grid.get_voxel_at(5, 5, 5)
        assert not_found is None

    def test_get_voxels_at_position(self, sample_dimensions):
        """Test retrieving all voxels at a time-person position."""
        grid = ScheduleVoxelGrid(dimensions=sample_dimensions)

        # Add two voxels at same x,y but different z
        grid.add_voxel(ScheduleVoxel(x=1, y=2, z=0, activity_type="clinic"))
        grid.add_voxel(ScheduleVoxel(x=1, y=2, z=1, activity_type="inpatient"))

        voxels = grid.get_voxels_at_position(1, 2)
        assert len(voxels) == 2

    def test_detect_conflicts(self, sample_dimensions):
        """Test conflict detection for double-bookings."""
        grid = ScheduleVoxelGrid(dimensions=sample_dimensions)

        # Add two voxels at same position (conflict)
        v1 = ScheduleVoxel(x=1, y=2, z=0)
        v2 = ScheduleVoxel(x=1, y=2, z=1)
        grid.add_voxel(v1)
        grid.add_voxel(v2)

        conflicts = grid.detect_conflicts()
        assert len(conflicts) == 1
        assert v1.is_conflict is True
        assert v2.is_conflict is True

    def test_no_conflicts_different_positions(self, sample_dimensions):
        """Test no conflicts when voxels are at different positions."""
        grid = ScheduleVoxelGrid(dimensions=sample_dimensions)

        grid.add_voxel(ScheduleVoxel(x=1, y=2, z=0))
        grid.add_voxel(ScheduleVoxel(x=2, y=2, z=0))  # Different x

        conflicts = grid.detect_conflicts()
        assert len(conflicts) == 0

    def test_get_coverage_gaps(self, sample_dimensions):
        """Test identifying coverage gaps."""
        grid = ScheduleVoxelGrid(dimensions=sample_dimensions)

        # Add only one voxel for person 0 at time 0
        grid.add_voxel(ScheduleVoxel(x=0, y=0, z=0))

        gaps = grid.get_coverage_gaps()
        # Should have gaps for all other time slots
        assert len(gaps) > 0

    def test_calculate_workload_distribution(self, sample_dimensions):
        """Test workload calculation per person."""
        grid = ScheduleVoxelGrid(dimensions=sample_dimensions)

        # Person 0 has 2 assignments (8 hours)
        grid.add_voxel(ScheduleVoxel(x=0, y=0, z=0, hours=4.0))
        grid.add_voxel(ScheduleVoxel(x=1, y=0, z=0, hours=4.0))

        # Person 1 has 1 assignment (4 hours)
        grid.add_voxel(ScheduleVoxel(x=0, y=1, z=0, hours=4.0))

        workload = grid.calculate_workload_distribution()
        assert workload[0] == 8.0
        assert workload[1] == 4.0
        assert workload[2] == 0.0

    def test_to_dict(self, sample_dimensions):
        """Test serialization of entire grid."""
        grid = ScheduleVoxelGrid(
            dimensions=sample_dimensions,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 10),
        )
        grid.add_voxel(ScheduleVoxel(x=0, y=0, z=0))

        result = grid.to_dict()

        assert "dimensions" in result
        assert result["dimensions"]["x_size"] == 10
        assert "voxels" in result
        assert len(result["voxels"]) == 1
        assert "statistics" in result
        assert result["date_range"]["start_date"] == "2024-01-01"


class TestScheduleVoxelTransformer:
    """Tests for ScheduleVoxelTransformer."""

    @pytest.fixture
    def sample_data(self):
        """Create sample assignment/person/block data."""
        persons = [
            {"id": str(uuid4()), "name": "Dr. Smith", "type": "faculty", "pgy_level": None},
            {"id": str(uuid4()), "name": "Resident A", "type": "resident", "pgy_level": 1},
            {"id": str(uuid4()), "name": "Resident B", "type": "resident", "pgy_level": 2},
        ]

        blocks = [
            {"id": str(uuid4()), "date": "2024-01-15", "time_of_day": "AM"},
            {"id": str(uuid4()), "date": "2024-01-15", "time_of_day": "PM"},
            {"id": str(uuid4()), "date": "2024-01-16", "time_of_day": "AM"},
        ]

        assignments = [
            {
                "id": str(uuid4()),
                "person_id": persons[0]["id"],
                "block_id": blocks[0]["id"],
                "activity_type": "clinic",
                "activity_name": "Morning Clinic",
                "role": "supervising",
                "confidence": 1.0,
            },
            {
                "id": str(uuid4()),
                "person_id": persons[1]["id"],
                "block_id": blocks[0]["id"],
                "activity_type": "clinic",
                "activity_name": "Morning Clinic",
                "role": "primary",
                "confidence": 0.9,
            },
            {
                "id": str(uuid4()),
                "person_id": persons[2]["id"],
                "block_id": blocks[1]["id"],
                "activity_type": "inpatient",
                "activity_name": "Ward Coverage",
                "role": "primary",
                "confidence": 1.0,
            },
        ]

        return {"persons": persons, "blocks": blocks, "assignments": assignments}

    def test_transform_basic(self, sample_data):
        """Test basic transformation of schedule data."""
        transformer = ScheduleVoxelTransformer()
        grid = transformer.transform(
            assignments=sample_data["assignments"],
            persons=sample_data["persons"],
            blocks=sample_data["blocks"],
        )

        assert grid.dimensions.x_size == 3  # 3 blocks
        assert grid.dimensions.y_size == 3  # 3 persons
        assert grid.dimensions.z_size == 2  # 2 activity types (clinic, inpatient)
        assert len(grid.voxels) == 3

    def test_transform_person_ordering(self, sample_data):
        """Test that persons are ordered correctly (faculty first, then by PGY)."""
        transformer = ScheduleVoxelTransformer()
        grid = transformer.transform(
            assignments=sample_data["assignments"],
            persons=sample_data["persons"],
            blocks=sample_data["blocks"],
        )

        # Faculty should be first (y=0)
        assert grid.dimensions.y_labels[0] == "Dr. Smith"

    def test_transform_block_ordering(self, sample_data):
        """Test that blocks are ordered by date then time."""
        transformer = ScheduleVoxelTransformer()
        grid = transformer.transform(
            assignments=sample_data["assignments"],
            persons=sample_data["persons"],
            blocks=sample_data["blocks"],
        )

        # Should be ordered: 01-15 AM, 01-15 PM, 01-16 AM
        assert "2024-01-15 AM" in grid.dimensions.x_labels[0]

    def test_transform_activity_colors(self, sample_data):
        """Test that voxels get correct activity colors."""
        transformer = ScheduleVoxelTransformer()
        grid = transformer.transform(
            assignments=sample_data["assignments"],
            persons=sample_data["persons"],
            blocks=sample_data["blocks"],
        )

        # Find clinic voxel
        clinic_voxels = [v for v in grid.voxels if v.activity_type == "clinic"]
        assert len(clinic_voxels) > 0
        assert clinic_voxels[0].color == ACTIVITY_COLORS[ActivityLayer.CLINIC]

    def test_transform_empty_data(self):
        """Test transformation with empty data."""
        transformer = ScheduleVoxelTransformer()
        grid = transformer.transform(
            assignments=[],
            persons=[],
            blocks=[],
        )

        assert grid.dimensions.x_size == 0
        assert grid.dimensions.y_size == 0
        assert len(grid.voxels) == 0


class TestTransformScheduleToVoxels:
    """Tests for the convenience function."""

    def test_convenience_function(self):
        """Test the transform_schedule_to_voxels convenience function."""
        persons = [{"id": "1", "name": "Test", "type": "resident", "pgy_level": 1}]
        blocks = [{"id": "b1", "date": "2024-01-15", "time_of_day": "AM"}]
        assignments = [
            {"id": "a1", "person_id": "1", "block_id": "b1", "activity_type": "clinic"}
        ]

        grid = transform_schedule_to_voxels(assignments, persons, blocks)

        assert grid.dimensions.x_size == 1
        assert grid.dimensions.y_size == 1
        assert len(grid.voxels) == 1


class TestVoxelGridNumpyConversion:
    """Tests for numpy grid conversion."""

    def test_to_numpy_grid(self):
        """Test conversion to numpy array."""
        try:
            import numpy as np
        except ImportError:
            pytest.skip("numpy not available")

        dimensions = VoxelGridDimensions(
            x_size=3,
            y_size=3,
            z_size=2,
            x_labels=[],
            y_labels=[],
            z_labels=[],
        )
        grid = ScheduleVoxelGrid(dimensions=dimensions)

        # Add normal voxel
        grid.add_voxel(ScheduleVoxel(x=0, y=0, z=0))

        # Add conflict voxel
        conflict = ScheduleVoxel(x=1, y=1, z=0, is_conflict=True)
        grid.voxels.append(conflict)

        # Add violation voxel
        violation = ScheduleVoxel(x=2, y=2, z=1, is_violation=True)
        grid.voxels.append(violation)

        numpy_grid = grid.to_numpy_grid()

        assert numpy_grid.shape == (3, 3, 2)
        assert numpy_grid[0, 0, 0] == 1  # occupied
        assert numpy_grid[1, 1, 0] == 2  # conflict
        assert numpy_grid[2, 2, 1] == 3  # violation


class TestActivityColors:
    """Tests for activity color constants."""

    def test_all_activity_layers_have_colors(self):
        """Test that all activity layers have assigned colors."""
        for layer in ActivityLayer:
            assert layer in ACTIVITY_COLORS, f"Missing color for {layer}"

    def test_colors_are_valid(self):
        """Test that all colors are valid VoxelColor instances."""
        for layer, color in ACTIVITY_COLORS.items():
            assert isinstance(color, VoxelColor)
            assert 0 <= color.r <= 1
            assert 0 <= color.g <= 1
            assert 0 <= color.b <= 1
