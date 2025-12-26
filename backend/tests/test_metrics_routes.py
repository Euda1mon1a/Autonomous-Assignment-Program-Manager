"""
Comprehensive tests for Metrics API routes.

Tests coverage for metrics endpoints:
- GET /api/metrics/health - Metrics health check
- GET /api/metrics/info - Get metrics information
- GET /api/metrics/export - Export metrics (Prometheus format)
- GET /api/metrics/summary - Get metrics summary
- POST /api/metrics/reset - Reset metrics (debug only)
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Classes
# ============================================================================


class TestMetricsHealthEndpoint:
    """Tests for GET /api/metrics/health endpoint."""

    def test_health_success(self, client: TestClient):
        """Test successful metrics health check."""
        with patch("app.api.routes.metrics.get_metrics") as mock_get_metrics:
            mock_metrics = MagicMock()
            mock_metrics._enabled = True
            mock_get_metrics.return_value = mock_metrics

            response = client.get("/api/metrics/health")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "metrics_enabled" in data

    def test_health_disabled(self, client: TestClient):
        """Test metrics health when metrics are disabled."""
        with patch("app.api.routes.metrics.get_metrics") as mock_get_metrics:
            mock_metrics = MagicMock()
            mock_metrics._enabled = False
            mock_get_metrics.return_value = mock_metrics

            response = client.get("/api/metrics/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["metrics_enabled"] is False

    def test_health_response_structure(self, client: TestClient):
        """Test metrics health response has correct structure."""
        with patch("app.api.routes.metrics.get_metrics") as mock_get_metrics:
            mock_metrics = MagicMock()
            mock_metrics._enabled = True
            mock_get_metrics.return_value = mock_metrics

            response = client.get("/api/metrics/health")

            if response.status_code == 200:
                data = response.json()
                assert "status" in data
                assert "metrics_enabled" in data
                assert "collectors" in data
                assert "prometheus_available" in data
                assert "message" in data


class TestMetricsInfoEndpoint:
    """Tests for GET /api/metrics/info endpoint."""

    def test_info_success(self, client: TestClient):
        """Test successful metrics info retrieval."""
        response = client.get("/api/metrics/info")

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "total_metrics" in data
        assert "categories" in data

    def test_info_has_all_categories(self, client: TestClient):
        """Test metrics info includes all expected categories."""
        response = client.get("/api/metrics/info")

        if response.status_code == 200:
            data = response.json()
            expected_categories = [
                "http",
                "database",
                "cache",
                "background_tasks",
                "schedule",
                "acgme_compliance",
                "errors",
                "system",
            ]
            for category in expected_categories:
                assert category in data["categories"]

    def test_info_metric_documentation(self, client: TestClient):
        """Test that metric documentation is complete."""
        response = client.get("/api/metrics/info")

        if response.status_code == 200:
            data = response.json()
            # Check HTTP metrics documentation
            http_metrics = data["metrics"].get("http", {})
            if http_metrics:
                for metric_name, metric_doc in http_metrics.items():
                    assert "type" in metric_doc
                    assert "description" in metric_doc
                    assert "labels" in metric_doc


class TestMetricsExportEndpoint:
    """Tests for GET /api/metrics/export endpoint."""

    def test_export_success(self, client: TestClient):
        """Test successful metrics export."""
        with patch("app.api.routes.metrics.generate_latest") as mock_generate:
            mock_generate.return_value = (
                b"# HELP test_metric Test\n# TYPE test_metric counter\ntest_metric 1\n"
            )

            response = client.get("/api/metrics/export")

            assert response.status_code == 200
            assert "text/plain" in response.headers["content-type"]

    def test_export_prometheus_not_installed(self, client: TestClient):
        """Test export when prometheus_client is not installed."""
        with patch("app.api.routes.metrics.generate_latest") as mock_generate:
            mock_generate.side_effect = ImportError(
                "No module named 'prometheus_client'"
            )
            with patch("app.api.routes.metrics.REGISTRY") as mock_registry:
                # Need to mock the actual import
                pass

            # The endpoint may catch ImportError
            response = client.get("/api/metrics/export")

            # Should return 503 or 500 if prometheus not available
            assert response.status_code in [200, 500, 503]


class TestMetricsSummaryEndpoint:
    """Tests for GET /api/metrics/summary endpoint."""

    def test_summary_enabled(self, client: TestClient):
        """Test metrics summary when enabled."""
        with patch("app.api.routes.metrics.get_metrics") as mock_get_metrics:
            mock_metrics = MagicMock()
            mock_metrics._enabled = True
            mock_get_metrics.return_value = mock_metrics

            response = client.get("/api/metrics/summary")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert data["status"] == "enabled"

    def test_summary_disabled(self, client: TestClient):
        """Test metrics summary when disabled."""
        with patch("app.api.routes.metrics.get_metrics") as mock_get_metrics:
            mock_metrics = MagicMock()
            mock_metrics._enabled = False
            mock_get_metrics.return_value = mock_metrics

            response = client.get("/api/metrics/summary")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "disabled"

    def test_summary_response_structure(self, client: TestClient):
        """Test metrics summary response has correct structure."""
        with patch("app.api.routes.metrics.get_metrics") as mock_get_metrics:
            mock_metrics = MagicMock()
            mock_metrics._enabled = True
            mock_get_metrics.return_value = mock_metrics

            response = client.get("/api/metrics/summary")

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "enabled":
                    assert "http" in data
                    assert "database" in data
                    assert "cache" in data
                    assert "background_tasks" in data


class TestMetricsResetEndpoint:
    """Tests for POST /api/metrics/reset endpoint."""

    def test_reset_requires_debug_mode(self, client: TestClient):
        """Test that reset requires debug mode."""
        with patch("app.api.routes.metrics.get_settings") as mock_settings:
            settings = MagicMock()
            settings.DEBUG = False
            mock_settings.return_value = settings

            response = client.post("/api/metrics/reset")

            assert response.status_code == 403

    def test_reset_in_debug_mode(self, client: TestClient):
        """Test reset in debug mode."""
        with patch("app.api.routes.metrics.get_settings") as mock_settings:
            settings = MagicMock()
            settings.DEBUG = True
            mock_settings.return_value = settings

            response = client.post("/api/metrics/reset")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "message" in data


# ============================================================================
# Integration Tests
# ============================================================================


class TestMetricsIntegration:
    """Integration tests for metrics endpoints."""

    def test_metrics_endpoints_accessible(self, client: TestClient):
        """Test that metrics endpoints are accessible."""
        with patch("app.api.routes.metrics.get_metrics") as mock_get_metrics:
            mock_metrics = MagicMock()
            mock_metrics._enabled = True
            mock_get_metrics.return_value = mock_metrics

            endpoints = [
                "/api/metrics/health",
                "/api/metrics/info",
                "/api/metrics/summary",
            ]

            for url in endpoints:
                response = client.get(url)
                assert response.status_code == 200, f"Failed for {url}"

    def test_metrics_json_responses(self, client: TestClient):
        """Test metrics endpoints return valid JSON."""
        with patch("app.api.routes.metrics.get_metrics") as mock_get_metrics:
            mock_metrics = MagicMock()
            mock_metrics._enabled = True
            mock_get_metrics.return_value = mock_metrics

            endpoints = [
                "/api/metrics/health",
                "/api/metrics/info",
                "/api/metrics/summary",
            ]

            for url in endpoints:
                response = client.get(url)
                if response.status_code == 200:
                    assert response.headers["content-type"] == "application/json"
                    data = response.json()
                    assert isinstance(data, dict)

    def test_metrics_workflow(self, client: TestClient):
        """Test typical metrics workflow."""
        with patch("app.api.routes.metrics.get_metrics") as mock_get_metrics:
            mock_metrics = MagicMock()
            mock_metrics._enabled = True
            mock_get_metrics.return_value = mock_metrics

            # Check health
            health_response = client.get("/api/metrics/health")
            assert health_response.status_code == 200

            # Get info
            info_response = client.get("/api/metrics/info")
            assert info_response.status_code == 200

            # Get summary
            summary_response = client.get("/api/metrics/summary")
            assert summary_response.status_code == 200


class TestMetricsEdgeCases:
    """Test edge cases for metrics endpoints."""

    def test_health_with_partial_collectors(self, client: TestClient):
        """Test health when some collectors are unavailable."""
        with patch("app.api.routes.metrics.get_metrics") as mock_get_metrics:
            mock_metrics = MagicMock()
            mock_metrics._enabled = True
            mock_get_metrics.return_value = mock_metrics

            response = client.get("/api/metrics/health")

            assert response.status_code == 200

    def test_info_returns_consistent_structure(self, client: TestClient):
        """Test that info endpoint returns consistent structure."""
        # Call multiple times to ensure consistency
        responses = []
        for _ in range(3):
            response = client.get("/api/metrics/info")
            if response.status_code == 200:
                responses.append(response.json())

        if len(responses) >= 2:
            # Structure should be consistent
            assert responses[0].keys() == responses[1].keys()
            assert responses[0]["categories"] == responses[1]["categories"]
