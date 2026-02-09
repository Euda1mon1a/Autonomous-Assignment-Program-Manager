"""Tests for report schemas (enums, defaults, nested models, default_factory)."""

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.reports import (
    ReportType,
    ReportFormat,
    ReportRequest,
    ScheduleReportRequest,
    ComplianceReportRequest,
    AnalyticsReportRequest,
    FacultySummaryReportRequest,
    ReportMetadata,
    ReportResponse,
    DetailedComplianceReportRequest,
    ComplianceSummary,
    ViolationDetail,
    ResidentComplianceSummary,
    ScheduledReportConfig,
)


class TestReportType:
    def test_values(self):
        assert ReportType.SCHEDULE == "schedule"
        assert ReportType.COMPLIANCE == "compliance"
        assert ReportType.ANALYTICS == "analytics"
        assert ReportType.FACULTY_SUMMARY == "faculty_summary"

    def test_count(self):
        assert len(ReportType) == 4


class TestReportFormat:
    def test_values(self):
        assert ReportFormat.PDF == "pdf"

    def test_count(self):
        assert len(ReportFormat) == 1


# ── ReportRequest ────────────────────────────────────────────────────────


class TestReportRequest:
    def test_defaults(self):
        r = ReportRequest(
            report_type=ReportType.SCHEDULE,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )
        assert r.format == ReportFormat.PDF
        assert r.include_logo is True
        assert r.include_toc is True
        assert r.include_page_numbers is True

    def test_override_defaults(self):
        r = ReportRequest(
            report_type=ReportType.COMPLIANCE,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            include_logo=False,
            include_toc=False,
            include_page_numbers=False,
        )
        assert r.include_logo is False
        assert r.include_toc is False
        assert r.include_page_numbers is False


# ── ScheduleReportRequest ───────────────────────────────────────────────


class TestScheduleReportRequest:
    def test_defaults(self):
        r = ScheduleReportRequest(
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31)
        )
        assert r.report_type == ReportType.SCHEDULE
        assert r.person_ids is None
        assert r.rotation_template_ids is None
        assert r.include_details is True

    def test_with_filters(self):
        uid = uuid4()
        r = ScheduleReportRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            person_ids=[uid],
            include_details=False,
        )
        assert r.person_ids == [uid]
        assert r.include_details is False


# ── ComplianceReportRequest ─────────────────────────────────────────────


class TestComplianceReportRequest:
    def test_defaults(self):
        r = ComplianceReportRequest(
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31)
        )
        assert r.report_type == ReportType.COMPLIANCE
        assert r.resident_ids is None
        assert r.pgy_levels is None
        assert r.include_violations_only is False

    def test_with_filters(self):
        r = ComplianceReportRequest(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            pgy_levels=[1, 2],
            include_violations_only=True,
        )
        assert r.pgy_levels == [1, 2]
        assert r.include_violations_only is True


# ── AnalyticsReportRequest ──────────────────────────────────────────────


class TestAnalyticsReportRequest:
    def test_defaults(self):
        r = AnalyticsReportRequest(
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31)
        )
        assert r.report_type == ReportType.ANALYTICS
        assert r.include_charts is True
        assert r.include_fairness_metrics is True
        assert r.include_trends is True


# ── FacultySummaryReportRequest ─────────────────────────────────────────


class TestFacultySummaryReportRequest:
    def test_defaults(self):
        r = FacultySummaryReportRequest(
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31)
        )
        assert r.report_type == ReportType.FACULTY_SUMMARY
        assert r.faculty_ids is None
        assert r.include_workload is True
        assert r.include_supervision is True


# ── ReportMetadata ──────────────────────────────────────────────────────


class TestReportMetadata:
    def test_valid(self):
        r = ReportMetadata(
            report_id=uuid4(),
            report_type=ReportType.SCHEDULE,
            generated_at="2026-01-15T10:30:00Z",
            generated_by="user@example.com",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            page_count=15,
            file_size_bytes=245678,
        )
        assert r.page_count == 15
        assert r.file_size_bytes == 245678


# ── ReportResponse ──────────────────────────────────────────────────────


class TestReportResponse:
    def test_defaults(self):
        r = ReportResponse(success=True, message="Report generated")
        assert r.metadata is None
        assert r.download_url is None
        assert r.filename is None

    def test_with_metadata(self):
        meta = ReportMetadata(
            report_id=uuid4(),
            report_type=ReportType.COMPLIANCE,
            generated_at="2026-01-15T10:30:00Z",
            generated_by="admin",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            page_count=25,
            file_size_bytes=500000,
        )
        r = ReportResponse(
            success=True,
            message="OK",
            metadata=meta,
            download_url="/reports/123",
            filename="report.pdf",
        )
        assert r.metadata.page_count == 25
        assert r.filename == "report.pdf"


# ── DetailedComplianceReportRequest ─────────────────────────────────────


class TestDetailedComplianceReportRequest:
    def test_defaults(self):
        r = DetailedComplianceReportRequest(
            start_date=date(2026, 1, 1), end_date=date(2026, 3, 31)
        )
        assert r.resident_ids is None
        assert r.pgy_levels is None
        assert r.include_violations_only is False
        assert r.include_charts is True
        assert r.include_details is True
        assert r.format == "pdf"


# ── ComplianceSummary ───────────────────────────────────────────────────


class TestComplianceSummary:
    def test_valid(self):
        r = ComplianceSummary(
            total_residents=12,
            residents_with_violations=2,
            total_violations=3,
            avg_weekly_hours=65.5,
            max_weekly_hours=78.2,
            compliance_rate=83.3,
            supervision_compliance_rate=95.0,
            coverage_rate=98.5,
        )
        assert r.total_residents == 12
        assert r.compliance_rate == 83.3


# ── ViolationDetail ─────────────────────────────────────────────────────


class TestViolationDetail:
    def test_defaults(self):
        r = ViolationDetail(
            type="80_HOUR_VIOLATION",
            severity="CRITICAL",
            message="82.5 hours/week",
        )
        assert r.person_id is None
        assert r.person_name is None
        assert r.block_id is None
        assert r.details == {}

    def test_with_details(self):
        uid = uuid4()
        r = ViolationDetail(
            type="SUPERVISION_GAP",
            severity="HIGH",
            message="Missing supervisor",
            person_id=uid,
            person_name="Dr. Smith",
            details={"window_start": "2026-01-01"},
        )
        assert r.person_id == uid
        assert r.details["window_start"] == "2026-01-01"


# ── ResidentComplianceSummary ───────────────────────────────────────────


class TestResidentComplianceSummary:
    def test_defaults(self):
        r = ResidentComplianceSummary(
            resident_id="res-1",
            resident_name="Dr. Smith",
            pgy_level=1,
            total_assignments=120,
            total_hours=720,
            avg_weekly_hours=65.5,
            max_weekly_hours=78.0,
            total_absence_days=5,
            violation_count=0,
            has_violations=False,
        )
        assert r.violations == []

    def test_with_violations(self):
        v = ViolationDetail(
            type="80_HOUR_VIOLATION", severity="CRITICAL", message="82h"
        )
        r = ResidentComplianceSummary(
            resident_id="res-2",
            resident_name="Dr. Jones",
            pgy_level=2,
            total_assignments=100,
            total_hours=800,
            avg_weekly_hours=72.0,
            max_weekly_hours=82.0,
            total_absence_days=2,
            violation_count=1,
            has_violations=True,
            violations=[v],
        )
        assert len(r.violations) == 1
        assert r.violations[0].type == "80_HOUR_VIOLATION"


# ── ScheduledReportConfig ───────────────────────────────────────────────


class TestScheduledReportConfig:
    def test_defaults(self):
        r = ScheduledReportConfig(
            report_name="Weekly Compliance",
            schedule_cron="0 8 * * 1",
        )
        assert r.report_type == "compliance"
        assert r.lookback_days == 30
        assert r.format == "pdf"
        assert r.recipients == []
        assert r.pgy_levels is None
        assert r.include_violations_only is False
        assert r.enabled is True

    def test_custom_values(self):
        r = ScheduledReportConfig(
            report_name="Monthly PGY-1",
            schedule_cron="0 6 1 * *",
            lookback_days=30,
            recipients=["admin@example.com"],
            pgy_levels=[1],
            include_violations_only=True,
            enabled=False,
        )
        assert r.recipients == ["admin@example.com"]
        assert r.pgy_levels == [1]
        assert r.enabled is False
