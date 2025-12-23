"""
Custom Prometheus Metric Collectors.

Provides custom collectors for system resources and application-specific metrics
that need periodic collection or complex calculation.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - system metrics disabled")

try:
    from prometheus_client.registry import Collector

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Stub Collector for when prometheus is not available
    class Collector:  # type: ignore
        """Stub Collector class."""

        pass


class SystemResourceCollector(Collector):
    """
    Custom collector for system resource metrics.

    Collects:
    - CPU usage (overall and per-core)
    - Memory usage (RSS, VMS, available)
    - Disk usage and I/O
    - Network I/O
    - Open file descriptors
    - Process count

    This collector is called by Prometheus during scrape, so metrics
    are always current without needing background updates.
    """

    def __init__(self, process: Optional["psutil.Process"] = None):
        """
        Initialize system resource collector.

        Args:
            process: psutil.Process instance (defaults to current process)
        """
        if not PSUTIL_AVAILABLE:
            logger.warning("SystemResourceCollector disabled - psutil not available")
            self._enabled = False
            return

        self._enabled = True
        self._process = process or psutil.Process()
        logger.info("SystemResourceCollector initialized")

    def collect(self):
        """
        Collect system resource metrics.

        This method is called by Prometheus during each scrape.

        Yields:
            Metric families for system resources
        """
        if not self._enabled:
            return

        try:
            # Import here to avoid issues if prometheus_client not available
            from prometheus_client.core import GaugeMetricFamily

            # ================================================================
            # CPU METRICS
            # ================================================================

            # Overall CPU usage
            cpu_percent = self._process.cpu_percent(interval=0.1)
            yield GaugeMetricFamily(
                "process_cpu_usage_percent",
                "Process CPU usage percentage",
                value=cpu_percent,
            )

            # System-wide CPU
            system_cpu = psutil.cpu_percent(interval=0.1, percpu=False)
            yield GaugeMetricFamily(
                "system_cpu_usage_percent",
                "System-wide CPU usage percentage",
                value=system_cpu,
            )

            # Per-core CPU usage
            cpu_percents = psutil.cpu_percent(interval=0.1, percpu=True)
            cpu_core_metric = GaugeMetricFamily(
                "system_cpu_core_usage_percent",
                "CPU usage per core",
                labels=["core"],
            )
            for i, percent in enumerate(cpu_percents):
                cpu_core_metric.add_metric([str(i)], percent)
            yield cpu_core_metric

            # CPU count
            yield GaugeMetricFamily(
                "system_cpu_count",
                "Number of CPU cores",
                value=psutil.cpu_count(),
            )

            # ================================================================
            # MEMORY METRICS
            # ================================================================

            # Process memory
            mem_info = self._process.memory_info()
            yield GaugeMetricFamily(
                "process_memory_rss_bytes",
                "Process resident set size (RSS) in bytes",
                value=mem_info.rss,
            )

            yield GaugeMetricFamily(
                "process_memory_vms_bytes",
                "Process virtual memory size (VMS) in bytes",
                value=mem_info.vms,
            )

            # Process memory percent
            mem_percent = self._process.memory_percent()
            yield GaugeMetricFamily(
                "process_memory_usage_percent",
                "Process memory usage as percentage of total RAM",
                value=mem_percent,
            )

            # System memory
            virtual_mem = psutil.virtual_memory()
            yield GaugeMetricFamily(
                "system_memory_total_bytes",
                "Total system memory in bytes",
                value=virtual_mem.total,
            )

            yield GaugeMetricFamily(
                "system_memory_available_bytes",
                "Available system memory in bytes",
                value=virtual_mem.available,
            )

            yield GaugeMetricFamily(
                "system_memory_used_bytes",
                "Used system memory in bytes",
                value=virtual_mem.used,
            )

            yield GaugeMetricFamily(
                "system_memory_usage_percent",
                "System memory usage percentage",
                value=virtual_mem.percent,
            )

            # Swap memory
            swap = psutil.swap_memory()
            yield GaugeMetricFamily(
                "system_swap_total_bytes",
                "Total swap memory in bytes",
                value=swap.total,
            )

            yield GaugeMetricFamily(
                "system_swap_used_bytes",
                "Used swap memory in bytes",
                value=swap.used,
            )

            yield GaugeMetricFamily(
                "system_swap_usage_percent",
                "Swap memory usage percentage",
                value=swap.percent,
            )

            # ================================================================
            # DISK METRICS
            # ================================================================

            # Disk usage for root partition
            disk_usage = psutil.disk_usage("/")
            disk_metric = GaugeMetricFamily(
                "system_disk_usage_percent",
                "Disk usage percentage by mount point",
                labels=["mount_point"],
            )
            disk_metric.add_metric(["/"], disk_usage.percent)
            yield disk_metric

            yield GaugeMetricFamily(
                "system_disk_total_bytes",
                "Total disk space in bytes",
                value=disk_usage.total,
            )

            yield GaugeMetricFamily(
                "system_disk_used_bytes",
                "Used disk space in bytes",
                value=disk_usage.used,
            )

            yield GaugeMetricFamily(
                "system_disk_free_bytes",
                "Free disk space in bytes",
                value=disk_usage.free,
            )

            # Disk I/O counters
            disk_io = psutil.disk_io_counters()
            if disk_io:
                yield GaugeMetricFamily(
                    "system_disk_read_bytes_total",
                    "Total bytes read from disk",
                    value=disk_io.read_bytes,
                )

                yield GaugeMetricFamily(
                    "system_disk_write_bytes_total",
                    "Total bytes written to disk",
                    value=disk_io.write_bytes,
                )

                yield GaugeMetricFamily(
                    "system_disk_read_count_total",
                    "Total number of read operations",
                    value=disk_io.read_count,
                )

                yield GaugeMetricFamily(
                    "system_disk_write_count_total",
                    "Total number of write operations",
                    value=disk_io.write_count,
                )

            # ================================================================
            # NETWORK METRICS
            # ================================================================

            net_io = psutil.net_io_counters()
            if net_io:
                yield GaugeMetricFamily(
                    "system_network_bytes_sent_total",
                    "Total bytes sent over network",
                    value=net_io.bytes_sent,
                )

                yield GaugeMetricFamily(
                    "system_network_bytes_recv_total",
                    "Total bytes received over network",
                    value=net_io.bytes_recv,
                )

                yield GaugeMetricFamily(
                    "system_network_packets_sent_total",
                    "Total packets sent over network",
                    value=net_io.packets_sent,
                )

                yield GaugeMetricFamily(
                    "system_network_packets_recv_total",
                    "Total packets received over network",
                    value=net_io.packets_recv,
                )

                yield GaugeMetricFamily(
                    "system_network_errors_in_total",
                    "Total incoming network errors",
                    value=net_io.errin,
                )

                yield GaugeMetricFamily(
                    "system_network_errors_out_total",
                    "Total outgoing network errors",
                    value=net_io.errout,
                )

            # ================================================================
            # PROCESS METRICS
            # ================================================================

            # Process threads
            num_threads = self._process.num_threads()
            yield GaugeMetricFamily(
                "process_threads_count",
                "Number of threads in the process",
                value=num_threads,
            )

            # Open file descriptors
            try:
                num_fds = (
                    self._process.num_fds() if hasattr(self._process, "num_fds") else 0
                )
                yield GaugeMetricFamily(
                    "process_open_fds_count",
                    "Number of open file descriptors",
                    value=num_fds,
                )
            except (AttributeError, NotImplementedError):
                # num_fds() not available on Windows
                pass

            # Process connections
            try:
                connections = len(self._process.connections())
                yield GaugeMetricFamily(
                    "process_connections_count",
                    "Number of open network connections",
                    value=connections,
                )
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            # Process uptime
            create_time = self._process.create_time()
            uptime = psutil.time.time() - create_time
            yield GaugeMetricFamily(
                "process_uptime_seconds",
                "Process uptime in seconds",
                value=uptime,
            )

            # ================================================================
            # SYSTEM INFO
            # ================================================================

            # System load average (Unix only)
            if hasattr(os, "getloadavg"):
                load_avg = os.getloadavg()
                load_metric = GaugeMetricFamily(
                    "system_load_average",
                    "System load average",
                    labels=["interval"],
                )
                load_metric.add_metric(["1m"], load_avg[0])
                load_metric.add_metric(["5m"], load_avg[1])
                load_metric.add_metric(["15m"], load_avg[2])
                yield load_metric

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}", exc_info=True)


class DatabasePoolCollector(Collector):
    """
    Custom collector for database connection pool metrics.

    Collects:
    - Pool size (min, max, current)
    - Active connections
    - Idle connections
    - Waiting connections
    - Connection timeouts

    This integrates with SQLAlchemy's connection pool statistics.
    """

    def __init__(self, engine=None):
        """
        Initialize database pool collector.

        Args:
            engine: SQLAlchemy engine instance
        """
        self._engine = engine
        self._enabled = engine is not None
        if self._enabled:
            logger.info("DatabasePoolCollector initialized")

    def collect(self):
        """
        Collect database pool metrics.

        Yields:
            Metric families for database connection pool
        """
        if not self._enabled or not PROMETHEUS_AVAILABLE:
            return

        try:
            from prometheus_client.core import GaugeMetricFamily

            pool = self._engine.pool

            # Pool size
            yield GaugeMetricFamily(
                "db_pool_size",
                "Database connection pool size",
                value=pool.size(),
            )

            # Checked out connections
            yield GaugeMetricFamily(
                "db_pool_checked_out",
                "Number of connections currently checked out",
                value=pool.checkedout(),
            )

            # Overflow (connections beyond pool size)
            if hasattr(pool, "overflow"):
                yield GaugeMetricFamily(
                    "db_pool_overflow",
                    "Number of connections beyond pool size",
                    value=pool.overflow(),
                )

            # Pool statistics
            if hasattr(pool, "_overflow"):
                yield GaugeMetricFamily(
                    "db_pool_overflow_count",
                    "Current number of overflow connections",
                    value=pool._overflow,
                )

        except Exception as e:
            logger.error(f"Error collecting database pool metrics: {e}", exc_info=True)


class ApplicationMetricsCollector(Collector):
    """
    Custom collector for application-specific metrics.

    Collects metrics that require database queries or complex calculations:
    - Total persons by role
    - Total assignments by status
    - Upcoming schedule blocks
    - Active swaps
    - Pending absences

    This collector should be registered carefully to avoid performance impact.
    """

    def __init__(self, db_session_factory=None):
        """
        Initialize application metrics collector.

        Args:
            db_session_factory: Factory function to create database sessions
        """
        self._db_session_factory = db_session_factory
        self._enabled = db_session_factory is not None
        if self._enabled:
            logger.info("ApplicationMetricsCollector initialized")

    def collect(self):
        """
        Collect application-specific metrics.

        Yields:
            Metric families for application state
        """
        if not self._enabled or not PROMETHEUS_AVAILABLE:
            return

        try:
            from prometheus_client.core import GaugeMetricFamily

            # This is a placeholder - actual implementation would query database
            # Disabled by default to avoid performance impact during scrapes

            yield GaugeMetricFamily(
                "app_collector_enabled",
                "Whether application metrics collector is enabled",
                value=1 if self._enabled else 0,
            )

        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}", exc_info=True)


def register_custom_collectors(registry=None, engine=None, db_session_factory=None):
    """
    Register all custom collectors with Prometheus registry.

    Args:
        registry: Prometheus registry (uses default if None)
        engine: SQLAlchemy engine for database pool metrics
        db_session_factory: Database session factory for app metrics

    Returns:
        List of registered collectors
    """
    if not PROMETHEUS_AVAILABLE:
        logger.warning("Cannot register collectors - prometheus_client not available")
        return []

    from prometheus_client import REGISTRY

    target_registry = registry or REGISTRY
    collectors = []

    # System resource collector
    if PSUTIL_AVAILABLE:
        system_collector = SystemResourceCollector()
        target_registry.register(system_collector)
        collectors.append(system_collector)
        logger.info("Registered SystemResourceCollector")

    # Database pool collector
    if engine:
        db_collector = DatabasePoolCollector(engine)
        target_registry.register(db_collector)
        collectors.append(db_collector)
        logger.info("Registered DatabasePoolCollector")

    # Application metrics collector (disabled by default for performance)
    # Uncomment to enable:
    # if db_session_factory:
    #     app_collector = ApplicationMetricsCollector(db_session_factory)
    #     target_registry.register(app_collector)
    #     collectors.append(app_collector)
    #     logger.info("Registered ApplicationMetricsCollector")

    return collectors
