"""Comprehensive tests for analytics API routes.

Tests all analytics endpoints including metrics, trends, comparisons,
what-if analysis, and research exports with various scenarios.
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.schedule_run import ScheduleRun

# ============================================================================
# Authentication Tests
# ============================================================================


class TestAnalyticsAuthentication:
    """Tests for analytics API authentication requirements."""

    def test_current_metrics_requires_authentication(self, client: TestClient):
        """Test that GET /api/analytics/metrics/current requires authentication."""
        response = client.get("/api/analytics/metrics/current")
        assert response.status_code == 401

    def test_metrics_history_requires_authentication(self, client: TestClient):
        """Test that GET /api/analytics/metrics/history requires authentication."""
        response = client.get(
            "/api/analytics/metrics/history",
            params={
                "metric_name": "fairness",
                "start_date": datetime.utcnow().isoformat(),
                "end_date": datetime.utcnow().isoformat(),
            },
        )
        assert response.status_code == 401

    def test_fairness_trend_requires_authentication(self, client: TestClient):
        """Test that GET /api/analytics/fairness/trend requires authentication."""
        response = client.get("/api/analytics/fairness/trend")
        assert response.status_code == 401

    def test_compare_versions_requires_authentication(self, client: TestClient):
        """Test that GET /api/analytics/compare/{version_a}/{version_b} requires authentication."""
        response = client.get(f"/api/analytics/compare/{uuid4()}/{uuid4()}")
        assert response.status_code == 401

    def test_what_if_requires_authentication(self, client: TestClient):
        """Test that POST /api/analytics/what-if requires authentication."""
        response = client.post(
            "/api/analytics/what-if",
            json=[
                {"personId": str(uuid4()), "blockId": str(uuid4()), "changeType": "add"}
            ],
        )
        assert response.status_code == 401

    def test_research_export_requires_authentication(self, client: TestClient):
        """Test that GET /api/analytics/export/research requires authentication."""
        response = client.get(
            "/api/analytics/export/research",
            params={
                "start_date": datetime.utcnow().isoformat(),
                "end_date": datetime.utcnow().isoformat(),
            },
        )
        assert response.status_code == 401


# ============================================================================
# Current Metrics Endpoint Tests
# ============================================================================


class TestCurrentMetricsEndpoint:
    """Tests for GET /api/analytics/metrics/current endpoint."""

    def test_get_current_metrics_no_schedules(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test getting current metrics when no schedule runs exist."""
        response = client.get("/api/analytics/metrics/current", headers=auth_headers)

        assert response.status_code == 404
        assert "no successful schedule runs" in response.json()["detail"].lower()

    def test_get_current_metrics_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test getting current metrics with a successful schedule run."""
        # Create a schedule run
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        schedule_run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=end_date,
            algorithm="cp_sat",
            status="success",
            total_blocks_assigned=14,
            acgme_violations=0,
            acgme_override_count=0,
            runtime_seconds=5.5,
            created_at=datetime.utcnow(),
        )
        db.add(schedule_run)

        # Create blocks and assignments
        blocks = []
        for i in range(7):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                    is_weekend=(start_date + timedelta(days=i)).weekday() >= 5,
                )
                db.add(block)
                blocks.append(block)

        db.commit()

        # Create some residents and assignments
        for i in range(3):
            resident = Person(
                id=uuid4(),
                name=f"Dr. Test Resident {i}",
                type="resident",
                pgy_level=i + 1,
                target_clinical_blocks=48,
            )
            db.add(resident)
            db.commit()

            # Assign to some blocks
            for j, block in enumerate(blocks[:5]):
                if j % 3 == i:
                    assignment = Assignment(
                        id=uuid4(),
                        block_id=block.id,
                        person_id=resident.id,
                        role="primary",
                    )
                    db.add(assignment)

        db.commit()

        response = client.get("/api/analytics/metrics/current", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "versionId" in data
        assert "scheduleRunId" in data
        assert "timestamp" in data
        assert "period" in data
        assert "fairnessIndex" in data
        assert "coverageRate" in data
        assert "acgmeCompliance" in data
        assert "preferenceSatisfaction" in data
        assert "totalBlocks" in data
        assert "totalAssignments" in data
        assert "uniqueResidents" in data
        assert "violations" in data
        assert "workloadDistribution" in data

        # Verify metric structure
        fairness = data["fairnessIndex"]
        assert "name" in fairness
        assert "value" in fairness
        assert "status" in fairness

        # Verify violations structure
        violations = data["violations"]
        assert "total" in violations
        assert "overrides_acknowledged" in violations
        assert "unacknowledged" in violations

    def test_get_current_metrics_only_uses_successful_runs(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that only successful runs are considered."""
        start_date = date.today()

        # Create a failed run (should be ignored)
        failed_run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="greedy",
            status="failed",
            created_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(failed_run)
        db.commit()

        response = client.get("/api/analytics/metrics/current", headers=auth_headers)

        # Should still return 404 since no successful runs
        assert response.status_code == 404

    def test_get_current_metrics_uses_most_recent(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that the most recent successful run is used."""
        start_date = date.today()

        # Create older successful run
        old_run = ScheduleRun(
            id=uuid4(),
            start_date=start_date - timedelta(days=14),
            end_date=start_date - timedelta(days=7),
            algorithm="greedy",
            status="success",
            created_at=datetime.utcnow() - timedelta(days=7),
        )
        db.add(old_run)

        # Create newer successful run
        new_run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow(),
        )
        db.add(new_run)

        # Create blocks for the new run
        for i in range(7):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)

        db.commit()

        response = client.get("/api/analytics/metrics/current", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Verify it's using the newer run
        assert data["scheduleRunId"] == str(new_run.id)


# ============================================================================
# Metrics History Endpoint Tests
# ============================================================================


class TestMetricsHistoryEndpoint:
    """Tests for GET /api/analytics/metrics/history endpoint."""

    def test_get_metrics_history_no_runs(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test metrics history when no runs exist in date range."""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()

        response = client.get(
            "/api/analytics/metrics/history",
            params={
                "metric_name": "fairness",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_metrics_history_fairness(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test getting fairness metric history."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        # Create a schedule run
        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=end_date,
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow(),
        )
        db.add(run)

        # Create blocks and assignments
        for i in range(7):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)

        db.commit()

        response = client.get(
            "/api/analytics/metrics/history",
            params={
                "metric_name": "fairness",
                "start_date": datetime.combine(
                    start_date, datetime.min.time()
                ).isoformat(),
                "end_date": datetime.combine(end_date, datetime.min.time()).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data) == 1
        time_series = data[0]

        assert time_series["metricName"] == "fairness"
        assert "startDate" in time_series
        assert "endDate" in time_series
        assert "dataPoints" in time_series
        assert "statistics" in time_series
        assert "trendDirection" in time_series

        # Verify statistics structure
        stats = time_series["statistics"]
        assert "mean" in stats
        assert "median" in stats
        assert "std_dev" in stats
        assert "min" in stats
        assert "max" in stats

    def test_get_metrics_history_coverage(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test getting coverage metric history."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=end_date,
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow(),
        )
        db.add(run)

        for i in range(7):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)

        db.commit()

        response = client.get(
            "/api/analytics/metrics/history",
            params={
                "metric_name": "coverage",
                "start_date": datetime.combine(
                    start_date, datetime.min.time()
                ).isoformat(),
                "end_date": datetime.combine(end_date, datetime.min.time()).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["metricName"] == "coverage"

    def test_get_metrics_history_compliance(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test getting compliance metric history."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=end_date,
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow(),
        )
        db.add(run)

        for i in range(7):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)

        db.commit()

        response = client.get(
            "/api/analytics/metrics/history",
            params={
                "metric_name": "compliance",
                "start_date": datetime.combine(
                    start_date, datetime.min.time()
                ).isoformat(),
                "end_date": datetime.combine(end_date, datetime.min.time()).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["metricName"] == "compliance"

    def test_get_metrics_history_violations(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test getting violations metric history."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=end_date,
            algorithm="cp_sat",
            status="success",
            acgme_violations=5,
            created_at=datetime.utcnow(),
        )
        db.add(run)

        for i in range(7):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)

        db.commit()

        response = client.get(
            "/api/analytics/metrics/history",
            params={
                "metric_name": "violations",
                "start_date": datetime.combine(
                    start_date, datetime.min.time()
                ).isoformat(),
                "end_date": datetime.combine(end_date, datetime.min.time()).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["metricName"] == "violations"

    def test_get_metrics_history_unknown_metric(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test getting history for unknown metric returns empty."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=end_date,
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow(),
        )
        db.add(run)

        for i in range(7):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)

        db.commit()

        response = client.get(
            "/api/analytics/metrics/history",
            params={
                "metric_name": "unknown_metric",
                "start_date": datetime.combine(
                    start_date, datetime.min.time()
                ).isoformat(),
                "end_date": datetime.combine(end_date, datetime.min.time()).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_metrics_history_trend_calculation(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that trend direction is calculated correctly."""
        start_date = date.today()

        # Create multiple runs with varying fairness
        for i in range(4):
            run_start = start_date + timedelta(days=i * 7)
            run_end = run_start + timedelta(days=6)

            run = ScheduleRun(
                id=uuid4(),
                start_date=run_start,
                end_date=run_end,
                algorithm="cp_sat",
                status="success",
                created_at=datetime.utcnow() + timedelta(days=i),
            )
            db.add(run)

            for j in range(7):
                for tod in ["AM", "PM"]:
                    block = Block(
                        id=uuid4(),
                        date=run_start + timedelta(days=j),
                        time_of_day=tod,
                        block_number=1,
                    )
                    db.add(block)

        db.commit()

        response = client.get(
            "/api/analytics/metrics/history",
            params={
                "metric_name": "fairness",
                "start_date": datetime.combine(
                    start_date, datetime.min.time()
                ).isoformat(),
                "end_date": datetime.combine(
                    start_date + timedelta(days=28), datetime.min.time()
                ).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["trendDirection"] in ["improving", "declining", "stable"]

    def test_get_metrics_history_rejects_large_range(
        self, client: TestClient, auth_headers: dict
    ):
        """Reject overly large date ranges to prevent DoS."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=366)

        response = client.get(
            "/api/analytics/metrics/history",
            params={
                "metric_name": "fairness",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "date range too large" in response.json()["detail"].lower()

    def test_get_metrics_history_rejects_reversed_range(
        self, client: TestClient, auth_headers: dict
    ):
        """Reject ranges where end_date precedes start_date."""
        start_date = datetime.utcnow()
        end_date = start_date - timedelta(days=1)

        response = client.get(
            "/api/analytics/metrics/history",
            params={
                "metric_name": "fairness",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "end_date" in response.json()["detail"].lower()


# ============================================================================
# Fairness Trend Endpoint Tests
# ============================================================================


class TestFairnessTrendEndpoint:
    """Tests for GET /api/analytics/fairness/trend endpoint."""

    def test_get_fairness_trend_no_runs(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test fairness trend when no runs exist."""
        response = client.get(
            "/api/analytics/fairness/trend",
            params={"months": 6},
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "no schedule runs found" in response.json()["detail"].lower()

    def test_get_fairness_trend_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test getting fairness trend successfully."""
        start_date = date.today() - timedelta(days=30)

        # Create some schedule runs
        for i in range(3):
            run_start = start_date + timedelta(days=i * 10)
            run_end = run_start + timedelta(days=7)

            run = ScheduleRun(
                id=uuid4(),
                start_date=run_start,
                end_date=run_end,
                algorithm="cp_sat",
                status="success",
                created_at=datetime.utcnow() - timedelta(days=30 - i * 10),
            )
            db.add(run)

            # Create blocks for the run
            for j in range(7):
                for tod in ["AM", "PM"]:
                    block = Block(
                        id=uuid4(),
                        date=run_start + timedelta(days=j),
                        time_of_day=tod,
                        block_number=1,
                    )
                    db.add(block)

        db.commit()

        response = client.get(
            "/api/analytics/fairness/trend",
            params={"months": 2},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "periodMonths" in data
        assert "startDate" in data
        assert "endDate" in data
        assert "dataPoints" in data
        assert "averageFairness" in data
        assert "trend" in data
        assert "mostUnfairPeriod" in data
        assert "mostFairPeriod" in data
        assert "recommendations" in data

        assert data["periodMonths"] == 2
        assert isinstance(data["dataPoints"], list)
        assert len(data["dataPoints"]) > 0
        assert data["trend"] in ["improving", "declining", "stable"]
        assert isinstance(data["recommendations"], list)

        # Verify data point structure
        for dp in data["dataPoints"]:
            assert "date" in dp
            assert "fairnessIndex" in dp
            assert "giniCoefficient" in dp
            assert "residentsCount" in dp

    def test_get_fairness_trend_different_months(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test fairness trend with different month parameters."""
        start_date = date.today() - timedelta(days=90)

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow() - timedelta(days=90),
        )
        db.add(run)

        for i in range(7):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)

        db.commit()

        # Test with 3 months
        response = client.get(
            "/api/analytics/fairness/trend",
            params={"months": 3},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["periodMonths"] == 3

    def test_get_fairness_trend_min_months(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test fairness trend with minimum months value."""
        start_date = date.today() - timedelta(days=15)

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow() - timedelta(days=15),
        )
        db.add(run)

        for i in range(7):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)

        db.commit()

        response = client.get(
            "/api/analytics/fairness/trend",
            params={"months": 1},
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_get_fairness_trend_max_months(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test fairness trend with maximum months value."""
        start_date = date.today() - timedelta(days=365)

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow() - timedelta(days=365),
        )
        db.add(run)

        for i in range(7):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)

        db.commit()

        response = client.get(
            "/api/analytics/fairness/trend",
            params={"months": 24},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["periodMonths"] == 24

    def test_get_fairness_trend_invalid_months_low(
        self, client: TestClient, auth_headers: dict
    ):
        """Test fairness trend with months below minimum."""
        response = client.get(
            "/api/analytics/fairness/trend",
            params={"months": 0},
            headers=auth_headers,
        )

        # Should fail validation
        assert response.status_code == 422

    def test_get_fairness_trend_invalid_months_high(
        self, client: TestClient, auth_headers: dict
    ):
        """Test fairness trend with months above maximum."""
        response = client.get(
            "/api/analytics/fairness/trend",
            params={"months": 25},
            headers=auth_headers,
        )

        # Should fail validation
        assert response.status_code == 422

    def test_get_fairness_trend_recommendations(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that fairness trend generates recommendations."""
        start_date = date.today() - timedelta(days=30)

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow() - timedelta(days=30),
        )
        db.add(run)

        for i in range(7):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)

        db.commit()

        response = client.get(
            "/api/analytics/fairness/trend",
            params={"months": 2},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have recommendations
        assert len(data["recommendations"]) > 0


# ============================================================================
# Version Comparison Endpoint Tests
# ============================================================================


class TestVersionComparisonEndpoint:
    """Tests for GET /api/analytics/compare/{version_a}/{version_b} endpoint."""

    def test_compare_versions_not_found(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test comparing versions when one or both don't exist."""
        version_a = str(uuid4())
        version_b = str(uuid4())

        response = client.get(
            f"/api/analytics/compare/{version_a}/{version_b}",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_compare_versions_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test successful version comparison."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        # Create two schedule runs
        run_a = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=end_date,
            algorithm="greedy",
            status="success",
            acgme_violations=5,
            created_at=datetime.utcnow() - timedelta(hours=2),
        )
        run_b = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=end_date,
            algorithm="cp_sat",
            status="success",
            acgme_violations=2,
            created_at=datetime.utcnow(),
        )
        db.add(run_a)
        db.add(run_b)

        # Create blocks for both runs
        for i in range(7):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)

        db.commit()

        response = client.get(
            f"/api/analytics/compare/{run_a.id}/{run_b.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "versionA" in data
        assert "versionB" in data
        assert "timestamp" in data
        assert "metrics" in data
        assert "overallImprovement" in data
        assert "improvementScore" in data
        assert "assignmentsChanged" in data
        assert "residentsAffected" in data
        assert "summary" in data
        assert "recommendations" in data

        assert data["versionA"] == str(run_a.id)
        assert data["versionB"] == str(run_b.id)
        assert isinstance(data["metrics"], list)
        assert len(data["metrics"]) > 0

        # Verify metric comparison structure
        for metric in data["metrics"]:
            assert "metricName" in metric
            assert "versionAValue" in metric
            assert "versionBValue" in metric
            assert "difference" in metric
            assert "percentChange" in metric
            assert "improvement" in metric

    def test_compare_versions_only_version_a_missing(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test comparison when only version A is missing."""
        start_date = date.today()

        run_b = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="cp_sat",
            status="success",
        )
        db.add(run_b)
        db.commit()

        fake_version_a = str(uuid4())

        response = client.get(
            f"/api/analytics/compare/{fake_version_a}/{run_b.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_compare_versions_only_version_b_missing(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test comparison when only version B is missing."""
        start_date = date.today()

        run_a = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="greedy",
            status="success",
        )
        db.add(run_a)
        db.commit()

        fake_version_b = str(uuid4())

        response = client.get(
            f"/api/analytics/compare/{run_a.id}/{fake_version_b}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_compare_versions_improvement_detection(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that improvements are correctly detected."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        # Version A - worse metrics
        run_a = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=end_date,
            algorithm="greedy",
            status="success",
            acgme_violations=10,
            created_at=datetime.utcnow() - timedelta(hours=2),
        )

        # Version B - better metrics
        run_b = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=end_date,
            algorithm="cp_sat",
            status="success",
            acgme_violations=2,
            created_at=datetime.utcnow(),
        )
        db.add(run_a)
        db.add(run_b)

        # Create blocks
        for i in range(7):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)

        db.commit()

        response = client.get(
            f"/api/analytics/compare/{run_a.id}/{run_b.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Find violations metric
        violations_metric = next(
            (m for m in data["metrics"] if "violations" in m["metricName"].lower()),
            None,
        )
        if violations_metric:
            # Violations should have improved (decreased)
            assert violations_metric["improvement"] == True


# ============================================================================
# What-If Analysis Endpoint Tests
# ============================================================================


class TestWhatIfAnalysisEndpoint:
    """Tests for POST /api/analytics/what-if endpoint."""

    def test_what_if_no_changes(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test what-if analysis with no changes provided."""
        response = client.post(
            "/api/analytics/what-if",
            json=[],
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "no changes" in response.json()["detail"].lower()

    def test_what_if_no_baseline(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test what-if analysis when no baseline schedule exists."""
        person_id = str(uuid4())
        block_id = str(uuid4())

        response = client.post(
            "/api/analytics/what-if",
            json=[
                {
                    "personId": person_id,
                    "blockId": block_id,
                    "changeType": "add",
                }
            ],
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "no baseline schedule" in response.json()["detail"].lower()

    def test_what_if_add_assignment(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test what-if analysis for adding an assignment."""
        start_date = date.today()

        # Create baseline schedule
        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow(),
        )
        db.add(run)

        # Create blocks
        blocks = []
        for i in range(7):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)
                blocks.append(block)

        # Create a resident
        resident = Person(
            id=uuid4(),
            name="Dr. Test Resident",
            type="resident",
            pgy_level=2,
            target_clinical_blocks=48,
        )
        db.add(resident)

        db.commit()

        response = client.post(
            "/api/analytics/what-if",
            json=[
                {
                    "personId": str(resident.id),
                    "blockId": str(blocks[0].id),
                    "changeType": "add",
                }
            ],
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "timestamp" in data
        assert "changesAnalyzed" in data
        assert "metricImpacts" in data
        assert "newViolations" in data
        assert "resolvedViolations" in data
        assert "overallImpact" in data
        assert "recommendation" in data
        assert "safeToApply" in data
        assert "affectedResidents" in data
        assert "workloadChanges" in data

        assert data["changesAnalyzed"] == 1
        assert resident.name in data["affectedResidents"]

    def test_what_if_remove_assignment(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test what-if analysis for removing an assignment."""
        start_date = date.today()

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow(),
        )
        db.add(run)

        block = Block(
            id=uuid4(),
            date=start_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

        resident = Person(
            id=uuid4(),
            name="Dr. Test Resident",
            type="resident",
            pgy_level=2,
            target_clinical_blocks=48,
        )
        db.add(resident)

        # Create existing assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=resident.id,
            role="primary",
        )
        db.add(assignment)

        db.commit()

        response = client.post(
            "/api/analytics/what-if",
            json=[
                {
                    "personId": str(resident.id),
                    "blockId": str(block.id),
                    "changeType": "remove",
                }
            ],
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["changesAnalyzed"] == 1

    def test_what_if_multiple_changes(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test what-if analysis with multiple changes."""
        start_date = date.today()

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow(),
        )
        db.add(run)

        blocks = []
        for i in range(3):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)

        residents = []
        for i in range(2):
            resident = Person(
                id=uuid4(),
                name=f"Dr. Test Resident {i}",
                type="resident",
                pgy_level=i + 1,
                target_clinical_blocks=48,
            )
            db.add(resident)
            residents.append(resident)

        db.commit()

        changes = [
            {
                "personId": str(residents[0].id),
                "blockId": str(blocks[0].id),
                "changeType": "add",
            },
            {
                "personId": str(residents[1].id),
                "blockId": str(blocks[1].id),
                "changeType": "add",
            },
        ]

        response = client.post(
            "/api/analytics/what-if",
            json=changes,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["changesAnalyzed"] == 2
        assert len(data["affectedResidents"]) == 2

    def test_what_if_workload_violation(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test what-if detects workload violations."""
        start_date = date.today()

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow(),
        )
        db.add(run)

        blocks = []
        for i in range(60):  # Many blocks
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
            blocks.append(block)

        resident = Person(
            id=uuid4(),
            name="Dr. Overworked Resident",
            type="resident",
            pgy_level=2,
            target_clinical_blocks=48,  # Target is much lower than blocks
        )
        db.add(resident)

        # Create many existing assignments (will exceed target)
        for block in blocks[:55]:
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=resident.id,
                role="primary",
            )
            db.add(assignment)

        db.commit()

        # Try to add more (should trigger violation)
        response = client.post(
            "/api/analytics/what-if",
            json=[
                {
                    "personId": str(resident.id),
                    "blockId": str(blocks[55].id),
                    "changeType": "add",
                }
            ],
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have new violations
        assert len(data["newViolations"]) > 0
        assert data["safeToApply"] == False

    def test_what_if_metric_impacts(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that what-if returns metric impact predictions."""
        start_date = date.today()

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow(),
        )
        db.add(run)

        block = Block(
            id=uuid4(),
            date=start_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

        resident = Person(
            id=uuid4(),
            name="Dr. Test Resident",
            type="resident",
            pgy_level=2,
            target_clinical_blocks=48,
        )
        db.add(resident)

        db.commit()

        response = client.post(
            "/api/analytics/what-if",
            json=[
                {
                    "personId": str(resident.id),
                    "blockId": str(block.id),
                    "changeType": "add",
                }
            ],
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have metric impacts
        assert len(data["metricImpacts"]) > 0

        for impact in data["metricImpacts"]:
            assert "metricName" in impact
            assert "currentValue" in impact
            assert "predictedValue" in impact
            assert "change" in impact
            assert "impactSeverity" in impact
            assert "confidence" in impact


# ============================================================================
# Research Export Endpoint Tests
# ============================================================================


class TestResearchExportEndpoint:
    """Tests for GET /api/analytics/export/research endpoint."""

    def test_research_export_rejects_large_range(
        self, client: TestClient, auth_headers: dict
    ):
        """Reject overly large date ranges to prevent DoS."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=366)

        response = client.get(
            "/api/analytics/export/research",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "anonymize": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "date range too large" in response.json()["detail"].lower()

    def test_research_export_rejects_reversed_range(
        self, client: TestClient, auth_headers: dict
    ):
        """Reject ranges where end_date precedes start_date."""
        start_date = datetime.utcnow()
        end_date = start_date - timedelta(days=1)

        response = client.get(
            "/api/analytics/export/research",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "anonymize": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "end_date" in response.json()["detail"].lower()

    def test_research_export_success(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test successful research data export."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        # Create blocks
        for i in range(7):
            for tod in ["AM", "PM"]:
                block = Block(
                    id=uuid4(),
                    date=start_date + timedelta(days=i),
                    time_of_day=tod,
                    block_number=1,
                )
                db.add(block)

        # Create residents and assignments
        for i in range(3):
            resident = Person(
                id=uuid4(),
                name=f"Dr. Resident {i}",
                type="resident",
                pgy_level=i + 1,
                target_clinical_blocks=48,
            )
            db.add(resident)

        db.commit()

        response = client.get(
            "/api/analytics/export/research",
            params={
                "start_date": datetime.combine(
                    start_date, datetime.min.time()
                ).isoformat(),
                "end_date": datetime.combine(end_date, datetime.min.time()).isoformat(),
                "anonymize": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "exportId" in data
        assert "timestamp" in data
        assert "anonymized" in data
        assert "startDate" in data
        assert "endDate" in data
        assert "totalResidents" in data
        assert "totalBlocks" in data
        assert "totalAssignments" in data
        assert "totalRotations" in data
        assert "residentWorkload" in data
        assert "rotationCoverage" in data
        assert "complianceData" in data
        assert "fairnessMetrics" in data
        assert "coverageMetrics" in data

        assert data["anonymized"] == True

    def test_research_export_non_anonymized(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test research export without anonymization."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        # Create blocks
        for i in range(7):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)

        db.commit()

        response = client.get(
            "/api/analytics/export/research",
            params={
                "start_date": datetime.combine(
                    start_date, datetime.min.time()
                ).isoformat(),
                "end_date": datetime.combine(end_date, datetime.min.time()).isoformat(),
                "anonymize": False,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["anonymized"] == False
        # Should include institution details when not anonymized
        assert data.get("institutionType") is not None
        assert data.get("speciality") is not None

    def test_research_export_resident_workload_structure(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test resident workload data structure in export."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        block = Block(
            id=uuid4(),
            date=start_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

        resident = Person(
            id=uuid4(),
            name="Dr. Test Resident",
            type="resident",
            pgy_level=2,
            target_clinical_blocks=48,
        )
        db.add(resident)

        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=resident.id,
            role="primary",
        )
        db.add(assignment)

        db.commit()

        response = client.get(
            "/api/analytics/export/research",
            params={
                "start_date": datetime.combine(
                    start_date, datetime.min.time()
                ).isoformat(),
                "end_date": datetime.combine(end_date, datetime.min.time()).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        workload = data["residentWorkload"]
        assert len(workload) > 0

        for resident_data in workload:
            assert "residentId" in resident_data
            assert "pgyLevel" in resident_data
            assert "totalBlocks" in resident_data
            assert "targetBlocks" in resident_data
            assert "utilizationPercent" in resident_data
            assert "clinicalBlocks" in resident_data
            assert "nonClinicalBlocks" in resident_data
            assert "maxConsecutiveDays" in resident_data
            assert "averageRestDays" in resident_data

    def test_research_export_compliance_data_structure(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test compliance data structure in export."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=end_date,
            algorithm="cp_sat",
            status="success",
            acgme_violations=3,
            acgme_override_count=1,
        )
        db.add(run)

        for i in range(7):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)

        db.commit()

        response = client.get(
            "/api/analytics/export/research",
            params={
                "start_date": datetime.combine(
                    start_date, datetime.min.time()
                ).isoformat(),
                "end_date": datetime.combine(end_date, datetime.min.time()).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        compliance = data["complianceData"]
        assert "totalChecks" in compliance
        assert "totalViolations" in compliance
        assert "complianceRate" in compliance
        assert "violationsByType" in compliance
        assert "violationsBySeverity" in compliance
        assert "overrideCount" in compliance

    def test_research_export_fairness_metrics(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test fairness metrics in export."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        block = Block(
            id=uuid4(),
            date=start_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

        db.commit()

        response = client.get(
            "/api/analytics/export/research",
            params={
                "start_date": datetime.combine(
                    start_date, datetime.min.time()
                ).isoformat(),
                "end_date": datetime.combine(end_date, datetime.min.time()).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        fairness = data["fairnessMetrics"]
        assert "fairness_index" in fairness
        assert "gini_coefficient" in fairness

    def test_research_export_coverage_metrics(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test coverage metrics in export."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        block = Block(
            id=uuid4(),
            date=start_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

        db.commit()

        response = client.get(
            "/api/analytics/export/research",
            params={
                "start_date": datetime.combine(
                    start_date, datetime.min.time()
                ).isoformat(),
                "end_date": datetime.combine(end_date, datetime.min.time()).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        coverage = data["coverageMetrics"]
        assert "coverage_rate" in coverage
        assert "total_blocks" in coverage
        assert "covered_blocks" in coverage
        assert "uncovered_blocks" in coverage

    def test_research_export_anonymization(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that anonymization properly obscures IDs."""
        start_date = date.today()
        end_date = start_date + timedelta(days=7)

        block = Block(
            id=uuid4(),
            date=start_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

        resident = Person(
            id=uuid4(),
            name="Dr. Test Resident",
            type="resident",
            pgy_level=2,
            target_clinical_blocks=48,
        )
        db.add(resident)

        assignment = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=resident.id,
            role="primary",
        )
        db.add(assignment)

        db.commit()

        original_resident_id = str(resident.id)

        response = client.get(
            "/api/analytics/export/research",
            params={
                "start_date": datetime.combine(
                    start_date, datetime.min.time()
                ).isoformat(),
                "end_date": datetime.combine(end_date, datetime.min.time()).isoformat(),
                "anonymize": True,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Anonymized IDs should not match original IDs
        if data["residentWorkload"]:
            anonymized_id = data["residentWorkload"][0]["residentId"]
            assert anonymized_id != original_resident_id
            # Anonymized ID should be shorter (16 chars)
            assert len(anonymized_id) == 16

    def test_research_export_empty_date_range(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test research export with date range containing no data."""
        start_date = date.today() + timedelta(days=365)
        end_date = start_date + timedelta(days=7)

        response = client.get(
            "/api/analytics/export/research",
            params={
                "start_date": datetime.combine(
                    start_date, datetime.min.time()
                ).isoformat(),
                "end_date": datetime.combine(end_date, datetime.min.time()).isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should still return valid structure with zeros
        assert data["totalResidents"] == 0
        assert data["totalBlocks"] == 0
        assert data["totalAssignments"] == 0


# ============================================================================
# Error Handling and Edge Cases
# ============================================================================


class TestAnalyticsErrorHandling:
    """Tests for error handling and edge cases."""

    def test_metrics_history_missing_required_params(
        self, client: TestClient, auth_headers: dict
    ):
        """Test metrics history without required parameters."""
        response = client.get(
            "/api/analytics/metrics/history",
            headers=auth_headers,
        )

        # Should fail validation
        assert response.status_code == 422

    def test_research_export_missing_required_params(
        self, client: TestClient, auth_headers: dict
    ):
        """Test research export without required parameters."""
        response = client.get(
            "/api/analytics/export/research",
            headers=auth_headers,
        )

        # Should fail validation
        assert response.status_code == 422

    def test_what_if_invalid_change_type(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test what-if with invalid change type."""
        start_date = date.today()

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="cp_sat",
            status="success",
            created_at=datetime.utcnow(),
        )
        db.add(run)

        block = Block(
            id=uuid4(),
            date=start_date,
            time_of_day="AM",
            block_number=1,
        )
        db.add(block)

        resident = Person(
            id=uuid4(),
            name="Dr. Test",
            type="resident",
            pgy_level=2,
        )
        db.add(resident)

        db.commit()

        # Try with invalid change type
        response = client.post(
            "/api/analytics/what-if",
            json=[
                {
                    "personId": str(resident.id),
                    "blockId": str(block.id),
                    "changeType": "invalid_type",
                }
            ],
            headers=auth_headers,
        )

        # Should still process but may not calculate correctly
        # The endpoint doesn't strictly validate change_type in schema
        assert response.status_code in [200, 422]

    def test_compare_versions_with_same_version(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test comparing a version with itself."""
        start_date = date.today()

        run = ScheduleRun(
            id=uuid4(),
            start_date=start_date,
            end_date=start_date + timedelta(days=7),
            algorithm="cp_sat",
            status="success",
        )
        db.add(run)

        for i in range(7):
            block = Block(
                id=uuid4(),
                date=start_date + timedelta(days=i),
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)

        db.commit()

        response = client.get(
            f"/api/analytics/compare/{run.id}/{run.id}",
            headers=auth_headers,
        )

        # Should work, but all differences should be 0
        assert response.status_code == 200
        data = response.json()

        for metric in data["metrics"]:
            assert metric["difference"] == 0
            assert metric["percentChange"] == 0
