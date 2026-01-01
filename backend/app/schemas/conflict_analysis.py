"""Conflict analysis response schemas for API endpoints."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from app.scheduling.conflicts.types import Conflict, ConflictSummary


class ConflictAnalysisResponse(BaseModel):
    """Response schema for comprehensive conflict analysis."""

    conflicts: list[dict[str, Any]] = Field(
        ..., description="List of detected conflicts"
    )
    summary: dict[str, Any] = Field(..., description="Summary statistics")
    analysis_period: dict[str, str] = Field(..., description="Analysis date range")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "conflicts": [
                    {
                        "conflict_id": "conf_123",
                        "category": "acgme_violation",
                        "severity": "critical",
                        "title": "80-Hour Violation",
                    }
                ],
                "summary": {
                    "total_conflicts": 5,
                    "critical_count": 2,
                    "high_count": 3,
                },
                "analysis_period": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                },
            }
        }


class ConflictHeatmapResponse(BaseModel):
    """Response schema for conflict heatmap visualization."""

    heatmap_data: dict[str, Any] = Field(..., description="Heatmap data structure")
    date_range: dict[str, str] = Field(..., description="Date range for heatmap")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "heatmap_data": {
                    "x_labels": ["2024-01-01", "2024-01-02"],
                    "y_labels": ["Dr. Smith", "Dr. Johnson"],
                    "z_values": [[0.5, 0.8], [0.2, 0.9]],
                },
                "date_range": {"start_date": "2024-01-01", "end_date": "2024-01-31"},
                "metadata": {"total_conflicts": 15},
            }
        }


class GanttEntry(BaseModel):
    """Single entry in Gantt chart."""

    task_id: str = Field(..., description="Task identifier")
    task_name: str = Field(..., description="Task name")
    start_date: str = Field(..., description="Start date (ISO format)")
    end_date: str = Field(..., description="End date (ISO format)")
    severity: str = Field(..., description="Severity level")
    category: str = Field(..., description="Conflict category")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "task_id": "conf_123",
                "task_name": "80-Hour Violation",
                "start_date": "2024-01-08",
                "end_date": "2024-01-14",
                "severity": "critical",
                "category": "acgme_violation",
            }
        }


class ConflictGanttResponse(BaseModel):
    """Response schema for conflict Gantt chart."""

    gantt_entries: list[dict[str, Any]] = Field(
        ..., description="List of Gantt chart entries"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "gantt_entries": [
                    {
                        "task_id": "conf_123",
                        "task_name": "80-Hour Violation",
                        "start_date": "2024-01-08",
                        "end_date": "2024-01-14",
                    }
                ]
            }
        }


class ConflictDistributionResponse(BaseModel):
    """Response schema for conflict distribution charts."""

    by_type: dict[str, int] = Field(
        default_factory=dict, description="Distribution by conflict type"
    )
    by_severity: dict[str, int] = Field(
        default_factory=dict, description="Distribution by severity"
    )
    by_category: dict[str, int] = Field(
        default_factory=dict, description="Distribution by category"
    )
    total_conflicts: int = Field(..., description="Total number of conflicts")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "by_type": {"double_booking": 3, "eighty_hour_violation": 2},
                "by_severity": {"critical": 2, "high": 3},
                "by_category": {"time_overlap": 3, "acgme_violation": 2},
                "total_conflicts": 5,
            }
        }


class PersonImpact(BaseModel):
    """Impact data for a single person."""

    person_id: str = Field(..., description="Person UUID")
    person_name: str = Field(..., description="Person name")
    conflict_count: int = Field(..., description="Number of conflicts affecting person")
    severity_score: float = Field(
        ..., ge=0.0, le=1.0, description="Average severity score"
    )
    conflict_types: list[str] = Field(..., description="Types of conflicts affecting person")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "person_id": "uuid_123",
                "person_name": "Dr. Smith",
                "conflict_count": 5,
                "severity_score": 0.75,
                "conflict_types": ["double_booking", "eighty_hour_violation"],
            }
        }


class PersonImpactResponse(BaseModel):
    """Response schema for person impact analysis."""

    person_impacts: list[dict[str, Any]] = Field(
        ..., description="List of people sorted by impact"
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "person_impacts": [
                    {
                        "person_id": "uuid_123",
                        "person_name": "Dr. Smith",
                        "conflict_count": 5,
                        "severity_score": 0.75,
                    }
                ]
            }
        }


class BatchConflictAnalysisResponse(BaseModel):
    """Response schema for batch conflict analysis."""

    total_people_analyzed: int = Field(..., description="Number of people analyzed")
    conflicts: list[dict[str, Any]] = Field(..., description="All detected conflicts")
    summary: dict[str, Any] = Field(..., description="Aggregate summary statistics")

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "total_people_analyzed": 10,
                "conflicts": [
                    {
                        "conflict_id": "conf_123",
                        "severity": "critical",
                        "title": "80-Hour Violation",
                    }
                ],
                "summary": {
                    "total_conflicts": 15,
                    "critical_count": 5,
                    "high_count": 10,
                },
            }
        }
