"""Tests for profiling API routes.

Tests the performance profiling functionality including:
- Profiling status and session management
- CPU and memory profiling
- SQL query metrics
- HTTP request metrics
- Distributed traces
- Bottleneck detection
- Flame graph generation
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestProfilingRoutes:
    """Test suite for profiling API endpoints."""

    # ========================================================================
    # Status Tests
    # ========================================================================

    @patch("app.api.routes.profiling.cpu_profiler")
    @patch("app.api.routes.profiling.memory_profiler")
    @patch("app.api.routes.profiling.sql_collector")
    @patch("app.api.routes.profiling.request_collector")
    @patch("app.api.routes.profiling.trace_collector")
    def test_get_profiling_status_success(
        self,
        mock_trace: MagicMock,
        mock_request: MagicMock,
        mock_sql: MagicMock,
        mock_memory: MagicMock,
        mock_cpu: MagicMock,
        client: TestClient,
    ):
        """Test getting profiling status."""
        mock_cpu.enabled = True
        mock_cpu.results = []
        mock_memory.enabled = True
        mock_memory.results = []
        mock_sql.enabled = True
        mock_sql.get_count.return_value = 100
        mock_request.enabled = True
        mock_request.get_count.return_value = 50
        mock_trace.enabled = True
        mock_trace.get_count.return_value = 20

        response = client.get("/api/profiling/status")
        assert response.status_code == 200

        data = response.json()
        assert data["enabled"] is True
        assert data["cpu_profiling"] is True
        assert data["sql_collection"] is True
        assert "stats" in data

    # ========================================================================
    # Session Management Tests
    # ========================================================================

    @patch("app.api.routes.profiling.cpu_profiler")
    @patch("app.api.routes.profiling.memory_profiler")
    @patch("app.api.routes.profiling.sql_collector")
    @patch("app.api.routes.profiling.request_collector")
    @patch("app.api.routes.profiling.trace_collector")
    def test_start_profiling_session_success(
        self,
        mock_trace: MagicMock,
        mock_request: MagicMock,
        mock_sql: MagicMock,
        mock_memory: MagicMock,
        mock_cpu: MagicMock,
        client: TestClient,
    ):
        """Test starting profiling session."""
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
        assert data["config"]["cpu"] is True

    @patch("app.api.routes.profiling.cpu_profiler")
    @patch("app.api.routes.profiling.memory_profiler")
    @patch("app.api.routes.profiling.sql_collector")
    @patch("app.api.routes.profiling.request_collector")
    @patch("app.api.routes.profiling.trace_collector")
    def test_start_profiling_selective(
        self,
        mock_trace: MagicMock,
        mock_request: MagicMock,
        mock_sql: MagicMock,
        mock_memory: MagicMock,
        mock_cpu: MagicMock,
        client: TestClient,
    ):
        """Test starting profiling with selective features."""
        response = client.post(
            "/api/profiling/start",
            json={
                "cpu": True,
                "memory": False,
                "sql": True,
                "requests": False,
                "traces": False,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["config"]["cpu"] is True
        assert data["config"]["memory"] is False

    @patch("app.api.routes.profiling.cpu_profiler")
    @patch("app.api.routes.profiling.memory_profiler")
    @patch("app.api.routes.profiling.sql_collector")
    @patch("app.api.routes.profiling.request_collector")
    @patch("app.api.routes.profiling.trace_collector")
    def test_stop_profiling_session_success(
        self,
        mock_trace: MagicMock,
        mock_request: MagicMock,
        mock_sql: MagicMock,
        mock_memory: MagicMock,
        mock_cpu: MagicMock,
        client: TestClient,
    ):
        """Test stopping profiling session."""
        mock_cpu.results = [MagicMock()]
        mock_memory.results = []
        mock_sql.get_count.return_value = 50
        mock_request.get_count.return_value = 25
        mock_trace.get_count.return_value = 10

        response = client.post("/api/profiling/stop")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "stopped"
        assert "summary" in data

    # ========================================================================
    # Report Tests
    # ========================================================================

    @patch("app.api.routes.profiling.performance_reporter")
    @patch("app.api.routes.profiling.bottleneck_detector")
    @patch("app.api.routes.profiling.performance_analyzer")
    @patch("app.api.routes.profiling.cpu_profiler")
    @patch("app.api.routes.profiling.memory_profiler")
    @patch("app.api.routes.profiling.sql_collector")
    @patch("app.api.routes.profiling.request_collector")
    @patch("app.api.routes.profiling.trace_collector")
    def test_get_profiling_report_json(
        self,
        mock_trace: MagicMock,
        mock_request: MagicMock,
        mock_sql: MagicMock,
        mock_memory: MagicMock,
        mock_cpu: MagicMock,
        mock_analyzer: MagicMock,
        mock_detector: MagicMock,
        mock_reporter: MagicMock,
        client: TestClient,
    ):
        """Test getting profiling report in JSON format."""
        mock_cpu.results = []
        mock_memory.results = []
        mock_sql.items = []
        mock_request.items = []
        mock_trace.items = []

        mock_analyzer.analyze_profile_results.return_value = []
        mock_detector.detect_sql_bottlenecks.return_value = []
        mock_detector.detect_request_bottlenecks.return_value = []
        mock_detector.detect_trace_bottlenecks.return_value = []

        mock_report = MagicMock()
        mock_report.to_dict.return_value = {"report_id": "abc123", "summary": {}}
        mock_reporter.generate_report.return_value = mock_report

        response = client.get("/api/profiling/report?format=json")
        assert response.status_code == 200

    # ========================================================================
    # SQL Query Metrics Tests
    # ========================================================================

    @patch("app.api.routes.profiling.sql_collector")
    def test_get_query_metrics_success(
        self,
        mock_sql: MagicMock,
        client: TestClient,
    ):
        """Test getting SQL query metrics."""
        mock_query = MagicMock()
        mock_query.to_dict.return_value = {
            "query": "SELECT * FROM users",
            "duration_ms": 50,
        }
        mock_sql.items = [mock_query]
        mock_sql.get_count.return_value = 1
        mock_sql.get_slow_queries.return_value = []
        mock_sql.get_failed_queries.return_value = []
        mock_sql.get_query_stats.return_value = {"avg_duration_ms": 50}

        response = client.get("/api/profiling/queries?limit=100")
        assert response.status_code == 200

        data = response.json()
        assert data["total_queries"] == 1
        assert "queries" in data

    @patch("app.api.routes.profiling.sql_collector")
    def test_get_query_metrics_slow_only(
        self,
        mock_sql: MagicMock,
        client: TestClient,
    ):
        """Test getting only slow SQL queries."""
        mock_slow_query = MagicMock()
        mock_slow_query.to_dict.return_value = {
            "query": "SELECT * FROM large_table",
            "duration_ms": 500,
        }
        mock_sql.items = []
        mock_sql.get_slow_queries.return_value = [mock_slow_query]
        mock_sql.get_count.return_value = 100
        mock_sql.get_failed_queries.return_value = []
        mock_sql.get_query_stats.return_value = {}

        response = client.get(
            "/api/profiling/queries?slow_only=true&threshold_ms=100"
        )
        assert response.status_code == 200

    # ========================================================================
    # HTTP Request Metrics Tests
    # ========================================================================

    @patch("app.api.routes.profiling.request_collector")
    def test_get_request_metrics_success(
        self,
        mock_request: MagicMock,
        client: TestClient,
    ):
        """Test getting HTTP request metrics."""
        mock_req = MagicMock()
        mock_req.to_dict.return_value = {
            "path": "/api/users",
            "method": "GET",
            "duration_ms": 150,
        }
        mock_request.items = [mock_req]
        mock_request.get_count.return_value = 1
        mock_request.get_slow_requests.return_value = []
        mock_request.get_failed_requests.return_value = []
        mock_request.get_request_stats.return_value = {}

        response = client.get("/api/profiling/requests?limit=100")
        assert response.status_code == 200

        data = response.json()
        assert data["total_requests"] == 1

    # ========================================================================
    # Distributed Traces Tests
    # ========================================================================

    @patch("app.api.routes.profiling.trace_collector")
    def test_get_traces_success(
        self,
        mock_trace: MagicMock,
        client: TestClient,
    ):
        """Test getting distributed traces."""
        mock_t = MagicMock()
        mock_t.to_dict.return_value = {
            "trace_id": "abc123",
            "duration_ms": 200,
        }
        mock_trace.items = [mock_t]
        mock_trace.get_count.return_value = 1
        mock_trace.get_slow_traces.return_value = []

        response = client.get("/api/profiling/traces?limit=100")
        assert response.status_code == 200

        data = response.json()
        assert data["total_traces"] == 1

    @patch("app.api.routes.profiling.trace_collector")
    def test_get_traces_by_id(
        self,
        mock_trace: MagicMock,
        client: TestClient,
    ):
        """Test getting traces filtered by trace ID."""
        mock_t = MagicMock()
        mock_t.to_dict.return_value = {"trace_id": "specific-123"}
        mock_trace.get_trace_by_id.return_value = [mock_t]
        mock_trace.get_count.return_value = 1
        mock_trace.get_slow_traces.return_value = []

        response = client.get("/api/profiling/traces?trace_id=specific-123")
        assert response.status_code == 200

    # ========================================================================
    # Bottleneck Detection Tests
    # ========================================================================

    @patch("app.api.routes.profiling.BottleneckDetector")
    @patch("app.api.routes.profiling.sql_collector")
    @patch("app.api.routes.profiling.request_collector")
    @patch("app.api.routes.profiling.trace_collector")
    def test_detect_bottlenecks_success(
        self,
        mock_trace: MagicMock,
        mock_request: MagicMock,
        mock_sql: MagicMock,
        mock_detector_class: MagicMock,
        client: TestClient,
    ):
        """Test detecting performance bottlenecks."""
        mock_sql.items = []
        mock_request.items = []
        mock_trace.items = []

        mock_bottleneck = MagicMock()
        mock_bottleneck.severity = "high"
        mock_bottleneck.to_dict.return_value = {
            "type": "slow_query",
            "severity": "high",
        }

        mock_detector = MagicMock()
        mock_detector.detect_sql_bottlenecks.return_value = [mock_bottleneck]
        mock_detector.detect_request_bottlenecks.return_value = []
        mock_detector.detect_trace_bottlenecks.return_value = []
        mock_detector_class.return_value = mock_detector

        response = client.get(
            "/api/profiling/bottlenecks?sql_threshold_ms=100"
        )
        assert response.status_code == 200

        data = response.json()
        assert "bottlenecks" in data
        assert "summary" in data

    # ========================================================================
    # Flame Graph Tests
    # ========================================================================

    @patch("app.api.routes.profiling.flame_graph_generator")
    @patch("app.api.routes.profiling.cpu_profiler")
    def test_generate_flamegraph_cpu(
        self,
        mock_cpu: MagicMock,
        mock_fg: MagicMock,
        client: TestClient,
    ):
        """Test generating CPU flame graph."""
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
        assert data["name"] == "root"

    @patch("app.api.routes.profiling.cpu_profiler")
    def test_generate_flamegraph_no_data(
        self,
        mock_cpu: MagicMock,
        client: TestClient,
    ):
        """Test flame graph when no data available."""
        mock_cpu.results = []

        response = client.get("/api/profiling/flamegraph?type=cpu")
        assert response.status_code == 404
        assert "No CPU profiling data" in response.json()["detail"]

    def test_generate_flamegraph_invalid_type(
        self,
        client: TestClient,
    ):
        """Test flame graph with invalid type."""
        response = client.get("/api/profiling/flamegraph?type=invalid")
        assert response.status_code == 400
        assert "Invalid flame graph type" in response.json()["detail"]

    # ========================================================================
    # Analysis Tests
    # ========================================================================

    @patch("app.api.routes.profiling.query_analyzer")
    @patch("app.api.routes.profiling.BottleneckDetector")
    @patch("app.api.routes.profiling.PerformanceAnalyzer")
    @patch("app.api.routes.profiling.cpu_profiler")
    @patch("app.api.routes.profiling.memory_profiler")
    @patch("app.api.routes.profiling.sql_collector")
    @patch("app.api.routes.profiling.request_collector")
    @patch("app.api.routes.profiling.trace_collector")
    def test_analyze_profiling_data_success(
        self,
        mock_trace: MagicMock,
        mock_request: MagicMock,
        mock_sql: MagicMock,
        mock_memory: MagicMock,
        mock_cpu: MagicMock,
        mock_analyzer_class: MagicMock,
        mock_detector_class: MagicMock,
        mock_query_analyzer: MagicMock,
        client: TestClient,
    ):
        """Test analyzing profiling data."""
        mock_cpu.results = []
        mock_memory.results = []
        mock_sql.items = []
        mock_request.items = []
        mock_trace.items = []

        mock_insight = MagicMock()
        mock_insight.category = "performance"
        mock_insight.title = "High CPU usage"
        mock_insight.priority = 1
        mock_insight.impact = "high"
        mock_insight.effort = "medium"
        mock_insight.to_dict.return_value = {
            "category": "performance",
            "title": "High CPU usage",
        }

        mock_analyzer = MagicMock()
        mock_analyzer.analyze_profile_results.return_value = [mock_insight]
        mock_analyzer_class.return_value = mock_analyzer

        mock_detector = MagicMock()
        mock_detector.detect_sql_bottlenecks.return_value = []
        mock_detector.detect_request_bottlenecks.return_value = []
        mock_detector.detect_trace_bottlenecks.return_value = []
        mock_detector_class.return_value = mock_detector

        mock_query_analyzer.analyze_query_patterns.return_value = {}

        response = client.post(
            "/api/profiling/analyze",
            json={
                "cpu_threshold_percent": 80.0,
                "memory_threshold_mb": 1000.0,
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "insights" in data
        assert "recommendations" in data

    # ========================================================================
    # Clear Data Tests
    # ========================================================================

    @patch("app.api.routes.profiling.profiler_context")
    @patch("app.api.routes.profiling.cpu_profiler")
    @patch("app.api.routes.profiling.memory_profiler")
    @patch("app.api.routes.profiling.sql_collector")
    @patch("app.api.routes.profiling.request_collector")
    @patch("app.api.routes.profiling.trace_collector")
    def test_clear_profiling_data_success(
        self,
        mock_trace: MagicMock,
        mock_request: MagicMock,
        mock_sql: MagicMock,
        mock_memory: MagicMock,
        mock_cpu: MagicMock,
        mock_context: MagicMock,
        client: TestClient,
    ):
        """Test clearing all profiling data."""
        response = client.delete("/api/profiling/clear")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "cleared"

        # Verify clear was called on all collectors
        mock_cpu.clear.assert_called_once()
        mock_memory.clear.assert_called_once()
        mock_sql.clear.assert_called_once()
        mock_request.clear.assert_called_once()
        mock_trace.clear.assert_called_once()
