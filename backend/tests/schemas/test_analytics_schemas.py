"""Tests for analytics schemas (Pydantic validation, aliases, and max_length)."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.analytics import (
    MetricValue,
    ScheduleVersionMetrics,
    MetricDataPoint,
    MetricTimeSeries,
    FairnessTrendDataPoint,
    FairnessTrendReport,
    VersionMetricComparison,
    VersionComparison,
    AssignmentChange,
    WhatIfMetricImpact,
    WhatIfViolation,
    WhatIfResult,
    ResidentWorkloadData,
    RotationCoverageData,
    ComplianceData,
    ResearchDataExport,
)


# ===========================================================================
# MetricValue Tests
# ===========================================================================


class TestMetricValue:
    def _valid_kwargs(self):
        return {"name": "fairness", "value": 0.95, "status": "good"}

    def test_valid_minimal(self):
        r = MetricValue(**self._valid_kwargs())
        assert r.unit is None
        assert r.trend is None
        assert r.benchmark is None
        assert r.description is None
        assert r.details is None

    def test_full(self):
        r = MetricValue(
            name="coverage",
            value=98.5,
            unit="%",
            status="good",
            trend="up",
            benchmark=95.0,
            description="Overall coverage rate",
            details={"blocks_covered": 50},
        )
        assert r.trend == "up"

    # --- name min_length=1, max_length=100 ---

    def test_name_empty(self):
        with pytest.raises(ValidationError):
            MetricValue(name="", value=0.0, status="good")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            MetricValue(name="x" * 101, value=0.0, status="good")

    # --- status max_length=20 ---

    def test_status_too_long(self):
        with pytest.raises(ValidationError):
            MetricValue(name="test", value=0.0, status="x" * 21)

    # --- unit max_length=50 ---

    def test_unit_too_long(self):
        with pytest.raises(ValidationError):
            MetricValue(name="test", value=0.0, status="good", unit="x" * 51)

    # --- trend max_length=20 ---

    def test_trend_too_long(self):
        with pytest.raises(ValidationError):
            MetricValue(name="test", value=0.0, status="good", trend="x" * 21)

    # --- description max_length=500 ---

    def test_description_too_long(self):
        with pytest.raises(ValidationError):
            MetricValue(name="test", value=0.0, status="good", description="x" * 501)

    def test_description_max_length(self):
        r = MetricValue(name="test", value=0.0, status="good", description="x" * 500)
        assert len(r.description) == 500


# ===========================================================================
# ScheduleVersionMetrics Tests
# ===========================================================================


class TestScheduleVersionMetrics:
    def _make_metric(self, name="metric", value=0.9, status="good"):
        return MetricValue(name=name, value=value, status=status)

    def test_valid_with_aliases(self):
        r = ScheduleVersionMetrics(
            versionId="v1",
            timestamp="2026-03-01T00:00:00Z",
            period={"start_date": "2026-03-01", "end_date": "2026-03-31"},
            fairnessIndex=self._make_metric("fairness"),
            coverageRate=self._make_metric("coverage"),
            acgmeCompliance=self._make_metric("compliance"),
            preferenceSatisfaction=self._make_metric("preferences"),
            totalBlocks=10,
            totalAssignments=50,
            uniqueResidents=20,
            violations={"hard": 0, "soft": 2},
            workloadDistribution={"avg": 5.0},
        )
        assert r.version_id == "v1"
        assert r.total_blocks == 10

    def test_valid_with_python_names(self):
        r = ScheduleVersionMetrics(
            version_id="v1",
            timestamp="2026-03-01T00:00:00Z",
            period={"start_date": "2026-03-01", "end_date": "2026-03-31"},
            fairness_index=self._make_metric("fairness"),
            coverage_rate=self._make_metric("coverage"),
            acgme_compliance=self._make_metric("compliance"),
            preference_satisfaction=self._make_metric("preferences"),
            total_blocks=10,
            total_assignments=50,
            unique_residents=20,
            violations={},
            workload_distribution={},
        )
        assert r.version_id == "v1"

    def test_optional_schedule_run_id(self):
        r = ScheduleVersionMetrics(
            version_id="v1",
            schedule_run_id=uuid4(),
            timestamp="2026-03-01T00:00:00Z",
            period={},
            fairness_index=self._make_metric(),
            coverage_rate=self._make_metric(),
            acgme_compliance=self._make_metric(),
            preference_satisfaction=self._make_metric(),
            total_blocks=0,
            total_assignments=0,
            unique_residents=0,
            violations={},
            workload_distribution={},
        )
        assert r.schedule_run_id is not None


# ===========================================================================
# MetricTimeSeries Tests
# ===========================================================================


class TestMetricTimeSeries:
    def test_valid(self):
        dp = MetricDataPoint(timestamp="2026-03-01", value=0.95)
        r = MetricTimeSeries(
            metric_name="fairness",
            start_date="2026-03-01",
            end_date="2026-03-31",
            data_points=[dp],
            statistics={"mean": 0.95, "min": 0.9, "max": 1.0},
            trend_direction="stable",
        )
        assert len(r.data_points) == 1

    def test_alias_construction(self):
        r = MetricTimeSeries(
            metricName="coverage",
            startDate="2026-01-01",
            endDate="2026-03-31",
            dataPoints=[],
            statistics={},
            trendDirection="improving",
        )
        assert r.metric_name == "coverage"


# ===========================================================================
# FairnessTrendDataPoint Tests
# ===========================================================================


class TestFairnessTrendDataPoint:
    def test_valid(self):
        r = FairnessTrendDataPoint(
            date="2026-03-01",
            fairness_index=0.85,
            gini_coefficient=0.12,
            residents_count=20,
        )
        assert r.fairness_index == 0.85

    def test_alias_construction(self):
        r = FairnessTrendDataPoint(
            date="2026-03-01",
            fairnessIndex=0.9,
            giniCoefficient=0.1,
            residentsCount=25,
        )
        assert r.gini_coefficient == 0.1


# ===========================================================================
# FairnessTrendReport Tests
# ===========================================================================


class TestFairnessTrendReport:
    def test_valid(self):
        r = FairnessTrendReport(
            period_months=3,
            start_date="2026-01-01",
            end_date="2026-03-31",
            data_points=[],
            average_fairness=0.88,
            trend="improving",
            recommendations=["Increase elective diversity"],
        )
        assert r.most_unfair_period is None
        assert r.most_fair_period is None

    def test_with_optional_periods(self):
        r = FairnessTrendReport(
            period_months=6,
            start_date="2025-07-01",
            end_date="2026-01-01",
            data_points=[],
            average_fairness=0.75,
            trend="declining",
            most_unfair_period="2025-11",
            most_fair_period="2025-07",
            recommendations=[],
        )
        assert r.most_unfair_period == "2025-11"


# ===========================================================================
# VersionMetricComparison Tests
# ===========================================================================


class TestVersionMetricComparison:
    def test_valid(self):
        r = VersionMetricComparison(
            metric_name="fairness",
            version_a_value=0.8,
            version_b_value=0.9,
            difference=0.1,
            percent_change=12.5,
            improvement=True,
        )
        assert r.improvement is True


# ===========================================================================
# VersionComparison Tests
# ===========================================================================


class TestVersionComparison:
    def test_valid(self):
        r = VersionComparison(
            version_a="v1",
            version_b="v2",
            timestamp="2026-03-01T00:00:00Z",
            metrics=[],
            overall_improvement=True,
            improvement_score=85.0,
            assignments_changed=5,
            residents_affected=3,
            summary="Version B is better overall",
            recommendations=["Apply version B"],
        )
        assert r.assignments_changed == 5

    # --- summary max_length=1000 ---

    def test_summary_too_long(self):
        with pytest.raises(ValidationError):
            VersionComparison(
                version_a="v1",
                version_b="v2",
                timestamp="2026-03-01T00:00:00Z",
                metrics=[],
                overall_improvement=True,
                improvement_score=0.0,
                assignments_changed=0,
                residents_affected=0,
                summary="x" * 1001,
                recommendations=[],
            )


# ===========================================================================
# AssignmentChange Tests
# ===========================================================================


class TestAssignmentChange:
    def test_valid(self):
        r = AssignmentChange(
            person_id=uuid4(),
            block_id=uuid4(),
            change_type="add",
        )
        assert r.assignment_id is None
        assert r.rotation_template_id is None


# ===========================================================================
# WhatIfMetricImpact Tests
# ===========================================================================


class TestWhatIfMetricImpact:
    def test_valid(self):
        r = WhatIfMetricImpact(
            metric_name="fairness",
            current_value=0.8,
            predicted_value=0.85,
            change=0.05,
            impact_severity="positive",
            confidence=0.9,
        )
        assert r.confidence == 0.9


# ===========================================================================
# WhatIfViolation Tests
# ===========================================================================


class TestWhatIfViolation:
    def test_valid(self):
        r = WhatIfViolation(
            type="acgme_80_hour",
            severity="critical",
            message="Would exceed 80-hour limit",
        )
        assert r.person_id is None
        assert r.person_name is None


# ===========================================================================
# WhatIfResult Tests
# ===========================================================================


class TestWhatIfResult:
    def test_valid(self):
        r = WhatIfResult(
            timestamp="2026-03-01T00:00:00Z",
            changes_analyzed=3,
            metric_impacts=[],
            new_violations=[],
            resolved_violations=[],
            overall_impact="positive",
            recommendation="Safe to apply",
            safe_to_apply=True,
            affected_residents=[],
            workload_changes={},
        )
        assert r.safe_to_apply is True


# ===========================================================================
# ResidentWorkloadData Tests
# ===========================================================================


class TestResidentWorkloadData:
    def test_valid(self):
        r = ResidentWorkloadData(
            resident_id="R001",
            pgy_level=2,
            total_blocks=12,
            target_blocks=13,
            utilization_percent=92.3,
            clinical_blocks=10,
            non_clinical_blocks=2,
            max_consecutive_days=6,
            average_rest_days=1.5,
        )
        assert r.utilization_percent == 92.3

    def test_alias_construction(self):
        r = ResidentWorkloadData(
            residentId="R001",
            pgyLevel=3,
            totalBlocks=13,
            targetBlocks=13,
            utilizationPercent=100.0,
            clinicalBlocks=11,
            nonClinicalBlocks=2,
            maxConsecutiveDays=5,
            averageRestDays=2.0,
        )
        assert r.pgy_level == 3


# ===========================================================================
# RotationCoverageData Tests
# ===========================================================================


class TestRotationCoverageData:
    def test_valid(self):
        r = RotationCoverageData(
            rotation_id="ROT001",
            rotation_type="clinical",
            total_assignments=25,
            unique_residents=15,
            average_duration=4.0,
        )
        assert r.rotation_type == "clinical"


# ===========================================================================
# ComplianceData Tests
# ===========================================================================


class TestComplianceData:
    def test_valid(self):
        r = ComplianceData(
            total_checks=100,
            total_violations=2,
            compliance_rate=0.98,
            violations_by_type={"80_hour": 1, "rest_period": 1},
            violations_by_severity={"critical": 0, "warning": 2},
            override_count=1,
        )
        assert r.compliance_rate == 0.98


# ===========================================================================
# ResearchDataExport Tests
# ===========================================================================


class TestResearchDataExport:
    def _make_compliance(self):
        return ComplianceData(
            total_checks=100,
            total_violations=0,
            compliance_rate=1.0,
            violations_by_type={},
            violations_by_severity={},
            override_count=0,
        )

    def _valid_kwargs(self):
        return {
            "export_id": "exp-001",
            "timestamp": "2026-03-01T00:00:00Z",
            "anonymized": True,
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
            "total_residents": 20,
            "total_blocks": 13,
            "total_assignments": 100,
            "total_rotations": 10,
            "resident_workload": [],
            "rotation_coverage": [],
            "compliance_data": self._make_compliance(),
            "fairness_metrics": {"gini": 0.12},
            "coverage_metrics": {"rate": 0.98},
        }

    def test_valid(self):
        r = ResearchDataExport(**self._valid_kwargs())
        assert r.institution_type is None
        assert r.program_size is None
        assert r.speciality is None
        assert r.notes is None

    # --- institution_type max_length=100 ---

    def test_institution_type_too_long(self):
        kw = self._valid_kwargs()
        kw["institution_type"] = "x" * 101
        with pytest.raises(ValidationError):
            ResearchDataExport(**kw)

    # --- program_size max_length=50 ---

    def test_program_size_too_long(self):
        kw = self._valid_kwargs()
        kw["program_size"] = "x" * 51
        with pytest.raises(ValidationError):
            ResearchDataExport(**kw)

    # --- speciality max_length=100 ---

    def test_speciality_too_long(self):
        kw = self._valid_kwargs()
        kw["speciality"] = "x" * 101
        with pytest.raises(ValidationError):
            ResearchDataExport(**kw)

    # --- notes max_length=2000 ---

    def test_notes_too_long(self):
        kw = self._valid_kwargs()
        kw["notes"] = "x" * 2001
        with pytest.raises(ValidationError):
            ResearchDataExport(**kw)

    def test_notes_max_length(self):
        kw = self._valid_kwargs()
        kw["notes"] = "x" * 2000
        r = ResearchDataExport(**kw)
        assert len(r.notes) == 2000

    def test_with_all_optional_fields(self):
        kw = self._valid_kwargs()
        kw["institution_type"] = "Military MTF"
        kw["program_size"] = "Medium"
        kw["speciality"] = "Family Medicine"
        kw["notes"] = "Quarterly export"
        r = ResearchDataExport(**kw)
        assert r.institution_type == "Military MTF"
