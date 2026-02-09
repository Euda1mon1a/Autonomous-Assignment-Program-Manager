"""Tests for ACGME compliance engine utility methods and dataclasses (no DB)."""

from datetime import date, datetime, time
from uuid import uuid4

import pytest

from app.scheduling.acgme_compliance_engine import (
    ACGMEComplianceEngine,
    ComplianceCheckResult,
    ScheduleValidationReport,
)


# ==================== Dataclass Tests ====================


class TestComplianceCheckResult:
    """Test ComplianceCheckResult dataclass."""

    def test_basic_construction(self):
        pid = uuid4()
        r = ComplianceCheckResult(
            person_id=pid,
            check_date=date(2025, 6, 1),
            is_compliant=True,
        )
        assert r.person_id == pid
        assert r.check_date == date(2025, 6, 1)
        assert r.is_compliant is True

    def test_defaults_zero(self):
        r = ComplianceCheckResult(
            person_id=uuid4(),
            check_date=date.today(),
            is_compliant=True,
        )
        assert r.critical_violations == 0
        assert r.high_violations == 0
        assert r.medium_violations == 0
        assert r.warnings == 0
        assert r.violations_by_domain == {}
        assert r.warnings_by_domain == {}
        assert r.remediation_suggestions == []
        assert r.last_updated is None

    def test_non_compliant_with_violations(self):
        r = ComplianceCheckResult(
            person_id=uuid4(),
            check_date=date.today(),
            is_compliant=False,
            critical_violations=2,
            high_violations=1,
            remediation_suggestions=["Reduce hours"],
        )
        assert r.is_compliant is False
        assert r.critical_violations == 2
        assert len(r.remediation_suggestions) == 1


class TestScheduleValidationReport:
    """Test ScheduleValidationReport dataclass."""

    def test_basic_construction(self):
        r = ScheduleValidationReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 6, 30),
            total_residents=20,
            residents_compliant=18,
            compliance_percentage=90.0,
            critical_violations_count=1,
            high_violations_count=3,
        )
        assert r.total_residents == 20
        assert r.compliance_percentage == 90.0

    def test_defaults(self):
        r = ScheduleValidationReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 6, 30),
            total_residents=0,
            residents_compliant=0,
            compliance_percentage=100.0,
            critical_violations_count=0,
            high_violations_count=0,
        )
        assert r.by_resident == {}
        assert r.by_domain == {}
        assert r.executive_summary == ""


# ==================== Engine Utility Method Tests ====================


class TestNormalizeDate:
    """Test _normalize_date utility method."""

    def setup_method(self):
        self.engine = ACGMEComplianceEngine()

    def test_none_returns_none(self):
        assert self.engine._normalize_date(None) is None

    def test_date_passthrough(self):
        d = date(2025, 6, 1)
        assert self.engine._normalize_date(d) == d

    def test_iso_string(self):
        assert self.engine._normalize_date("2025-06-01") == date(2025, 6, 1)

    def test_invalid_string_returns_none(self):
        assert self.engine._normalize_date("not-a-date") is None

    def test_integer_returns_none(self):
        assert self.engine._normalize_date(12345) is None


class TestParseTimeToDatetime:
    """Test _parse_time_to_datetime utility method."""

    def setup_method(self):
        self.engine = ACGMEComplianceEngine()
        self.d = date(2025, 6, 1)

    def test_string_hhmm(self):
        result = self.engine._parse_time_to_datetime(self.d, "13:30")
        assert result == datetime(2025, 6, 1, 13, 30, 0)

    def test_string_hhmmss(self):
        result = self.engine._parse_time_to_datetime(self.d, "07:00:30")
        assert result == datetime(2025, 6, 1, 7, 0, 30)

    def test_time_object(self):
        t = time(14, 45)
        result = self.engine._parse_time_to_datetime(self.d, t)
        assert result == datetime(2025, 6, 1, 14, 45, 0)

    def test_invalid_returns_none(self):
        assert self.engine._parse_time_to_datetime(self.d, "invalid") is None

    def test_none_returns_none(self):
        assert self.engine._parse_time_to_datetime(self.d, None) is None


class TestCalculateDurationHours:
    """Test _calculate_duration_hours utility method."""

    def setup_method(self):
        self.engine = ACGMEComplianceEngine()
        self.d = date(2025, 6, 1)

    def test_same_day_duration(self):
        result = self.engine._calculate_duration_hours(self.d, "07:00", "13:00", 6.0)
        assert result == pytest.approx(6.0)

    def test_overnight_duration(self):
        result = self.engine._calculate_duration_hours(self.d, "19:00", "07:00", 12.0)
        assert result == pytest.approx(12.0)

    def test_invalid_start_returns_default(self):
        result = self.engine._calculate_duration_hours(self.d, "invalid", "07:00", 8.0)
        assert result == 8.0

    def test_invalid_end_returns_default(self):
        result = self.engine._calculate_duration_hours(self.d, "07:00", "invalid", 8.0)
        assert result == 8.0


class TestGetCallValue:
    """Test _get_call_value helper."""

    def setup_method(self):
        self.engine = ACGMEComplianceEngine()

    def test_dict_access(self):
        call = {"date": "2025-06-01", "call_type": "primary"}
        assert self.engine._get_call_value(call, "date") == "2025-06-01"
        assert self.engine._get_call_value(call, "call_type") == "primary"

    def test_dict_missing_key(self):
        call = {"date": "2025-06-01"}
        assert self.engine._get_call_value(call, "missing") is None

    def test_object_attribute_access(self):
        class CallObj:
            date = "2025-06-01"
            call_type = "backup"

        obj = CallObj()
        assert self.engine._get_call_value(obj, "date") == "2025-06-01"
        assert self.engine._get_call_value(obj, "call_type") == "backup"

    def test_object_missing_attribute(self):
        class CallObj:
            pass

        obj = CallObj()
        assert self.engine._get_call_value(obj, "missing") is None


class TestCalculateHoursByDate:
    """Test _calculate_hours_by_date utility method."""

    def setup_method(self):
        self.engine = ACGMEComplianceEngine()

    def test_empty_assignments(self):
        result = self.engine._calculate_hours_by_date([], [])
        assert result == {}

    def test_single_assignment(self):
        blocks = [{"id": "b1", "date": date(2025, 6, 1)}]
        assignments = [{"block_id": "b1"}]
        result = self.engine._calculate_hours_by_date(assignments, blocks)
        assert result[date(2025, 6, 1)] == 6.0

    def test_multiple_assignments_same_date(self):
        blocks = [
            {"id": "b1", "date": date(2025, 6, 1)},
            {"id": "b2", "date": date(2025, 6, 1)},
        ]
        assignments = [{"block_id": "b1"}, {"block_id": "b2"}]
        result = self.engine._calculate_hours_by_date(assignments, blocks)
        assert result[date(2025, 6, 1)] == 12.0

    def test_missing_block_skipped(self):
        blocks = []
        assignments = [{"block_id": "missing"}]
        result = self.engine._calculate_hours_by_date(assignments, blocks)
        assert result == {}


class TestBuildShiftData:
    """Test _build_shift_data utility method."""

    def setup_method(self):
        self.engine = ACGMEComplianceEngine()

    def test_empty_input(self):
        result = self.engine._build_shift_data([], [])
        assert result == []

    def test_am_block_defaults(self):
        blocks = [{"id": "b1", "date": date(2025, 6, 1), "time_of_day": "AM"}]
        assignments = [{"block_id": "b1"}]
        result = self.engine._build_shift_data(assignments, blocks)
        assert len(result) == 1
        assert result[0]["start_time"] == "07:00"
        assert result[0]["end_time"] == "13:00"

    def test_pm_block_defaults(self):
        blocks = [{"id": "b1", "date": date(2025, 6, 1), "time_of_day": "PM"}]
        assignments = [{"block_id": "b1"}]
        result = self.engine._build_shift_data(assignments, blocks)
        assert result[0]["start_time"] == "13:00"
        assert result[0]["end_time"] == "19:00"

    def test_explicit_times_used(self):
        blocks = [
            {
                "id": "b1",
                "date": date(2025, 6, 1),
                "start_time": "08:00",
                "end_time": "16:00",
            }
        ]
        assignments = [{"block_id": "b1"}]
        result = self.engine._build_shift_data(assignments, blocks)
        assert result[0]["start_time"] == "08:00"
        assert result[0]["end_time"] == "16:00"

    def test_call_assignment_included(self):
        call_assignments = [{"date": date(2025, 6, 1), "call_type": "primary"}]
        result = self.engine._build_shift_data([], [], call_assignments)
        assert len(result) == 1
        assert result[0]["is_call"] is True
        assert result[0]["source"] == "call_assignment"

    def test_backup_call_excluded(self):
        call_assignments = [{"date": date(2025, 6, 1), "call_type": "backup"}]
        result = self.engine._build_shift_data([], [], call_assignments)
        assert len(result) == 0

    def test_sorted_by_date(self):
        blocks = [
            {"id": "b1", "date": date(2025, 6, 3)},
            {"id": "b2", "date": date(2025, 6, 1)},
        ]
        assignments = [{"block_id": "b1"}, {"block_id": "b2"}]
        result = self.engine._build_shift_data(assignments, blocks)
        assert result[0]["date"] == date(2025, 6, 1)
        assert result[1]["date"] == date(2025, 6, 3)


class TestBuildBlockSupervisionData:
    """Test _build_block_supervision_data utility method."""

    def setup_method(self):
        self.engine = ACGMEComplianceEngine()

    def test_empty_input(self):
        result = self.engine._build_block_supervision_data([], [], [])
        assert result == []

    def test_pgy1_classified_correctly(self):
        residents = [{"id": "r1", "type": "resident", "pgy_level": 1}]
        blocks = [{"id": "b1", "date": date(2025, 6, 1)}]
        assignments = [{"block_id": "b1", "person_id": "r1"}]
        result = self.engine._build_block_supervision_data(
            assignments, blocks, residents
        )
        assert len(result) == 1
        assert "r1" in result[0]["pgy1_residents"]

    def test_senior_resident_classified(self):
        residents = [{"id": "r2", "type": "resident", "pgy_level": 3}]
        blocks = [{"id": "b1", "date": date(2025, 6, 1)}]
        assignments = [{"block_id": "b1", "person_id": "r2"}]
        result = self.engine._build_block_supervision_data(
            assignments, blocks, residents
        )
        assert "r2" in result[0]["other_residents"]

    def test_faculty_classified(self):
        persons = [{"id": "f1", "type": "faculty"}]
        blocks = [{"id": "b1", "date": date(2025, 6, 1)}]
        assignments = [{"block_id": "b1", "person_id": "f1"}]
        result = self.engine._build_block_supervision_data(assignments, blocks, persons)
        assert "f1" in result[0]["faculty_assigned"]

    def test_unknown_person_skipped(self):
        residents = []
        blocks = [{"id": "b1", "date": date(2025, 6, 1)}]
        assignments = [{"block_id": "b1", "person_id": "unknown"}]
        result = self.engine._build_block_supervision_data(
            assignments, blocks, residents
        )
        assert len(result) == 1
        assert result[0]["pgy1_residents"] == []
        assert result[0]["faculty_assigned"] == []


# ==================== Executive Summary Tests ====================


class TestGenerateExecutiveSummary:
    """Test _generate_executive_summary method."""

    def setup_method(self):
        self.engine = ACGMEComplianceEngine()

    def test_fully_compliant(self):
        summary = self.engine._generate_executive_summary(10, 10, 0, 0, 100.0)
        assert "FULLY COMPLIANT" in summary
        assert "10/10" in summary

    def test_critical_violations(self):
        summary = self.engine._generate_executive_summary(8, 10, 2, 1, 80.0)
        assert "CRITICAL VIOLATIONS: 2" in summary
        assert "NON-COMPLIANT (Critical Issues)" in summary

    def test_high_only(self):
        summary = self.engine._generate_executive_summary(9, 10, 0, 3, 90.0)
        assert "HIGH VIOLATIONS: 3" in summary
        assert "NON-COMPLIANT (High Issues)" in summary

    def test_warnings_only(self):
        summary = self.engine._generate_executive_summary(10, 10, 0, 0, 95.0)
        # 95% but no critical/high -> compliant with warnings
        assert "COMPLIANT WITH WARNINGS" in summary


# ==================== Recommendations Tests ====================


class TestGenerateRecommendations:
    """Test _generate_recommendations method."""

    def setup_method(self):
        self.engine = ACGMEComplianceEngine()

    def _make_report(self, pct=100.0, critical=0, high=0):
        return ScheduleValidationReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 6, 30),
            total_residents=10,
            residents_compliant=int(10 * pct / 100),
            compliance_percentage=pct,
            critical_violations_count=critical,
            high_violations_count=high,
        )

    def test_no_issues_returns_compliant_message(self):
        report = self._make_report(pct=100.0)
        recs = self.engine._generate_recommendations(report)
        assert len(recs) == 1
        assert "compliant" in recs[0].lower()

    def test_low_compliance_flags_gap(self):
        report = self._make_report(pct=90.0)
        recs = self.engine._generate_recommendations(report)
        assert any("compliance gaps" in r.lower() for r in recs)

    def test_critical_violations_flagged_urgent(self):
        report = self._make_report(critical=3)
        recs = self.engine._generate_recommendations(report)
        assert any("urgent" in r.lower() for r in recs)

    def test_high_violations_flagged(self):
        report = self._make_report(high=5)
        recs = self.engine._generate_recommendations(report)
        assert any("high priority" in r.lower() for r in recs)


# ==================== Dashboard Data Tests ====================


class TestGenerateComplianceDashboardData:
    """Test generate_compliance_dashboard_data method."""

    def setup_method(self):
        self.engine = ACGMEComplianceEngine()

    def test_dashboard_structure(self):
        report = ScheduleValidationReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 6, 30),
            total_residents=10,
            residents_compliant=9,
            compliance_percentage=90.0,
            critical_violations_count=0,
            high_violations_count=1,
            executive_summary="Test summary",
        )
        data = self.engine.generate_compliance_dashboard_data(report)
        assert "summary" in data
        assert "period" in data
        assert "by_domain" in data
        assert "executive_summary" in data
        assert "recommendations" in data

    def test_dashboard_summary_values(self):
        report = ScheduleValidationReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 6, 30),
            total_residents=20,
            residents_compliant=18,
            compliance_percentage=90.0,
            critical_violations_count=1,
            high_violations_count=2,
        )
        data = self.engine.generate_compliance_dashboard_data(report)
        assert data["summary"]["total_residents"] == 20
        assert data["summary"]["compliant"] == 18
        assert data["summary"]["percentage"] == 90.0
        assert data["summary"]["critical_violations"] == 1

    def test_dashboard_period_iso_format(self):
        report = ScheduleValidationReport(
            period_start=date(2025, 1, 1),
            period_end=date(2025, 6, 30),
            total_residents=0,
            residents_compliant=0,
            compliance_percentage=100.0,
            critical_violations_count=0,
            high_violations_count=0,
        )
        data = self.engine.generate_compliance_dashboard_data(report)
        assert data["period"]["start"] == "2025-01-01"
        assert data["period"]["end"] == "2025-06-30"
