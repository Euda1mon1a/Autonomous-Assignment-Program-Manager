"""Tests for custom Prometheus metric collectors."""

from unittest.mock import MagicMock, patch

from app.core.metrics.collectors import (
    ApplicationMetricsCollector,
    DatabasePoolCollector,
    SystemResourceCollector,
)


# ==================== SystemResourceCollector ====================


class TestSystemResourceCollector:
    def test_init_no_psutil(self):
        with patch("app.core.metrics.collectors.PSUTIL_AVAILABLE", False):
            collector = SystemResourceCollector()
            assert collector._enabled is False

    def test_init_with_psutil(self):
        mock_process = MagicMock()
        with patch("app.core.metrics.collectors.PSUTIL_AVAILABLE", True):
            collector = SystemResourceCollector(process=mock_process)
            assert collector._enabled is True
            assert collector._process is mock_process

    def test_collect_disabled(self):
        with patch("app.core.metrics.collectors.PSUTIL_AVAILABLE", False):
            collector = SystemResourceCollector()
            result = list(collector.collect())
            assert result == []


# ==================== DatabasePoolCollector ====================


class TestDatabasePoolCollector:
    def test_init_no_engine(self):
        collector = DatabasePoolCollector(engine=None)
        assert collector._enabled is False
        assert collector._engine is None

    def test_init_with_engine(self):
        mock_engine = MagicMock()
        collector = DatabasePoolCollector(engine=mock_engine)
        assert collector._enabled is True
        assert collector._engine is mock_engine

    def test_collect_disabled(self):
        collector = DatabasePoolCollector(engine=None)
        result = list(collector.collect())
        assert result == []

    def test_collect_prometheus_unavailable(self):
        mock_engine = MagicMock()
        collector = DatabasePoolCollector(engine=mock_engine)
        with patch("app.core.metrics.collectors.PROMETHEUS_AVAILABLE", False):
            result = list(collector.collect())
            assert result == []


# ==================== ApplicationMetricsCollector ====================


class TestApplicationMetricsCollector:
    def test_init_no_factory(self):
        collector = ApplicationMetricsCollector(db_session_factory=None)
        assert collector._enabled is False

    def test_init_with_factory(self):
        mock_factory = MagicMock()
        collector = ApplicationMetricsCollector(db_session_factory=mock_factory)
        assert collector._enabled is True

    def test_collect_disabled(self):
        collector = ApplicationMetricsCollector(db_session_factory=None)
        result = list(collector.collect())
        assert result == []

    def test_collect_prometheus_unavailable(self):
        mock_factory = MagicMock()
        collector = ApplicationMetricsCollector(db_session_factory=mock_factory)
        with patch("app.core.metrics.collectors.PROMETHEUS_AVAILABLE", False):
            result = list(collector.collect())
            assert result == []


# ==================== register_custom_collectors ====================


class TestRegisterCustomCollectors:
    def test_prometheus_unavailable(self):
        with patch("app.core.metrics.collectors.PROMETHEUS_AVAILABLE", False):
            from app.core.metrics.collectors import register_custom_collectors

            result = register_custom_collectors()
            assert result == []
