"""Unified heatmap schemas for combined residency and FMIT schedule visualization."""
from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class UnifiedCoverageRequest(BaseModel):
    """Request schema for unified coverage heatmap."""

    start_date: date = Field(..., description="Start date for heatmap")
    end_date: date = Field(..., description="End date for heatmap")
    include_fmit: bool = Field(True, description="Include FMIT assignments in heatmap")
    include_residency: bool = Field(True, description="Include residency assignments in heatmap")

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "include_fmit": True,
                "include_residency": True,
            }
        }


class UnifiedCoverageResponse(BaseModel):
    """Response schema for unified coverage heatmap."""

    x_labels: list[str] = Field(..., description="X-axis labels (dates)")
    y_labels: list[str] = Field(..., description="Y-axis labels (rotations)")
    z_values: list[list[float]] = Field(..., description="Matrix of coverage values")
    color_scale: str = Field(..., description="Plotly color scale name")
    metadata: dict[str, Any] = Field(..., description="Additional metadata")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of generation")

    class Config:
        json_schema_extra = {
            "example": {
                "x_labels": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "y_labels": ["FMIT", "Clinic", "Procedures"],
                "z_values": [[2, 1, 2], [3, 3, 2], [1, 2, 1]],
                "color_scale": "Viridis",
                "metadata": {
                    "total_assignments": 17,
                    "date_range_days": 3,
                    "rotations_count": 3,
                    "max_coverage": 3,
                },
                "generated_at": "2024-01-15T10:00:00",
            }
        }


class PersonCoverageRequest(BaseModel):
    """Request schema for person-level coverage heatmap."""

    start_date: date = Field(..., description="Start date for heatmap")
    end_date: date = Field(..., description="End date for heatmap")
    person_ids: list[UUID] | None = Field(None, description="Optional filter by person IDs")
    include_call: bool = Field(False, description="Include call assignments in coverage")

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "person_ids": None,
                "include_call": False,
            }
        }


class PersonCoverageResponse(BaseModel):
    """Response schema for person-level coverage heatmap."""

    x_labels: list[str] = Field(..., description="X-axis labels (dates)")
    y_labels: list[str] = Field(..., description="Y-axis labels (person names)")
    z_values: list[list[float]] = Field(..., description="Matrix of assignment counts per person per day")
    color_scale: str = Field(..., description="Plotly color scale name")
    metadata: dict[str, Any] = Field(..., description="Additional metadata")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of generation")

    class Config:
        json_schema_extra = {
            "example": {
                "x_labels": ["2024-01-01", "2024-01-02"],
                "y_labels": ["Dr. Smith", "Dr. Johnson"],
                "z_values": [[2, 1], [1, 2]],
                "color_scale": "Blues",
                "metadata": {
                    "total_assignments": 6,
                    "date_range_days": 2,
                    "people_count": 2,
                    "include_call": False,
                },
                "generated_at": "2024-01-15T10:00:00",
            }
        }


class WeeklyFMITRequest(BaseModel):
    """Request schema for weekly FMIT assignment heatmap."""

    start_date: date = Field(..., description="Start date for heatmap")
    end_date: date = Field(..., description="End date for heatmap")

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
            }
        }


class WeeklyFMITResponse(BaseModel):
    """Response schema for weekly FMIT assignment heatmap."""

    x_labels: list[str] = Field(..., description="X-axis labels (week start dates)")
    y_labels: list[str] = Field(..., description="Y-axis labels (faculty names)")
    z_values: list[list[float]] = Field(..., description="Matrix showing FMIT assignments (1=assigned, 0=not assigned)")
    color_scale: str = Field(..., description="Plotly color scale name")
    metadata: dict[str, Any] = Field(..., description="Additional metadata")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of generation")

    class Config:
        json_schema_extra = {
            "example": {
                "x_labels": ["2024-01-01", "2024-01-08", "2024-01-15"],
                "y_labels": ["Dr. Adams", "Dr. Brown", "Dr. Chen"],
                "z_values": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
                "color_scale": "RdYlGn",
                "metadata": {
                    "total_weeks": 3,
                    "total_weeks_assigned": 3,
                    "faculty_count": 3,
                },
                "generated_at": "2024-01-15T10:00:00",
            }
        }


class HeatmapExportRequest(BaseModel):
    """Request schema for exporting heatmap as image."""

    start_date: date = Field(..., description="Start date for heatmap")
    end_date: date = Field(..., description="End date for heatmap")
    format: str = Field("png", description="Export format: 'png', 'svg', or 'pdf'")
    include_fmit: bool = Field(True, description="Include FMIT assignments")
    include_residency: bool = Field(True, description="Include residency assignments")
    width: int = Field(1200, description="Image width in pixels", gt=0, le=4000)
    height: int = Field(800, description="Image height in pixels", gt=0, le=4000)

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "format": "png",
                "include_fmit": True,
                "include_residency": True,
                "width": 1200,
                "height": 800,
            }
        }


class HeatmapRenderRequest(BaseModel):
    """Request schema for rendering heatmap as HTML."""

    start_date: date = Field(..., description="Start date for heatmap")
    end_date: date = Field(..., description="End date for heatmap")
    include_fmit: bool = Field(True, description="Include FMIT assignments")
    include_residency: bool = Field(True, description="Include residency assignments")

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-01-01",
                "end_date": "2024-03-31",
                "include_fmit": True,
                "include_residency": True,
            }
        }
