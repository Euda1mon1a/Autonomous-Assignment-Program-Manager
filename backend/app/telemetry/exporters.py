"""
OpenTelemetry trace exporters.

Supports multiple exporter backends:
- Jaeger (via OTLP or legacy Jaeger protocol)
- Zipkin
- OTLP (OpenTelemetry Protocol)
- Console (for debugging)
"""

import logging
from enum import Enum

from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
)

logger = logging.getLogger(__name__)


class ExporterType(str, Enum):
    """Supported exporter types."""

    JAEGER = "jaeger"
    ZIPKIN = "zipkin"
    OTLP_HTTP = "otlp_http"
    OTLP_GRPC = "otlp_grpc"
    CONSOLE = "console"


class ExporterConfig:
    """
    Configuration for trace exporters.

    Attributes:
        exporter_type: Type of exporter to use
        endpoint: Exporter endpoint URL
        service_name: Service name for traces
        headers: Optional headers for authenticated exporters
        insecure: Whether to use insecure connection (HTTP instead of HTTPS)
        timeout: Export timeout in seconds
    """

    def __init__(
        self,
        exporter_type: ExporterType,
        endpoint: str | None = None,
        service_name: str = "residency-scheduler",
        headers: dict[str, str] | None = None,
        insecure: bool = True,
        timeout: int = 10,
    ) -> None:
        self.exporter_type = exporter_type
        self.endpoint = endpoint
        self.service_name = service_name
        self.headers = headers or {}
        self.insecure = insecure
        self.timeout = timeout


class ExporterFactory:
    """Factory for creating trace exporters."""

    @staticmethod
    def create_exporter(config: ExporterConfig) -> SpanExporter:
        """
        Create a span exporter based on configuration.

        Args:
            config: Exporter configuration

        Returns:
            SpanExporter: Configured span exporter

        Raises:
            ValueError: If exporter type is unsupported or configuration is invalid
        """
        if config.exporter_type == ExporterType.JAEGER:
            return ExporterFactory._create_jaeger_exporter(config)
        elif config.exporter_type == ExporterType.ZIPKIN:
            return ExporterFactory._create_zipkin_exporter(config)
        elif config.exporter_type == ExporterType.OTLP_HTTP:
            return ExporterFactory._create_otlp_http_exporter(config)
        elif config.exporter_type == ExporterType.OTLP_GRPC:
            return ExporterFactory._create_otlp_grpc_exporter(config)
        elif config.exporter_type == ExporterType.CONSOLE:
            return ConsoleSpanExporter()
        else:
            raise ValueError(f"Unsupported exporter type: {config.exporter_type}")

    @staticmethod
    def _create_jaeger_exporter(config: ExporterConfig) -> SpanExporter:
        """
        Create Jaeger exporter.

        Uses OTLP protocol by default (Jaeger v1.35+).
        Falls back to legacy Jaeger protocol if OTLP is not available.

        Args:
            config: Exporter configuration

        Returns:
            SpanExporter: Jaeger exporter

        Raises:
            ImportError: If required Jaeger exporter package is not installed
        """
        endpoint = config.endpoint or "http://localhost:4317"

        try:
            # Try OTLP exporter first (preferred for Jaeger 1.35+)
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            exporter = OTLPSpanExporter(
                endpoint=endpoint,
                headers=config.headers,
                insecure=config.insecure,
                timeout=config.timeout,
            )
            logger.info(f"Jaeger exporter created via OTLP: {endpoint}")
            return exporter

        except ImportError:
            # Fall back to legacy Jaeger exporter
            try:
                from opentelemetry.exporter.jaeger.thrift import JaegerExporter

                # Legacy Jaeger uses different endpoint format
                jaeger_endpoint = config.endpoint or "localhost"
                if "://" in jaeger_endpoint:
                    # Extract host from URL
                    jaeger_endpoint = jaeger_endpoint.split("://")[1].split(":")[0]

                exporter = JaegerExporter(
                    agent_host_name=jaeger_endpoint,
                    agent_port=6831,  # Default Jaeger agent port
                )
                logger.info(f"Jaeger exporter created (legacy): {jaeger_endpoint}")
                return exporter

            except ImportError as e:
                raise ImportError(
                    "Jaeger exporter not available. Install with: "
                    "pip install opentelemetry-exporter-jaeger or "
                    "pip install opentelemetry-exporter-otlp-proto-grpc"
                ) from e

    @staticmethod
    def _create_zipkin_exporter(config: ExporterConfig) -> SpanExporter:
        """
        Create Zipkin exporter.

        Args:
            config: Exporter configuration

        Returns:
            SpanExporter: Zipkin exporter

        Raises:
            ImportError: If Zipkin exporter package is not installed
        """
        try:
            from opentelemetry.exporter.zipkin.json import ZipkinExporter

            endpoint = config.endpoint or "http://localhost:9411/api/v2/spans"

            exporter = ZipkinExporter(
                endpoint=endpoint,
                timeout=config.timeout,
            )
            logger.info(f"Zipkin exporter created: {endpoint}")
            return exporter

        except ImportError as e:
            raise ImportError(
                "Zipkin exporter not available. Install with: "
                "pip install opentelemetry-exporter-zipkin-json"
            ) from e

    @staticmethod
    def _create_otlp_http_exporter(config: ExporterConfig) -> SpanExporter:
        """
        Create OTLP HTTP exporter.

        Args:
            config: Exporter configuration

        Returns:
            SpanExporter: OTLP HTTP exporter

        Raises:
            ImportError: If OTLP HTTP exporter package is not installed
        """
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            endpoint = config.endpoint or "http://localhost:4318/v1/traces"

            exporter = OTLPSpanExporter(
                endpoint=endpoint,
                headers=config.headers,
                timeout=config.timeout,
            )
            logger.info(f"OTLP HTTP exporter created: {endpoint}")
            return exporter

        except ImportError as e:
            raise ImportError(
                "OTLP HTTP exporter not available. Install with: "
                "pip install opentelemetry-exporter-otlp-proto-http"
            ) from e

    @staticmethod
    def _create_otlp_grpc_exporter(config: ExporterConfig) -> SpanExporter:
        """
        Create OTLP gRPC exporter.

        Args:
            config: Exporter configuration

        Returns:
            SpanExporter: OTLP gRPC exporter

        Raises:
            ImportError: If OTLP gRPC exporter package is not installed
        """
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            endpoint = config.endpoint or "http://localhost:4317"

            exporter = OTLPSpanExporter(
                endpoint=endpoint,
                headers=config.headers,
                insecure=config.insecure,
                timeout=config.timeout,
            )
            logger.info(f"OTLP gRPC exporter created: {endpoint}")
            return exporter

        except ImportError as e:
            raise ImportError(
                "OTLP gRPC exporter not available. Install with: "
                "pip install opentelemetry-exporter-otlp-proto-grpc"
            ) from e


def create_span_processor(
    exporter_config: ExporterConfig,
    max_queue_size: int = 2048,
    max_export_batch_size: int = 512,
    export_timeout_millis: int = 30000,
) -> BatchSpanProcessor:
    """
    Create a batch span processor with the specified exporter.

    Args:
        exporter_config: Exporter configuration
        max_queue_size: Maximum queue size for pending spans
        max_export_batch_size: Maximum batch size for export
        export_timeout_millis: Export timeout in milliseconds

    Returns:
        BatchSpanProcessor: Configured batch span processor
    """
    exporter = ExporterFactory.create_exporter(exporter_config)

    processor = BatchSpanProcessor(
        exporter,
        max_queue_size=max_queue_size,
        max_export_batch_size=max_export_batch_size,
        export_timeout_millis=export_timeout_millis,
    )

    logger.info(
        f"Span processor created: type={exporter_config.exporter_type}, "
        f"max_queue={max_queue_size}, max_batch={max_export_batch_size}"
    )

    return processor


def create_multi_exporter_processor(
    configs: list[ExporterConfig],
    **processor_kwargs,
) -> list[BatchSpanProcessor]:
    """
    Create multiple span processors for different exporters.

    This allows sending traces to multiple backends simultaneously
    (e.g., Jaeger for development + OTLP for production monitoring).

    Args:
        configs: List of exporter configurations
        **processor_kwargs: Additional arguments for BatchSpanProcessor

    Returns:
        list[BatchSpanProcessor]: List of configured processors
    """
    processors = []

    for config in configs:
        try:
            processor = create_span_processor(config, **processor_kwargs)
            processors.append(processor)
        except Exception as e:
            logger.error(
                f"Failed to create exporter {config.exporter_type}: {e}",
                exc_info=True,
            )

    logger.info(f"Created {len(processors)} span processor(s)")
    return processors

    # Convenience functions for common configurations


def create_jaeger_processor(
    endpoint: str = "http://localhost:4317",
    **kwargs,
) -> BatchSpanProcessor:
    """
    Create Jaeger span processor with default configuration.

    Args:
        endpoint: Jaeger endpoint URL
        **kwargs: Additional processor arguments

    Returns:
        BatchSpanProcessor: Configured processor
    """
    config = ExporterConfig(
        exporter_type=ExporterType.JAEGER,
        endpoint=endpoint,
    )
    return create_span_processor(config, **kwargs)


def create_zipkin_processor(
    endpoint: str = "http://localhost:9411/api/v2/spans",
    **kwargs,
) -> BatchSpanProcessor:
    """
    Create Zipkin span processor with default configuration.

    Args:
        endpoint: Zipkin endpoint URL
        **kwargs: Additional processor arguments

    Returns:
        BatchSpanProcessor: Configured processor
    """
    config = ExporterConfig(
        exporter_type=ExporterType.ZIPKIN,
        endpoint=endpoint,
    )
    return create_span_processor(config, **kwargs)


def create_otlp_processor(
    endpoint: str = "http://localhost:4318/v1/traces",
    use_grpc: bool = False,
    headers: dict[str, str] | None = None,
    **kwargs,
) -> BatchSpanProcessor:
    """
    Create OTLP span processor with default configuration.

    Args:
        endpoint: OTLP endpoint URL
        use_grpc: Use gRPC instead of HTTP
        headers: Optional headers (e.g., for authentication)
        **kwargs: Additional processor arguments

    Returns:
        BatchSpanProcessor: Configured processor
    """
    exporter_type = ExporterType.OTLP_GRPC if use_grpc else ExporterType.OTLP_HTTP

    config = ExporterConfig(
        exporter_type=exporter_type,
        endpoint=endpoint,
        headers=headers,
    )
    return create_span_processor(config, **kwargs)
