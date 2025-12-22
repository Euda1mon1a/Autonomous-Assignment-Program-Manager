"""
Chaos engineering experiments for testing system resilience.

Implements controlled failure injection with safety mechanisms:
1. Blast radius control - Limit scope of affected components
2. SLO monitoring - Track service level objectives during experiments
3. Automatic rollback - Stop experiment if SLOs breach
4. Audit logging - Track all experiment execution

Inspired by:
- Netflix Chaos Monkey (random failure injection)
- LinkedIn Waterbear (dependency failure testing)
- Google DiRT (Disaster Recovery Testing)
- Amazon GameDays (controlled failure scenarios)
"""

import asyncio
import enum
import logging
import multiprocessing
import os
import random
import time
import uuid
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.types import GUID, JSONType

logger = logging.getLogger(__name__)

# Prometheus metrics (if available)
try:
    from prometheus_client import Counter, Gauge, Histogram

    PROMETHEUS_AVAILABLE = True

    chaos_experiments_total = Counter(
        "chaos_experiments_total",
        "Total chaos experiments executed",
        ["experiment_type", "status"],
    )

    chaos_injections_total = Counter(
        "chaos_injections_total",
        "Total chaos injections performed",
        ["injector_type"],
    )

    chaos_slo_breaches_total = Counter(
        "chaos_slo_breaches_total",
        "SLO breaches during chaos experiments",
        ["experiment_id", "slo_metric"],
    )

    chaos_rollbacks_total = Counter(
        "chaos_rollbacks_total",
        "Automatic rollbacks triggered",
        ["experiment_id", "reason"],
    )

    chaos_active_experiments = Gauge(
        "chaos_active_experiments",
        "Number of active chaos experiments",
    )

    chaos_injection_duration = Histogram(
        "chaos_injection_duration_seconds",
        "Duration of chaos injections",
        ["injector_type"],
    )

except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not available - chaos metrics disabled")


# =============================================================================
# Enums and Constants
# =============================================================================


class InjectorType(str, enum.Enum):
    """Types of chaos injectors."""

    LATENCY = "latency"
    ERROR = "error"
    CPU_STRESS = "cpu_stress"
    MEMORY_STRESS = "memory_stress"
    NETWORK_PARTITION = "network_partition"
    SERVICE_FAILURE = "service_failure"
    DATABASE_SLOWDOWN = "database_slowdown"
    CACHE_MISS = "cache_miss"


class ChaosExperimentStatus(str, enum.Enum):
    """Status of chaos experiment execution."""

    PENDING = "pending"  # Scheduled but not started
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Finished successfully
    ROLLED_BACK = "rolled_back"  # Stopped due to SLO breach
    FAILED = "failed"  # Technical failure
    CANCELLED = "cancelled"  # Manually stopped


class BlastRadiusScope(str, enum.Enum):
    """Scope of blast radius for chaos experiments."""

    SINGLE_REQUEST = "single_request"  # Single request only
    PERCENTAGE = "percentage"  # % of requests/operations
    SPECIFIC_USER = "specific_user"  # Specific user ID
    SPECIFIC_SERVICE = "specific_service"  # Specific service/component
    ZONE_ISOLATED = "zone_isolated"  # Within scheduling zone
    GLOBAL = "global"  # Entire system (use with caution!)


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class SLOThreshold:
    """Service Level Objective threshold for monitoring."""

    metric_name: str
    threshold_value: float
    comparison: str = "less_than"  # less_than, greater_than, equals
    breach_count_limit: int = 3  # Consecutive breaches before rollback
    description: str = ""

    def is_breached(self, current_value: float) -> bool:
        """
        Check if current value breaches this SLO.

        Args:
            current_value: Current metric value

        Returns:
            bool: True if SLO is breached
        """
        if self.comparison == "less_than":
            return current_value >= self.threshold_value
        elif self.comparison == "greater_than":
            return current_value <= self.threshold_value
        elif self.comparison == "equals":
            return abs(current_value - self.threshold_value) < 0.001
        return False


@dataclass
class ChaosExperimentConfig:
    """Configuration for a chaos experiment."""

    name: str
    description: str
    injector_type: InjectorType
    blast_radius: float = 0.1  # 0.0 to 1.0 (10% by default)
    blast_radius_scope: BlastRadiusScope = BlastRadiusScope.PERCENTAGE
    max_duration_minutes: int = 15
    auto_rollback: bool = True
    slo_thresholds: list[SLOThreshold] = field(default_factory=list)
    target_component: Optional[str] = None  # Specific component to target
    target_zone_id: Optional[uuid.UUID] = None  # Specific zone (for zone isolation)
    target_user_id: Optional[uuid.UUID] = None  # Specific user (for user isolation)
    injector_params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExperimentResult:
    """Result of chaos experiment execution."""

    experiment_id: uuid.UUID
    status: ChaosExperimentStatus
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_injections: int = 0
    successful_injections: int = 0
    failed_injections: int = 0
    slo_breaches: list[str] = field(default_factory=list)
    rollback_reason: Optional[str] = None
    observations: list[str] = field(default_factory=list)
    metrics_snapshot: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_minutes(self) -> float:
        """Get experiment duration in minutes."""
        if not self.ended_at:
            return 0.0
        delta = self.ended_at - self.started_at
        return delta.total_seconds() / 60

    @property
    def success_rate(self) -> float:
        """Get injection success rate."""
        if self.total_injections == 0:
            return 0.0
        return self.successful_injections / self.total_injections


# =============================================================================
# Database Models
# =============================================================================


class ChaosExperimentRecord(Base):
    """
    Database record for chaos experiments.

    Provides audit trail for all chaos engineering activities.
    """

    __tablename__ = "chaos_experiments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(String(1000))
    injector_type = Column(String(50), nullable=False)

    # Blast radius configuration
    blast_radius = Column(Float, nullable=False, default=0.1)
    blast_radius_scope = Column(String(50), nullable=False)
    target_component = Column(String(200))
    target_zone_id = Column(GUID())
    target_user_id = Column(GUID())

    # Execution tracking
    status = Column(String(50), nullable=False, default="pending")
    scheduled_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    max_duration_minutes = Column(Integer, nullable=False, default=15)

    # Safety configuration
    auto_rollback = Column(Boolean, nullable=False, default=True)
    slo_thresholds = Column(JSONType())

    # Results
    total_injections = Column(Integer, default=0)
    successful_injections = Column(Integer, default=0)
    failed_injections = Column(Integer, default=0)
    slo_breaches = Column(JSONType())
    rollback_reason = Column(String(500))

    # Data
    injector_params = Column(JSONType())
    observations = Column(JSONType())
    metrics_snapshot = Column(JSONType())
    # Map Python attr 'experiment_metadata' to DB column 'metadata' (reserved name workaround)
    experiment_metadata = Column('metadata', JSONType())

    # Authorization
    created_by = Column(String(100))
    approved_by = Column(String(100))

    def __repr__(self):
        return f"<ChaosExperiment(name='{self.name}', status='{self.status}')>"


# =============================================================================
# SLO Monitoring
# =============================================================================


class SLOMonitor:
    """
    Monitors Service Level Objectives during chaos experiments.

    Tracks metrics and triggers automatic rollback if SLOs are breached.
    """

    def __init__(self, thresholds: list[SLOThreshold]):
        """
        Initialize SLO monitor.

        Args:
            thresholds: List of SLO thresholds to monitor
        """
        self.thresholds = thresholds
        self.breach_counts: dict[str, int] = {t.metric_name: 0 for t in thresholds}
        self.breached_slos: list[str] = []

    def check_metric(self, metric_name: str, current_value: float) -> bool:
        """
        Check if a metric breaches its SLO threshold.

        Args:
            metric_name: Name of the metric
            current_value: Current metric value

        Returns:
            bool: True if SLO is breached and rollback should occur
        """
        for threshold in self.thresholds:
            if threshold.metric_name != metric_name:
                continue

            if threshold.is_breached(current_value):
                self.breach_counts[metric_name] += 1
                logger.warning(
                    f"SLO breach detected: {metric_name}={current_value} "
                    f"(threshold={threshold.threshold_value}, "
                    f"breaches={self.breach_counts[metric_name]}/{threshold.breach_count_limit})"
                )

                if self.breach_counts[metric_name] >= threshold.breach_count_limit:
                    self.breached_slos.append(metric_name)

                    if PROMETHEUS_AVAILABLE:
                        chaos_slo_breaches_total.labels(
                            experiment_id="current", slo_metric=metric_name
                        ).inc()

                    return True
            else:
                # Reset breach count if metric is healthy
                self.breach_counts[metric_name] = 0

        return False

    def get_breach_summary(self) -> str:
        """
        Get summary of SLO breaches.

        Returns:
            str: Human-readable summary
        """
        if not self.breached_slos:
            return "No SLO breaches"
        return f"SLO breaches: {', '.join(self.breached_slos)}"


# =============================================================================
# Chaos Injectors
# =============================================================================


class LatencyInjector:
    """
    Injects artificial latency into operations.

    Simulates slow network, database, or external service calls.
    """

    def __init__(
        self,
        min_ms: int = 100,
        max_ms: int = 1000,
        probability: float = 1.0,
        target_function: Optional[str] = None,
    ):
        """
        Initialize latency injector.

        Args:
            min_ms: Minimum latency in milliseconds
            max_ms: Maximum latency in milliseconds
            probability: Probability of injection (0.0 to 1.0)
            target_function: Optional specific function to target
        """
        self.min_ms = min_ms
        self.max_ms = max_ms
        self.probability = probability
        self.target_function = target_function
        self.active = False

    async def inject_async(self) -> None:
        """Inject latency asynchronously."""
        if not self.active or random.random() > self.probability:
            return

        latency_ms = random.randint(self.min_ms, self.max_ms)
        logger.debug(f"Injecting {latency_ms}ms latency")

        await asyncio.sleep(latency_ms / 1000.0)

        if PROMETHEUS_AVAILABLE:
            chaos_injections_total.labels(injector_type="latency").inc()

    def inject_sync(self) -> None:
        """Inject latency synchronously."""
        if not self.active or random.random() > self.probability:
            return

        latency_ms = random.randint(self.min_ms, self.max_ms)
        logger.debug(f"Injecting {latency_ms}ms latency")

        time.sleep(latency_ms / 1000.0)

        if PROMETHEUS_AVAILABLE:
            chaos_injections_total.labels(injector_type="latency").inc()

    @asynccontextmanager
    async def context_async(self):
        """Async context manager for latency injection."""
        self.active = True
        try:
            await self.inject_async()
            yield
        finally:
            self.active = False

    @contextmanager
    def context(self):
        """Sync context manager for latency injection."""
        self.active = True
        try:
            self.inject_sync()
            yield
        finally:
            self.active = False


class ErrorInjector:
    """
    Injects errors and exceptions into operations.

    Simulates transient failures, timeouts, and error conditions.
    """

    def __init__(
        self,
        error_type: type[Exception] = Exception,
        error_message: str = "Chaos engineering: injected error",
        probability: float = 0.1,
        target_operations: Optional[list[str]] = None,
    ):
        """
        Initialize error injector.

        Args:
            error_type: Type of exception to raise
            error_message: Error message
            probability: Probability of injection (0.0 to 1.0)
            target_operations: Optional list of operation names to target
        """
        self.error_type = error_type
        self.error_message = error_message
        self.probability = probability
        self.target_operations = target_operations or []
        self.active = False

    def should_inject(self, operation_name: Optional[str] = None) -> bool:
        """
        Determine if error should be injected.

        Args:
            operation_name: Name of the operation being performed

        Returns:
            bool: True if error should be injected
        """
        if not self.active:
            return False

        if self.target_operations and operation_name not in self.target_operations:
            return False

        return random.random() < self.probability

    def inject(self, operation_name: Optional[str] = None) -> None:
        """
        Inject an error if conditions are met.

        Args:
            operation_name: Name of the operation being performed

        Raises:
            Exception: The configured error type
        """
        if self.should_inject(operation_name):
            logger.warning(f"Injecting error: {self.error_message}")

            if PROMETHEUS_AVAILABLE:
                chaos_injections_total.labels(injector_type="error").inc()

            raise self.error_type(self.error_message)

    @contextmanager
    def context(self, operation_name: Optional[str] = None):
        """Context manager for error injection."""
        self.active = True
        try:
            self.inject(operation_name)
            yield
        finally:
            self.active = False


class CPUStressor:
    """
    Simulates CPU stress by performing intensive calculations.

    Uses multiprocessing to consume CPU resources.
    """

    def __init__(
        self,
        cpu_percent: int = 50,
        duration_seconds: int = 10,
        num_processes: Optional[int] = None,
    ):
        """
        Initialize CPU stressor.

        Args:
            cpu_percent: Target CPU utilization percentage (0-100)
            duration_seconds: Duration of stress test
            num_processes: Number of processes to spawn (default: CPU count)
        """
        self.cpu_percent = min(100, max(0, cpu_percent))
        self.duration_seconds = duration_seconds
        self.num_processes = num_processes or multiprocessing.cpu_count()
        self.processes: list[multiprocessing.Process] = []
        self.active = False

    @staticmethod
    def _burn_cpu(duration: int, work_ratio: float) -> None:
        """
        Burn CPU cycles.

        Args:
            duration: Duration in seconds
            work_ratio: Ratio of work to sleep time
        """
        end_time = time.time() + duration
        while time.time() < end_time:
            # Work period
            work_start = time.time()
            while time.time() - work_start < work_ratio:
                _ = sum(i * i for i in range(1000))
            # Sleep period
            if work_ratio < 1.0:
                time.sleep(1.0 - work_ratio)

    def start(self) -> None:
        """Start CPU stress test."""
        if self.active:
            logger.warning("CPU stressor already active")
            return

        work_ratio = self.cpu_percent / 100.0
        logger.info(
            f"Starting CPU stress: {self.cpu_percent}% for {self.duration_seconds}s "
            f"using {self.num_processes} processes"
        )

        self.active = True

        for _ in range(self.num_processes):
            process = multiprocessing.Process(
                target=self._burn_cpu,
                args=(self.duration_seconds, work_ratio),
            )
            process.start()
            self.processes.append(process)

        if PROMETHEUS_AVAILABLE:
            chaos_injections_total.labels(injector_type="cpu_stress").inc()

    def stop(self) -> None:
        """Stop CPU stress test."""
        if not self.active:
            return

        logger.info("Stopping CPU stress")

        for process in self.processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)

        self.processes.clear()
        self.active = False

    @contextmanager
    def context(self):
        """Context manager for CPU stress."""
        self.start()
        try:
            yield
        finally:
            self.stop()


class MemoryStressor:
    """
    Simulates memory pressure by allocating large buffers.

    Allocates memory to test behavior under memory constraints.
    """

    def __init__(self, size_mb: int = 100, duration_seconds: int = 10):
        """
        Initialize memory stressor.

        Args:
            size_mb: Amount of memory to allocate in MB
            duration_seconds: Duration to hold memory
        """
        self.size_mb = size_mb
        self.duration_seconds = duration_seconds
        self.buffers: list[bytearray] = []
        self.active = False

    def allocate(self) -> None:
        """Allocate memory."""
        if self.active:
            logger.warning("Memory stressor already active")
            return

        logger.info(f"Allocating {self.size_mb}MB memory for {self.duration_seconds}s")

        self.active = True

        try:
            # Allocate memory in chunks
            chunk_size = 1024 * 1024  # 1MB chunks
            for _ in range(self.size_mb):
                buffer = bytearray(chunk_size)
                # Touch the memory to ensure it's actually allocated
                buffer[0] = 1
                buffer[-1] = 1
                self.buffers.append(buffer)

            if PROMETHEUS_AVAILABLE:
                chaos_injections_total.labels(injector_type="memory_stress").inc()

        except MemoryError as e:
            logger.error(f"Failed to allocate memory: {e}")
            self.release()
            raise

    def release(self) -> None:
        """Release allocated memory."""
        if not self.active:
            return

        logger.info(f"Releasing {self.size_mb}MB memory")
        self.buffers.clear()
        self.active = False

    @contextmanager
    def context(self):
        """Context manager for memory stress."""
        self.allocate()
        try:
            time.sleep(self.duration_seconds)
            yield
        finally:
            self.release()


class ResourceStressor:
    """
    Combined CPU and memory stress simulator.

    Convenience class for applying multiple resource stressors.
    """

    def __init__(
        self,
        cpu_percent: int = 0,
        memory_mb: int = 0,
        duration_seconds: int = 10,
    ):
        """
        Initialize resource stressor.

        Args:
            cpu_percent: CPU utilization percentage (0 to disable)
            memory_mb: Memory to allocate in MB (0 to disable)
            duration_seconds: Duration of stress test
        """
        self.cpu_stressor = (
            CPUStressor(cpu_percent, duration_seconds) if cpu_percent > 0 else None
        )
        self.memory_stressor = (
            MemoryStressor(memory_mb, duration_seconds) if memory_mb > 0 else None
        )

    @contextmanager
    def context(self):
        """Context manager for combined resource stress."""
        try:
            if self.cpu_stressor:
                self.cpu_stressor.start()
            if self.memory_stressor:
                self.memory_stressor.allocate()
            yield
        finally:
            if self.cpu_stressor:
                self.cpu_stressor.stop()
            if self.memory_stressor:
                self.memory_stressor.release()


class NetworkPartitioner:
    """
    Simulates network partitions and connectivity issues.

    Blocks communication with specific services or endpoints.
    """

    def __init__(
        self,
        blocked_services: list[str],
        probability: float = 1.0,
    ):
        """
        Initialize network partitioner.

        Args:
            blocked_services: List of service names to block
            probability: Probability of blocking (0.0 to 1.0)
        """
        self.blocked_services = set(blocked_services)
        self.probability = probability
        self.active = False

    def is_blocked(self, service_name: str) -> bool:
        """
        Check if service is blocked.

        Args:
            service_name: Name of the service

        Returns:
            bool: True if service is blocked
        """
        if not self.active:
            return False

        if service_name not in self.blocked_services:
            return False

        if random.random() > self.probability:
            return False

        logger.warning(f"Network partition: blocking {service_name}")

        if PROMETHEUS_AVAILABLE:
            chaos_injections_total.labels(injector_type="network_partition").inc()

        return True

    @contextmanager
    def context(self):
        """Context manager for network partition."""
        self.active = True
        try:
            yield
        finally:
            self.active = False


class ServiceFailureSimulator:
    """
    Simulates failures of dependent services.

    Useful for testing graceful degradation and circuit breakers.
    """

    def __init__(
        self,
        service_name: str,
        failure_mode: str = "unavailable",
        probability: float = 1.0,
        latency_ms: int = 0,
    ):
        """
        Initialize service failure simulator.

        Args:
            service_name: Name of the service to simulate
            failure_mode: Type of failure (unavailable, slow, error)
            probability: Probability of failure (0.0 to 1.0)
            latency_ms: Latency to add if mode is 'slow'
        """
        self.service_name = service_name
        self.failure_mode = failure_mode
        self.probability = probability
        self.latency_ms = latency_ms
        self.active = False

    async def simulate(self) -> None:
        """
        Simulate service failure.

        Raises:
            ConnectionError: If failure mode is 'unavailable'
            TimeoutError: If failure mode is 'timeout'
            Exception: If failure mode is 'error'
        """
        if not self.active or random.random() > self.probability:
            return

        logger.warning(
            f"Simulating {self.failure_mode} failure for {self.service_name}"
        )

        if PROMETHEUS_AVAILABLE:
            chaos_injections_total.labels(injector_type="service_failure").inc()

        if self.failure_mode == "unavailable":
            raise ConnectionError(f"Service {self.service_name} is unavailable")
        elif self.failure_mode == "timeout":
            await asyncio.sleep(30)  # Long delay to simulate timeout
            raise TimeoutError(f"Service {self.service_name} timed out")
        elif self.failure_mode == "slow":
            await asyncio.sleep(self.latency_ms / 1000.0)
        elif self.failure_mode == "error":
            raise Exception(f"Service {self.service_name} returned error")

    @asynccontextmanager
    async def context(self):
        """Async context manager for service failure."""
        self.active = True
        try:
            yield
        finally:
            self.active = False


# =============================================================================
# Chaos Experiment Orchestration
# =============================================================================


class ChaosExperiment:
    """
    Orchestrates chaos engineering experiments with safety controls.

    Manages experiment lifecycle, blast radius, and automatic rollback.
    """

    def __init__(
        self,
        config: ChaosExperimentConfig,
        db: Optional[Session] = None,
    ):
        """
        Initialize chaos experiment.

        Args:
            config: Experiment configuration
            db: Database session for persistence
        """
        self.config = config
        self.db = db
        self.experiment_id = uuid.uuid4()
        self.status = ChaosExperimentStatus.PENDING
        self.slo_monitor = SLOMonitor(config.slo_thresholds)
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None
        self.observations: list[str] = []
        self.injection_count = 0
        self.successful_injections = 0
        self.failed_injections = 0
        self._stop_requested = False

    def should_apply_to_request(
        self,
        user_id: Optional[uuid.UUID] = None,
        component: Optional[str] = None,
        zone_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """
        Determine if chaos should be applied to a specific request.

        Implements blast radius control based on scope configuration.

        Args:
            user_id: User making the request
            component: Component being accessed
            zone_id: Scheduling zone

        Returns:
            bool: True if chaos should be applied
        """
        if self.status != ChaosExperimentStatus.RUNNING:
            return False

        scope = self.config.blast_radius_scope

        # Scope-based filtering
        if scope == BlastRadiusScope.SPECIFIC_USER:
            if user_id != self.config.target_user_id:
                return False
        elif scope == BlastRadiusScope.SPECIFIC_SERVICE:
            if component != self.config.target_component:
                return False
        elif scope == BlastRadiusScope.ZONE_ISOLATED:
            if zone_id != self.config.target_zone_id:
                return False
        elif scope == BlastRadiusScope.PERCENTAGE:
            # Random sampling based on blast radius percentage
            if random.random() > self.config.blast_radius:
                return False

        return True

    def add_observation(self, observation: str) -> None:
        """
        Add an observation to the experiment log.

        Args:
            observation: Human-readable observation
        """
        timestamp = datetime.utcnow().isoformat()
        self.observations.append(f"[{timestamp}] {observation}")
        logger.info(f"Chaos observation: {observation}")

    def check_slo(self, metric_name: str, value: float) -> None:
        """
        Check SLO and trigger rollback if breached.

        Args:
            metric_name: Name of the metric
            value: Current metric value
        """
        if not self.config.auto_rollback:
            return

        if self.slo_monitor.check_metric(metric_name, value):
            reason = f"SLO breach: {metric_name}={value}"
            self.add_observation(reason)
            self.rollback(reason)

    def rollback(self, reason: str) -> None:
        """
        Stop experiment due to SLO breach or other issue.

        Args:
            reason: Reason for rollback
        """
        if self.status != ChaosExperimentStatus.RUNNING:
            return

        logger.warning(f"Rolling back chaos experiment: {reason}")
        self._stop_requested = True
        self.status = ChaosExperimentStatus.ROLLED_BACK

        if PROMETHEUS_AVAILABLE:
            chaos_rollbacks_total.labels(
                experiment_id=str(self.experiment_id), reason=reason[:50]
            ).inc()

    def start(self) -> None:
        """Start the chaos experiment."""
        if self.status != ChaosExperimentStatus.PENDING:
            logger.warning(f"Cannot start experiment in status: {self.status}")
            return

        logger.info(
            f"Starting chaos experiment: {self.config.name} "
            f"(type={self.config.injector_type}, "
            f"blast_radius={self.config.blast_radius:.1%})"
        )

        self.status = ChaosExperimentStatus.RUNNING
        self.started_at = datetime.utcnow()

        if PROMETHEUS_AVAILABLE:
            chaos_active_experiments.inc()
            chaos_experiments_total.labels(
                experiment_type=self.config.injector_type, status="started"
            ).inc()

        # Persist to database if session provided
        if self.db:
            self._save_to_db()

    def stop(self) -> ExperimentResult:
        """
        Stop the chaos experiment and return results.

        Returns:
            ExperimentResult: Experiment results
        """
        if self.status not in [
            ChaosExperimentStatus.RUNNING,
            ChaosExperimentStatus.ROLLED_BACK,
        ]:
            logger.warning(f"Cannot stop experiment in status: {self.status}")

        self.ended_at = datetime.utcnow()

        if self.status == ChaosExperimentStatus.RUNNING:
            self.status = ChaosExperimentStatus.COMPLETED

        logger.info(
            f"Stopped chaos experiment: {self.config.name} "
            f"(status={self.status}, "
            f"injections={self.successful_injections}/{self.injection_count})"
        )

        if PROMETHEUS_AVAILABLE:
            chaos_active_experiments.dec()
            chaos_experiments_total.labels(
                experiment_type=self.config.injector_type, status=self.status
            ).inc()

        result = ExperimentResult(
            experiment_id=self.experiment_id,
            status=self.status,
            started_at=self.started_at or datetime.utcnow(),
            ended_at=self.ended_at,
            total_injections=self.injection_count,
            successful_injections=self.successful_injections,
            failed_injections=self.failed_injections,
            slo_breaches=self.slo_monitor.breached_slos,
            rollback_reason=self.slo_monitor.get_breach_summary()
            if self.status == ChaosExperimentStatus.ROLLED_BACK
            else None,
            observations=self.observations,
        )

        # Persist to database
        if self.db:
            self._update_db(result)

        return result

    def _save_to_db(self) -> None:
        """Save experiment to database."""
        if not self.db:
            return

        try:
            record = ChaosExperimentRecord(
                id=self.experiment_id,
                name=self.config.name,
                description=self.config.description,
                injector_type=self.config.injector_type,
                blast_radius=self.config.blast_radius,
                blast_radius_scope=self.config.blast_radius_scope,
                target_component=self.config.target_component,
                target_zone_id=self.config.target_zone_id,
                target_user_id=self.config.target_user_id,
                status=self.status,
                scheduled_at=datetime.utcnow(),
                started_at=self.started_at,
                max_duration_minutes=self.config.max_duration_minutes,
                auto_rollback=self.config.auto_rollback,
                slo_thresholds=[
                    {
                        "metric_name": t.metric_name,
                        "threshold_value": t.threshold_value,
                        "comparison": t.comparison,
                    }
                    for t in self.config.slo_thresholds
                ],
                injector_params=self.config.injector_params,
                metadata=self.config.metadata,
            )

            self.db.add(record)
            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to save experiment to DB: {e}")
            self.db.rollback()

    def _update_db(self, result: ExperimentResult) -> None:
        """
        Update experiment in database with results.

        Args:
            result: Experiment results
        """
        if not self.db:
            return

        try:
            record = (
                self.db.query(ChaosExperimentRecord)
                .filter(ChaosExperimentRecord.id == self.experiment_id)
                .first()
            )

            if record:
                record.status = result.status
                record.ended_at = result.ended_at
                record.total_injections = result.total_injections
                record.successful_injections = result.successful_injections
                record.failed_injections = result.failed_injections
                record.slo_breaches = result.slo_breaches
                record.rollback_reason = result.rollback_reason
                record.observations = result.observations
                record.metrics_snapshot = result.metrics_snapshot

                self.db.commit()

        except Exception as e:
            logger.error(f"Failed to update experiment in DB: {e}")
            self.db.rollback()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False


# =============================================================================
# Experiment Scheduler
# =============================================================================


class ChaosExperimentScheduler:
    """
    Schedules and manages chaos experiments.

    Supports scheduled experiments and experiment campaigns.
    """

    def __init__(self, db: Session):
        """
        Initialize scheduler.

        Args:
            db: Database session
        """
        self.db = db
        self.active_experiments: dict[uuid.UUID, ChaosExperiment] = {}

    def schedule_experiment(
        self,
        config: ChaosExperimentConfig,
        scheduled_time: datetime,
    ) -> uuid.UUID:
        """
        Schedule a chaos experiment for future execution.

        Args:
            config: Experiment configuration
            scheduled_time: When to run the experiment

        Returns:
            uuid.UUID: Experiment ID
        """
        experiment = ChaosExperiment(config, self.db)
        experiment_id = experiment.experiment_id

        logger.info(
            f"Scheduled chaos experiment {config.name} for {scheduled_time.isoformat()}"
        )

        # Save to database with scheduled status
        experiment._save_to_db()

        return experiment_id

    def start_experiment(self, experiment_id: uuid.UUID) -> ChaosExperiment:
        """
        Start a scheduled experiment.

        Args:
            experiment_id: Experiment ID

        Returns:
            ChaosExperiment: Started experiment

        Raises:
            ValueError: If experiment not found or already running
        """
        if experiment_id in self.active_experiments:
            raise ValueError(f"Experiment {experiment_id} is already running")

        # Load from database
        record = (
            self.db.query(ChaosExperimentRecord)
            .filter(ChaosExperimentRecord.id == experiment_id)
            .first()
        )

        if not record:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Reconstruct config
        config = ChaosExperimentConfig(
            name=record.name,
            description=record.description or "",
            injector_type=InjectorType(record.injector_type),
            blast_radius=record.blast_radius,
            blast_radius_scope=BlastRadiusScope(record.blast_radius_scope),
            max_duration_minutes=record.max_duration_minutes,
            auto_rollback=record.auto_rollback,
            target_component=record.target_component,
            target_zone_id=record.target_zone_id,
            target_user_id=record.target_user_id,
            injector_params=record.injector_params or {},
            metadata=record.metadata or {},
        )

        experiment = ChaosExperiment(config, self.db)
        experiment.experiment_id = experiment_id
        experiment.start()

        self.active_experiments[experiment_id] = experiment

        return experiment

    def stop_experiment(self, experiment_id: uuid.UUID) -> ExperimentResult:
        """
        Stop a running experiment.

        Args:
            experiment_id: Experiment ID

        Returns:
            ExperimentResult: Experiment results

        Raises:
            ValueError: If experiment not found or not running
        """
        if experiment_id not in self.active_experiments:
            raise ValueError(f"Experiment {experiment_id} is not running")

        experiment = self.active_experiments[experiment_id]
        result = experiment.stop()

        del self.active_experiments[experiment_id]

        return result

    def get_active_experiments(self) -> list[ChaosExperiment]:
        """
        Get all currently active experiments.

        Returns:
            list[ChaosExperiment]: Active experiments
        """
        return list(self.active_experiments.values())

    def cleanup_expired_experiments(self) -> int:
        """
        Stop experiments that have exceeded max duration.

        Returns:
            int: Number of experiments stopped
        """
        stopped_count = 0
        current_time = datetime.utcnow()

        for experiment_id, experiment in list(self.active_experiments.items()):
            if not experiment.started_at:
                continue

            max_duration = timedelta(minutes=experiment.config.max_duration_minutes)
            elapsed = current_time - experiment.started_at

            if elapsed > max_duration:
                logger.warning(
                    f"Stopping experiment {experiment.config.name} - "
                    f"exceeded max duration of {experiment.config.max_duration_minutes}m"
                )
                experiment.rollback("Max duration exceeded")
                experiment.stop()
                del self.active_experiments[experiment_id]
                stopped_count += 1

        return stopped_count
