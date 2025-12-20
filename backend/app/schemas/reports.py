"""Report generation schemas for PDF reports."""
from datetime import date
from enum import Enum
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
