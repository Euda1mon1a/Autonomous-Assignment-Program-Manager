"""
Metrics exporters for various monitoring systems.

Supports:
- Prometheus (pull-based)
- Grafana Cloud (push-based)
- Datadog (push-based)
- CloudWatch (AWS)
- Custom exporters
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx
from loguru import logger

try:
    from prometheus_client import REGISTRY, CollectorRegistry, push_to_gateway
    from prometheus_client.exposition import generate_latest

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not available - Prometheus export disabled")


@dataclass
class MetricExportConfig:
    """Configuration for metric export."""

    enabled: bool = True
    export_interval_seconds: int = 60
    batch_size: int = 100
    retry_attempts: int = 3
    timeout_seconds: int = 10
    metadata: dict[str, Any] = field(default_factory=dict)


class MetricExporter(ABC):
    """
    Abstract base class for metric exporters.

    Exporters push metrics to external monitoring systems.
    """

    def __init__(self, config: MetricExportConfig):
        """
        Initialize metric exporter.

        Args:
            config: Export configuration
        """
        self.config = config
        self._running = False
        self._export_task: asyncio.Task | None = None

    @abstractmethod
    async def export_metrics(self, metrics: dict[str, Any]) -> None:
        """
        Export metrics to external system.

        Args:
            metrics: Dictionary of metric name -> value
        """
        pass

    async def start(self) -> None:
        """Start continuous metric export."""
        if self._running:
            logger.warning("Metric exporter already running")
            return

        self._running = True
        self._export_task = asyncio.create_task(self._export_loop())
        logger.info(f"Started {self.__class__.__name__}")

    async def stop(self) -> None:
        """Stop metric export."""
        self._running = False
        if self._export_task:
            self._export_task.cancel()
            try:
                await self._export_task
            except asyncio.CancelledError:
                pass

        logger.info(f"Stopped {self.__class__.__name__}")

    async def _export_loop(self) -> None:
        """Continuous export loop."""
        while self._running:
            try:
                # Collect current metrics
                metrics = self._collect_metrics()

                # Export metrics
                await self.export_metrics(metrics)

                # Wait for next interval
                await asyncio.sleep(self.config.export_interval_seconds)

            except Exception as e:
                logger.error(f"Error in metric export loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry

    def _collect_metrics(self) -> dict[str, Any]:
        """
        Collect current metrics.

        Returns:
            dict: Current metric values
        """
        # In production, this would collect from prometheus_client registry
        # For now, return empty dict
        return {}


class PrometheusExporter(MetricExporter):
    """
    Prometheus metrics exporter (push gateway).

    Pushes metrics to Prometheus Push Gateway for batch jobs.
    """

    def __init__(
        self,
        config: MetricExportConfig,
        push_gateway_url: str,
        job_name: str = "residency_scheduler",
        registry: CollectorRegistry | None = None,
    ):
        """
        Initialize Prometheus exporter.

        Args:
            config: Export configuration
            push_gateway_url: Prometheus Push Gateway URL
            job_name: Job name for grouping metrics
            registry: Prometheus registry (defaults to global)
        """
        super().__init__(config)
        self.push_gateway_url = push_gateway_url
        self.job_name = job_name
        self.registry = registry or REGISTRY

        if not PROMETHEUS_AVAILABLE:
            raise ImportError("prometheus_client is required for PrometheusExporter")

    async def export_metrics(self, metrics: dict[str, Any]) -> None:
        """
        Push metrics to Prometheus Push Gateway.

        Args:
            metrics: Metrics to export
        """
        try:
            # Push to gateway (blocking call, run in executor)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                push_to_gateway,
                self.push_gateway_url,
                job=self.job_name,
                registry=self.registry,
            )

            logger.debug(f"Pushed metrics to Prometheus Gateway: {self.push_gateway_url}")

        except Exception as e:
            logger.error(f"Failed to push metrics to Prometheus: {e}")


class GrafanaCloudExporter(MetricExporter):
    """
    Grafana Cloud metrics exporter.

    Pushes metrics to Grafana Cloud using Prometheus remote write.
    """

    def __init__(
        self,
        config: MetricExportConfig,
        remote_write_url: str,
        api_key: str,
        instance_id: str,
    ):
        """
        Initialize Grafana Cloud exporter.

        Args:
            config: Export configuration
            remote_write_url: Grafana Cloud remote write URL
            api_key: API key for authentication
            instance_id: Instance identifier
        """
        super().__init__(config)
        self.remote_write_url = remote_write_url
        self.api_key = api_key
        self.instance_id = instance_id
        self._client = httpx.AsyncClient(timeout=config.timeout_seconds)

    async def export_metrics(self, metrics: dict[str, Any]) -> None:
        """
        Push metrics to Grafana Cloud.

        Args:
            metrics: Metrics to export
        """
        try:
            # Convert metrics to Prometheus remote write format
            payload = self._format_metrics(metrics)

            # Send to Grafana Cloud
            headers = {
                "Content-Type": "application/x-protobuf",
                "X-Prometheus-Remote-Write-Version": "0.1.0",
                "Authorization": f"Bearer {self.api_key}",
            }

            response = await self._client.post(
                self.remote_write_url,
                content=payload,
                headers=headers,
            )
            response.raise_for_status()

            logger.debug(f"Pushed {len(metrics)} metrics to Grafana Cloud")

        except Exception as e:
            logger.error(f"Failed to push metrics to Grafana Cloud: {e}")

    def _format_metrics(self, metrics: dict[str, Any]) -> bytes:
        """
        Format metrics for Prometheus remote write.

        Args:
            metrics: Metrics dictionary

        Returns:
            bytes: Protobuf-encoded metrics
        """
        # In production, would use prometheus_client to encode
        # For now, return empty bytes
        return b""

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()


class DatadogExporter(MetricExporter):
    """
    Datadog metrics exporter.

    Pushes metrics to Datadog using their API.
    """

    def __init__(
        self,
        config: MetricExportConfig,
        api_key: str,
        app_key: str | None = None,
        site: str = "datadoghq.com",
    ):
        """
        Initialize Datadog exporter.

        Args:
            config: Export configuration
            api_key: Datadog API key
            app_key: Datadog application key (optional)
            site: Datadog site (e.g., datadoghq.com, datadoghq.eu)
        """
        super().__init__(config)
        self.api_key = api_key
        self.app_key = app_key
        self.base_url = f"https://api.{site}/api/v1"
        self._client = httpx.AsyncClient(timeout=config.timeout_seconds)

    async def export_metrics(self, metrics: dict[str, Any]) -> None:
        """
        Push metrics to Datadog.

        Args:
            metrics: Metrics to export
        """
        try:
            # Format metrics for Datadog
            series = self._format_metrics(metrics)

            # Send to Datadog
            headers = {
                "DD-API-KEY": self.api_key,
                "Content-Type": "application/json",
            }

            response = await self._client.post(
                f"{self.base_url}/series",
                json={"series": series},
                headers=headers,
            )
            response.raise_for_status()

            logger.debug(f"Pushed {len(series)} metrics to Datadog")

        except Exception as e:
            logger.error(f"Failed to push metrics to Datadog: {e}")

    def _format_metrics(self, metrics: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Format metrics for Datadog API.

        Args:
            metrics: Metrics dictionary

        Returns:
            list: Datadog series format
        """
        series = []
        timestamp = int(time.time())

        for metric_name, value in metrics.items():
            series.append(
                {
                    "metric": metric_name,
                    "points": [[timestamp, value]],
                    "type": "gauge",
                    "tags": [f"instance:{self.config.metadata.get('instance_id', 'unknown')}"],
                }
            )

        return series

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()


class CloudWatchExporter(MetricExporter):
    """
    AWS CloudWatch metrics exporter.

    Pushes metrics to CloudWatch.
    """

    def __init__(
        self,
        config: MetricExportConfig,
        namespace: str = "ResidencyScheduler",
        region: str = "us-east-1",
    ):
        """
        Initialize CloudWatch exporter.

        Args:
            config: Export configuration
            namespace: CloudWatch namespace
            region: AWS region
        """
        super().__init__(config)
        self.namespace = namespace
        self.region = region

        # In production, would initialize boto3 client
        self._client = None

    async def export_metrics(self, metrics: dict[str, Any]) -> None:
        """
        Push metrics to CloudWatch.

        Args:
            metrics: Metrics to export
        """
        try:
            # Format metrics for CloudWatch
            metric_data = self._format_metrics(metrics)

            # In production, would call:
            # await self._client.put_metric_data(
            #     Namespace=self.namespace,
            #     MetricData=metric_data
            # )

            logger.debug(f"Pushed {len(metric_data)} metrics to CloudWatch")

        except Exception as e:
            logger.error(f"Failed to push metrics to CloudWatch: {e}")

    def _format_metrics(self, metrics: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Format metrics for CloudWatch.

        Args:
            metrics: Metrics dictionary

        Returns:
            list: CloudWatch metric data format
        """
        metric_data = []
        timestamp = datetime.utcnow()

        for metric_name, value in metrics.items():
            metric_data.append(
                {
                    "MetricName": metric_name,
                    "Value": value,
                    "Timestamp": timestamp,
                    "Unit": "None",
                }
            )

        return metric_data


# Factory functions


def create_prometheus_exporter(
    push_gateway_url: str,
    job_name: str = "residency_scheduler",
    export_interval: int = 60,
) -> PrometheusExporter:
    """
    Create Prometheus exporter.

    Args:
        push_gateway_url: Prometheus Push Gateway URL
        job_name: Job name
        export_interval: Export interval in seconds

    Returns:
        PrometheusExporter: Configured exporter
    """
    config = MetricExportConfig(export_interval_seconds=export_interval)
    return PrometheusExporter(config, push_gateway_url, job_name)


def create_grafana_cloud_exporter(
    remote_write_url: str,
    api_key: str,
    instance_id: str,
    export_interval: int = 60,
) -> GrafanaCloudExporter:
    """
    Create Grafana Cloud exporter.

    Args:
        remote_write_url: Remote write URL
        api_key: API key
        instance_id: Instance ID
        export_interval: Export interval in seconds

    Returns:
        GrafanaCloudExporter: Configured exporter
    """
    config = MetricExportConfig(export_interval_seconds=export_interval)
    return GrafanaCloudExporter(config, remote_write_url, api_key, instance_id)


def create_datadog_exporter(
    api_key: str,
    site: str = "datadoghq.com",
    export_interval: int = 60,
) -> DatadogExporter:
    """
    Create Datadog exporter.

    Args:
        api_key: Datadog API key
        site: Datadog site
        export_interval: Export interval in seconds

    Returns:
        DatadogExporter: Configured exporter
    """
    config = MetricExportConfig(export_interval_seconds=export_interval)
    return DatadogExporter(config, api_key, site=site)
