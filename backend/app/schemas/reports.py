"""Report generation schemas for PDF reports."""
from datetime import date
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ReportType(str, Enum):
    """Available report types."""
    SCHEDULE = "schedule"
    COMPLIANCE = "compliance"
    ANALYTICS = "analytics"
    FACULTY_SUMMARY = "faculty_summary"


class ReportFormat(str, Enum):
    """Available report formats."""
    PDF = "pdf"


class ReportRequest(BaseModel):
    """Base schema for report generation requests."""
    report_type: ReportType
    start_date: date
    end_date: date
    format: ReportFormat = ReportFormat.PDF
    include_logo: bool = Field(default=True, description="Include organization logo")
    include_toc: bool = Field(default=True, description="Include table of contents")
    include_page_numbers: bool = Field(default=True, description="Include page numbers")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "report_type": "schedule",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "format": "pdf",
                "include_logo": True,
                "include_toc": True,
                "include_page_numbers": True,
            }
        }


class ScheduleReportRequest(ReportRequest):
    """Request schema for schedule overview report."""
    report_type: ReportType = ReportType.SCHEDULE
    person_ids: list[UUID] | None = Field(
        default=None,
        description="Filter by specific people (residents/faculty)"
    )
    rotation_template_ids: list[UUID] | None = Field(
        default=None,
        description="Filter by specific rotation templates"
    )
    include_details: bool = Field(
        default=True,
        description="Include detailed assignment information"
    )


class ComplianceReportRequest(ReportRequest):
    """Request schema for ACGME compliance report."""
    report_type: ReportType = ReportType.COMPLIANCE
    resident_ids: list[UUID] | None = Field(
        default=None,
        description="Filter by specific residents"
    )
    pgy_levels: list[int] | None = Field(
        default=None,
        description="Filter by PGY level (1, 2, 3)"
    )
    include_violations_only: bool = Field(
        default=False,
        description="Only include residents with violations"
    )


class AnalyticsReportRequest(ReportRequest):
    """Request schema for workload analytics report."""
    report_type: ReportType = ReportType.ANALYTICS
    include_charts: bool = Field(
        default=True,
        description="Include charts and visualizations"
    )
    include_fairness_metrics: bool = Field(
        default=True,
        description="Include fairness and equity metrics"
    )
    include_trends: bool = Field(
        default=True,
        description="Include trend analysis"
    )


class FacultySummaryReportRequest(ReportRequest):
    """Request schema for faculty summary report."""
    report_type: ReportType = ReportType.FACULTY_SUMMARY
    faculty_ids: list[UUID] | None = Field(
        default=None,
        description="Filter by specific faculty members"
    )
    include_workload: bool = Field(
        default=True,
        description="Include workload statistics"
    )
    include_supervision: bool = Field(
        default=True,
        description="Include supervision metrics"
    )


class ReportMetadata(BaseModel):
    """Metadata about generated report."""
    report_id: UUID
    report_type: ReportType
    generated_at: str
    generated_by: str
    start_date: date
    end_date: date
    page_count: int
    file_size_bytes: int


class ReportResponse(BaseModel):
    """Response schema for report generation."""
    success: bool
    message: str
    metadata: ReportMetadata | None = None
    download_url: str | None = None
    filename: str | None = None

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Report generated successfully",
                "metadata": {
                    "report_id": "123e4567-e89b-12d3-a456-426614174000",
                    "report_type": "schedule",
                    "generated_at": "2025-01-15T10:30:00Z",
                    "generated_by": "user@example.com",
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-31",
                    "page_count": 15,
                    "file_size_bytes": 245678,
                },
                "download_url": "/api/reports/download/123e4567-e89b-12d3-a456-426614174000",
                "filename": "schedule_report_2025-01-01_to_2025-01-31.pdf",
            }
        }


class DetailedComplianceReportRequest(BaseModel):
    """Request schema for detailed compliance report generation."""
    start_date: date = Field(..., description="Report period start date")
    end_date: date = Field(..., description="Report period end date")
    resident_ids: list[UUID] | None = Field(
        default=None,
        description="Filter by specific resident IDs (None = all residents)"
    )
    pgy_levels: list[int] | None = Field(
        default=None,
        description="Filter by PGY levels (e.g., [1, 2, 3])"
    )
    include_violations_only: bool = Field(
        default=False,
        description="Only include residents with violations"
    )
    include_charts: bool = Field(
        default=True,
        description="Include trend charts in PDF export"
    )
    include_details: bool = Field(
        default=True,
        description="Include detailed resident summaries"
    )
    format: str = Field(
        default="pdf",
        description="Export format: 'pdf' or 'excel'"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "start_date": "2025-01-01",
                "end_date": "2025-03-31",
                "pgy_levels": [1],
                "include_violations_only": True,
                "include_charts": True,
                "include_details": True,
                "format": "pdf",
            }
        }


class ComplianceSummary(BaseModel):
    """Summary statistics for compliance report."""
    total_residents: int
    residents_with_violations: int
    total_violations: int
    avg_weekly_hours: float
    max_weekly_hours: float
    compliance_rate: float
    supervision_compliance_rate: float
    coverage_rate: float

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "total_residents": 12,
                "residents_with_violations": 2,
                "total_violations": 3,
                "avg_weekly_hours": 65.5,
                "max_weekly_hours": 78.2,
                "compliance_rate": 83.3,
                "supervision_compliance_rate": 95.0,
                "coverage_rate": 98.5,
            }
        }


class ViolationDetail(BaseModel):
    """Detail of a single compliance violation."""
    type: str = Field(..., description="Violation type (80_HOUR_VIOLATION, etc.)")
    severity: str = Field(..., description="Severity level (CRITICAL, HIGH, MEDIUM)")
    message: str = Field(..., description="Human-readable violation message")
    person_id: UUID | None = Field(None, description="Affected person ID")
    person_name: str | None = Field(None, description="Affected person name")
    block_id: UUID | None = Field(None, description="Affected block ID")
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional violation details"
    )

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "type": "80_HOUR_VIOLATION",
                "severity": "CRITICAL",
                "message": "Dr. Smith: 82.5 hours/week (limit: 80)",
                "person_id": "123e4567-e89b-12d3-a456-426614174000",
                "person_name": "Dr. Jane Smith",
                "block_id": None,
                "details": {
                    "window_start": "2025-01-01",
                    "window_end": "2025-01-28",
                    "average_weekly_hours": 82.5,
                },
            }
        }


class ResidentComplianceSummary(BaseModel):
    """Compliance summary for a single resident."""
    resident_id: str
    resident_name: str
    pgy_level: int
    total_assignments: int
    total_hours: int
    avg_weekly_hours: float
    max_weekly_hours: float
    total_absence_days: int
    violation_count: int
    has_violations: bool
    violations: list[ViolationDetail] = Field(default_factory=list)

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "resident_id": "123e4567-e89b-12d3-a456-426614174000",
                "resident_name": "Dr. Jane Smith",
                "pgy_level": 1,
                "total_assignments": 120,
                "total_hours": 720,
                "avg_weekly_hours": 65.5,
                "max_weekly_hours": 78.0,
                "total_absence_days": 5,
                "violation_count": 1,
                "has_violations": True,
                "violations": [],
            }
        }


class ScheduledReportConfig(BaseModel):
    """Configuration for scheduled compliance report generation."""
    report_name: str = Field(..., description="Descriptive name for the report")
    schedule_cron: str = Field(
        ...,
        description="Cron expression for schedule (e.g., '0 8 * * 1' = Mon 8am)"
    )
    report_type: str = Field(
        default="compliance",
        description="Type of report to generate"
    )
    lookback_days: int = Field(
        default=30,
        description="Number of days to include in report (from today)"
    )
    format: str = Field(
        default="pdf",
        description="Export format: 'pdf' or 'excel'"
    )
    recipients: list[str] = Field(
        default_factory=list,
        description="Email addresses to send report to"
    )
    pgy_levels: list[int] | None = Field(
        default=None,
        description="Filter by PGY levels"
    )
    include_violations_only: bool = Field(
        default=False,
        description="Only include residents with violations"
    )
    enabled: bool = Field(default=True, description="Whether schedule is active")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "report_name": "Weekly PGY-1 Compliance Report",
                "schedule_cron": "0 8 * * 1",
                "report_type": "compliance",
                "lookback_days": 7,
                "format": "pdf",
                "recipients": ["program_director@example.com"],
                "pgy_levels": [1],
                "include_violations_only": True,
                "enabled": True,
            }
        }
