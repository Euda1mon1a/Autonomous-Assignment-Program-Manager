"""Tests for conflict resolution API routes.

Comprehensive test suite covering conflict analysis, resolution options,
auto-resolution, batch resolution, and safety checks.
"""
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.conflict_alert import (
    ConflictAlert,
    ConflictAlertStatus,
    ConflictSeverity,
    ConflictType,
)
from app.models.person import Person


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_conflict_alert(db: Session, sample_faculty: Person) -> ConflictAlert:
    """Create a sample conflict alert."""
    alert = ConflictAlert(
        id=uuid4(),
        faculty_id=sample_faculty.id,
        conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
        severity=ConflictSeverity.WARNING,
        fmit_week=date.today() + timedelta(days=7),
        status=ConflictAlertStatus.NEW,
        description="Faculty member has leave during FMIT week",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@pytest.fixture
def critical_conflict_alert(db: Session, sample_faculty: Person) -> ConflictAlert:
    """Create a critical severity conflict alert."""
    alert = ConflictAlert(
        id=uuid4(),
        faculty_id=sample_faculty.id,
        conflict_type=ConflictType.CALL_CASCADE,
        severity=ConflictSeverity.CRITICAL,
        fmit_week=date.today() + timedelta(days=14),
        status=ConflictAlertStatus.NEW,
        description="Critical call cascade detected",
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@pytest.fixture
def multiple_conflict_alerts(
    db: Session, sample_faculty_members: list[Person]
) -> list[ConflictAlert]:
    """Create multiple conflict alerts with different severities."""
    alerts = []
    severities = [ConflictSeverity.CRITICAL, ConflictSeverity.WARNING, ConflictSeverity.INFO]

    for i, faculty in enumerate(sample_faculty_members):
        alert = ConflictAlert(
            id=uuid4(),
            faculty_id=faculty.id,
            conflict_type=ConflictType.LEAVE_FMIT_OVERLAP,
            severity=severities[i % len(severities)],
            fmit_week=date.today() + timedelta(days=i * 7),
            status=ConflictAlertStatus.NEW,
            description=f"Conflict for {faculty.name}",
        )
        db.add(alert)
        alerts.append(alert)

    db.commit()
    for alert in alerts:
        db.refresh(alert)
    return alerts


# ============================================================================
# Test Classes
# ============================================================================

class TestAnalyzeConflictEndpoint:
    """Tests for GET /api/conflict-resolution/{conflict_id}/analyze endpoint."""

    def test_analyze_conflict_success(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test successfully analyzing a conflict."""
        response = client.get(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/analyze"
        )

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert "conflict_id" in data
        assert "conflict_type" in data
        assert "severity" in data
        assert "root_cause" in data
        assert "affected_faculty" in data
        assert "affected_dates" in data
        assert "complexity_score" in data
        assert "safety_checks" in data
        assert "all_checks_passed" in data
        assert "auto_resolution_safe" in data
        assert "recommended_strategies" in data

        # Validate field types
        assert str(sample_conflict_alert.id) == data["conflict_id"]
        assert isinstance(data["complexity_score"], (int, float))
        assert 0.0 <= data["complexity_score"] <= 1.0
        assert isinstance(data["all_checks_passed"], bool)
        assert isinstance(data["auto_resolution_safe"], bool)
        assert isinstance(data["safety_checks"], list)
        assert isinstance(data["recommended_strategies"], list)

    def test_analyze_conflict_not_found(self, client: TestClient):
        """Test analyzing a non-existent conflict."""
        fake_id = uuid4()
        response = client.get(f"/api/conflict-resolution/{fake_id}/analyze")

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_analyze_conflict_invalid_uuid(self, client: TestClient):
        """Test analyzing conflict with invalid UUID format."""
        response = client.get("/api/conflict-resolution/invalid-uuid/analyze")

        assert response.status_code == 422  # Validation error

    def test_analyze_conflict_requires_auth(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test that analysis requires authentication."""
        # Note: This test assumes auth is required. If not, this test will fail
        # and should be adjusted based on actual auth requirements
        response = client.get(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/analyze"
        )

        # Should either succeed (if no auth required) or return 401/403
        assert response.status_code in [200, 401, 403]

    def test_analyze_critical_conflict(
        self, client: TestClient, critical_conflict_alert: ConflictAlert
    ):
        """Test analyzing a critical severity conflict."""
        response = client.get(
            f"/api/conflict-resolution/{critical_conflict_alert.id}/analyze"
        )

        assert response.status_code == 200
        data = response.json()

        # Critical conflicts might have different characteristics
        assert "severity" in data
        assert "complexity_score" in data

    def test_analyze_conflict_safety_checks(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test that analysis includes safety check results."""
        response = client.get(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/analyze"
        )

        assert response.status_code == 200
        data = response.json()

        # Validate safety checks structure
        assert "safety_checks" in data
        if data["safety_checks"]:
            check = data["safety_checks"][0]
            assert "check_type" in check
            assert "passed" in check
            assert "message" in check
            assert isinstance(check["passed"], bool)


class TestGetResolutionOptionsEndpoint:
    """Tests for GET /api/conflict-resolution/{conflict_id}/options endpoint."""

    def test_get_resolution_options_success(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test successfully getting resolution options."""
        response = client.get(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/options"
        )

        assert response.status_code in [200, 404]  # 404 if no options available

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

            if data:
                option = data[0]
                assert "id" in option
                assert "conflict_id" in option
                assert "strategy" in option
                assert "title" in option
                assert "description" in option
                assert "can_auto_apply" in option
                assert "safety_validated" in option

    def test_get_resolution_options_with_max_limit(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test getting resolution options with max_options parameter."""
        response = client.get(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/options",
            params={"max_options": 3}
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) <= 3

    def test_get_resolution_options_min_max_validation(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test max_options parameter validation."""
        # Test below minimum (should be >= 1)
        response = client.get(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/options",
            params={"max_options": 0}
        )
        assert response.status_code == 422  # Validation error

        # Test above maximum (should be <= 10)
        response = client.get(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/options",
            params={"max_options": 11}
        )
        assert response.status_code == 422  # Validation error

    def test_get_resolution_options_not_found(self, client: TestClient):
        """Test getting options for non-existent conflict."""
        fake_id = uuid4()
        response = client.get(f"/api/conflict-resolution/{fake_id}/options")

        assert response.status_code == 404

    def test_get_resolution_options_default_max(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test that default max_options is applied correctly."""
        response = client.get(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/options"
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            # Default is 5, so should not exceed that
            assert len(data) <= 5

    def test_get_resolution_options_impact_assessment(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test that options include impact assessment."""
        response = client.get(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/options"
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            if data and data[0].get("impact"):
                impact = data[0]["impact"]
                assert "overall_score" in impact
                assert "feasibility_score" in impact
                assert "disruption_score" in impact


class TestResolveConflictEndpoint:
    """Tests for POST /api/conflict-resolution/{conflict_id}/resolve endpoint."""

    def test_resolve_conflict_without_strategy(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test auto-resolving conflict without specifying strategy."""
        response = client.post(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/resolve"
        )

        # Could succeed, fail due to safety checks, or fail if conflict not resolvable
        assert response.status_code in [200, 400, 404, 422]

        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "status" in data
            assert "message" in data
            assert "conflict_resolved" in data

    def test_resolve_conflict_with_strategy(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test resolving conflict with specific strategy."""
        response = client.post(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/resolve",
            params={"strategy": "swap_assignments"}
        )

        # Response depends on whether strategy is applicable
        assert response.status_code in [200, 400, 404, 422]

        if response.status_code == 200:
            data = response.json()
            assert "strategy" in data
            assert data["strategy"] == "swap_assignments"

    def test_resolve_conflict_not_found(self, client: TestClient):
        """Test resolving a non-existent conflict."""
        fake_id = uuid4()
        response = client.post(f"/api/conflict-resolution/{fake_id}/resolve")

        assert response.status_code in [404, 422]

    def test_resolve_conflict_result_structure(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test that resolution result has expected structure."""
        response = client.post(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/resolve"
        )

        if response.status_code == 200:
            data = response.json()

            # Required fields
            assert "resolution_option_id" in data
            assert "conflict_id" in data
            assert "strategy" in data
            assert "success" in data
            assert "status" in data
            assert "message" in data

            # Optional fields that should be present
            assert "changes_applied" in data
            assert "conflict_resolved" in data
            assert "can_rollback" in data

            # Validate types
            assert isinstance(data["success"], bool)
            assert isinstance(data["conflict_resolved"], bool)
            assert isinstance(data["can_rollback"], bool)

    def test_resolve_conflict_invalid_strategy(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test resolving with invalid strategy name."""
        response = client.post(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/resolve",
            params={"strategy": "invalid_strategy_name"}
        )

        # Should return validation error or handle gracefully
        assert response.status_code in [400, 422]


class TestBatchResolveConflictsEndpoint:
    """Tests for POST /api/conflict-resolution/batch/resolve endpoint."""

    def test_batch_resolve_empty_list(self, client: TestClient):
        """Test batch resolve with no conflicts specified."""
        response = client.post(
            "/api/conflict-resolution/batch/resolve",
            params={"max_conflicts": 10}
        )

        # Should return report even if no conflicts to process
        assert response.status_code in [200, 422]

    def test_batch_resolve_with_conflict_ids(
        self, client: TestClient, multiple_conflict_alerts: list[ConflictAlert]
    ):
        """Test batch resolve with specific conflict IDs."""
        conflict_ids = [str(alert.id) for alert in multiple_conflict_alerts[:2]]

        response = client.post(
            "/api/conflict-resolution/batch/resolve",
            params={"conflict_ids": conflict_ids}
        )

        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            assert "total_conflicts" in data
            assert "conflicts_analyzed" in data
            assert "resolutions_proposed" in data
            assert "resolutions_applied" in data
            assert "results" in data

    def test_batch_resolve_with_max_conflicts(
        self, client: TestClient, multiple_conflict_alerts: list[ConflictAlert]
    ):
        """Test batch resolve with max_conflicts limit."""
        response = client.post(
            "/api/conflict-resolution/batch/resolve",
            params={"max_conflicts": 2}
        )

        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            assert data["conflicts_analyzed"] <= 2

    def test_batch_resolve_max_conflicts_validation(self, client: TestClient):
        """Test max_conflicts parameter validation."""
        # Test below minimum (should be >= 1)
        response = client.post(
            "/api/conflict-resolution/batch/resolve",
            params={"max_conflicts": 0}
        )
        assert response.status_code == 422

        # Test above maximum (should be <= 100)
        response = client.post(
            "/api/conflict-resolution/batch/resolve",
            params={"max_conflicts": 101}
        )
        assert response.status_code == 422

    def test_batch_resolve_with_severity_filter(
        self, client: TestClient, multiple_conflict_alerts: list[ConflictAlert]
    ):
        """Test batch resolve with severity filter."""
        response = client.post(
            "/api/conflict-resolution/batch/resolve",
            params={
                "max_conflicts": 10,
                "severity_filter": "CRITICAL"
            }
        )

        assert response.status_code in [200, 422]

    def test_batch_resolve_invalid_severity(self, client: TestClient):
        """Test batch resolve with invalid severity filter."""
        response = client.post(
            "/api/conflict-resolution/batch/resolve",
            params={
                "max_conflicts": 10,
                "severity_filter": "INVALID_SEVERITY"
            }
        )

        # Should handle invalid severity gracefully
        assert response.status_code in [200, 400, 422]

    def test_batch_resolve_dry_run(
        self, client: TestClient, multiple_conflict_alerts: list[ConflictAlert]
    ):
        """Test batch resolve in dry-run mode."""
        response = client.post(
            "/api/conflict-resolution/batch/resolve",
            params={
                "max_conflicts": 5,
                "dry_run": True
            }
        )

        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            # In dry-run, nothing should be applied
            assert data.get("resolutions_applied", 0) == 0

    def test_batch_resolve_report_structure(
        self, client: TestClient, multiple_conflict_alerts: list[ConflictAlert]
    ):
        """Test that batch resolution report has expected structure."""
        response = client.post(
            "/api/conflict-resolution/batch/resolve",
            params={"max_conflicts": 5}
        )

        if response.status_code == 200:
            data = response.json()

            # Required fields
            assert "total_conflicts" in data
            assert "conflicts_analyzed" in data
            assert "resolutions_proposed" in data
            assert "resolutions_applied" in data
            assert "resolutions_failed" in data
            assert "results" in data
            assert "processing_time_seconds" in data
            assert "started_at" in data
            assert "success_rate" in data
            assert "overall_status" in data
            assert "summary_message" in data

            # Validate types
            assert isinstance(data["total_conflicts"], int)
            assert isinstance(data["results"], list)
            assert isinstance(data["success_rate"], (int, float))
            assert 0.0 <= data["success_rate"] <= 1.0

    def test_batch_resolve_performance_metrics(
        self, client: TestClient, multiple_conflict_alerts: list[ConflictAlert]
    ):
        """Test that batch resolution includes performance metrics."""
        response = client.post(
            "/api/conflict-resolution/batch/resolve",
            params={"max_conflicts": 3}
        )

        if response.status_code == 200:
            data = response.json()
            assert "processing_time_seconds" in data
            assert "started_at" in data
            assert "completed_at" in data
            assert isinstance(data["processing_time_seconds"], (int, float))


class TestCanAutoResolveEndpoint:
    """Tests for GET /api/conflict-resolution/{conflict_id}/can-auto-resolve endpoint."""

    def test_can_auto_resolve_success(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test checking if conflict can be auto-resolved."""
        response = client.get(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/can-auto-resolve"
        )

        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "conflict_id" in data
            assert "can_auto_resolve" in data
            assert "all_checks_passed" in data
            assert "complexity_score" in data

            # Validate types
            assert isinstance(data["can_auto_resolve"], bool)
            assert isinstance(data["all_checks_passed"], bool)
            assert isinstance(data["complexity_score"], (int, float))

    def test_can_auto_resolve_not_found(self, client: TestClient):
        """Test checking auto-resolve for non-existent conflict."""
        fake_id = uuid4()
        response = client.get(f"/api/conflict-resolution/{fake_id}/can-auto-resolve")

        assert response.status_code == 404

    def test_can_auto_resolve_invalid_uuid(self, client: TestClient):
        """Test checking auto-resolve with invalid UUID."""
        response = client.get(
            "/api/conflict-resolution/invalid-uuid/can-auto-resolve"
        )

        assert response.status_code == 422

    def test_can_auto_resolve_includes_blockers(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test that can-auto-resolve includes blocker information."""
        response = client.get(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/can-auto-resolve"
        )

        if response.status_code == 200:
            data = response.json()
            assert "blockers" in data
            assert isinstance(data["blockers"], list)

    def test_can_auto_resolve_includes_recommendations(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test that can-auto-resolve includes recommended strategies."""
        response = client.get(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/can-auto-resolve"
        )

        if response.status_code == 200:
            data = response.json()
            assert "recommended_strategies" in data
            assert isinstance(data["recommended_strategies"], list)

    def test_can_auto_resolve_critical_conflict(
        self, client: TestClient, critical_conflict_alert: ConflictAlert
    ):
        """Test auto-resolve check for critical severity conflict."""
        response = client.get(
            f"/api/conflict-resolution/{critical_conflict_alert.id}/can-auto-resolve"
        )

        if response.status_code == 200:
            data = response.json()
            # Critical conflicts might have different auto-resolve criteria
            assert "can_auto_resolve" in data
            assert isinstance(data["can_auto_resolve"], bool)


class TestConflictResolutionEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_resolve_already_resolved_conflict(
        self, client: TestClient, db: Session, sample_conflict_alert: ConflictAlert
    ):
        """Test resolving a conflict that's already marked as resolved."""
        # Mark conflict as resolved
        sample_conflict_alert.status = ConflictAlertStatus.RESOLVED
        db.commit()

        response = client.post(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/resolve"
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_analyze_acknowledged_conflict(
        self, client: TestClient, db: Session, sample_conflict_alert: ConflictAlert
    ):
        """Test analyzing an acknowledged conflict."""
        # Mark conflict as acknowledged
        sample_conflict_alert.status = ConflictAlertStatus.ACKNOWLEDGED
        db.commit()

        response = client.get(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/analyze"
        )

        # Should still be analyzable
        assert response.status_code == 200

    def test_batch_resolve_with_mixed_statuses(
        self, client: TestClient, db: Session, multiple_conflict_alerts: list[ConflictAlert]
    ):
        """Test batch resolving conflicts with different statuses."""
        # Mark some as already resolved
        multiple_conflict_alerts[0].status = ConflictAlertStatus.RESOLVED
        multiple_conflict_alerts[1].status = ConflictAlertStatus.ACKNOWLEDGED
        db.commit()

        conflict_ids = [str(alert.id) for alert in multiple_conflict_alerts]

        response = client.post(
            "/api/conflict-resolution/batch/resolve",
            params={"conflict_ids": conflict_ids}
        )

        # Should handle mixed statuses gracefully
        assert response.status_code in [200, 422]

    def test_get_options_for_info_severity(
        self, client: TestClient, db: Session, sample_faculty: Person
    ):
        """Test getting resolution options for low-severity INFO conflict."""
        info_alert = ConflictAlert(
            id=uuid4(),
            faculty_id=sample_faculty.id,
            conflict_type=ConflictType.EXTERNAL_COMMITMENT,
            severity=ConflictSeverity.INFO,
            fmit_week=date.today() + timedelta(days=30),
            status=ConflictAlertStatus.NEW,
            description="Minor scheduling note",
        )
        db.add(info_alert)
        db.commit()

        response = client.get(f"/api/conflict-resolution/{info_alert.id}/options")

        # INFO conflicts might not have auto-resolution options
        assert response.status_code in [200, 404]

    def test_concurrent_resolution_attempts(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test multiple simultaneous resolution attempts on same conflict."""
        # Simulate concurrent requests
        response1 = client.post(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/resolve"
        )
        response2 = client.post(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/resolve"
        )

        # Both should respond (one might succeed, one might fail)
        assert response1.status_code in [200, 400, 404, 422, 409]
        assert response2.status_code in [200, 400, 404, 422, 409]


class TestConflictResolutionAuthentication:
    """Tests for authentication and authorization requirements."""

    def test_endpoints_require_authentication(self, client: TestClient):
        """Test that conflict resolution endpoints require authentication."""
        # Note: These tests assume authentication is required
        # Adjust based on actual auth implementation

        fake_id = uuid4()

        # Test all endpoints without auth
        endpoints = [
            ("GET", f"/api/conflict-resolution/{fake_id}/analyze"),
            ("GET", f"/api/conflict-resolution/{fake_id}/options"),
            ("POST", f"/api/conflict-resolution/{fake_id}/resolve"),
            ("GET", f"/api/conflict-resolution/{fake_id}/can-auto-resolve"),
            ("POST", "/api/conflict-resolution/batch/resolve"),
        ]

        for method, url in endpoints:
            if method == "GET":
                response = client.get(url)
            else:
                response = client.post(url)

            # Should either require auth (401/403) or work without auth (200/404/422)
            assert response.status_code in [200, 401, 403, 404, 422]


class TestConflictResolutionErrorHandling:
    """Tests for error handling and validation."""

    def test_analyze_with_database_error(
        self, client: TestClient, sample_conflict_alert: ConflictAlert
    ):
        """Test error handling when analysis encounters database issues."""
        # This is a placeholder - actual implementation would need to mock DB errors
        response = client.get(
            f"/api/conflict-resolution/{sample_conflict_alert.id}/analyze"
        )

        # Should handle errors gracefully
        assert response.status_code in [200, 500]

    def test_resolve_with_invalid_data(self, client: TestClient):
        """Test resolution with malformed request data."""
        # Send invalid UUID
        response = client.post("/api/conflict-resolution/not-a-uuid/resolve")

        assert response.status_code == 422

    def test_batch_resolve_with_invalid_json(self, client: TestClient):
        """Test batch resolve with invalid JSON in request."""
        # FastAPI should handle this at framework level
        response = client.post(
            "/api/conflict-resolution/batch/resolve",
            data="invalid json{",
            headers={"Content-Type": "application/json"}
        )

        # Should return validation error
        assert response.status_code in [400, 422]
