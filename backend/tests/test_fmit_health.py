"""
Tests for FMIT Health Check API routes.

Comprehensive test coverage for the FMIT health monitoring endpoints including:
- Health check endpoint
- Detailed status endpoint
- Metrics endpoint
- Coverage report endpoint
- Coverage gaps endpoint
- Coverage suggestions endpoint
- Coverage forecast endpoint
- Alert summary endpoint
"""
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.conflict_alert import (
    ConflictAlert,
    ConflictAlertStatus,
    ConflictSeverity,
    ConflictType,
)
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord, SwapStatus, SwapType


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_fmit_blocks(db: Session) -> list[Block]:
    """Create FMIT blocks for the next 30 days."""
    blocks = []
    start_date = date.today()

    for i in range(30):
        current_date = start_date + timedelta(days=i)
        block = Block(
            id=uuid4(),
            date=current_date,
            time_of_day="AM",
            block_number=1,
            service_type="FMIT",
            is_weekend=(current_date.weekday() >= 5),
            is_holiday=False,
        )
        db.add(block)
        blocks.append(block)

    db.commit()
    for block in blocks:
        db.refresh(block)
    return blocks


@pytest.fixture
def sample_fmit_rotation_template(db: Session) -> RotationTemplate:
    """Create a sample FMIT rotation template."""
    template = RotationTemplate(
        id=uuid4(),
        name="FMIT Coverage",
        activity_type="fmit",
        abbreviation="FMIT",
        max_residents=1,
        supervision_required=False,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture
def sample_fmit_faculty(db: Session) -> list[Person]:
    """Create multiple faculty members for FMIT coverage."""
    faculty = []
    for i in range(5):
        person = Person(
            id=uuid4(),
            name=f"Dr. FMIT Faculty {i}",
            first_name=f"FMIT{i}",
            last_name=f"Faculty{i}",
            type="faculty",
            role="faculty",
            email=f"fmit.faculty{i}@hospital.org",
        )
        db.add(person)
        faculty.append(person)

    db.commit()
    for f in faculty:
        db.refresh(f)
    return faculty


@pytest.fixture
def sample_fmit_assignments(
    db: Session,
    sample_fmit_blocks: list[Block],
    sample_fmit_faculty: list[Person],
    sample_fmit_rotation_template: RotationTemplate,
) -> list[Assignment]:
    """Create FMIT assignments covering most (but not all) blocks."""
    assignments = []

    # Cover 80% of blocks (leaving some gaps)
    covered_blocks = sample_fmit_blocks[:24]

    for i, block in enumerate(covered_blocks):
        faculty = sample_fmit_faculty[i % len(sample_fmit_faculty)]
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=faculty.id,
            rotation_template_id=sample_fmit_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        assignments.append(assignment)

    db.commit()
    for a in assignments:
        db.refresh(a)
    return assignments


@pytest.fixture
def sample_swap_records(
    db: Session,
    sample_fmit_faculty: list[Person],
    admin_user,
) -> list[SwapRecord]:
    """Create sample swap records with various statuses."""
    swaps = []
    today = date.today()
    month_start = today.replace(day=1)

    # Create swaps with different statuses
    statuses = [
        SwapStatus.PENDING,
        SwapStatus.PENDING,
        SwapStatus.APPROVED,
        SwapStatus.EXECUTED,
        SwapStatus.REJECTED,
        SwapStatus.CANCELLED,
        SwapStatus.ROLLED_BACK,
    ]

    for i, status in enumerate(statuses):
        source_faculty = sample_fmit_faculty[i % len(sample_fmit_faculty)]
        target_faculty = sample_fmit_faculty[(i + 1) % len(sample_fmit_faculty)]

        swap = SwapRecord(
            id=uuid4(),
            source_faculty_id=source_faculty.id,
            source_week=month_start + timedelta(days=i * 7),
            target_faculty_id=target_faculty.id,
            target_week=month_start + timedelta(days=(i + 1) * 7) if i % 2 == 0 else None,
            swap_type=SwapType.ONE_TO_ONE if i % 2 == 0 else SwapType.ABSORB,
            status=status,
            requested_at=datetime.utcnow() - timedelta(days=i),
            requested_by_id=admin_user.id,
            reason="Test swap reason",
        )

        # Set additional timestamps for executed swaps
        if status == SwapStatus.EXECUTED:
            swap.executed_at = swap.requested_at + timedelta(hours=24)
            swap.executed_by_id = admin_user.id
        elif status == SwapStatus.APPROVED:
            swap.approved_at = swap.requested_at + timedelta(hours=12)
            swap.approved_by_id = admin_user.id

        db.add(swap)
        swaps.append(swap)

    db.commit()
    for s in swaps:
        db.refresh(s)
    return swaps


@pytest.fixture
def sample_conflict_alerts(
    db: Session,
    sample_fmit_faculty: list[Person],
    admin_user,
) -> list[ConflictAlert]:
    """Create sample conflict alerts with various statuses and severities."""
    alerts = []
    today = date.today()

    # Create alerts with different combinations
    alert_configs = [
        (ConflictSeverity.CRITICAL, ConflictAlertStatus.NEW, ConflictType.LEAVE_FMIT_OVERLAP),
        (ConflictSeverity.CRITICAL, ConflictAlertStatus.ACKNOWLEDGED, ConflictType.CALL_CASCADE),
        (ConflictSeverity.WARNING, ConflictAlertStatus.NEW, ConflictType.BACK_TO_BACK),
        (ConflictSeverity.WARNING, ConflictAlertStatus.ACKNOWLEDGED, ConflictType.EXCESSIVE_ALTERNATING),
        (ConflictSeverity.INFO, ConflictAlertStatus.NEW, ConflictType.EXTERNAL_COMMITMENT),
        (ConflictSeverity.INFO, ConflictAlertStatus.RESOLVED, ConflictType.BACK_TO_BACK),
    ]

    for i, (severity, status, conflict_type) in enumerate(alert_configs):
        faculty = sample_fmit_faculty[i % len(sample_fmit_faculty)]

        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=faculty.id,
            conflict_type=conflict_type,
            severity=severity,
            fmit_week=today + timedelta(days=i * 7),
            status=status,
            description=f"Test {severity.value} {conflict_type.value} alert",
            created_at=datetime.utcnow() - timedelta(days=i * 2),
        )

        # Set additional timestamps for acknowledged/resolved alerts
        if status == ConflictAlertStatus.ACKNOWLEDGED:
            alert.acknowledged_at = alert.created_at + timedelta(hours=2)
            alert.acknowledged_by_id = admin_user.id
        elif status == ConflictAlertStatus.RESOLVED:
            alert.acknowledged_at = alert.created_at + timedelta(hours=2)
            alert.acknowledged_by_id = admin_user.id
            alert.resolved_at = alert.created_at + timedelta(hours=24)
            alert.resolved_by_id = admin_user.id
            alert.resolution_notes = "Test resolution"

        db.add(alert)
        alerts.append(alert)

    db.commit()
    for a in alerts:
        db.refresh(a)
    return alerts


# ============================================================================
# Test Classes
# ============================================================================


class TestFMITHealthEndpoint:
    """Tests for GET /api/fmit/health endpoint."""

    def test_health_check_basic(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test basic health check without any data."""
        response = client.get("/api/fmit/health", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "timestamp" in data
        assert "status" in data
        assert "total_swaps_this_month" in data
        assert "pending_swap_requests" in data
        assert "active_conflict_alerts" in data
        assert "coverage_percentage" in data
        assert "issues" in data
        assert "recommendations" in data

        # With no data, status should be healthy
        assert data["status"] == "healthy"
        assert data["total_swaps_this_month"] == 0
        assert data["pending_swap_requests"] == 0
        assert data["active_conflict_alerts"] == 0

    def test_health_check_with_data(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
        sample_swap_records: list[SwapRecord],
        sample_conflict_alerts: list[ConflictAlert],
    ):
        """Test health check with existing swap and alert data."""
        response = client.get("/api/fmit/health", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should have some swaps and alerts
        assert data["total_swaps_this_month"] > 0
        assert data["pending_swap_requests"] == 2  # Two pending swaps in fixture
        assert data["active_conflict_alerts"] > 0

        # Coverage should be around 80% (24 out of 30 blocks covered)
        assert 70 < data["coverage_percentage"] < 90

    def test_health_check_degraded_status(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_blocks: list[Block],
        sample_conflict_alerts: list[ConflictAlert],
    ):
        """Test health check returns degraded status with issues."""
        response = client.get("/api/fmit/health", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # With uncovered blocks and critical alerts, status might be degraded
        assert data["status"] in ["healthy", "degraded", "critical"]

        # Should have some issues and recommendations
        assert isinstance(data["issues"], list)
        assert isinstance(data["recommendations"], list)

    def test_health_check_unauthorized(self, client: TestClient):
        """Test health check requires authentication."""
        response = client.get("/api/fmit/health")

        assert response.status_code == 401


class TestFMITStatusEndpoint:
    """Tests for GET /api/fmit/status endpoint."""

    def test_detailed_status_basic(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test detailed status without any data."""
        response = client.get("/api/fmit/status", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "timestamp" in data
        assert "pending_swaps" in data
        assert "approved_swaps" in data
        assert "executed_swaps" in data
        assert "rejected_swaps" in data
        assert "cancelled_swaps" in data
        assert "rolled_back_swaps" in data
        assert "active_alerts" in data
        assert "new_alerts" in data
        assert "acknowledged_alerts" in data
        assert "resolved_alerts" in data
        assert "critical_alerts" in data
        assert "warning_alerts" in data
        assert "info_alerts" in data
        assert "recent_swap_activity" in data
        assert "recent_alerts" in data

        # All counts should be zero with no data
        assert data["pending_swaps"] == 0
        assert data["active_alerts"] == 0

    def test_detailed_status_with_swaps(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_swap_records: list[SwapRecord],
    ):
        """Test detailed status with swap records."""
        response = client.get("/api/fmit/status", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify swap counts match fixture
        assert data["pending_swaps"] == 2
        assert data["approved_swaps"] == 1
        assert data["executed_swaps"] == 1
        assert data["rejected_swaps"] == 1
        assert data["cancelled_swaps"] == 1
        assert data["rolled_back_swaps"] == 1

        # Verify recent swap activity
        assert len(data["recent_swap_activity"]) > 0
        assert len(data["recent_swap_activity"]) <= 10

        # Check swap activity structure
        activity = data["recent_swap_activity"][0]
        assert "id" in activity
        assert "status" in activity
        assert "swap_type" in activity
        assert "requested_at" in activity

    def test_detailed_status_with_alerts(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_conflict_alerts: list[ConflictAlert],
    ):
        """Test detailed status with conflict alerts."""
        response = client.get("/api/fmit/status", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify alert counts
        assert data["critical_alerts"] == 2  # Two critical alerts in fixture
        assert data["warning_alerts"] == 2
        assert data["info_alerts"] == 1  # One info alert is still active
        assert data["new_alerts"] == 3
        assert data["acknowledged_alerts"] == 2
        assert data["resolved_alerts"] == 1

        # Verify recent alerts
        assert len(data["recent_alerts"]) > 0
        assert len(data["recent_alerts"]) <= 10

        # Check alert structure
        alert = data["recent_alerts"][0]
        assert "id" in alert
        assert "severity" in alert
        assert "status" in alert
        assert "conflict_type" in alert
        assert "created_at" in alert

    def test_detailed_status_unauthorized(self, client: TestClient):
        """Test status endpoint requires authentication."""
        response = client.get("/api/fmit/status")

        assert response.status_code == 401


class TestFMITMetricsEndpoint:
    """Tests for GET /api/fmit/metrics endpoint."""

    def test_metrics_basic(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test metrics without any data."""
        response = client.get("/api/fmit/metrics", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "timestamp" in data
        assert "total_swaps_this_month" in data
        assert "pending_swap_requests" in data
        assert "active_conflict_alerts" in data
        assert "coverage_percentage" in data
        assert "swap_approval_rate" in data
        assert "average_swap_processing_time_hours" in data
        assert "alert_resolution_rate" in data
        assert "critical_alerts_count" in data
        assert "one_to_one_swaps_count" in data
        assert "absorb_swaps_count" in data

        # Default values with no data
        assert data["total_swaps_this_month"] == 0
        assert data["swap_approval_rate"] == 0.0
        assert data["average_swap_processing_time_hours"] is None

    def test_metrics_with_data(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
        sample_swap_records: list[SwapRecord],
        sample_conflict_alerts: list[ConflictAlert],
    ):
        """Test metrics with complete data."""
        response = client.get("/api/fmit/metrics", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify swap metrics
        assert data["total_swaps_this_month"] > 0
        assert data["pending_swap_requests"] == 2

        # Verify swap type breakdown
        assert data["one_to_one_swaps_count"] > 0
        assert data["absorb_swaps_count"] > 0

        # Verify coverage percentage
        assert 0 <= data["coverage_percentage"] <= 100

        # Verify approval rate
        assert 0 <= data["swap_approval_rate"] <= 100

        # Verify processing time (should be set for executed swaps)
        assert data["average_swap_processing_time_hours"] is not None
        assert data["average_swap_processing_time_hours"] > 0

        # Verify alert metrics
        assert data["critical_alerts_count"] == 2
        assert 0 <= data["alert_resolution_rate"] <= 100

    def test_metrics_swap_approval_rate(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_swap_records: list[SwapRecord],
    ):
        """Test swap approval rate calculation."""
        response = client.get("/api/fmit/metrics", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # With 1 approved + 1 executed = 2 approved
        # Out of (1 approved + 1 executed + 1 rejected) = 3 completed
        # Approval rate = 2/3 = 66.67%
        assert 60 < data["swap_approval_rate"] < 70

    def test_metrics_unauthorized(self, client: TestClient):
        """Test metrics endpoint requires authentication."""
        response = client.get("/api/fmit/metrics")

        assert response.status_code == 401


class TestFMITCoverageEndpoint:
    """Tests for GET /api/fmit/coverage endpoint."""

    def test_coverage_report_default(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
    ):
        """Test coverage report with default parameters."""
        response = client.get("/api/fmit/coverage", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "start_date" in data
        assert "end_date" in data
        assert "total_weeks" in data
        assert "overall_coverage_percentage" in data
        assert "weeks" in data

        # Should have weekly data
        assert data["total_weeks"] > 0
        assert len(data["weeks"]) > 0

        # Check week structure
        week = data["weeks"][0]
        assert "week_start" in week
        assert "total_fmit_slots" in week
        assert "covered_slots" in week
        assert "uncovered_slots" in week
        assert "coverage_percentage" in week
        assert "faculty_assigned" in week

        # Coverage percentage should be between 0 and 100
        assert 0 <= data["overall_coverage_percentage"] <= 100

    def test_coverage_report_custom_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
    ):
        """Test coverage report with custom date range."""
        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        response = client.get(
            "/api/fmit/coverage",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify date range
        assert data["start_date"] == start_date.isoformat()
        assert data["end_date"] == end_date.isoformat()

        # Should have 2-3 weeks of data
        assert 2 <= data["total_weeks"] <= 3

    def test_coverage_report_daily_period(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
    ):
        """Test coverage report with daily grouping."""
        response = client.get(
            "/api/fmit/coverage",
            params={"period": "daily"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # With daily grouping, should have more periods
        assert data["total_weeks"] >= 30  # One per day for 30-day default range

    def test_coverage_report_monthly_period(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
    ):
        """Test coverage report with monthly grouping."""
        response = client.get(
            "/api/fmit/coverage",
            params={"period": "monthly"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # With monthly grouping, should have fewer periods
        assert data["total_weeks"] <= 2  # At most 2 months for 30-day range

    def test_coverage_report_faculty_assigned(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
    ):
        """Test coverage report includes faculty names."""
        response = client.get("/api/fmit/coverage", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # At least one week should have faculty assigned
        weeks_with_faculty = [w for w in data["weeks"] if len(w["faculty_assigned"]) > 0]
        assert len(weeks_with_faculty) > 0

        # Faculty names should be sorted
        for week in weeks_with_faculty:
            faculty_list = week["faculty_assigned"]
            assert faculty_list == sorted(faculty_list)

    def test_coverage_report_unauthorized(self, client: TestClient):
        """Test coverage endpoint requires authentication."""
        response = client.get("/api/fmit/coverage")

        assert response.status_code == 401


class TestFMITCoverageGapsEndpoint:
    """Tests for GET /api/fmit/coverage/gaps endpoint."""

    def test_coverage_gaps_basic(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_blocks: list[Block],
    ):
        """Test coverage gaps detection with no assignments."""
        response = client.get("/api/fmit/coverage/gaps", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "timestamp" in data
        assert "total_gaps" in data
        assert "critical_gaps" in data
        assert "high_priority_gaps" in data
        assert "medium_priority_gaps" in data
        assert "low_priority_gaps" in data
        assert "gaps_by_period" in data
        assert "gaps" in data

        # Should detect gaps (since no assignments)
        assert data["total_gaps"] > 0

        # Check gap structure
        if len(data["gaps"]) > 0:
            gap = data["gaps"][0]
            assert "gap_id" in gap
            assert "date" in gap
            assert "time_of_day" in gap
            assert "block_id" in gap
            assert "severity" in gap
            assert "days_until" in gap
            assert "affected_area" in gap
            assert "current_assignments" in gap
            assert "required_assignments" in gap
            assert "gap_size" in gap

    def test_coverage_gaps_with_assignments(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
    ):
        """Test coverage gaps with partial coverage."""
        response = client.get("/api/fmit/coverage/gaps", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should have some gaps (since only 80% covered)
        assert data["total_gaps"] > 0

        # Total should equal sum of severity categories
        total_by_severity = (
            data["critical_gaps"] +
            data["high_priority_gaps"] +
            data["medium_priority_gaps"] +
            data["low_priority_gaps"]
        )
        assert data["total_gaps"] == total_by_severity

        # Verify gaps_by_period structure
        assert "daily" in data["gaps_by_period"]
        assert "weekly" in data["gaps_by_period"]
        assert "monthly" in data["gaps_by_period"]

    def test_coverage_gaps_severity_filter(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
    ):
        """Test coverage gaps with severity filter."""
        response = client.get(
            "/api/fmit/coverage/gaps",
            params={"severity_filter": "critical"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # All returned gaps should be critical
        for gap in data["gaps"]:
            assert gap["severity"] == "critical"

    def test_coverage_gaps_custom_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
    ):
        """Test coverage gaps with custom date range."""
        start_date = date.today() + timedelta(days=30)
        end_date = start_date + timedelta(days=30)

        response = client.get(
            "/api/fmit/coverage/gaps",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all gaps are within date range
        for gap in data["gaps"]:
            gap_date = date.fromisoformat(gap["date"])
            assert start_date <= gap_date <= end_date

    def test_coverage_gaps_unauthorized(self, client: TestClient):
        """Test coverage gaps endpoint requires authentication."""
        response = client.get("/api/fmit/coverage/gaps")

        assert response.status_code == 401


class TestFMITCoverageSuggestionsEndpoint:
    """Tests for GET /api/fmit/coverage/suggestions endpoint."""

    def test_coverage_suggestions_basic(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_blocks: list[Block],
        sample_fmit_faculty: list[Person],
    ):
        """Test coverage suggestions generation."""
        response = client.get("/api/fmit/coverage/suggestions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "timestamp" in data
        assert "total_suggestions" in data
        assert "gaps_addressed" in data
        assert "suggestions" in data

        # Should have suggestions for gaps
        assert data["total_suggestions"] > 0
        assert data["gaps_addressed"] > 0

        # Check suggestion structure
        if len(data["suggestions"]) > 0:
            suggestion = data["suggestions"][0]
            assert "gap_id" in suggestion
            assert "suggestion_type" in suggestion
            assert "priority" in suggestion
            assert "faculty_candidates" in suggestion
            assert "estimated_conflict_score" in suggestion
            assert "reasoning" in suggestion
            assert "alternative_dates" in suggestion

    def test_coverage_suggestions_with_faculty(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_blocks: list[Block],
        sample_fmit_faculty: list[Person],
    ):
        """Test suggestions include faculty candidates."""
        response = client.get("/api/fmit/coverage/suggestions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # At least some suggestions should have faculty candidates
        suggestions_with_faculty = [
            s for s in data["suggestions"]
            if len(s["faculty_candidates"]) > 0
        ]
        assert len(suggestions_with_faculty) > 0

        # Verify conflict scores are in valid range
        for suggestion in data["suggestions"]:
            assert 0 <= suggestion["estimated_conflict_score"] <= 1.0

    def test_coverage_suggestions_max_limit(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_blocks: list[Block],
        sample_fmit_faculty: list[Person],
    ):
        """Test suggestions respect max_suggestions parameter."""
        response = client.get(
            "/api/fmit/coverage/suggestions",
            params={"max_suggestions": 5},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should not exceed max_suggestions
        assert len(data["suggestions"]) <= 5

    def test_coverage_suggestions_custom_date_range(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_blocks: list[Block],
        sample_fmit_faculty: list[Person],
    ):
        """Test suggestions for custom date range."""
        start_date = date.today()
        end_date = start_date + timedelta(days=14)

        response = client.get(
            "/api/fmit/coverage/suggestions",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have suggestions
        assert "suggestions" in data

    def test_coverage_suggestions_unauthorized(self, client: TestClient):
        """Test coverage suggestions endpoint requires authentication."""
        response = client.get("/api/fmit/coverage/suggestions")

        assert response.status_code == 401


class TestFMITCoverageForecastEndpoint:
    """Tests for GET /api/fmit/coverage/forecast endpoint."""

    def test_coverage_forecast_basic(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
    ):
        """Test coverage forecast generation."""
        response = client.get("/api/fmit/coverage/forecast", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "timestamp" in data
        assert "forecast_start_date" in data
        assert "forecast_end_date" in data
        assert "overall_trend" in data
        assert "average_predicted_coverage" in data
        assert "forecasts" in data

        # Default is 12 weeks ahead
        assert len(data["forecasts"]) == 12

        # Verify trend is valid
        assert data["overall_trend"] in ["improving", "stable", "declining"]

        # Check forecast structure
        forecast = data["forecasts"][0]
        assert "forecast_date" in forecast
        assert "predicted_coverage_percentage" in forecast
        assert "predicted_gaps" in forecast
        assert "confidence_level" in forecast
        assert "trend" in forecast
        assert "risk_factors" in forecast

    def test_coverage_forecast_custom_weeks(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
    ):
        """Test coverage forecast with custom weeks ahead."""
        response = client.get(
            "/api/fmit/coverage/forecast",
            params={"weeks_ahead": 4},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have 4 weeks of forecasts
        assert len(data["forecasts"]) == 4

    def test_coverage_forecast_confidence_decreases(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
    ):
        """Test forecast confidence decreases over time."""
        response = client.get(
            "/api/fmit/coverage/forecast",
            params={"weeks_ahead": 12},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Confidence should generally decrease over time
        confidences = [f["confidence_level"] for f in data["forecasts"]]

        # First confidence should be higher than last
        assert confidences[0] > confidences[-1]

        # All confidences should be between 0 and 1
        for confidence in confidences:
            assert 0 <= confidence <= 1.0

    def test_coverage_forecast_predictions_valid(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
    ):
        """Test forecast predictions are in valid ranges."""
        response = client.get("/api/fmit/coverage/forecast", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify all predictions are valid
        for forecast in data["forecasts"]:
            # Coverage percentage should be 0-100
            assert 0 <= forecast["predicted_coverage_percentage"] <= 100

            # Gaps should be non-negative
            assert forecast["predicted_gaps"] >= 0

            # Trend should be valid
            assert forecast["trend"] in ["improving", "stable", "declining"]

            # Risk factors should be a list
            assert isinstance(forecast["risk_factors"], list)

    def test_coverage_forecast_unauthorized(self, client: TestClient):
        """Test coverage forecast endpoint requires authentication."""
        response = client.get("/api/fmit/coverage/forecast")

        assert response.status_code == 401


class TestFMITAlertsSummaryEndpoint:
    """Tests for GET /api/fmit/alerts/summary endpoint."""

    def test_alerts_summary_basic(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test alerts summary without any data."""
        response = client.get("/api/fmit/alerts/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "timestamp" in data
        assert "critical_count" in data
        assert "warning_count" in data
        assert "info_count" in data
        assert "total_count" in data
        assert "by_type" in data
        assert "by_status" in data
        assert "oldest_unresolved" in data
        assert "average_resolution_time_hours" in data

        # With no data, all counts should be zero
        assert data["critical_count"] == 0
        assert data["warning_count"] == 0
        assert data["info_count"] == 0
        assert data["total_count"] == 0
        assert data["oldest_unresolved"] is None
        assert data["average_resolution_time_hours"] is None

    def test_alerts_summary_with_data(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_conflict_alerts: list[ConflictAlert],
    ):
        """Test alerts summary with conflict alert data."""
        response = client.get("/api/fmit/alerts/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify alert counts by severity (active only)
        assert data["critical_count"] == 2
        assert data["warning_count"] == 2
        assert data["info_count"] == 1  # Only unresolved info alerts

        # Total should equal sum of severities
        assert data["total_count"] == data["critical_count"] + data["warning_count"] + data["info_count"]

    def test_alerts_summary_by_type(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_conflict_alerts: list[ConflictAlert],
    ):
        """Test alerts summary includes counts by type."""
        response = client.get("/api/fmit/alerts/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should have by_type dictionary
        assert isinstance(data["by_type"], dict)

        # All conflict types should be represented
        for conflict_type in ConflictType:
            assert conflict_type.value in data["by_type"]

    def test_alerts_summary_by_status(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_conflict_alerts: list[ConflictAlert],
    ):
        """Test alerts summary includes counts by status."""
        response = client.get("/api/fmit/alerts/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should have by_status dictionary
        assert isinstance(data["by_status"], dict)

        # All alert statuses should be represented
        for status in ConflictAlertStatus:
            assert status.value in data["by_status"]

        # Verify status counts
        assert data["by_status"]["new"] == 3
        assert data["by_status"]["acknowledged"] == 2
        assert data["by_status"]["resolved"] == 1

    def test_alerts_summary_oldest_unresolved(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_conflict_alerts: list[ConflictAlert],
    ):
        """Test alerts summary includes oldest unresolved alert."""
        response = client.get("/api/fmit/alerts/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should have oldest unresolved timestamp
        assert data["oldest_unresolved"] is not None

        # Should be a valid ISO format datetime
        oldest_dt = datetime.fromisoformat(data["oldest_unresolved"].replace("Z", "+00:00"))
        assert isinstance(oldest_dt, datetime)

    def test_alerts_summary_resolution_time(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_conflict_alerts: list[ConflictAlert],
    ):
        """Test alerts summary includes average resolution time."""
        response = client.get("/api/fmit/alerts/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should have average resolution time (we have one resolved alert)
        assert data["average_resolution_time_hours"] is not None
        assert data["average_resolution_time_hours"] > 0

    def test_alerts_summary_unauthorized(self, client: TestClient):
        """Test alerts summary endpoint requires authentication."""
        response = client.get("/api/fmit/alerts/summary")

        assert response.status_code == 401


# ============================================================================
# Integration Tests
# ============================================================================


class TestFMITHealthIntegration:
    """Integration tests for FMIT health endpoints."""

    def test_full_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_assignments: list[Assignment],
        sample_swap_records: list[SwapRecord],
        sample_conflict_alerts: list[ConflictAlert],
    ):
        """Test complete workflow accessing all health endpoints."""
        # 1. Check overall health
        health_response = client.get("/api/fmit/health", headers=auth_headers)
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["status"] in ["healthy", "degraded", "critical"]

        # 2. Get detailed status
        status_response = client.get("/api/fmit/status", headers=auth_headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["pending_swaps"] > 0

        # 3. Get metrics
        metrics_response = client.get("/api/fmit/metrics", headers=auth_headers)
        assert metrics_response.status_code == 200
        metrics_data = metrics_response.json()
        assert metrics_data["total_swaps_this_month"] > 0

        # 4. Get coverage report
        coverage_response = client.get("/api/fmit/coverage", headers=auth_headers)
        assert coverage_response.status_code == 200
        coverage_data = coverage_response.json()
        assert len(coverage_data["weeks"]) > 0

        # 5. Get alert summary
        alerts_response = client.get("/api/fmit/alerts/summary", headers=auth_headers)
        assert alerts_response.status_code == 200
        alerts_data = alerts_response.json()
        assert alerts_data["total_count"] > 0

        # Verify consistency across endpoints
        assert health_data["pending_swap_requests"] == status_data["pending_swaps"]
        assert health_data["total_swaps_this_month"] == metrics_data["total_swaps_this_month"]
        assert health_data["active_conflict_alerts"] == alerts_data["total_count"]

    def test_coverage_gaps_and_suggestions_consistency(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_fmit_blocks: list[Block],
        sample_fmit_faculty: list[Person],
    ):
        """Test coverage gaps and suggestions are consistent."""
        # Get gaps
        gaps_response = client.get("/api/fmit/coverage/gaps", headers=auth_headers)
        assert gaps_response.status_code == 200
        gaps_data = gaps_response.json()

        # Get suggestions
        suggestions_response = client.get(
            "/api/fmit/coverage/suggestions",
            headers=auth_headers,
        )
        assert suggestions_response.status_code == 200
        suggestions_data = suggestions_response.json()

        # Should have suggestions for the gaps
        if gaps_data["total_gaps"] > 0:
            assert suggestions_data["total_suggestions"] > 0
            assert suggestions_data["gaps_addressed"] > 0
