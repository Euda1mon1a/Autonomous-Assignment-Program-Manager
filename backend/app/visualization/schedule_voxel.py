"""
3D Voxel Schedule Visualization Module.

A novel approach to schedule visualization that represents assignments
as voxels in a 3D space where:
- X-axis: Time (blocks/dates)
- Y-axis: People (residents, faculty)
- Z-axis: Activity type (clinic, inpatient, procedures, etc.)

Each voxel's properties encode:
- Presence: Whether an assignment exists
- Color: Activity type or compliance status
- Opacity: Confidence score
- Height: Workload intensity

This enables spatial reasoning about scheduling:
- Collision detection = double-booking
- Empty space = coverage gaps
- Layer overlap = supervision compliance
- Volume distribution = workload balance
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Optional
import math


class ActivityLayer(Enum):
    """Z-axis layers for different activity types."""

    CLINIC = 0
    INPATIENT = 1
    PROCEDURES = 2
    CONFERENCE = 3
    CALL = 4
    LEAVE = 5
    ADMIN = 6
    SUPERVISION = 7  ***REMOVED*** Special layer for faculty oversight

    @classmethod
    def from_activity_type(cls, activity_type: str) -> "ActivityLayer":
        """Convert activity type string to layer enum."""
        mapping = {
            "clinic": cls.CLINIC,
            "inpatient": cls.INPATIENT,
            "procedure": cls.PROCEDURES,
            "procedures": cls.PROCEDURES,
            "conference": cls.CONFERENCE,
            "call": cls.CALL,
            "leave": cls.LEAVE,
            "admin": cls.ADMIN,
            "supervision": cls.SUPERVISION,
        }
        return mapping.get(activity_type.lower(), cls.ADMIN)


@dataclass
class VoxelColor:
    """RGBA color for a voxel."""

    r: float  ***REMOVED*** 0-1
    g: float  ***REMOVED*** 0-1
    b: float  ***REMOVED*** 0-1
    a: float = 1.0  ***REMOVED*** opacity

    def to_hex(self) -> str:
        """Convert to hex color string."""
        return f"***REMOVED***{int(self.r * 255):02x}{int(self.g * 255):02x}{int(self.b * 255):02x}"

    def to_rgba_tuple(self) -> tuple[float, float, float, float]:
        """Return as (r, g, b, a) tuple."""
        return (self.r, self.g, self.b, self.a)

    @classmethod
    def from_hex(cls, hex_color: str) -> "VoxelColor":
        """Create from hex string like '***REMOVED***ff0000'."""
        hex_color = hex_color.lstrip("***REMOVED***")
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
        return cls(r, g, b)


***REMOVED*** Activity type color palette (matches frontend ScheduleCell colors)
ACTIVITY_COLORS: dict[ActivityLayer, VoxelColor] = {
    ActivityLayer.CLINIC: VoxelColor.from_hex("***REMOVED***3B82F6"),  ***REMOVED*** blue
    ActivityLayer.INPATIENT: VoxelColor.from_hex("***REMOVED***8B5CF6"),  ***REMOVED*** purple
    ActivityLayer.PROCEDURES: VoxelColor.from_hex("***REMOVED***EF4444"),  ***REMOVED*** red
    ActivityLayer.CONFERENCE: VoxelColor.from_hex("***REMOVED***6B7280"),  ***REMOVED*** gray
    ActivityLayer.CALL: VoxelColor.from_hex("***REMOVED***F97316"),  ***REMOVED*** orange
    ActivityLayer.LEAVE: VoxelColor.from_hex("***REMOVED***F59E0B"),  ***REMOVED*** amber
    ActivityLayer.ADMIN: VoxelColor.from_hex("***REMOVED***10B981"),  ***REMOVED*** green
    ActivityLayer.SUPERVISION: VoxelColor.from_hex("***REMOVED***EC4899"),  ***REMOVED*** pink
}

***REMOVED*** Compliance status colors (override activity colors when violations exist)
COMPLIANCE_COLORS = {
    "compliant": VoxelColor(0.2, 0.8, 0.2, 1.0),  ***REMOVED*** green
    "warning": VoxelColor(1.0, 0.8, 0.0, 1.0),  ***REMOVED*** yellow
    "violation": VoxelColor(1.0, 0.2, 0.2, 1.0),  ***REMOVED*** red
    "critical": VoxelColor(0.6, 0.0, 0.0, 1.0),  ***REMOVED*** dark red
}


@dataclass
class ScheduleVoxel:
    """
    A single voxel in the 3D schedule space.

    Represents one assignment at a specific (time, person, activity) coordinate.
    """

    ***REMOVED*** Position in 3D grid
    x: int  ***REMOVED*** Time index (block index from start date)
    y: int  ***REMOVED*** Person index
    z: int  ***REMOVED*** Activity layer

    ***REMOVED*** Identity
    assignment_id: str | None = None
    person_id: str | None = None
    person_name: str | None = None
    block_id: str | None = None
    block_date: date | None = None
    block_time_of_day: str | None = None  ***REMOVED*** "AM" or "PM"
    activity_name: str | None = None
    activity_type: str | None = None

    ***REMOVED*** Visual properties
    color: VoxelColor = field(default_factory=lambda: VoxelColor(0.5, 0.5, 0.5))
    opacity: float = 1.0  ***REMOVED*** Based on confidence score
    height: float = 1.0  ***REMOVED*** Based on workload intensity

    ***REMOVED*** State
    is_occupied: bool = True
    is_conflict: bool = False  ***REMOVED*** Double-booking detected
    is_violation: bool = False  ***REMOVED*** ACGME violation
    violation_details: list[str] = field(default_factory=list)

    ***REMOVED*** Metadata for tooltips
    role: str | None = None  ***REMOVED*** "primary", "supervising", "backup"
    confidence: float = 1.0
    hours: float = 4.0  ***REMOVED*** Default half-day = 4 hours

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON/API response."""
        return {
            "position": {"x": self.x, "y": self.y, "z": self.z},
            "identity": {
                "assignment_id": self.assignment_id,
                "person_id": self.person_id,
                "person_name": self.person_name,
                "block_id": self.block_id,
                "block_date": self.block_date.isoformat() if self.block_date else None,
                "block_time_of_day": self.block_time_of_day,
                "activity_name": self.activity_name,
                "activity_type": self.activity_type,
            },
            "visual": {
                "color": self.color.to_hex(),
                "rgba": self.color.to_rgba_tuple(),
                "opacity": self.opacity,
                "height": self.height,
            },
            "state": {
                "is_occupied": self.is_occupied,
                "is_conflict": self.is_conflict,
                "is_violation": self.is_violation,
                "violation_details": self.violation_details,
            },
            "metadata": {
                "role": self.role,
                "confidence": self.confidence,
                "hours": self.hours,
            },
        }


@dataclass
class VoxelGridDimensions:
    """Dimensions of the 3D voxel grid."""

    x_size: int  ***REMOVED*** Number of time blocks
    y_size: int  ***REMOVED*** Number of people
    z_size: int  ***REMOVED*** Number of activity layers

    ***REMOVED*** Axis metadata for labels
    x_labels: list[str] = field(default_factory=list)  ***REMOVED*** Date strings
    y_labels: list[str] = field(default_factory=list)  ***REMOVED*** Person names
    z_labels: list[str] = field(default_factory=list)  ***REMOVED*** Activity types

    ***REMOVED*** Mapping from IDs to indices
    x_id_to_index: dict[str, int] = field(default_factory=dict)  ***REMOVED*** block_id -> x
    y_id_to_index: dict[str, int] = field(default_factory=dict)  ***REMOVED*** person_id -> y
    z_type_to_index: dict[str, int] = field(default_factory=dict)  ***REMOVED*** activity_type -> z


@dataclass
class ScheduleVoxelGrid:
    """
    A 3D grid of schedule voxels.

    This is the core data structure for 3D schedule visualization.
    Think of it as a "space-time cube" for workforce scheduling.
    """

    dimensions: VoxelGridDimensions
    voxels: list[ScheduleVoxel] = field(default_factory=list)

    ***REMOVED*** Statistics
    total_assignments: int = 0
    total_conflicts: int = 0
    total_violations: int = 0
    coverage_percentage: float = 0.0

    ***REMOVED*** Date range
    start_date: date | None = None
    end_date: date | None = None

    def add_voxel(self, voxel: ScheduleVoxel) -> None:
        """Add a voxel to the grid."""
        self.voxels.append(voxel)
        self.total_assignments += 1
        if voxel.is_conflict:
            self.total_conflicts += 1
        if voxel.is_violation:
            self.total_violations += 1

    def get_voxel_at(self, x: int, y: int, z: int) -> ScheduleVoxel | None:
        """Get voxel at specific coordinate (if exists)."""
        for voxel in self.voxels:
            if voxel.x == x and voxel.y == y and voxel.z == z:
                return voxel
        return None

    def get_voxels_at_position(self, x: int, y: int) -> list[ScheduleVoxel]:
        """Get all voxels at a time-person position (across all z layers)."""
        return [v for v in self.voxels if v.x == x and v.y == y]

    def detect_conflicts(self) -> list[tuple[ScheduleVoxel, ScheduleVoxel]]:
        """
        Detect double-bookings (multiple voxels at same x,y position).

        Returns list of conflicting voxel pairs.
        """
        conflicts = []
        position_map: dict[tuple[int, int], list[ScheduleVoxel]] = {}

        for voxel in self.voxels:
            pos = (voxel.x, voxel.y)
            if pos not in position_map:
                position_map[pos] = []
            position_map[pos].append(voxel)

        for pos, voxels_at_pos in position_map.items():
            if len(voxels_at_pos) > 1:
                ***REMOVED*** Mark all as conflicts
                for v in voxels_at_pos:
                    v.is_conflict = True
                    self.total_conflicts += 1

                ***REMOVED*** Return pairs
                for i, v1 in enumerate(voxels_at_pos):
                    for v2 in voxels_at_pos[i + 1 :]:
                        conflicts.append((v1, v2))

        return conflicts

    def get_coverage_gaps(self) -> list[tuple[int, int, int]]:
        """
        Find empty positions that should have coverage.

        Returns list of (x, y, z) positions with gaps.
        """
        gaps = []
        occupied = {(v.x, v.y, v.z) for v in self.voxels}

        ***REMOVED*** For now, just identify completely empty time-person combinations
        ***REMOVED*** Could be enhanced to require specific activity coverage
        for x in range(self.dimensions.x_size):
            for y in range(self.dimensions.y_size):
                voxels_here = self.get_voxels_at_position(x, y)
                if not voxels_here:
                    ***REMOVED*** No assignments for this person at this time
                    gaps.append((x, y, -1))  ***REMOVED*** z=-1 indicates any layer

        return gaps

    def calculate_workload_distribution(self) -> dict[int, float]:
        """
        Calculate total workload per person (y-axis).

        Returns dict mapping person index to total hours.
        """
        workload: dict[int, float] = dict.fromkeys(range(self.dimensions.y_size), 0.0)

        for voxel in self.voxels:
            if voxel.is_occupied:
                workload[voxel.y] += voxel.hours

        return workload

    def to_dict(self) -> dict:
        """Serialize entire grid for JSON/API response."""
        return {
            "dimensions": {
                "x_size": self.dimensions.x_size,
                "y_size": self.dimensions.y_size,
                "z_size": self.dimensions.z_size,
                "x_labels": self.dimensions.x_labels,
                "y_labels": self.dimensions.y_labels,
                "z_labels": self.dimensions.z_labels,
            },
            "voxels": [v.to_dict() for v in self.voxels],
            "statistics": {
                "total_assignments": self.total_assignments,
                "total_conflicts": self.total_conflicts,
                "total_violations": self.total_violations,
                "coverage_percentage": self.coverage_percentage,
            },
            "date_range": {
                "start_date": self.start_date.isoformat() if self.start_date else None,
                "end_date": self.end_date.isoformat() if self.end_date else None,
            },
        }

    def to_numpy_grid(self) -> "np.ndarray":
        """
        Convert to 3D numpy array for analysis.

        Array values: 0 = empty, 1 = occupied, 2 = conflict, 3 = violation
        """
        import numpy as np

        grid = np.zeros(
            (self.dimensions.x_size, self.dimensions.y_size, self.dimensions.z_size),
            dtype=np.int8,
        )

        for voxel in self.voxels:
            if voxel.is_violation:
                grid[voxel.x, voxel.y, voxel.z] = 3
            elif voxel.is_conflict:
                grid[voxel.x, voxel.y, voxel.z] = 2
            elif voxel.is_occupied:
                grid[voxel.x, voxel.y, voxel.z] = 1

        return grid


class ScheduleVoxelTransformer:
    """
    Transforms schedule assignment data into 3D voxel representation.

    This is the bridge between the database models and the 3D visualization.
    """

    def __init__(self):
        self._person_index_map: dict[str, int] = {}
        self._block_index_map: dict[str, int] = {}
        self._activity_index_map: dict[str, int] = {}

    def transform(
        self,
        assignments: list[dict],
        persons: list[dict],
        blocks: list[dict],
        activity_types: list[str] | None = None,
    ) -> ScheduleVoxelGrid:
        """
        Transform schedule data into a 3D voxel grid.

        Args:
            assignments: List of assignment dicts with person_id, block_id, activity_type
            persons: List of person dicts with id, name, type, pgy_level
            blocks: List of block dicts with id, date, time_of_day
            activity_types: Optional list of activity types (auto-detected if None)

        Returns:
            ScheduleVoxelGrid ready for visualization
        """
        ***REMOVED*** Build index maps
        self._build_person_index(persons)
        self._build_block_index(blocks)

        if activity_types is None:
            activity_types = self._detect_activity_types(assignments)
        self._build_activity_index(activity_types)

        ***REMOVED*** Create dimensions
        dimensions = VoxelGridDimensions(
            x_size=len(blocks),
            y_size=len(persons),
            z_size=len(activity_types),
            x_labels=self._generate_block_labels(blocks),
            y_labels=[p.get("name", f"Person {i}") for i, p in enumerate(persons)],
            z_labels=activity_types,
            x_id_to_index=self._block_index_map.copy(),
            y_id_to_index=self._person_index_map.copy(),
            z_type_to_index=self._activity_index_map.copy(),
        )

        ***REMOVED*** Create grid
        grid = ScheduleVoxelGrid(dimensions=dimensions)

        ***REMOVED*** Set date range
        if blocks:
            dates = [self._parse_date(b.get("date")) for b in blocks if b.get("date")]
            if dates:
                grid.start_date = min(dates)
                grid.end_date = max(dates)

        ***REMOVED*** Transform each assignment to a voxel
        for assignment in assignments:
            voxel = self._assignment_to_voxel(assignment, blocks)
            if voxel:
                grid.add_voxel(voxel)

        ***REMOVED*** Detect conflicts
        grid.detect_conflicts()

        ***REMOVED*** Calculate coverage
        total_possible = dimensions.x_size * dimensions.y_size
        if total_possible > 0:
            grid.coverage_percentage = (len(grid.voxels) / total_possible) * 100

        return grid

    def _build_person_index(self, persons: list[dict]) -> None:
        """Build mapping from person_id to y-index."""
        ***REMOVED*** Sort by type (faculty first) then by PGY level
        sorted_persons = sorted(
            persons,
            key=lambda p: (
                0 if p.get("type") == "faculty" else 1,
                p.get("pgy_level", 0),
                p.get("name", ""),
            ),
        )
        self._person_index_map = {
            p.get("id", str(i)): i for i, p in enumerate(sorted_persons)
        }

    def _build_block_index(self, blocks: list[dict]) -> None:
        """Build mapping from block_id to x-index."""
        ***REMOVED*** Sort by date then by time_of_day (AM before PM)
        sorted_blocks = sorted(
            blocks,
            key=lambda b: (
                b.get("date", ""),
                0 if b.get("time_of_day") == "AM" else 1,
            ),
        )
        self._block_index_map = {
            b.get("id", str(i)): i for i, b in enumerate(sorted_blocks)
        }

    def _build_activity_index(self, activity_types: list[str]) -> None:
        """Build mapping from activity_type to z-index."""

        ***REMOVED*** Use ActivityLayer enum order if possible
        def sort_key(activity_type: str) -> int:
            try:
                return ActivityLayer.from_activity_type(activity_type).value
            except (KeyError, ValueError):
                return 100  ***REMOVED*** Unknown types go last

        sorted_types = sorted(activity_types, key=sort_key)
        self._activity_index_map = {t: i for i, t in enumerate(sorted_types)}

    def _detect_activity_types(self, assignments: list[dict]) -> list[str]:
        """Auto-detect unique activity types from assignments."""
        types = set()
        for assignment in assignments:
            activity_type = assignment.get("activity_type")
            if activity_type:
                types.add(activity_type)
        return list(types) or ["unknown"]

    def _generate_block_labels(self, blocks: list[dict]) -> list[str]:
        """Generate human-readable labels for blocks (x-axis)."""
        labels = []
        for block in sorted(
            blocks, key=lambda b: (b.get("date", ""), b.get("time_of_day", ""))
        ):
            date_str = block.get("date", "")
            tod = block.get("time_of_day", "")
            labels.append(f"{date_str} {tod}")
        return labels

    def _parse_date(self, date_value) -> date | None:
        """Parse date from various formats."""
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, datetime):
            return date_value.date()
        if isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value.replace("Z", "+00:00")).date()
            except ValueError:
                try:
                    return datetime.strptime(date_value, "%Y-%m-%d").date()
                except ValueError:
                    return None
        return None

    def _assignment_to_voxel(
        self,
        assignment: dict,
        blocks: list[dict],
    ) -> ScheduleVoxel | None:
        """Convert a single assignment to a voxel."""
        person_id = assignment.get("person_id")
        block_id = assignment.get("block_id")
        activity_type = assignment.get("activity_type", "unknown")

        ***REMOVED*** Get indices
        x = self._block_index_map.get(block_id)
        y = self._person_index_map.get(person_id)
        z = self._activity_index_map.get(activity_type, 0)

        if x is None or y is None:
            return None

        ***REMOVED*** Find block for date info
        block_info = next((b for b in blocks if b.get("id") == block_id), {})

        ***REMOVED*** Determine color based on activity type
        try:
            layer = ActivityLayer.from_activity_type(activity_type)
            color = ACTIVITY_COLORS.get(layer, VoxelColor(0.5, 0.5, 0.5))
        except (KeyError, ValueError):
            color = VoxelColor(0.5, 0.5, 0.5)

        ***REMOVED*** Create voxel
        voxel = ScheduleVoxel(
            x=x,
            y=y,
            z=z,
            assignment_id=assignment.get("id"),
            person_id=person_id,
            person_name=assignment.get("person_name"),
            block_id=block_id,
            block_date=self._parse_date(block_info.get("date")),
            block_time_of_day=block_info.get("time_of_day"),
            activity_name=assignment.get("activity_name"),
            activity_type=activity_type,
            color=color,
            opacity=assignment.get("confidence", 1.0),
            role=assignment.get("role"),
            confidence=assignment.get("confidence", 1.0),
        )

        ***REMOVED*** Check for violations
        if assignment.get("acgme_warnings"):
            voxel.is_violation = True
            voxel.violation_details = assignment.get("acgme_warnings", [])
            voxel.color = COMPLIANCE_COLORS["violation"]

        return voxel


***REMOVED*** Convenience function for quick transformation
def transform_schedule_to_voxels(
    assignments: list[dict],
    persons: list[dict],
    blocks: list[dict],
) -> ScheduleVoxelGrid:
    """
    Quick transformation of schedule data to 3D voxel grid.

    Example usage:
        grid = transform_schedule_to_voxels(
            assignments=[{"person_id": "...", "block_id": "...", "activity_type": "clinic"}],
            persons=[{"id": "...", "name": "Dr. Smith", "type": "faculty"}],
            blocks=[{"id": "...", "date": "2024-01-15", "time_of_day": "AM"}],
        )

        ***REMOVED*** Convert to JSON for API response
        response = grid.to_dict()

        ***REMOVED*** Or get numpy array for analysis
        array = grid.to_numpy_grid()
    """
    transformer = ScheduleVoxelTransformer()
    return transformer.transform(assignments, persons, blocks)
