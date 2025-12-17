"""Visualization schemas for heatmap generation."""
from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class HeatmapRequest(BaseModel):
    """Request schema for heatmap generation."""
    start_date: date = Field(..., description="Start date for heatmap")
    end_date: date = Field(..., description="End date for heatmap")
    person_ids: list[UUID] | None = Field(None, description="Filter by specific people")
    rotation_ids: list[UUID] | None = Field(None, description="Filter by specific rotation templates")
    include_fmit: bool = Field(True, description="Include FMIT swap data in heatmap")
    group_by: str = Field("person", description="Group heatmap by 'person' or 'rotation'")

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "person_ids": None,
                "rotation_ids": None,
                "include_fmit": True,
                "group_by": "person"
            }
        }


class HeatmapData(BaseModel):
    """Heatmap data structure."""
    x_labels: list[str] = Field(..., description="X-axis labels (dates)")
    y_labels: list[str] = Field(..., description="Y-axis labels (people or rotations)")
    z_values: list[list[float]] = Field(..., description="Matrix of values for heatmap")
    color_scale: str = Field("Viridis", description="Plotly color scale name")
    annotations: list[dict[str, Any]] | None = Field(None, description="Annotations for heatmap cells")

    class Config:
        json_schema_extra = {
            "example": {
                "x_labels": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "y_labels": ["Dr. Smith", "Dr. Johnson", "Dr. Williams"],
                "z_values": [[1, 0, 1], [0, 1, 0], [1, 1, 0]],
                "color_scale": "Viridis",
                "annotations": None
            }
        }


class HeatmapResponse(BaseModel):
    """Response schema for heatmap."""
    data: HeatmapData = Field(..., description="Heatmap data")
    title: str = Field(..., description="Title for the heatmap")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of generation")
    metadata: dict[str, Any] | None = Field(None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "x_labels": ["2024-01-01", "2024-01-02"],
                    "y_labels": ["Dr. Smith", "Dr. Johnson"],
                    "z_values": [[1, 0], [0, 1]],
                    "color_scale": "Viridis",
                    "annotations": None
                },
                "title": "Residency Schedule Heatmap",
                "generated_at": "2024-01-15T10:00:00",
                "metadata": {"total_assignments": 4}
            }
        }


class CoverageGap(BaseModel):
    """Represents a coverage gap in the schedule."""
    date: date = Field(..., description="Date of the gap")
    time_of_day: str = Field(..., description="AM or PM")
    rotation: str | None = Field(None, description="Rotation with gap")
    severity: str = Field(..., description="low, medium, high")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-01-15",
                "time_of_day": "PM",
                "rotation": "FMIT Inpatient",
                "severity": "high"
            }
        }


class CoverageHeatmapResponse(BaseModel):
    """Response schema for coverage heatmap."""
    data: HeatmapData = Field(..., description="Coverage heatmap data")
    coverage_percentage: float = Field(..., description="Overall coverage percentage", ge=0, le=100)
    gaps: list[CoverageGap] = Field(default_factory=list, description="List of coverage gaps")
    title: str = Field(..., description="Title for the heatmap")
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "x_labels": ["2024-01-01", "2024-01-02"],
                    "y_labels": ["FMIT", "Clinic"],
                    "z_values": [[1, 0.5], [1, 1]],
                    "color_scale": "RdYlGn",
                    "annotations": None
                },
                "coverage_percentage": 87.5,
                "gaps": [
                    {
                        "date": "2024-01-01",
                        "time_of_day": "PM",
                        "rotation": "Clinic",
                        "severity": "medium"
                    }
                ],
                "title": "Coverage Heatmap",
                "generated_at": "2024-01-15T10:00:00"
            }
        }


class WorkloadRequest(BaseModel):
    """Request schema for workload heatmap."""
    person_ids: list[UUID] = Field(..., description="People to include in workload analysis")
    start_date: date = Field(..., description="Start date")
    end_date: date = Field(..., description="End date")
    include_weekends: bool = Field(False, description="Include weekends in analysis")

    class Config:
        json_schema_extra = {
            "example": {
                "person_ids": ["550e8400-e29b-41d4-a716-446655440000"],
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "include_weekends": False
            }
        }


class ExportRequest(BaseModel):
    """Request schema for exporting heatmap as image."""
    heatmap_type: str = Field(..., description="Type: 'unified', 'coverage', or 'workload'")
    format: str = Field("png", description="Export format: 'png', 'pdf', 'svg'")
    width: int = Field(1200, description="Width in pixels", gt=0)
    height: int = Field(800, description="Height in pixels", gt=0)
    request_params: dict[str, Any] = Field(..., description="Parameters for heatmap generation")

    class Config:
        json_schema_extra = {
            "example": {
                "heatmap_type": "unified",
                "format": "png",
                "width": 1200,
                "height": 800,
                "request_params": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-03-31",
                    "include_fmit": True,
                    "group_by": "person"
                }
            }
        }


class TimeRangeType(BaseModel):
    """Time range specification for heatmap queries."""
    range_type: str = Field(..., description="Type: 'week', 'month', 'quarter', 'custom'")
    reference_date: date | None = Field(None, description="Reference date for week/month/quarter (defaults to today)")
    start_date: date | None = Field(None, description="Custom start date (required for 'custom' range)")
    end_date: date | None = Field(None, description="Custom end date (required for 'custom' range)")

    class Config:
        json_schema_extra = {
            "example": {
                "range_type": "month",
                "reference_date": "2024-01-15",
                "start_date": None,
                "end_date": None
            }
        }


class UnifiedHeatmapRequest(BaseModel):
    """Request schema for unified heatmap with time range support."""
    time_range: TimeRangeType = Field(..., description="Time range specification")
    person_ids: list[UUID] | None = Field(None, description="Filter by specific people")
    rotation_ids: list[UUID] | None = Field(None, description="Filter by specific rotation templates")
    include_fmit: bool = Field(True, description="Include FMIT swap data in heatmap")
    group_by: str = Field("person", description="Group heatmap by 'person' or 'rotation'")

    class Config:
        json_schema_extra = {
            "example": {
                "time_range": {
                    "range_type": "month",
                    "reference_date": "2024-01-15"
                },
                "person_ids": None,
                "rotation_ids": None,
                "include_fmit": True,
                "group_by": "person"
            }
        }
