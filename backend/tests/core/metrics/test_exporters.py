"""Tests for metrics exporters (Prometheus, Grafana, Datadog, CloudWatch)."""

import sys
from unittest.mock import MagicMock

import pytest

# Ensure prometheus_client is available (or mock it) before importing exporters
if "prometheus_client" not in sys.modules:
    mock_prom = MagicMock()
    mock_prom.CollectorRegistry = MagicMock
    mock_prom.REGISTRY = MagicMock()
    mock_prom.push_to_gateway = MagicMock()
    mock_exposition = MagicMock()
    mock_exposition.generate_latest = MagicMock()
    sys.modules["prometheus_client"] = mock_prom
    sys.modules["prometheus_client.exposition"] = mock_exposition
    sys.modules["prometheus_client.registry"] = MagicMock()

from app.core.metrics.exporters import (  # noqa: E402
    CloudWatchExporter,
    DatadogExporter,
    GrafanaCloudExporter,
    MetricExportConfig,
    MetricExporter,
    create_datadog_exporter,
    create_grafana_cloud_exporter,
)


# ==================== MetricExportConfig ====================


class TestMetricExportConfig:
    def test_defaults(self):
        config = MetricExportConfig()
        assert config.enabled is True
        assert config.export_interval_seconds == 60
        assert config.batch_size == 100
        assert config.retry_attempts == 3
        assert config.timeout_seconds == 10
        assert config.metadata == {}

    def test_custom(self):
        config = MetricExportConfig(
            enabled=False,
            export_interval_seconds=30,
            batch_size=50,
            retry_attempts=5,
            timeout_seconds=20,
            metadata={"instance_id": "abc"},
        )
        assert config.enabled is False
        assert config.export_interval_seconds == 30
        assert config.metadata["instance_id"] == "abc"


# ==================== MetricExporter (abstract) ====================


class TestMetricExporterBase:
    def test_is_abstract(self):
        with pytest.raises(TypeError):
            MetricExporter(MetricExportConfig())

    def test_collect_metrics_returns_empty(self):
        # Use a concrete subclass to test base method
        config = MetricExportConfig()
        exporter = CloudWatchExporter(config)
        result = exporter._collect_metrics()
        assert result == {}

    def test_init_state(self):
        config = MetricExportConfig()
        exporter = CloudWatchExporter(config)
        assert exporter._running is False
        assert exporter._export_task is None
        assert exporter.config is config


# ==================== GrafanaCloudExporter ====================


class TestGrafanaCloudExporter:
    def test_init(self):
        config = MetricExportConfig()
        exporter = GrafanaCloudExporter(
            config,
            remote_write_url="https://grafana.example.com/push",
            api_key="test-key",
            instance_id="inst-1",
        )
        assert exporter.remote_write_url == "https://grafana.example.com/push"
        assert exporter.api_key == "test-key"
        assert exporter.instance_id == "inst-1"

    def test_format_metrics(self):
        config = MetricExportConfig()
        exporter = GrafanaCloudExporter(
            config,
            remote_write_url="https://grafana.example.com",
            api_key="key",
            instance_id="inst",
        )
        result = exporter._format_metrics({"cpu": 50.0})
        assert isinstance(result, bytes)


# ==================== DatadogExporter ====================


class TestDatadogExporter:
    def test_init_defaults(self):
        config = MetricExportConfig()
        exporter = DatadogExporter(config, api_key="dd-key")
        assert exporter.api_key == "dd-key"
        assert exporter.app_key is None
        assert "datadoghq.com" in exporter.base_url

    def test_init_custom_site(self):
        config = MetricExportConfig()
        exporter = DatadogExporter(config, api_key="dd-key", site="datadoghq.eu")
        assert "datadoghq.eu" in exporter.base_url

    def test_format_metrics(self):
        config = MetricExportConfig(metadata={"instance_id": "inst-1"})
        exporter = DatadogExporter(config, api_key="dd-key")
        series = exporter._format_metrics({"cpu_usage": 42.0, "mem_usage": 70.0})
        assert len(series) == 2
        for entry in series:
            assert "metric" in entry
            assert "points" in entry
            assert "type" in entry
            assert entry["type"] == "gauge"

    def test_format_metrics_empty(self):
        config = MetricExportConfig()
        exporter = DatadogExporter(config, api_key="dd-key")
        assert exporter._format_metrics({}) == []


# ==================== CloudWatchExporter ====================


class TestCloudWatchExporter:
    def test_init_defaults(self):
        config = MetricExportConfig()
        exporter = CloudWatchExporter(config)
        assert exporter.namespace == "ResidencyScheduler"
        assert exporter.region == "us-east-1"
        assert exporter._client is None

    def test_init_custom(self):
        config = MetricExportConfig()
        exporter = CloudWatchExporter(config, namespace="CustomNS", region="eu-west-1")
        assert exporter.namespace == "CustomNS"
        assert exporter.region == "eu-west-1"

    def test_format_metrics(self):
        config = MetricExportConfig()
        exporter = CloudWatchExporter(config)
        data = exporter._format_metrics({"cpu": 50.0, "memory": 70.0})
        assert len(data) == 2
        for entry in data:
            assert "MetricName" in entry
            assert "Value" in entry
            assert "Timestamp" in entry
            assert "Unit" in entry

    def test_format_metrics_empty(self):
        config = MetricExportConfig()
        exporter = CloudWatchExporter(config)
        assert exporter._format_metrics({}) == []


# ==================== Factory functions ====================


class TestFactoryFunctions:
    def test_create_grafana_cloud_exporter(self):
        exporter = create_grafana_cloud_exporter(
            remote_write_url="https://grafana.example.com",
            api_key="key",
            instance_id="inst",
        )
        assert isinstance(exporter, GrafanaCloudExporter)
        assert exporter.config.export_interval_seconds == 60

    def test_create_grafana_custom_interval(self):
        exporter = create_grafana_cloud_exporter(
            remote_write_url="url",
            api_key="key",
            instance_id="inst",
            export_interval=30,
        )
        assert exporter.config.export_interval_seconds == 30

    def test_create_datadog_exporter(self):
        exporter = create_datadog_exporter(api_key="dd-key")
        assert isinstance(exporter, DatadogExporter)
        assert exporter.config.export_interval_seconds == 60

    def test_create_datadog_custom_site(self):
        exporter = create_datadog_exporter(
            api_key="dd-key", site="datadoghq.eu", export_interval=15
        )
        assert "datadoghq.eu" in exporter.base_url
        assert exporter.config.export_interval_seconds == 15
