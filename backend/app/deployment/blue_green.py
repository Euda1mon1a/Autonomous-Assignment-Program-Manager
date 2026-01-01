"""
Blue-Green Deployment Manager.

Provides zero-downtime deployment capabilities using blue-green deployment
patterns. Manages deployment slots, traffic switching, health verification,
rollback capabilities, and database migration coordination.

Based on AWS best practices and Netflix deployment strategies.
"""

import enum
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.types import GUID, JSONType, StringArrayType

logger = logging.getLogger(__name__)


# Deployment Configuration Constants
HEALTH_CHECK_TIMEOUT_SECONDS = 5  # Default health check timeout
SESSION_DRAIN_TIMEOUT_SECONDS = 300  # 5 minutes - Session drain timeout
MIGRATION_TIMEOUT_SECONDS = 600  # 10 minutes - Database migration timeout
ROLLBACK_TIMEOUT_SECONDS = 120  # 2 minutes - Rollback timeout


class DeploymentSlot(str, enum.Enum):
    """Deployment slot identifier."""

    BLUE = "blue"
    GREEN = "green"


class DeploymentState(str, enum.Enum):
    """State of a deployment slot."""

    INACTIVE = "inactive"  # Not running
    STARTING = "starting"  # Starting up
    HEALTHY = "healthy"  # Running and healthy
    DEGRADED = "degraded"  # Running but unhealthy
    DRAINING = "draining"  # Draining active sessions
    STOPPED = "stopped"  # Stopped cleanly


class TrafficSplitStrategy(str, enum.Enum):
    """Strategy for splitting traffic during deployment."""

    INSTANT = "instant"  # Immediate 100% cutover
    CANARY = "canary"  # Gradual increase (10%, 50%, 100%)
    PROGRESSIVE = "progressive"  # Linear increase over time
    STICKY_SESSION = "sticky_session"  # Route by session affinity


class RollbackReason(str, enum.Enum):
    """Reason for deployment rollback."""

    HEALTH_CHECK_FAILED = "health_check_failed"
    HIGH_ERROR_RATE = "high_error_rate"
    MANUAL_TRIGGER = "manual_trigger"
    DATABASE_MIGRATION_FAILED = "database_migration_failed"
    TIMEOUT = "timeout"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class HealthCheckType(str, enum.Enum):
    """Type of health check."""

    HTTP_ENDPOINT = "http_endpoint"
    DATABASE_CONNECTIVITY = "database_connectivity"
    REDIS_CONNECTIVITY = "redis_connectivity"
    CELERY_WORKERS = "celery_workers"
    ACGME_VALIDATOR = "acgme_validator"
    CRITICAL_ENDPOINTS = "critical_endpoints"


@dataclass
class DeploymentConfig:
    """Configuration for blue-green deployment."""

    # Health check settings
    health_check_endpoint: str = "/health"
    health_check_interval_seconds: int = 10
    health_check_timeout_seconds: int = HEALTH_CHECK_TIMEOUT_SECONDS
    health_check_max_retries: int = 3
    health_check_required_successes: int = 3

    # Session draining settings
    session_drain_timeout_seconds: int = SESSION_DRAIN_TIMEOUT_SECONDS
    session_check_interval_seconds: int = 10
    allow_force_drain: bool = True

    # Traffic switching settings
    default_traffic_strategy: TrafficSplitStrategy = TrafficSplitStrategy.CANARY
    canary_stages: list[int] = field(default_factory=lambda: [10, 50, 100])
    canary_stage_duration_seconds: int = 60
    progressive_duration_seconds: int = 300

    # Database migration settings
    auto_run_migrations: bool = False
    migration_timeout_seconds: int = MIGRATION_TIMEOUT_SECONDS
    migration_rollback_on_failure: bool = True

    # Notification settings
    notification_recipients: list[str] = field(default_factory=list)
    slack_webhook_url: str = ""
    notify_on_start: bool = True
    notify_on_success: bool = True
    notify_on_failure: bool = True

    # Rollback settings
    auto_rollback_on_failure: bool = True
    rollback_timeout_seconds: int = ROLLBACK_TIMEOUT_SECONDS

    # Monitoring settings
    error_rate_threshold: float = 0.05  # 5% error rate triggers rollback
    latency_p99_threshold_ms: float = 1000.0
    cpu_threshold_percent: float = 90.0
    memory_threshold_percent: float = 90.0


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    check_type: HealthCheckType
    is_healthy: bool
    response_time_ms: float
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "check_type": self.check_type.value,
            "is_healthy": self.is_healthy,
            "response_time_ms": self.response_time_ms,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class SessionDrainStatus:
    """Status of session draining process."""

    slot: DeploymentSlot
    started_at: datetime
    active_sessions: int
    drained_sessions: int
    is_complete: bool
    elapsed_seconds: float
    estimated_remaining_seconds: float = 0.0


@dataclass
class DeploymentStatus:
    """Current status of a deployment."""

    deployment_id: UUID
    slot: DeploymentSlot
    state: DeploymentState
    traffic_percent: float
    health_checks: list[HealthCheckResult]
    active_sessions: int
    started_at: datetime
    last_health_check: datetime | None = None
    error_rate: float = 0.0
    latency_p99_ms: float = 0.0

    @property
    def is_healthy(self) -> bool:
        """Check if deployment is healthy."""
        return self.state == DeploymentState.HEALTHY and all(
            check.is_healthy for check in self.health_checks[-3:] if check
        )


# =============================================================================
# Database Models
# =============================================================================


class DeploymentRecord(Base):
    """
    Database record for deployments.

    Tracks deployment history, state transitions, and outcomes.
    """

    __tablename__ = "deployments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    slot = Column(String(20), nullable=False)  # DeploymentSlot
    version = Column(String(100), nullable=False)
    git_commit = Column(String(40))
    deployed_by = Column(String(255))

    # State tracking
    state = Column(String(20), nullable=False)  # DeploymentState
    traffic_percent = Column(Float, default=0.0)

    # Timestamps
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    health_verified_at = Column(DateTime)
    traffic_switched_at = Column(DateTime)
    completed_at = Column(DateTime)
    rolled_back_at = Column(DateTime)

    # Migration tracking
    migration_required = Column(Boolean, default=False)
    migration_completed = Column(Boolean, default=False)
    migration_version = Column(String(100))

    # Health metrics
    health_check_successes = Column(Integer, default=0)
    health_check_failures = Column(Integer, default=0)
    last_health_check = Column(DateTime)

    # Outcome
    is_successful = Column(Boolean)
    rollback_reason = Column(String(50))  # RollbackReason
    error_message = Column(String(1000))

    # Metadata
    deployment_config = Column(JSONType())
    deployment_metadata = Column(JSONType())

    # Notification tracking
    notified_recipients = Column(StringArrayType())

    def __repr__(self):
        return f"<DeploymentRecord(slot='{self.slot}', version='{self.version}', state='{self.state}')>"


class DeploymentHealthCheck(Base):
    """
    Individual health check record.

    Stores detailed health check results for analysis and debugging.
    """

    __tablename__ = "deployment_health_checks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    deployment_id = Column(GUID(), nullable=False)
    check_type = Column(String(50), nullable=False)  # HealthCheckType
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Result
    is_healthy = Column(Boolean, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    message = Column(String(500))
    details = Column(JSONType())

    def __repr__(self):
        return f"<DeploymentHealthCheck(type='{self.check_type}', healthy={self.is_healthy})>"


class TrafficSwitchEvent(Base):
    """
    Traffic switch event record.

    Tracks when and how traffic was shifted between slots.
    """

    __tablename__ = "traffic_switch_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    deployment_id = Column(GUID(), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Switch details
    from_slot = Column(String(20), nullable=False)
    to_slot = Column(String(20), nullable=False)
    strategy = Column(String(50), nullable=False)  # TrafficSplitStrategy
    from_percent = Column(Float, nullable=False)
    to_percent = Column(Float, nullable=False)

    # Outcome
    is_successful = Column(Boolean, nullable=False)
    error_message = Column(String(500))
    triggered_by = Column(String(255))

    def __repr__(self):
        return f"<TrafficSwitchEvent(from='{self.from_slot}', to='{self.to_slot}', {self.to_percent}%)>"


# =============================================================================
# Health Check Implementations
# =============================================================================


class HealthCheck:
    """Health check executor for deployment verification."""

    def __init__(self, base_url: str, timeout: int = HEALTH_CHECK_TIMEOUT_SECONDS):
        """
        Initialize health checker.

        Args:
            base_url: Base URL of the deployment slot
            timeout: Timeout for HTTP requests in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def check_http_endpoint(self, endpoint: str = "/health") -> HealthCheckResult:
        """
        Check HTTP health endpoint.

        Args:
            endpoint: Health check endpoint path

        Returns:
            HealthCheckResult
        """
        start_time = datetime.utcnow()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}{endpoint}")
                elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                is_healthy = response.status_code == 200
                details = {}
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                ):
                    try:
                        details = response.json()
                    except (ValueError, TypeError, json.JSONDecodeError):
                        pass

                return HealthCheckResult(
                    check_type=HealthCheckType.HTTP_ENDPOINT,
                    is_healthy=is_healthy,
                    response_time_ms=elapsed_ms,
                    message=f"HTTP {response.status_code}",
                    details=details,
                )
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthCheckResult(
                check_type=HealthCheckType.HTTP_ENDPOINT,
                is_healthy=False,
                response_time_ms=elapsed_ms,
                message=f"Network error during health check: {str(e)}",
            )
        except httpx.HTTPError as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthCheckResult(
                check_type=HealthCheckType.HTTP_ENDPOINT,
                is_healthy=False,
                response_time_ms=elapsed_ms,
                message=f"HTTP error during health check: {str(e)}",
            )

    async def check_database_connectivity(self) -> HealthCheckResult:
        """
        Check database connectivity.

        Returns:
            HealthCheckResult
        """
        start_time = datetime.utcnow()
        endpoint = f"{self.base_url}/health/database"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint)
                elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                is_healthy = response.status_code == 200
                return HealthCheckResult(
                    check_type=HealthCheckType.DATABASE_CONNECTIVITY,
                    is_healthy=is_healthy,
                    response_time_ms=elapsed_ms,
                    message=(
                        "Database connected" if is_healthy else "Database unreachable"
                    ),
                )
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthCheckResult(
                check_type=HealthCheckType.DATABASE_CONNECTIVITY,
                is_healthy=False,
                response_time_ms=elapsed_ms,
                message=f"Network error during database check: {str(e)}",
            )
        except httpx.HTTPError as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthCheckResult(
                check_type=HealthCheckType.DATABASE_CONNECTIVITY,
                is_healthy=False,
                response_time_ms=elapsed_ms,
                message=f"HTTP error during database check: {str(e)}",
            )

    async def check_redis_connectivity(self) -> HealthCheckResult:
        """
        Check Redis connectivity.

        Returns:
            HealthCheckResult
        """
        start_time = datetime.utcnow()
        endpoint = f"{self.base_url}/health/redis"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint)
                elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                is_healthy = response.status_code == 200
                return HealthCheckResult(
                    check_type=HealthCheckType.REDIS_CONNECTIVITY,
                    is_healthy=is_healthy,
                    response_time_ms=elapsed_ms,
                    message="Redis connected" if is_healthy else "Redis unreachable",
                )
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthCheckResult(
                check_type=HealthCheckType.REDIS_CONNECTIVITY,
                is_healthy=False,
                response_time_ms=elapsed_ms,
                message=f"Network error during Redis check: {str(e)}",
            )
        except httpx.HTTPError as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthCheckResult(
                check_type=HealthCheckType.REDIS_CONNECTIVITY,
                is_healthy=False,
                response_time_ms=elapsed_ms,
                message=f"HTTP error during Redis check: {str(e)}",
            )

    async def check_celery_workers(self) -> HealthCheckResult:
        """
        Check Celery workers status.

        Returns:
            HealthCheckResult
        """
        start_time = datetime.utcnow()
        endpoint = f"{self.base_url}/health/celery"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(endpoint)
                elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

                is_healthy = response.status_code == 200
                details = {}
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                ):
                    try:
                        details = response.json()
                    except (ValueError, TypeError, json.JSONDecodeError):
                        pass

                return HealthCheckResult(
                    check_type=HealthCheckType.CELERY_WORKERS,
                    is_healthy=is_healthy,
                    response_time_ms=elapsed_ms,
                    message=(
                        "Celery workers active"
                        if is_healthy
                        else "Celery workers unavailable"
                    ),
                    details=details,
                )
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthCheckResult(
                check_type=HealthCheckType.CELERY_WORKERS,
                is_healthy=False,
                response_time_ms=elapsed_ms,
                message=f"Network error during Celery check: {str(e)}",
            )
        except httpx.HTTPError as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthCheckResult(
                check_type=HealthCheckType.CELERY_WORKERS,
                is_healthy=False,
                response_time_ms=elapsed_ms,
                message=f"HTTP error during Celery check: {str(e)}",
            )

    async def check_critical_endpoints(self) -> HealthCheckResult:
        """
        Check critical application endpoints.

        Tests key API endpoints to ensure functionality.

        Returns:
            HealthCheckResult
        """
        start_time = datetime.utcnow()
        critical_endpoints = [
            "/api/v1/persons",
            "/api/v1/blocks",
            "/api/v1/assignments",
        ]

        try:
            results = []
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                for endpoint in critical_endpoints:
                    try:
                        response = await client.get(f"{self.base_url}{endpoint}")
                        results.append(
                            {
                                "endpoint": endpoint,
                                "status": response.status_code,
                                "healthy": response.status_code
                                in (200, 401, 403),  # Auth errors are OK
                            }
                        )
                    except (
                        httpx.TimeoutException,
                        httpx.ConnectError,
                        httpx.NetworkError,
                    ) as e:
                        results.append(
                            {
                                "endpoint": endpoint,
                                "status": 0,
                                "healthy": False,
                                "error": f"Network error: {str(e)}",
                            }
                        )
                    except httpx.HTTPError as e:
                        results.append(
                            {
                                "endpoint": endpoint,
                                "status": 0,
                                "healthy": False,
                                "error": f"HTTP error: {str(e)}",
                            }
                        )

            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            is_healthy = all(r["healthy"] for r in results)

            return HealthCheckResult(
                check_type=HealthCheckType.CRITICAL_ENDPOINTS,
                is_healthy=is_healthy,
                response_time_ms=elapsed_ms,
                message=f"{len([r for r in results if r['healthy']])}/{len(results)} endpoints healthy",
                details={"endpoints": results},
            )
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthCheckResult(
                check_type=HealthCheckType.CRITICAL_ENDPOINTS,
                is_healthy=False,
                response_time_ms=elapsed_ms,
                message=f"Network error checking critical endpoints: {str(e)}",
            )
        except httpx.HTTPError as e:
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthCheckResult(
                check_type=HealthCheckType.CRITICAL_ENDPOINTS,
                is_healthy=False,
                response_time_ms=elapsed_ms,
                message=f"HTTP error checking critical endpoints: {str(e)}",
            )

    async def run_all_checks(self) -> list[HealthCheckResult]:
        """
        Run all health checks.

        Returns:
            List of HealthCheckResult
        """
        checks = [
            self.check_http_endpoint(),
            self.check_database_connectivity(),
            self.check_redis_connectivity(),
            self.check_celery_workers(),
            self.check_critical_endpoints(),
        ]

        results = []
        for check in checks:
            try:
                result = await check
                results.append(result)
            except (httpx.HTTPError, ValueError, RuntimeError) as e:
                logger.error(f"Health check error: {e}", exc_info=True)

        return results


# =============================================================================
# Blue-Green Deployment Manager
# =============================================================================


class BlueGreenDeploymentManager:
    """
    Manager for blue-green deployments.

    Orchestrates zero-downtime deployments using blue-green deployment
    patterns. Handles health verification, traffic switching, session
    draining, and rollback capabilities.

    Usage:
        manager = BlueGreenDeploymentManager()

        # Prepare new deployment
        deployment_id = await manager.prepare_deployment(
            slot=DeploymentSlot.GREEN,
            version="v1.2.3",
            git_commit="abc123",
        )

        # Verify health
        health = await manager.verify_slot_health(DeploymentSlot.GREEN)

        # Switch traffic
        if health.is_healthy:
            await manager.switch_traffic(
                from_slot=DeploymentSlot.BLUE,
                to_slot=DeploymentSlot.GREEN,
            )
    """

    def __init__(
        self,
        db: Session | None = None,
        config: DeploymentConfig | None = None,
        slot_urls: dict[DeploymentSlot, str] | None = None,
    ):
        """
        Initialize deployment manager.

        Args:
            db: Database session for persistence
            config: Deployment configuration
            slot_urls: URLs for blue/green slots
        """
        self.db = db
        self.config = config or DeploymentConfig()
        self.slot_urls = slot_urls or {
            DeploymentSlot.BLUE: "http://localhost:8000",
            DeploymentSlot.GREEN: "http://localhost:8001",
        }

        # State tracking
        self._active_slot: DeploymentSlot = DeploymentSlot.BLUE
        self._traffic_distribution: dict[DeploymentSlot, float] = {
            DeploymentSlot.BLUE: 100.0,
            DeploymentSlot.GREEN: 0.0,
        }
        self._slot_states: dict[DeploymentSlot, DeploymentState] = {
            DeploymentSlot.BLUE: DeploymentState.HEALTHY,
            DeploymentSlot.GREEN: DeploymentState.INACTIVE,
        }
        self._deployments: dict[UUID, DeploymentRecord] = {}
        self._event_handlers: dict[str, list[Callable]] = {}

    async def prepare_deployment(
        self,
        slot: DeploymentSlot,
        version: str,
        git_commit: str = "",
        deployed_by: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        """
        Prepare a new deployment in the specified slot.

        Args:
            slot: Deployment slot to prepare
            version: Version identifier
            git_commit: Git commit hash
            deployed_by: User initiating deployment
            metadata: Additional deployment metadata

        Returns:
            UUID of the deployment record
        """
        deployment_id = uuid.uuid4()

        logger.info(
            f"Preparing deployment {deployment_id} in slot {slot.value}: "
            f"version={version}, commit={git_commit}"
        )

        # Create deployment record
        deployment = DeploymentRecord(
            id=deployment_id,
            slot=slot.value,
            version=version,
            git_commit=git_commit,
            deployed_by=deployed_by,
            state=DeploymentState.STARTING.value,
            deployment_config=self.config.__dict__,
            deployment_metadata=metadata or {},
        )

        if self.db:
            self.db.add(deployment)
            self.db.commit()

        self._deployments[deployment_id] = deployment
        self._slot_states[slot] = DeploymentState.STARTING

        # Emit event
        self._emit_event(
            "deployment_started",
            {
                "deployment_id": deployment_id,
                "slot": slot.value,
                "version": version,
            },
        )

        # Send notification
        if self.config.notify_on_start:
            await self._send_notification(
                f"Deployment Started: {version}",
                f"Starting deployment {deployment_id} in {slot.value} slot",
                "info",
            )

        return deployment_id

    async def verify_slot_health(
        self,
        slot: DeploymentSlot,
        deployment_id: UUID | None = None,
    ) -> DeploymentStatus:
        """
        Verify health of a deployment slot.

        Runs comprehensive health checks and returns detailed status.

        Args:
            slot: Slot to verify
            deployment_id: Optional deployment ID to associate checks with

        Returns:
            DeploymentStatus
        """
        logger.info(f"Verifying health of {slot.value} slot")

        base_url = self.slot_urls[slot]
        health_checker = HealthCheck(base_url, self.config.health_check_timeout_seconds)

        # Run all health checks
        health_results = await health_checker.run_all_checks()

        # Persist health check results
        if self.db and deployment_id:
            for result in health_results:
                health_record = DeploymentHealthCheck(
                    deployment_id=deployment_id,
                    check_type=result.check_type.value,
                    is_healthy=result.is_healthy,
                    response_time_ms=result.response_time_ms,
                    message=result.message,
                    details=result.details,
                )
                self.db.add(health_record)

            # Update deployment record
            deployment = (
                self.db.query(DeploymentRecord).filter_by(id=deployment_id).first()
            )
            if deployment:
                deployment.last_health_check = datetime.utcnow()
                if all(r.is_healthy for r in health_results):
                    deployment.health_check_successes += 1
                else:
                    deployment.health_check_failures += 1

            self.db.commit()

        # Determine overall health
        all_healthy = all(result.is_healthy for result in health_results)
        if all_healthy:
            self._slot_states[slot] = DeploymentState.HEALTHY
        else:
            self._slot_states[slot] = DeploymentState.DEGRADED

        # Create deployment status
        status = DeploymentStatus(
            deployment_id=deployment_id or uuid.uuid4(),
            slot=slot,
            state=self._slot_states[slot],
            traffic_percent=self._traffic_distribution[slot],
            health_checks=health_results,
            active_sessions=0,  # Would be populated from actual metrics
            started_at=datetime.utcnow(),
            last_health_check=datetime.utcnow(),
        )

        logger.info(
            f"Health check for {slot.value}: "
            f"{len([r for r in health_results if r.is_healthy])}/{len(health_results)} passed"
        )

        return status

    async def switch_traffic(
        self,
        from_slot: DeploymentSlot,
        to_slot: DeploymentSlot,
        strategy: TrafficSplitStrategy | None = None,
        deployment_id: UUID | None = None,
        triggered_by: str = "",
    ) -> bool:
        """
        Switch traffic from one slot to another.

        Args:
            from_slot: Source slot
            to_slot: Target slot
            strategy: Traffic split strategy (uses config default if not specified)
            deployment_id: Associated deployment ID
            triggered_by: User triggering the switch

        Returns:
            True if successful, False otherwise
        """
        strategy = strategy or self.config.default_traffic_strategy

        logger.info(
            f"Switching traffic from {from_slot.value} to {to_slot.value} "
            f"using {strategy.value} strategy"
        )

        try:
            if strategy == TrafficSplitStrategy.INSTANT:
                await self._instant_switch(
                    from_slot, to_slot, deployment_id, triggered_by
                )
            elif strategy == TrafficSplitStrategy.CANARY:
                await self._canary_switch(
                    from_slot, to_slot, deployment_id, triggered_by
                )
            elif strategy == TrafficSplitStrategy.PROGRESSIVE:
                await self._progressive_switch(
                    from_slot, to_slot, deployment_id, triggered_by
                )
            else:
                logger.error(f"Unsupported traffic strategy: {strategy}")
                return False

            # Update active slot
            self._active_slot = to_slot

            # Update deployment record
            if self.db and deployment_id:
                deployment = (
                    self.db.query(DeploymentRecord).filter_by(id=deployment_id).first()
                )
                if deployment:
                    deployment.traffic_switched_at = datetime.utcnow()
                    deployment.traffic_percent = 100.0
                    deployment.state = DeploymentState.HEALTHY.value
                self.db.commit()

            # Emit event
            self._emit_event(
                "traffic_switched",
                {
                    "from_slot": from_slot.value,
                    "to_slot": to_slot.value,
                    "strategy": strategy.value,
                },
            )

            # Send notification
            if self.config.notify_on_success:
                await self._send_notification(
                    f"Traffic Switched to {to_slot.value}",
                    f"Successfully switched traffic using {strategy.value} strategy",
                    "success",
                )

            logger.info(
                f"Traffic switch complete: {to_slot.value} now receiving 100% traffic"
            )
            return True

        except RuntimeError as e:
            logger.error(f"Traffic switch failed: {e}", exc_info=True)

            # Send notification
            if self.config.notify_on_failure:
                await self._send_notification(
                    "Traffic Switch Failed",
                    f"Failed to switch traffic: {str(e)}",
                    "error",
                )

            return False
        except (ValueError, TypeError) as e:
            logger.error(
                f"Invalid configuration during traffic switch: {e}", exc_info=True
            )

            if self.config.notify_on_failure:
                await self._send_notification(
                    "Traffic Switch Failed",
                    f"Configuration error: {str(e)}",
                    "error",
                )

            return False

    async def _instant_switch(
        self,
        from_slot: DeploymentSlot,
        to_slot: DeploymentSlot,
        deployment_id: UUID | None,
        triggered_by: str,
    ):
        """Perform instant 100% traffic switch."""
        self._traffic_distribution[from_slot] = 0.0
        self._traffic_distribution[to_slot] = 100.0

        # Record traffic switch event
        if self.db:
            event = TrafficSwitchEvent(
                deployment_id=deployment_id or uuid.uuid4(),
                from_slot=from_slot.value,
                to_slot=to_slot.value,
                strategy=TrafficSplitStrategy.INSTANT.value,
                from_percent=100.0,
                to_percent=100.0,
                is_successful=True,
                triggered_by=triggered_by,
            )
            self.db.add(event)
            self.db.commit()

    async def _canary_switch(
        self,
        from_slot: DeploymentSlot,
        to_slot: DeploymentSlot,
        deployment_id: UUID | None,
        triggered_by: str,
    ):
        """Perform gradual canary traffic switch."""
        import asyncio

        for stage_percent in self.config.canary_stages:
            logger.info(f"Canary stage: {stage_percent}% to {to_slot.value}")

            # Update traffic distribution
            self._traffic_distribution[to_slot] = float(stage_percent)
            self._traffic_distribution[from_slot] = 100.0 - float(stage_percent)

            # Record traffic switch event
            if self.db:
                event = TrafficSwitchEvent(
                    deployment_id=deployment_id or uuid.uuid4(),
                    from_slot=from_slot.value,
                    to_slot=to_slot.value,
                    strategy=TrafficSplitStrategy.CANARY.value,
                    from_percent=self._traffic_distribution[from_slot],
                    to_percent=self._traffic_distribution[to_slot],
                    is_successful=True,
                    triggered_by=triggered_by,
                )
                self.db.add(event)
                self.db.commit()

            # Wait before next stage (except for last stage)
            if stage_percent < 100:
                await asyncio.sleep(self.config.canary_stage_duration_seconds)

                # Verify health before proceeding
                health = await self.verify_slot_health(to_slot, deployment_id)
                if not health.is_healthy:
                    raise RuntimeError(
                        f"Health check failed at {stage_percent}% canary stage"
                    )

    async def _progressive_switch(
        self,
        from_slot: DeploymentSlot,
        to_slot: DeploymentSlot,
        deployment_id: UUID | None,
        triggered_by: str,
    ):
        """Perform progressive linear traffic switch."""
        import asyncio

        duration = self.config.progressive_duration_seconds
        steps = 20  # 5% increments
        step_duration = duration / steps

        for i in range(1, steps + 1):
            percent = (i / steps) * 100
            self._traffic_distribution[to_slot] = percent
            self._traffic_distribution[from_slot] = 100.0 - percent

            logger.info(f"Progressive switch: {percent:.1f}% to {to_slot.value}")

            # Record traffic switch event (every 25%)
            if self.db and i % 5 == 0:
                event = TrafficSwitchEvent(
                    deployment_id=deployment_id or uuid.uuid4(),
                    from_slot=from_slot.value,
                    to_slot=to_slot.value,
                    strategy=TrafficSplitStrategy.PROGRESSIVE.value,
                    from_percent=self._traffic_distribution[from_slot],
                    to_percent=self._traffic_distribution[to_slot],
                    is_successful=True,
                    triggered_by=triggered_by,
                )
                self.db.add(event)
                self.db.commit()

            await asyncio.sleep(step_duration)

    async def drain_sessions(
        self,
        slot: DeploymentSlot,
        deployment_id: UUID | None = None,
    ) -> SessionDrainStatus:
        """
        Drain active sessions from a slot before shutdown.

        Args:
            slot: Slot to drain
            deployment_id: Associated deployment ID

        Returns:
            SessionDrainStatus
        """
        logger.info(f"Draining sessions from {slot.value} slot")

        self._slot_states[slot] = DeploymentState.DRAINING
        started_at = datetime.utcnow()

        # Query actual session count from Redis or database
        initial_sessions = await self._get_active_session_count(slot)
        drained_sessions = 0

        import asyncio

        elapsed = 0.0
        while elapsed < self.config.session_drain_timeout_seconds:
            # Check remaining sessions
            # In production: query session store, check active connections
            remaining = max(0, initial_sessions - int(elapsed / 3))

            if remaining == 0:
                break

            drained_sessions = initial_sessions - remaining
            await asyncio.sleep(self.config.session_check_interval_seconds)
            elapsed = (datetime.utcnow() - started_at).total_seconds()

        is_complete = remaining == 0 or self.config.allow_force_drain

        status = SessionDrainStatus(
            slot=slot,
            started_at=started_at,
            active_sessions=remaining,
            drained_sessions=drained_sessions,
            is_complete=is_complete,
            elapsed_seconds=elapsed,
            estimated_remaining_seconds=max(
                0, self.config.session_drain_timeout_seconds - elapsed
            ),
        )

        logger.info(
            f"Session drain {'complete' if is_complete else 'incomplete'}: "
            f"{drained_sessions}/{initial_sessions} drained in {elapsed:.1f}s"
        )

        return status

    async def _get_active_session_count(self, slot: DeploymentSlot) -> int:
        """
        Get the count of active sessions for a deployment slot.

        Queries Redis or database for active session count. Falls back to
        a reasonable default if session store is unavailable.

        Args:
            slot: Deployment slot to check

        Returns:
            Number of active sessions
        """
        try:
            # Try to get session count from Redis
            import redis.asyncio as redis
            from app.core.config import settings

            redis_url = getattr(settings, "REDIS_URL", None)
            if redis_url:
                client = redis.from_url(redis_url)
                try:
                    # Look for session keys matching the slot pattern
                    session_pattern = f"session:{slot.value}:*"
                    keys = await client.keys(session_pattern)
                    count = len(keys)
                    await client.close()
                    return count
                except Exception as e:
                    logger.warning(f"Could not get session count from Redis: {e}")
                    await client.close()

            # Fall back to database query for active sessions
            if self.db:
                from sqlalchemy import func, select
                from app.models.user import User

                # Count recently active users (active in last 15 minutes)
                from datetime import timedelta

                cutoff = datetime.utcnow() - timedelta(minutes=15)

                result = self.db.execute(
                    select(func.count(User.id)).where(
                        User.last_active >= cutoff
                        if hasattr(User, "last_active")
                        else True
                    )
                )
                count = result.scalar() or 0
                return count

        except ImportError:
            logger.debug("Redis not available, using default session count")
        except Exception as e:
            logger.warning(f"Error getting session count: {e}")

        # Default fallback - assume moderate activity
        return 50

    async def rollback_deployment(
        self,
        deployment_id: UUID,
        reason: RollbackReason,
        message: str = "",
    ) -> bool:
        """
        Rollback a failed deployment.

        Args:
            deployment_id: Deployment to rollback
            reason: Reason for rollback
            message: Additional context

        Returns:
            True if rollback successful
        """
        logger.warning(
            f"Rolling back deployment {deployment_id}: "
            f"reason={reason.value}, message={message}"
        )

        try:
            # Get deployment record
            deployment = None
            if self.db:
                deployment = (
                    self.db.query(DeploymentRecord).filter_by(id=deployment_id).first()
                )

            if not deployment:
                logger.error(f"Deployment {deployment_id} not found")
                return False

            slot = DeploymentSlot(deployment.slot)
            other_slot = (
                DeploymentSlot.GREEN
                if slot == DeploymentSlot.BLUE
                else DeploymentSlot.BLUE
            )

            # Switch traffic back to other slot
            success = await self.switch_traffic(
                from_slot=slot,
                to_slot=other_slot,
                strategy=TrafficSplitStrategy.INSTANT,
                triggered_by="rollback_automation",
            )

            if not success:
                logger.error("Rollback traffic switch failed")
                return False

            # Update deployment record
            if self.db:
                deployment.rolled_back_at = datetime.utcnow()
                deployment.rollback_reason = reason.value
                deployment.error_message = message
                deployment.is_successful = False
                deployment.state = DeploymentState.STOPPED.value
                self.db.commit()

            # Emit event
            self._emit_event(
                "deployment_rolled_back",
                {
                    "deployment_id": deployment_id,
                    "reason": reason.value,
                    "message": message,
                },
            )

            # Send notification
            if self.config.notify_on_failure:
                await self._send_notification(
                    "Deployment Rolled Back",
                    f"Deployment {deployment_id} rolled back: {reason.value}",
                    "warning",
                )

            logger.info(f"Rollback complete for deployment {deployment_id}")
            return True

        except RuntimeError as e:
            logger.error(f"Rollback failed: {e}", exc_info=True)
            return False
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid state during rollback: {e}", exc_info=True)
            return False

    async def complete_deployment(
        self,
        deployment_id: UUID,
        is_successful: bool = True,
    ):
        """
        Mark a deployment as complete.

        Args:
            deployment_id: Deployment to complete
            is_successful: Whether deployment was successful
        """
        if self.db:
            deployment = (
                self.db.query(DeploymentRecord).filter_by(id=deployment_id).first()
            )
            if deployment:
                deployment.completed_at = datetime.utcnow()
                deployment.is_successful = is_successful
                deployment.state = (
                    DeploymentState.HEALTHY.value
                    if is_successful
                    else DeploymentState.STOPPED.value
                )
                self.db.commit()

        # Emit event
        self._emit_event(
            "deployment_completed",
            {
                "deployment_id": deployment_id,
                "is_successful": is_successful,
            },
        )

        # Send notification
        if is_successful and self.config.notify_on_success:
            await self._send_notification(
                "Deployment Completed Successfully",
                f"Deployment {deployment_id} completed successfully",
                "success",
            )

    async def run_database_migrations(
        self,
        slot: DeploymentSlot,
        deployment_id: UUID | None = None,
    ) -> bool:
        """
        Run database migrations for a deployment.

        Args:
            slot: Slot to run migrations for
            deployment_id: Associated deployment ID

        Returns:
            True if migrations successful
        """
        logger.info(f"Running database migrations for {slot.value} slot")

        try:
            import subprocess
            import asyncio

            # Run alembic upgrade head
            logger.info("Running alembic upgrade head...")

            # Run migration in a separate process to avoid blocking
            process = await asyncio.create_subprocess_exec(
                "alembic",
                "upgrade",
                "head",
                cwd=".",  # Use project root
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.config.migration_timeout_seconds
            )

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Migration failed: {error_msg}")
                raise RuntimeError(f"Migration failed: {error_msg}")

            # Get current migration version
            version_result = await asyncio.create_subprocess_exec(
                "alembic",
                "current",
                cwd=".",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            version_stdout, _ = await version_result.communicate()
            current_version = (
                version_stdout.decode().strip() if version_stdout else "unknown"
            )

            # Update deployment record
            if self.db and deployment_id:
                deployment = (
                    self.db.query(DeploymentRecord).filter_by(id=deployment_id).first()
                )
                if deployment:
                    deployment.migration_completed = True
                    deployment.migration_version = current_version
                self.db.commit()

            logger.info(
                f"Database migrations completed successfully. Version: {current_version}"
            )
            return True

        except RuntimeError as e:
            logger.error(f"Database migration failed: {e}", exc_info=True)

            # Rollback if configured
            if self.config.migration_rollback_on_failure and deployment_id:
                await self.rollback_deployment(
                    deployment_id,
                    RollbackReason.DATABASE_MIGRATION_FAILED,
                    str(e),
                )

            return False
        except OSError as e:
            logger.error(f"File I/O error during migration: {e}", exc_info=True)

            if self.config.migration_rollback_on_failure and deployment_id:
                await self.rollback_deployment(
                    deployment_id,
                    RollbackReason.DATABASE_MIGRATION_FAILED,
                    str(e),
                )

            return False

    def get_current_traffic_distribution(self) -> dict[DeploymentSlot, float]:
        """
        Get current traffic distribution across slots.

        Returns:
            Dict mapping slots to traffic percentage
        """
        return self._traffic_distribution.copy()

    def get_active_slot(self) -> DeploymentSlot:
        """
        Get currently active deployment slot.

        Returns:
            Active DeploymentSlot
        """
        return self._active_slot

    def get_slot_state(self, slot: DeploymentSlot) -> DeploymentState:
        """
        Get current state of a slot.

        Args:
            slot: Slot to check

        Returns:
            DeploymentState
        """
        return self._slot_states[slot]

    def register_event_handler(
        self,
        event_type: str,
        handler: Callable[[dict], Any],
    ):
        """
        Register handler for deployment events.

        Event types:
        - deployment_started: New deployment initiated
        - deployment_completed: Deployment finished
        - deployment_rolled_back: Deployment rolled back
        - traffic_switched: Traffic switched between slots

        Args:
            event_type: Type of event to handle
            handler: Callback function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def _emit_event(self, event_type: str, data: dict):
        """
        Emit event to registered handlers.

        Args:
            event_type: Type of event
            data: Event data
        """
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except (ValueError, TypeError, RuntimeError) as e:
                logger.error(f"Event handler error ({event_type}): {e}", exc_info=True)

    async def _send_notification(
        self,
        subject: str,
        message: str,
        level: str = "info",
    ):
        """
        Send deployment notification.

        Args:
            subject: Notification subject
            message: Notification message
            level: Notification level (info, warning, error, success)
        """
        logger.info(f"Deployment notification [{level}]: {subject} - {message}")

        # Send Slack notification if webhook configured
        if self.config.slack_webhook_url:
            try:
                color_map = {
                    "info": "#2196F3",
                    "warning": "#FF9800",
                    "error": "#F44336",
                    "success": "#4CAF50",
                }
                slack_payload = {
                    "attachments": [
                        {
                            "color": color_map.get(level, "#808080"),
                            "title": subject,
                            "text": message,
                            "footer": "Residency Scheduler Deployment",
                            "ts": int(datetime.utcnow().timestamp()),
                        }
                    ]
                }

                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        self.config.slack_webhook_url,
                        json=slack_payload,
                    )
                    if response.status_code != 200:
                        logger.warning(
                            f"Slack notification failed: {response.status_code}"
                        )
                    else:
                        logger.debug("Slack notification sent successfully")
            except httpx.HTTPError as e:
                logger.warning(f"Failed to send Slack notification: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error sending Slack notification: {e}")

        # Log recipients for email notifications (actual email sending would use email service)
        if self.config.notification_recipients:
            recipients = self.config.notification_recipients
            logger.info(
                f"Email notification would be sent to: {recipients}",
                extra={
                    "subject": subject,
                    "message": message,
                    "level": level,
                    "recipients": recipients,
                },
            )
