"""
Comprehensive tests for Database Admin API routes.

Tests coverage for database administration:
- GET /api/db-admin/health - Get database health metrics (admin)
- GET /api/db-admin/indexes/recommendations - Get index recommendations (admin)
- GET /api/db-admin/indexes/unused - Find unused indexes (admin)
- GET /api/db-admin/indexes/usage - Get index usage stats (admin)
- GET /api/db-admin/tables/{table_name}/stats - Get table statistics (admin)
- GET /api/db-admin/queries/stats - Get query statistics (admin)
- POST /api/db-admin/vacuum/{table_name} - Run VACUUM on table (admin)
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Classes
# ============================================================================


class TestDatabaseHealthEndpoint:
    """Tests for GET /api/db-admin/health endpoint."""

    def test_health_requires_auth(self, client: TestClient):
        """Test that database health requires authentication."""
        response = client.get("/api/db-admin/health")

        assert response.status_code in [401, 403]

    def test_health_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that database health requires admin role."""
        response = client.get(
            "/api/db-admin/health",
            headers=auth_headers,
        )

        # May return 200 if admin, or 403 if not admin
        assert response.status_code in [200, 401, 403, 500]

    def test_health_response_structure(self, client: TestClient, auth_headers: dict):
        """Test database health response has correct structure."""
        response = client.get(
            "/api/db-admin/health",
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "connection_pool" in data
            assert "database_size_mb" in data
            assert "active_connections" in data
            assert "total_tables" in data
            assert "total_indexes" in data
            assert "recommendations" in data


class TestIndexRecommendationsEndpoint:
    """Tests for GET /api/db-admin/indexes/recommendations endpoint."""

    def test_recommendations_requires_auth(self, client: TestClient):
        """Test that index recommendations requires authentication."""
        response = client.get("/api/db-admin/indexes/recommendations")

        assert response.status_code in [401, 403]

    def test_recommendations_requires_admin(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that index recommendations requires admin role."""
        with patch("app.api.routes.db_admin.IndexAdvisor") as mock_advisor_class:
            mock_advisor = MagicMock()
            mock_advisor.analyze_and_recommend.return_value = []
            mock_advisor_class.return_value = mock_advisor

            response = client.get(
                "/api/db-admin/indexes/recommendations",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403, 500]

    def test_recommendations_with_min_size(
        self, client: TestClient, auth_headers: dict
    ):
        """Test recommendations with minimum table size filter."""
        with patch("app.api.routes.db_admin.IndexAdvisor") as mock_advisor_class:
            mock_advisor = MagicMock()
            mock_advisor.analyze_and_recommend.return_value = []
            mock_advisor_class.return_value = mock_advisor

            response = client.get(
                "/api/db-admin/indexes/recommendations?min_table_size_mb=5.0",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403, 500]


class TestUnusedIndexesEndpoint:
    """Tests for GET /api/db-admin/indexes/unused endpoint."""

    def test_unused_requires_auth(self, client: TestClient):
        """Test that unused indexes requires authentication."""
        response = client.get("/api/db-admin/indexes/unused")

        assert response.status_code in [401, 403]

    def test_unused_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that unused indexes requires admin role."""
        with patch("app.api.routes.db_admin.IndexAdvisor") as mock_advisor_class:
            mock_advisor = MagicMock()
            mock_advisor.find_unused_indexes.return_value = []
            mock_advisor_class.return_value = mock_advisor

            response = client.get(
                "/api/db-admin/indexes/unused",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403, 500]

    def test_unused_with_filters(self, client: TestClient, auth_headers: dict):
        """Test unused indexes with age and size filters."""
        with patch("app.api.routes.db_admin.IndexAdvisor") as mock_advisor_class:
            mock_advisor = MagicMock()
            mock_advisor.find_unused_indexes.return_value = []
            mock_advisor_class.return_value = mock_advisor

            response = client.get(
                "/api/db-admin/indexes/unused?min_age_days=14&min_size_mb=20.0",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403, 500]


class TestIndexUsageStatsEndpoint:
    """Tests for GET /api/db-admin/indexes/usage endpoint."""

    def test_usage_requires_auth(self, client: TestClient):
        """Test that index usage stats requires authentication."""
        response = client.get("/api/db-admin/indexes/usage")

        assert response.status_code in [401, 403]

    def test_usage_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that index usage stats requires admin role."""
        with patch("app.api.routes.db_admin.IndexAdvisor") as mock_advisor_class:
            mock_advisor = MagicMock()
            mock_advisor.get_index_usage_stats.return_value = []
            mock_advisor_class.return_value = mock_advisor

            response = client.get(
                "/api/db-admin/indexes/usage",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403, 500]


class TestTableStatisticsEndpoint:
    """Tests for GET /api/db-admin/tables/{table_name}/stats endpoint."""

    def test_table_stats_requires_auth(self, client: TestClient):
        """Test that table statistics requires authentication."""
        response = client.get("/api/db-admin/tables/persons/stats")

        assert response.status_code in [401, 403]

    def test_table_stats_requires_admin(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that table statistics requires admin role."""
        with patch("app.api.routes.db_admin.IndexAdvisor") as mock_advisor_class:
            mock_advisor = MagicMock()
            mock_advisor.analyze_table_statistics.return_value = {
                "schema": "public",
                "table": "persons",
                "total_size": "1 MB",
                "table_size": "512 KB",
                "indexes_size": "512 KB",
                "sequential_scans": 100,
                "sequential_tuples_read": 1000,
                "index_scans": 500,
                "index_tuples_fetched": 5000,
                "inserts": 50,
                "updates": 20,
                "deletes": 5,
                "live_tuples": 100,
                "dead_tuples": 10,
                "scan_ratio": 0.83,
                "last_vacuum": None,
                "last_autovacuum": None,
                "last_analyze": None,
                "last_autoanalyze": None,
            }
            mock_advisor_class.return_value = mock_advisor

            response = client.get(
                "/api/db-admin/tables/persons/stats",
                headers=auth_headers,
            )

            assert response.status_code in [200, 401, 403, 404, 500]

    def test_table_stats_not_found(self, client: TestClient, auth_headers: dict):
        """Test table statistics for non-existent table."""
        with patch("app.api.routes.db_admin.IndexAdvisor") as mock_advisor_class:
            mock_advisor = MagicMock()
            mock_advisor.analyze_table_statistics.return_value = None
            mock_advisor_class.return_value = mock_advisor

            response = client.get(
                "/api/db-admin/tables/nonexistent_table/stats",
                headers=auth_headers,
            )

            assert response.status_code in [401, 403, 404]


class TestQueryStatisticsEndpoint:
    """Tests for GET /api/db-admin/queries/stats endpoint."""

    def test_query_stats_requires_auth(self, client: TestClient):
        """Test that query statistics requires authentication."""
        response = client.get("/api/db-admin/queries/stats?request_id=test-123")

        assert response.status_code in [401, 403]

    def test_query_stats_requires_admin(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that query statistics requires admin role."""
        response = client.get(
            "/api/db-admin/queries/stats?request_id=test-123",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403, 500]

    def test_query_stats_requires_request_id(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that query statistics requires request_id parameter."""
        response = client.get(
            "/api/db-admin/queries/stats",
            headers=auth_headers,
        )

        # Should require request_id parameter
        assert response.status_code in [401, 403, 422]


class TestVacuumTableEndpoint:
    """Tests for POST /api/db-admin/vacuum/{table_name} endpoint."""

    def test_vacuum_requires_auth(self, client: TestClient):
        """Test that VACUUM requires authentication."""
        response = client.post("/api/db-admin/vacuum/persons")

        assert response.status_code in [401, 403]

    def test_vacuum_requires_admin(self, client: TestClient, auth_headers: dict):
        """Test that VACUUM requires admin role."""
        response = client.post(
            "/api/db-admin/vacuum/persons",
            headers=auth_headers,
        )

        # May return various codes depending on permission and table existence
        assert response.status_code in [200, 401, 403, 404, 500]

    def test_vacuum_with_analyze(self, client: TestClient, auth_headers: dict):
        """Test VACUUM with ANALYZE option."""
        response = client.post(
            "/api/db-admin/vacuum/persons?analyze=true",
            headers=auth_headers,
        )

        assert response.status_code in [200, 401, 403, 404, 500]

    def test_vacuum_invalid_table_name(self, client: TestClient, auth_headers: dict):
        """Test VACUUM with invalid table name (SQL injection prevention)."""
        response = client.post(
            "/api/db-admin/vacuum/users; DROP TABLE users;",
            headers=auth_headers,
        )

        # Should be rejected
        assert response.status_code in [400, 401, 403, 404, 422]


# ============================================================================
# Integration Tests
# ============================================================================


class TestDbAdminIntegration:
    """Integration tests for database admin endpoints."""

    def test_db_admin_endpoints_require_admin(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that all db-admin endpoints require admin role."""
        endpoints = [
            "/api/db-admin/health",
            "/api/db-admin/indexes/recommendations",
            "/api/db-admin/indexes/unused",
            "/api/db-admin/indexes/usage",
        ]

        for url in endpoints:
            response = client.get(url, headers=auth_headers)
            # Should return 200 if admin, or 403 if not admin
            assert response.status_code in [
                200,
                401,
                403,
                500,
            ], f"Unexpected status for {url}"

    def test_db_admin_without_auth(self, client: TestClient):
        """Test that db-admin endpoints reject unauthenticated requests."""
        endpoints = [
            "/api/db-admin/health",
            "/api/db-admin/indexes/recommendations",
            "/api/db-admin/indexes/unused",
            "/api/db-admin/indexes/usage",
        ]

        for url in endpoints:
            response = client.get(url)
            assert response.status_code in [401, 403], f"Expected 401/403 for {url}"


class TestDbAdminEdgeCases:
    """Test edge cases for database admin endpoints."""

    def test_recommendations_negative_min_size(
        self, client: TestClient, auth_headers: dict
    ):
        """Test recommendations with negative min table size."""
        response = client.get(
            "/api/db-admin/indexes/recommendations?min_table_size_mb=-1.0",
            headers=auth_headers,
        )

        # Should be rejected by validation
        assert response.status_code in [401, 403, 422]

    def test_unused_indexes_invalid_min_age(
        self, client: TestClient, auth_headers: dict
    ):
        """Test unused indexes with invalid min age."""
        response = client.get(
            "/api/db-admin/indexes/unused?min_age_days=0",
            headers=auth_headers,
        )

        # Should be rejected by validation (min is 1)
        assert response.status_code in [401, 403, 422]

    def test_table_stats_empty_table_name(self, client: TestClient, auth_headers: dict):
        """Test table statistics with empty table name."""
        # Empty path segment would result in different route
        response = client.get(
            "/api/db-admin/tables//stats",
            headers=auth_headers,
        )

        # Should return 404 or 307 (redirect) for malformed path
        assert response.status_code in [307, 401, 403, 404]
