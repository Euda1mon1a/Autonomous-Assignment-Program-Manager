"""Tests for compliance analytics."""

import pytest
from datetime import date
from unittest.mock import AsyncMock

from app.analytics.compliance.violation_tracker import ViolationTracker
from app.analytics.compliance.compliance_score import ComplianceScore
from app.analytics.compliance.risk_predictor import RiskPredictor
from app.analytics.compliance.audit_reporter import AuditReporter
from app.analytics.compliance.benchmark import ComplianceBenchmark


@pytest.mark.asyncio
class TestViolationTracker:
    """Test violation tracker."""

    async def test_track_violations(self, async_db_session):
        """Test violation tracking."""
        tracker = ViolationTracker(async_db_session)

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        violations = await tracker.track_violations(start_date, end_date)

        assert isinstance(violations, dict)
        assert "work_hour_violations" in violations
        assert "day_off_violations" in violations
        assert "total_violations" in violations

    def test_check_80_hour_windows(self):
        """Test 80-hour rule checking."""
        from app.models.person import Person

        tracker = ViolationTracker(None)
        person = Person(id="test", name="Test", type="resident")

        # Test with empty assignments
        violations = tracker._check_80_hour_windows([], person)

        assert isinstance(violations, list)
        assert len(violations) == 0


@pytest.mark.asyncio
class TestComplianceScore:
    """Test compliance score calculator."""

    async def test_calculate_score(self, async_db_session):
        """Test compliance score calculation."""
        calculator = ComplianceScore(async_db_session)

        # Mock violation tracker
        calculator.violation_tracker.track_violations = AsyncMock(return_value={
            "total_violations": 5,
            "work_hour_violations": [],
            "day_off_violations": [],
        })

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        score = await calculator.calculate_score(start_date, end_date)

        assert isinstance(score, dict)
        assert "compliance_score" in score
        assert "rating" in score
        assert 0 <= score["compliance_score"] <= 100


@pytest.mark.asyncio
class TestRiskPredictor:
    """Test risk predictor."""

    async def test_predict_risks(self, async_db_session):
        """Test risk prediction."""
        predictor = RiskPredictor(async_db_session)

        start_date = date(2024, 1, 1)

        risks = await predictor.predict_risks(start_date, forecast_days=30)

        assert isinstance(risks, dict)
        assert "high_risk_persons" in risks
        assert "forecast_period" in risks
        assert "risk_level" in risks


@pytest.mark.asyncio
class TestAuditReporter:
    """Test audit reporter."""

    async def test_generate_audit_report(self, async_db_session):
        """Test audit report generation."""
        reporter = AuditReporter(async_db_session)

        # Mock dependencies
        reporter.violation_tracker.track_violations = AsyncMock(return_value={
            "total_violations": 5,
        })
        reporter.compliance_score.calculate_score = AsyncMock(return_value={
            "compliance_score": 95.0,
            "rating": "excellent",
        })

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        report = await reporter.generate_audit_report(start_date, end_date)

        assert isinstance(report, dict)
        assert "audit_period" in report
        assert "compliance_score" in report
        assert "violations" in report
        assert "recommendations" in report


@pytest.mark.asyncio
class TestComplianceBenchmark:
    """Test compliance benchmark."""

    async def test_benchmark_program(self, async_db_session):
        """Test program benchmarking."""
        benchmark = ComplianceBenchmark(async_db_session)

        # Mock compliance score
        benchmark.compliance_score.calculate_score = AsyncMock(return_value={
            "compliance_score": 92.0,
            "rating": "good",
        })

        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 31)

        result = await benchmark.benchmark_program(start_date, end_date)

        assert isinstance(result, dict)
        assert "program_score" in result
        assert "benchmark_category" in result
        assert "estimated_percentile" in result
