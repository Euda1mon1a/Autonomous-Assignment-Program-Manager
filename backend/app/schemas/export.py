"""
Export job schemas.

Pydantic models for scheduled data export jobs including:
- Export job configuration
- Export execution history
- Export templates and filters
- Delivery settings
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.export_job import (
    ExportDeliveryMethod,
    ExportFormat,
    ExportJobStatus,
    ExportTemplate,
)

# ============================================================================
# Base Schemas
# ============================================================================


class ExportJobBase(BaseModel):
    """Base schema for export job."""

    name: str = Field(..., min_length=1, max_length=255, description="Job name")
    description: str | None = Field(None, description="Job description")
    template: ExportTemplate = Field(..., description="Export template")
    format: ExportFormat = Field(default=ExportFormat.CSV, description="Export format")
    delivery_method: ExportDeliveryMethod = Field(
        default=ExportDeliveryMethod.EMAIL, description="Delivery method"
    )


class ExportJobCreate(ExportJobBase):
    """Schema for creating an export job."""

    # Email delivery settings
    email_recipients: list[str] | None = Field(None, description="Email recipients")
    email_subject_template: str | None = Field(
        None, max_length=500, description="Email subject template"
    )
    email_body_template: str | None = Field(None, description="Email body template")

    # S3 delivery settings
    s3_bucket: str | None = Field(None, max_length=255, description="S3 bucket name")
    s3_key_prefix: str | None = Field(None, max_length=500, description="S3 key prefix")
    s3_region: str | None = Field(
        default="us-east-1", max_length=50, description="S3 region"
    )

    # Scheduling
    schedule_cron: str | None = Field(
        None, max_length=100, description="Cron expression (e.g., '0 8 * * 1')"
    )
    schedule_enabled: bool = Field(
        default=False, description="Enable scheduled execution"
    )

    # Export configuration
    filters: dict[str, Any] | None = Field(default=None, description="Export filters")
    columns: list[str] | None = Field(None, description="Columns to include")
    include_headers: bool = Field(default=True, description="Include column headers")

    # Status
    enabled: bool = Field(default=True, description="Job enabled")

    @field_validator("email_recipients")
    @classmethod
    def validate_email_recipients(cls, v: list[str] | None) -> list[str] | None:
        """Validate email addresses."""
        if v is not None:
            import re

            email_regex = re.compile(
                r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            )
            for email in v:
                if not email_regex.match(email):
                    raise ValueError(f"Invalid email address: {email}")
        return v

    @field_validator("schedule_cron")
    @classmethod
    def validate_cron_expression(cls, v: str | None) -> str | None:
        """Validate cron expression format."""
        if v is not None:
            # Basic validation: should have 5 space-separated fields
            parts = v.split()
            if len(parts) != 5:
                raise ValueError(
                    "Cron expression must have 5 fields: minute hour day month day_of_week"
                )
        return v


class ExportJobUpdate(BaseModel):
    """Schema for updating an export job."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    template: ExportTemplate | None = None
    format: ExportFormat | None = None
    delivery_method: ExportDeliveryMethod | None = None
    email_recipients: list[str] | None = None
    email_subject_template: str | None = Field(None, max_length=500)
    email_body_template: str | None = None
    s3_bucket: str | None = Field(None, max_length=255)
    s3_key_prefix: str | None = Field(None, max_length=500)
    s3_region: str | None = Field(None, max_length=50)
    schedule_cron: str | None = Field(None, max_length=100)
    schedule_enabled: bool | None = None
    filters: dict[str, Any] | None = None
    columns: list[str] | None = None
    include_headers: bool | None = None
    enabled: bool | None = None

    @field_validator("email_recipients")
    @classmethod
    def validate_email_recipients(cls, v: list[str] | None) -> list[str] | None:
        """Validate email addresses."""
        if v is not None:
            import re

            email_regex = re.compile(
                r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            )
            for email in v:
                if not email_regex.match(email):
                    raise ValueError(f"Invalid email address: {email}")
        return v


class ExportJobResponse(ExportJobBase):
    """Schema for export job response."""

    id: str
    email_recipients: list[str] | None = None
    email_subject_template: str | None = None
    email_body_template: str | None = None
    s3_bucket: str | None = None
    s3_key_prefix: str | None = None
    s3_region: str | None = None
    schedule_cron: str | None = None
    schedule_enabled: bool
    filters: dict[str, Any] | None = None
    columns: list[str] | None = None
    include_headers: bool
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    run_count: int
    enabled: bool
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None

    class Config:
        from_attributes = True


class ExportJobListResponse(BaseModel):
    """Schema for paginated export job list."""

    jobs: list[ExportJobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Execution Schemas
# ============================================================================


class ExportJobExecutionCreate(BaseModel):
    """Schema for creating an export job execution."""

    job_id: str
    triggered_by: str = "manual"
    execution_metadata: dict[str, Any] | None = None


class ExportJobExecutionResponse(BaseModel):
    """Schema for export job execution response."""

    id: str
    job_id: str
    job_name: str
    started_at: datetime
    finished_at: datetime | None = None
    runtime_seconds: int | None = None
    scheduled_run_time: datetime | None = None
    status: ExportJobStatus
    row_count: int | None = None
    file_size_bytes: int | None = None
    file_path: str | None = None
    s3_url: str | None = None
    email_sent: bool
    email_recipients: list[str] | None = None
    error_message: str | None = None
    triggered_by: str | None = None
    execution_metadata: dict[str, Any] | None = None

    class Config:
        from_attributes = True


class ExportJobExecutionListResponse(BaseModel):
    """Schema for paginated export job execution list."""

    executions: list[ExportJobExecutionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Template Schemas
# ============================================================================


class ExportTemplateInfo(BaseModel):
    """Information about an export template."""

    template: ExportTemplate
    name: str
    description: str
    supported_formats: list[ExportFormat]
    default_filters: dict[str, Any] | None = None
    available_columns: list[str]


class ExportTemplateListResponse(BaseModel):
    """Schema for list of available export templates."""

    templates: list[ExportTemplateInfo]


# ============================================================================
# Action Schemas
# ============================================================================


class ExportJobRunRequest(BaseModel):
    """Request to run an export job immediately."""

    job_id: str
    override_filters: dict[str, Any] | None = Field(
        None, description="Temporary filter overrides for this execution"
    )
    override_recipients: list[str] | None = Field(
        None, description="Temporary recipient overrides for this execution"
    )


class ExportJobRunResponse(BaseModel):
    """Response for export job run request."""

    execution_id: str
    job_id: str
    job_name: str
    status: str
    message: str


class ExportJobStatsResponse(BaseModel):
    """Statistics for export jobs."""

    total_jobs: int = Field(alias="totalJobs")
    active_jobs: int = Field(alias="activeJobs")
    scheduled_jobs: int = Field(alias="scheduledJobs")
    total_executions: int = Field(alias="totalExecutions")
    successful_executions: int = Field(alias="successfulExecutions")
    failed_executions: int = Field(alias="failedExecutions")
    average_runtime_seconds: float | None = Field(None, alias="averageRuntimeSeconds")
    total_rows_exported: int | None = Field(None, alias="totalRowsExported")
    total_bytes_exported: int | None = Field(None, alias="totalBytesExported")

    class Config:
        populate_by_name = True
