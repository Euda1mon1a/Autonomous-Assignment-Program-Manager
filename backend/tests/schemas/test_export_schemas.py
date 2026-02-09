"""Tests for export job schemas (Field bounds, field_validators, defaults, aliases)."""

import pytest
from pydantic import ValidationError

from app.models.export_job import (
    ExportDeliveryMethod,
    ExportFormat,
    ExportJobStatus,
    ExportTemplate,
)
from app.schemas.export import (
    ExportJobBase,
    ExportJobCreate,
    ExportJobUpdate,
    ExportJobResponse,
    ExportJobListResponse,
    ExportJobExecutionCreate,
    ExportJobExecutionResponse,
    ExportJobExecutionListResponse,
    ExportTemplateInfo,
    ExportTemplateListResponse,
    ExportJobRunRequest,
    ExportJobRunResponse,
    ExportJobStatsResponse,
)
from datetime import datetime


# ── Enums (imported from model) ──────────────────────────────────────────


class TestExportFormat:
    def test_values(self):
        assert ExportFormat.CSV == "csv"
        assert ExportFormat.JSON == "json"
        assert ExportFormat.XLSX == "xlsx"

    def test_count(self):
        assert len(ExportFormat) == 4


class TestExportDeliveryMethod:
    def test_values(self):
        assert ExportDeliveryMethod.EMAIL == "email"
        assert ExportDeliveryMethod.S3 == "s3"
        assert ExportDeliveryMethod.BOTH == "both"

    def test_count(self):
        assert len(ExportDeliveryMethod) == 3


class TestExportJobStatus:
    def test_values(self):
        assert ExportJobStatus.PENDING == "pending"
        assert ExportJobStatus.RUNNING == "running"
        assert ExportJobStatus.COMPLETED == "completed"
        assert ExportJobStatus.FAILED == "failed"
        assert ExportJobStatus.CANCELLED == "cancelled"

    def test_count(self):
        assert len(ExportJobStatus) == 5


class TestExportTemplate:
    def test_values(self):
        assert ExportTemplate.FULL_SCHEDULE == "full_schedule"
        assert ExportTemplate.PERSONNEL == "personnel"
        assert ExportTemplate.CUSTOM == "custom"

    def test_count(self):
        assert len(ExportTemplate) == 7


# ── ExportJobBase ────────────────────────────────────────────────────────


class TestExportJobBase:
    def test_defaults(self):
        r = ExportJobBase(name="Weekly Export", template=ExportTemplate.FULL_SCHEDULE)
        assert r.format == ExportFormat.CSV
        assert r.delivery_method == ExportDeliveryMethod.EMAIL
        assert r.description is None

    # --- name min_length=1, max_length=255 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            ExportJobBase(name="", template=ExportTemplate.FULL_SCHEDULE)

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            ExportJobBase(name="x" * 256, template=ExportTemplate.FULL_SCHEDULE)


# ── ExportJobCreate ─────────────────────────────────────────────────────


class TestExportJobCreate:
    def test_defaults(self):
        r = ExportJobCreate(name="Export", template=ExportTemplate.PERSONNEL)
        assert r.email_recipients is None
        assert r.s3_region == "us-east-1"
        assert r.schedule_cron is None
        assert r.schedule_enabled is False
        assert r.include_headers is True
        assert r.enabled is True
        assert r.filters is None
        assert r.columns is None

    # --- email_recipients validator ---

    def test_valid_emails(self):
        r = ExportJobCreate(
            name="Export",
            template=ExportTemplate.PERSONNEL,
            email_recipients=["a@example.com", "b@test.org"],
        )
        assert len(r.email_recipients) == 2

    def test_invalid_email(self):
        with pytest.raises(ValidationError, match="Invalid email"):
            ExportJobCreate(
                name="Export",
                template=ExportTemplate.PERSONNEL,
                email_recipients=["not-an-email"],
            )

    def test_email_recipients_none_ok(self):
        r = ExportJobCreate(
            name="Export", template=ExportTemplate.PERSONNEL, email_recipients=None
        )
        assert r.email_recipients is None

    # --- schedule_cron validator (5 fields) ---

    def test_valid_cron(self):
        r = ExportJobCreate(
            name="Export",
            template=ExportTemplate.PERSONNEL,
            schedule_cron="0 8 * * 1",
        )
        assert r.schedule_cron == "0 8 * * 1"

    def test_cron_wrong_fields(self):
        with pytest.raises(ValidationError, match="5 fields"):
            ExportJobCreate(
                name="Export",
                template=ExportTemplate.PERSONNEL,
                schedule_cron="0 8 *",
            )

    def test_cron_none_ok(self):
        r = ExportJobCreate(
            name="Export", template=ExportTemplate.PERSONNEL, schedule_cron=None
        )
        assert r.schedule_cron is None

    # --- max_length bounds ---

    def test_email_subject_too_long(self):
        with pytest.raises(ValidationError):
            ExportJobCreate(
                name="Export",
                template=ExportTemplate.PERSONNEL,
                email_subject_template="x" * 501,
            )

    def test_s3_bucket_too_long(self):
        with pytest.raises(ValidationError):
            ExportJobCreate(
                name="Export",
                template=ExportTemplate.PERSONNEL,
                s3_bucket="x" * 256,
            )

    def test_s3_key_prefix_too_long(self):
        with pytest.raises(ValidationError):
            ExportJobCreate(
                name="Export",
                template=ExportTemplate.PERSONNEL,
                s3_key_prefix="x" * 501,
            )

    def test_s3_region_too_long(self):
        with pytest.raises(ValidationError):
            ExportJobCreate(
                name="Export",
                template=ExportTemplate.PERSONNEL,
                s3_region="x" * 51,
            )


# ── ExportJobUpdate ─────────────────────────────────────────────────────


class TestExportJobUpdate:
    def test_all_none(self):
        r = ExportJobUpdate()
        assert r.name is None
        assert r.template is None
        assert r.format is None
        assert r.delivery_method is None

    def test_partial(self):
        r = ExportJobUpdate(name="Updated", format=ExportFormat.JSON)
        assert r.name == "Updated"
        assert r.format == ExportFormat.JSON

    def test_email_recipients_validator_on_update(self):
        with pytest.raises(ValidationError, match="Invalid email"):
            ExportJobUpdate(email_recipients=["bad"])

    def test_name_bounds_on_update(self):
        with pytest.raises(ValidationError):
            ExportJobUpdate(name="")


# ── ExportJobResponse ───────────────────────────────────────────────────


class TestExportJobResponse:
    def test_valid(self):
        r = ExportJobResponse(
            id="job-1",
            name="Weekly",
            template=ExportTemplate.FULL_SCHEDULE,
            format=ExportFormat.CSV,
            delivery_method=ExportDeliveryMethod.EMAIL,
            schedule_enabled=False,
            include_headers=True,
            run_count=3,
            enabled=True,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
        assert r.last_run_at is None
        assert r.next_run_at is None
        assert r.created_by is None


# ── ExportJobListResponse ───────────────────────────────────────────────


class TestExportJobListResponse:
    def test_valid(self):
        r = ExportJobListResponse(jobs=[], total=0, page=1, page_size=20, total_pages=0)
        assert r.jobs == []


# ── Execution schemas ───────────────────────────────────────────────────


class TestExportJobExecutionCreate:
    def test_defaults(self):
        r = ExportJobExecutionCreate(job_id="job-1")
        assert r.triggered_by == "manual"
        assert r.execution_metadata is None


class TestExportJobExecutionResponse:
    def test_valid(self):
        r = ExportJobExecutionResponse(
            id="exec-1",
            job_id="job-1",
            job_name="Weekly",
            started_at=datetime(2026, 1, 1),
            status=ExportJobStatus.COMPLETED,
            email_sent=True,
        )
        assert r.finished_at is None
        assert r.row_count is None
        assert r.error_message is None


class TestExportJobExecutionListResponse:
    def test_valid(self):
        r = ExportJobExecutionListResponse(
            executions=[], total=0, page=1, page_size=20, total_pages=0
        )
        assert r.executions == []


# ── Template schemas ────────────────────────────────────────────────────


class TestExportTemplateInfo:
    def test_valid(self):
        r = ExportTemplateInfo(
            template=ExportTemplate.PERSONNEL,
            name="Personnel",
            description="All personnel",
            supported_formats=[ExportFormat.CSV, ExportFormat.JSON],
            available_columns=["name", "email"],
        )
        assert r.default_filters is None
        assert len(r.supported_formats) == 2


class TestExportTemplateListResponse:
    def test_valid(self):
        r = ExportTemplateListResponse(templates=[])
        assert r.templates == []


# ── Action schemas ──────────────────────────────────────────────────────


class TestExportJobRunRequest:
    def test_defaults(self):
        r = ExportJobRunRequest(job_id="job-1")
        assert r.override_filters is None
        assert r.override_recipients is None


class TestExportJobRunResponse:
    def test_valid(self):
        r = ExportJobRunResponse(
            execution_id="exec-1",
            job_id="job-1",
            job_name="Weekly",
            status="running",
            message="Started",
        )
        assert r.status == "running"


# ── Stats (aliases) ────────────────────────────────────────────────────


class TestExportJobStatsResponse:
    def test_by_alias(self):
        r = ExportJobStatsResponse(
            totalJobs=10,
            activeJobs=5,
            scheduledJobs=3,
            totalExecutions=100,
            successfulExecutions=95,
            failedExecutions=5,
        )
        assert r.total_jobs == 10
        assert r.active_jobs == 5

    def test_by_field_name(self):
        r = ExportJobStatsResponse(
            total_jobs=10,
            active_jobs=5,
            scheduled_jobs=3,
            total_executions=100,
            successful_executions=95,
            failed_executions=5,
        )
        assert r.total_jobs == 10

    def test_optional_defaults(self):
        r = ExportJobStatsResponse(
            totalJobs=0,
            activeJobs=0,
            scheduledJobs=0,
            totalExecutions=0,
            successfulExecutions=0,
            failedExecutions=0,
        )
        assert r.average_runtime_seconds is None
        assert r.total_rows_exported is None
        assert r.total_bytes_exported is None
