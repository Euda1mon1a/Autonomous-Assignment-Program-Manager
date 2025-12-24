"""
Comprehensive tests for Profiling API routes.

Tests coverage for performance profiling:
- GET /api/profiling/status - Get profiling status
- POST /api/profiling/start - Start profiling session
- POST /api/profiling/stop - Stop profiling session
- GET /api/profiling/report - Get profiling report
- GET /api/profiling/queries - Get SQL query metrics
- GET /api/profiling/requests - Get HTTP request metrics
- GET /api/profiling/traces - Get distributed traces
- GET /api/profiling/bottlenecks - Detect performance bottlenecks
- GET /api/profiling/flamegraph - Generate flame graph data
- POST /api/profiling/analyze - Analyze profiling data
- DELETE /api/profiling/clear - Clear profiling data
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


# ============================================================================
# Test Classes
# ============================================================================


class TestProfilingStatusEndpoint:
    """Tests for GET /api/profiling/status endpoint."""

    def test_status_success(self, client: TestClient):
        """Test successful profiling status retrieval."""
        with patch("app.api.routes.profiling.cpu_profiler") as mock_cpu, \
             patch("app.api.routes.profiling.memory_profiler") as mock_mem, \
             patch("app.api.routes.profiling.sql_collector") as mock_sql, \
             patch("app.api.routes.profiling.request_collector") as mock_req, \
             patch("app.api.routes.profiling.trace_collector") as mock_trace:
            mock_cpu.enabled = True
            mock_cpu.results = []
            mock_mem.enabled = True
            mock_mem.results = []
            mock_sql.enabled = True
            mock_sql.get_count.return_value = 0
            mock_req.enabled = True
            mock_req.get_count.return_value = 0
            mock_trace.enabled = True
            mock_trace.get_count.return_value = 0

            response = client.get("/api/profiling/status")

            assert response.status_code == 200

    def test_status_response_structure(self, client: TestClient):
        """Test profiling status response has correct structure."""
        with patch("app.api.routes.profiling.cpu_profiler") as mock_cpu, \
             patch("app.api.routes.profiling.memory_profiler") as mock_mem, \
             patch("app.api.routes.profiling.sql_collector") as mock_sql, \
             patch("app.api.routes.profiling.request_collector") as mock_req, \
             patch("app.api.routes.profiling.trace_collector") as mock_trace:
            mock_cpu.enabled = True
            mock_cpu.results = []
            mock_mem.enabled = True
            mock_mem.results = []
            mock_sql.enabled = True
            mock_sql.get_count.return_value = 100
            mock_req.enabled = True
            mock_req.get_count.return_value = 50
            mock_trace.enabled = True
            mock_trace.get_count.return_value = 25

            response = client.get("/api/profiling/status")

            if response.status_code == 200:
                data = response.json()
                assert "enabled" in data
                assert "cpu_profiling" in data
                assert "memory_profiling" in data
                assert "sql_collection" in data
                assert "request_collection" in data
                assert "trace_collection" in data
                assert "stats" in data


class TestProfilingStartEndpoint:
    """Tests for POST /api/profiling/start endpoint."""

    def test_start_session_success(self, client: TestClient):
        """Test starting a profiling session."""
        with patch("app.api.routes.profiling.cpu_profiler") as mock_cpu, \
             patch("app.api.routes.profiling.memory_profiler") as mock_mem, \
             patch("app.api.routes.profiling.sql_collector") as mock_sql, \
             patch("app.api.routes.profiling.request_collector") as mock_req, \
             patch("app.api.routes.profiling.trace_collector") as mock_trace:
            response = client.post(
                "/api/profiling/start",
                json={
                    "cpu": True,
                    "memory": True,
                    "sql": True,
                    "requests": True,
                    "traces": True,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "started"
            assert "session_id" in data

    def test_start_session_partial_config(self, client: TestClient):
        """Test starting session with partial configuration."""
        with patch("app.api.routes.profiling.cpu_profiler"), \
             patch("app.api.routes.profiling.memory_profiler"), \
             patch("app.api.routes.profiling.sql_collector"), \
             patch("app.api.routes.profiling.request_collector"), \
             patch("app.api.routes.profiling.trace_collector"):
            response = client.post(
                "/api/profiling/start",
                json={
                    "cpu": True,
                    "memory": False,
                    "sql": True,
                    "requests": False,
                    "traces": True,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["config"]["cpu"] is True
            assert data["config"]["memory"] is False

    def test_start_session_default_config(self, client: TestClient):
        """Test starting session with default configuration."""
        with patch("app.api.routes.profiling.cpu_profiler"), \
             patch("app.api.routes.profiling.memory_profiler"), \
             patch("app.api.routes.profiling.sql_collector"), \
             patch("app.api.routes.profiling.request_collector"), \
             patch("app.api.routes.profiling.trace_collector"):
            response = client.post(
                "/api/profiling/start",
                json={},
            )

            assert response.status_code == 200


class TestProfilingStopEndpoint:
    """Tests for POST /api/profiling/stop endpoint."""

    def test_stop_session_success(self, client: TestClient):
        """Test stopping a profiling session."""
        with patch("app.api.routes.profiling.cpu_profiler") as mock_cpu, \
             patch("app.api.routes.profiling.memory_profiler") as mock_mem, \
             patch("app.api.routes.profiling.sql_collector") as mock_sql, \
             patch("app.api.routes.profiling.request_collector") as mock_req, \
             patch("app.api.routes.profiling.trace_collector") as mock_trace:
            mock_cpu.results = [MagicMock()]
            mock_mem.results = [MagicMock()]
            mock_sql.get_count.return_value = 100
            mock_req.get_count.return_value = 50
            mock_trace.get_count.return_value = 25

            response = client.post("/api/profiling/stop")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "stopped"
            assert "summary" in data


class TestProfilingReportEndpoint:
    """Tests for GET /api/profiling/report endpoint."""

    def test_report_json_format(self, client: TestClient):
        """Test getting profiling report in JSON format."""
        with patch("app.api.routes.profiling.cpu_profiler") as mock_cpu, \
             patch("app.api.routes.profiling.memory_profiler") as mock_mem, \
             patch("app.api.routes.profiling.sql_collector") as mock_sql, \
             patch("app.api.routes.profiling.request_collector") as mock_req, \
             patch("app.api.routes.profiling.trace_collector") as mock_trace, \
             patch("app.api.routes.profiling.performance_analyzer") as mock_analyzer, \
             patch("app.api.routes.profiling.bottleneck_detector") as mock_detector, \
             patch("app.api.routes.profiling.performance_reporter") as mock_reporter:
            mock_cpu.results = []
            mock_mem.results = []
            mock_sql.items = []
            mock_req.items = []
            mock_trace.items = []
            mock_analyzer.analyze_profile_results.return_value = []
            mock_detector.detect_sql_bottlenecks.return_value = []
            mock_detector.detect_request_bottlenecks.return_value = []
            mock_detector.detect_trace_bottlenecks.return_value = []
            mock_report = MagicMock()
            mock_report.to_dict.return_value = {"report_id": "test"}
            mock_reporter.generate_report.return_value = mock_report

            response = client.get("/api/profiling/report?format=json")

            assert response.status_code == 200

    def test_report_html_format(self, client: TestClient):
        """Test getting profiling report in HTML format."""
        with patch("app.api.routes.profiling.cpu_profiler") as mock_cpu, \
             patch("app.api.routes.profiling.memory_profiler") as mock_mem, \
             patch("app.api.routes.profiling.sql_collector") as mock_sql, \
             patch("app.api.routes.profiling.request_collector") as mock_req, \
             patch("app.api.routes.profiling.trace_collector") as mock_trace, \
             patch("app.api.routes.profiling.performance_analyzer") as mock_analyzer, \
             patch("app.api.routes.profiling.bottleneck_detector") as mock_detector, \
             patch("app.api.routes.profiling.performance_reporter") as mock_reporter:
            mock_cpu.results = []
            mock_mem.results = []
            mock_sql.items = []
            mock_req.items = []
            mock_trace.items = []
            mock_analyzer.analyze_profile_results.return_value = []
            mock_detector.detect_sql_bottlenecks.return_value = []
            mock_detector.detect_request_bottlenecks.return_value = []
            mock_detector.detect_trace_bottlenecks.return_value = []
            mock_report = MagicMock()
            mock_reporter.generate_report.return_value = mock_report
            mock_reporter.export_to_html.return_value = "<html>Report</html>"

            response = client.get("/api/profiling/report?format=html")

            assert response.status_code == 200


class TestProfilingQueriesEndpoint:
    """Tests for GET /api/profiling/queries endpoint."""

    def test_queries_success(self, client: TestClient):
        """Test getting SQL query metrics."""
        with patch("app.api.routes.profiling.sql_collector") as mock_sql:
            mock_sql.items = []
            mock_sql.get_count.return_value = 0
            mock_sql.get_slow_queries.return_value = []
            mock_sql.get_failed_queries.return_value = []
            mock_sql.get_query_stats.return_value = {}

            response = client.get("/api/profiling/queries")

            assert response.status_code == 200
            data = response.json()
            assert "total_queries" in data
            assert "slow_queries" in data
            assert "failed_queries" in data

    def test_queries_with_limit(self, client: TestClient):
        """Test getting SQL query metrics with limit."""
        with patch("app.api.routes.profiling.sql_collector") as mock_sql:
            mock_sql.items = []
            mock_sql.get_count.return_value = 0
            mock_sql.get_slow_queries.return_value = []
            mock_sql.get_failed_queries.return_value = []
            mock_sql.get_query_stats.return_value = {}

            response = client.get("/api/profiling/queries?limit=50")

            assert response.status_code == 200

    def test_queries_slow_only(self, client: TestClient):
        """Test getting only slow SQL queries."""
        with patch("app.api.routes.profiling.sql_collector") as mock_sql:
            mock_sql.get_count.return_value = 100
            mock_sql.get_slow_queries.return_value = []
            mock_sql.get_failed_queries.return_value = []
            mock_sql.get_query_stats.return_value = {}

            response = client.get(
                "/api/profiling/queries?slow_only=true&threshold_ms=50"
            )

            assert response.status_code == 200


class TestProfilingRequestsEndpoint:
    """Tests for GET /api/profiling/requests endpoint."""

    def test_requests_success(self, client: TestClient):
        """Test getting HTTP request metrics."""
        with patch("app.api.routes.profiling.request_collector") as mock_req:
            mock_req.items = []
            mock_req.get_count.return_value = 0
            mock_req.get_slow_requests.return_value = []
            mock_req.get_failed_requests.return_value = []
            mock_req.get_request_stats.return_value = {}

            response = client.get("/api/profiling/requests")

            assert response.status_code == 200
            data = response.json()
            assert "total_requests" in data
            assert "slow_requests" in data
            assert "failed_requests" in data

    def test_requests_slow_only(self, client: TestClient):
        """Test getting only slow HTTP requests."""
        with patch("app.api.routes.profiling.request_collector") as mock_req:
            mock_req.get_count.return_value = 50
            mock_req.get_slow_requests.return_value = []
            mock_req.get_failed_requests.return_value = []
            mock_req.get_request_stats.return_value = {}

            response = client.get(
                "/api/profiling/requests?slow_only=true&threshold_ms=500"
            )

            assert response.status_code == 200


class TestProfilingTracesEndpoint:
    """Tests for GET /api/profiling/traces endpoint."""

    def test_traces_success(self, client: TestClient):
        """Test getting distributed traces."""
        with patch("app.api.routes.profiling.trace_collector") as mock_trace:
            mock_trace.items = []
            mock_trace.get_count.return_value = 0
            mock_trace.get_slow_traces.return_value = []

            response = client.get("/api/profiling/traces")

            assert response.status_code == 200
            data = response.json()
            assert "total_traces" in data
            assert "slow_traces" in data
            assert "traces" in data

    def test_traces_by_id(self, client: TestClient):
        """Test getting traces filtered by trace ID."""
        with patch("app.api.routes.profiling.trace_collector") as mock_trace:
            mock_trace.get_trace_by_id.return_value = []
            mock_trace.get_count.return_value = 0
            mock_trace.get_slow_traces.return_value = []

            response = client.get("/api/profiling/traces?trace_id=abc123")

            assert response.status_code == 200

    def test_traces_slow_only(self, client: TestClient):
        """Test getting only slow traces."""
        with patch("app.api.routes.profiling.trace_collector") as mock_trace:
            mock_trace.get_count.return_value = 25
            mock_trace.get_slow_traces.return_value = []
            mock_trace.items = []

            response = client.get(
                "/api/profiling/traces?slow_only=true&threshold_ms=500"
            )

            assert response.status_code == 200


class TestProfilingBottlenecksEndpoint:
    """Tests for GET /api/profiling/bottlenecks endpoint."""

    def test_bottlenecks_success(self, client: TestClient):
        """Test detecting performance bottlenecks."""
        with patch("app.api.routes.profiling.sql_collector") as mock_sql, \
             patch("app.api.routes.profiling.request_collector") as mock_req, \
             patch("app.api.routes.profiling.trace_collector") as mock_trace, \
             patch("app.api.routes.profiling.BottleneckDetector") as mock_detector_class:
            mock_sql.items = []
            mock_req.items = []
            mock_trace.items = []
            mock_detector = MagicMock()
            mock_detector.detect_sql_bottlenecks.return_value = []
            mock_detector.detect_request_bottlenecks.return_value = []
            mock_detector.detect_trace_bottlenecks.return_value = []
            mock_detector_class.return_value = mock_detector

            response = client.get("/api/profiling/bottlenecks")

            assert response.status_code == 200
            data = response.json()
            assert "bottlenecks" in data
            assert "summary" in data

    def test_bottlenecks_with_thresholds(self, client: TestClient):
        """Test bottleneck detection with custom thresholds."""
        with patch("app.api.routes.profiling.sql_collector") as mock_sql, \
             patch("app.api.routes.profiling.request_collector") as mock_req, \
             patch("app.api.routes.profiling.trace_collector") as mock_trace, \
             patch("app.api.routes.profiling.BottleneckDetector") as mock_detector_class:
            mock_sql.items = []
            mock_req.items = []
            mock_trace.items = []
            mock_detector = MagicMock()
            mock_detector.detect_sql_bottlenecks.return_value = []
            mock_detector.detect_request_bottlenecks.return_value = []
            mock_detector.detect_trace_bottlenecks.return_value = []
            mock_detector_class.return_value = mock_detector

            response = client.get(
                "/api/profiling/bottlenecks?sql_threshold_ms=50&request_threshold_ms=500"
            )

            assert response.status_code == 200


class TestProfilingFlamegraphEndpoint:
    """Tests for GET /api/profiling/flamegraph endpoint."""

    def test_flamegraph_cpu_no_data(self, client: TestClient):
        """Test flamegraph when no CPU data is available."""
        with patch("app.api.routes.profiling.cpu_profiler") as mock_cpu:
            mock_cpu.results = []

            response = client.get("/api/profiling/flamegraph?type=cpu")

            assert response.status_code == 404

    def test_flamegraph_traces_no_data(self, client: TestClient):
        """Test flamegraph when no trace data is available."""
        with patch("app.api.routes.profiling.trace_collector") as mock_trace:
            mock_trace.items = []

            response = client.get("/api/profiling/flamegraph?type=traces")

            assert response.status_code == 404

    def test_flamegraph_invalid_type(self, client: TestClient):
        """Test flamegraph with invalid type."""
        response = client.get("/api/profiling/flamegraph?type=invalid")

        assert response.status_code == 400

    def test_flamegraph_cpu_success(self, client: TestClient):
        """Test flamegraph generation with CPU data."""
        with patch("app.api.routes.profiling.cpu_profiler") as mock_cpu, \
             patch("app.api.routes.profiling.flame_graph_generator") as mock_fg:
            mock_profile = MagicMock()
            mock_cpu.results = [mock_profile]
            mock_fg.generate_from_profile.return_value = {
                "name": "root",
                "value": 100,
                "children": [],
            }

            response = client.get("/api/profiling/flamegraph?type=cpu")

            assert response.status_code == 200
            data = response.json()
            assert "name" in data


class TestProfilingAnalyzeEndpoint:
    """Tests for POST /api/profiling/analyze endpoint."""

    def test_analyze_success(self, client: TestClient):
        """Test analyzing profiling data."""
        with patch("app.api.routes.profiling.cpu_profiler") as mock_cpu, \
             patch("app.api.routes.profiling.memory_profiler") as mock_mem, \
             patch("app.api.routes.profiling.sql_collector") as mock_sql, \
             patch("app.api.routes.profiling.request_collector") as mock_req, \
             patch("app.api.routes.profiling.trace_collector") as mock_trace, \
             patch("app.api.routes.profiling.PerformanceAnalyzer") as mock_analyzer_class, \
             patch("app.api.routes.profiling.BottleneckDetector") as mock_detector_class, \
             patch("app.api.routes.profiling.query_analyzer") as mock_qa:
            mock_cpu.results = []
            mock_mem.results = []
            mock_sql.items = []
            mock_req.items = []
            mock_trace.items = []
            mock_analyzer = MagicMock()
            mock_analyzer.analyze_profile_results.return_value = []
            mock_analyzer_class.return_value = mock_analyzer
            mock_detector = MagicMock()
            mock_detector.detect_sql_bottlenecks.return_value = []
            mock_detector.detect_request_bottlenecks.return_value = []
            mock_detector.detect_trace_bottlenecks.return_value = []
            mock_detector_class.return_value = mock_detector
            mock_qa.analyze_query_patterns.return_value = {}

            response = client.post(
                "/api/profiling/analyze",
                json={
                    "cpu_threshold_percent": 80.0,
                    "memory_threshold_mb": 1000.0,
                    "duration_threshold_ms": 1000.0,
                    "sql_slow_threshold_ms": 100.0,
                    "request_slow_threshold_ms": 1000.0,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "insights" in data
            assert "bottlenecks" in data
            assert "recommendations" in data

    def test_analyze_default_thresholds(self, client: TestClient):
        """Test analyzing with default thresholds."""
        with patch("app.api.routes.profiling.cpu_profiler") as mock_cpu, \
             patch("app.api.routes.profiling.memory_profiler") as mock_mem, \
             patch("app.api.routes.profiling.sql_collector") as mock_sql, \
             patch("app.api.routes.profiling.request_collector") as mock_req, \
             patch("app.api.routes.profiling.trace_collector") as mock_trace, \
             patch("app.api.routes.profiling.PerformanceAnalyzer") as mock_analyzer_class, \
             patch("app.api.routes.profiling.BottleneckDetector") as mock_detector_class, \
             patch("app.api.routes.profiling.query_analyzer") as mock_qa:
            mock_cpu.results = []
            mock_mem.results = []
            mock_sql.items = []
            mock_req.items = []
            mock_trace.items = []
            mock_analyzer = MagicMock()
            mock_analyzer.analyze_profile_results.return_value = []
            mock_analyzer_class.return_value = mock_analyzer
            mock_detector = MagicMock()
            mock_detector.detect_sql_bottlenecks.return_value = []
            mock_detector.detect_request_bottlenecks.return_value = []
            mock_detector.detect_trace_bottlenecks.return_value = []
            mock_detector_class.return_value = mock_detector
            mock_qa.analyze_query_patterns.return_value = {}

            response = client.post(
                "/api/profiling/analyze",
                json={},
            )

            assert response.status_code == 200


class TestProfilingClearEndpoint:
    """Tests for DELETE /api/profiling/clear endpoint."""

    def test_clear_success(self, client: TestClient):
        """Test clearing profiling data."""
        with patch("app.api.routes.profiling.cpu_profiler") as mock_cpu, \
             patch("app.api.routes.profiling.memory_profiler") as mock_mem, \
             patch("app.api.routes.profiling.sql_collector") as mock_sql, \
             patch("app.api.routes.profiling.request_collector") as mock_req, \
             patch("app.api.routes.profiling.trace_collector") as mock_trace, \
             patch("app.api.routes.profiling.profiler_context") as mock_ctx:
            response = client.delete("/api/profiling/clear")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "cleared"

            # Verify clear was called on all collectors
            mock_cpu.clear.assert_called_once()
            mock_mem.clear.assert_called_once()
            mock_sql.clear.assert_called_once()
            mock_req.clear.assert_called_once()
            mock_trace.clear.assert_called_once()


# ============================================================================
# Integration Tests
# ============================================================================


class TestProfilingIntegration:
    """Integration tests for profiling endpoints."""

    def test_profiling_workflow(self, client: TestClient):
        """Test complete profiling workflow: start -> stop -> report."""
        with patch("app.api.routes.profiling.cpu_profiler") as mock_cpu, \
             patch("app.api.routes.profiling.memory_profiler") as mock_mem, \
             patch("app.api.routes.profiling.sql_collector") as mock_sql, \
             patch("app.api.routes.profiling.request_collector") as mock_req, \
             patch("app.api.routes.profiling.trace_collector") as mock_trace, \
             patch("app.api.routes.profiling.performance_analyzer") as mock_analyzer, \
             patch("app.api.routes.profiling.bottleneck_detector") as mock_detector, \
             patch("app.api.routes.profiling.performance_reporter") as mock_reporter:
            mock_cpu.enabled = True
            mock_cpu.results = []
            mock_mem.enabled = True
            mock_mem.results = []
            mock_sql.enabled = True
            mock_sql.items = []
            mock_sql.get_count.return_value = 0
            mock_req.enabled = True
            mock_req.items = []
            mock_req.get_count.return_value = 0
            mock_trace.enabled = True
            mock_trace.items = []
            mock_trace.get_count.return_value = 0
            mock_analyzer.analyze_profile_results.return_value = []
            mock_detector.detect_sql_bottlenecks.return_value = []
            mock_detector.detect_request_bottlenecks.return_value = []
            mock_detector.detect_trace_bottlenecks.return_value = []
            mock_report = MagicMock()
            mock_report.to_dict.return_value = {"report_id": "test"}
            mock_reporter.generate_report.return_value = mock_report

            # Start session
            start_response = client.post(
                "/api/profiling/start",
                json={"cpu": True, "memory": True},
            )
            assert start_response.status_code == 200

            # Stop session
            stop_response = client.post("/api/profiling/stop")
            assert stop_response.status_code == 200

            # Get report
            report_response = client.get("/api/profiling/report")
            assert report_response.status_code == 200

    def test_profiling_endpoints_accessible(self, client: TestClient):
        """Test profiling endpoints are accessible."""
        with patch("app.api.routes.profiling.cpu_profiler") as mock_cpu, \
             patch("app.api.routes.profiling.memory_profiler") as mock_mem, \
             patch("app.api.routes.profiling.sql_collector") as mock_sql, \
             patch("app.api.routes.profiling.request_collector") as mock_req, \
             patch("app.api.routes.profiling.trace_collector") as mock_trace:
            mock_cpu.enabled = True
            mock_cpu.results = []
            mock_mem.enabled = True
            mock_mem.results = []
            mock_sql.enabled = True
            mock_sql.items = []
            mock_sql.get_count.return_value = 0
            mock_sql.get_slow_queries.return_value = []
            mock_sql.get_failed_queries.return_value = []
            mock_sql.get_query_stats.return_value = {}
            mock_req.enabled = True
            mock_req.items = []
            mock_req.get_count.return_value = 0
            mock_req.get_slow_requests.return_value = []
            mock_req.get_failed_requests.return_value = []
            mock_req.get_request_stats.return_value = {}
            mock_trace.enabled = True
            mock_trace.items = []
            mock_trace.get_count.return_value = 0
            mock_trace.get_slow_traces.return_value = []

            endpoints = [
                ("/api/profiling/status", "GET"),
                ("/api/profiling/queries", "GET"),
                ("/api/profiling/requests", "GET"),
                ("/api/profiling/traces", "GET"),
            ]

            for url, method in endpoints:
                response = client.get(url)
                assert response.status_code == 200, f"Failed for {url}"
