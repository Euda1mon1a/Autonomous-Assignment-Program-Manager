"""Voxel grid visualization response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class VoxelDimensions(BaseModel):
    """Dimensions of the voxel grid."""

    x_size: int = Field(..., ge=0, description="Number of blocks (time dimension)")
    y_size: int = Field(..., ge=0, description="Number of people")
    z_size: int = Field(..., ge=0, description="Number of activity types")
    x_labels: list[str] = Field(default_factory=list, description="Time labels")
    y_labels: list[str] = Field(default_factory=list, description="Person labels")
    z_labels: list[str] = Field(default_factory=list, description="Activity type labels")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "x_size": 60,
                "y_size": 15,
                "z_size": 8,
                "x_labels": ["2024-01-01 AM", "2024-01-01 PM"],
                "y_labels": ["Dr. Smith", "Dr. Johnson"],
                "z_labels": ["clinic", "inpatient", "procedure"],
            }
        }


class VoxelPosition(BaseModel):
    """3D position in voxel grid."""

    x: int = Field(..., ge=0, description="Time coordinate")
    y: int = Field(..., ge=0, description="Person coordinate")
    z: int = Field(..., ge=0, description="Activity coordinate")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"example": {"x": 5, "y": 2, "z": 1}}


class VoxelIdentity(BaseModel):
    """Identity information for a voxel."""

    assignment_id: str = Field(..., description="Assignment UUID")
    person_id: str = Field(..., description="Person UUID")
    person_name: str = Field(..., description="Person name")
    block_id: str = Field(..., description="Block UUID")
    activity_type: str = Field(..., description="Activity type")
    activity_name: str = Field(..., description="Activity name")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "assignment_id": "uuid_123",
                "person_id": "uuid_456",
                "person_name": "Dr. Smith",
                "block_id": "uuid_789",
                "activity_type": "clinic",
                "activity_name": "Outpatient Clinic",
            }
        }


class VoxelState(BaseModel):
    """State information for a voxel."""

    is_occupied: bool = Field(..., description="Whether voxel is occupied")
    is_conflict: bool = Field(default=False, description="Whether voxel has a conflict")
    is_violation: bool = Field(
        default=False, description="Whether voxel has ACGME violation"
    )
    violation_details: list[str] = Field(
        default_factory=list, description="List of violations"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "is_occupied": True,
                "is_conflict": False,
                "is_violation": False,
                "violation_details": [],
            }
        }


class VoxelGridStatistics(BaseModel):
    """Statistics about the voxel grid."""

    total_assignments: int = Field(..., ge=0, description="Total assignments")
    total_conflicts: int = Field(default=0, ge=0, description="Total conflicts")
    total_violations: int = Field(default=0, ge=0, description="Total violations")
    occupancy_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Grid occupancy rate"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "total_assignments": 150,
                "total_conflicts": 3,
                "total_violations": 1,
                "occupancy_rate": 0.65,
            }
        }


class VoxelGridResponse(BaseModel):
    """Response schema for 3D voxel grid visualization."""

    dimensions: VoxelDimensions = Field(..., description="Grid dimensions")
    voxels: list[dict[str, Any]] = Field(..., description="List of voxel data")
    statistics: VoxelGridStatistics = Field(..., description="Grid statistics")
    date_range: dict[str, str] = Field(..., description="Date range for visualization")
    error: str | None = Field(None, description="Error message if any")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "dimensions": {
                    "x_size": 60,
                    "y_size": 15,
                    "z_size": 8,
                    "x_labels": ["2024-01-01 AM"],
                    "y_labels": ["Dr. Smith"],
                    "z_labels": ["clinic"],
                },
                "voxels": [
                    {
                        "position": {"x": 0, "y": 0, "z": 0},
                        "identity": {
                            "assignment_id": "uuid_123",
                            "person_name": "Dr. Smith",
                        },
                        "state": {"is_occupied": True, "is_conflict": False},
                    }
                ],
                "statistics": {"total_assignments": 150, "total_conflicts": 3},
                "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            }
        }


class ConflictPosition(BaseModel):
    """Position information for a conflict in 2D (time, person)."""

    x: int = Field(..., ge=0, description="Time coordinate")
    y: int = Field(..., ge=0, description="Person coordinate")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {"example": {"x": 5, "y": 2}}


class VoxelConflictsResponse(BaseModel):
    """Response schema for 3D conflict detection."""

    total_conflicts: int = Field(..., ge=0, description="Total number of conflicts")
    conflict_voxels: list[dict[str, Any]] = Field(
        ..., description="List of conflicting voxels"
    )
    conflict_positions: list[dict[str, int]] = Field(
        ..., description="Unique conflict positions (x, y)"
    )
    date_range: dict[str, str] | None = Field(None, description="Date range")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "total_conflicts": 3,
                "conflict_voxels": [
                    {
                        "position": {"x": 5, "y": 2, "z": 1},
                        "identity": {"person_name": "Dr. Smith"},
                        "details": ["Double booking detected"],
                    }
                ],
                "conflict_positions": [{"x": 5, "y": 2}, {"x": 10, "y": 3}],
                "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            }
        }


class CoverageGapEntry(BaseModel):
    """Single coverage gap entry."""

    x: int = Field(..., ge=0, description="Time coordinate")
    time_label: str = Field(..., description="Human-readable time label")
    coverage_count: int = Field(..., ge=0, description="Number of people assigned")
    severity: str = Field(..., description="Gap severity: critical, warning")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "x": 5,
                "time_label": "2024-01-03 AM",
                "coverage_count": 0,
                "severity": "critical",
            }
        }


class VoxelCoverageGapsResponse(BaseModel):
    """Response schema for 3D coverage gap analysis."""

    total_gaps: int = Field(..., ge=0, description="Number of critical gaps")
    total_warnings: int = Field(..., ge=0, description="Number of warnings")
    gaps: list[dict[str, Any]] = Field(..., description="List of gap entries")
    dimensions: dict[str, Any] = Field(..., description="Grid dimensions")
    date_range: dict[str, str] | None = Field(None, description="Date range")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "total_gaps": 2,
                "total_warnings": 5,
                "gaps": [
                    {
                        "x": 5,
                        "time_label": "2024-01-03 AM",
                        "coverage_count": 0,
                        "severity": "critical",
                    }
                ],
                "dimensions": {"x_size": 60, "y_size": 15, "z_size": 8},
                "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
            }
        }
