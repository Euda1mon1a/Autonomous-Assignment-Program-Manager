"""
Disaster Recovery Service for Residency Scheduler.

Provides comprehensive disaster recovery capabilities including:
- Recovery Point Objectives (RPO) tracking
- Recovery Time Objectives (RTO) monitoring
- Automated failover triggers
- Data synchronization verification
- Recovery plan execution
- Health checks during recovery
- Recovery testing utilities
- Recovery documentation generation

This service ensures business continuity and data protection in the event
of system failures, data center outages, or catastrophic events.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class RecoveryStatus(str, Enum):
    """Overall recovery status."""

    NORMAL = "normal"  # Normal operations
    DEGRADED = "degraded"  # Partial functionality
    FAILOVER_IN_PROGRESS = "failover_in_progress"  # Failing over
    RECOVERED = "recovered"  # Recovery complete
    RECOVERY_FAILED = "recovery_failed"  # Recovery unsuccessful


class RecoveryPlanStatus(str, Enum):
    """Status of a recovery plan."""

    DRAFT = "draft"  # Plan being developed
    APPROVED = "approved"  # Ready for execution
    IN_PROGRESS = "in_progress"  # Currently executing
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Execution failed
    CANCELLED = "cancelled"  # Cancelled before completion


class FailoverTrigger(str, Enum):
    """Reason for failover trigger."""

    MANUAL = "manual"  # Manual trigger
    AUTOMATED = "automated"  # Automated detection
    SCHEDULED = "scheduled"  # Scheduled maintenance
    HEALTH_CHECK_FAILED = "health_check_failed"  # Health check failure
    DATA_CENTER_OUTAGE = "data_center_outage"  # Data center down
    NETWORK_FAILURE = "network_failure"  # Network issues
    DATABASE_FAILURE = "database_failure"  # Database failure
    APPLICATION_FAILURE = "application_failure"  # App failure


class FailoverStatus(str, Enum):
    """Status of failover operation."""

    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    VERIFYING_REPLICA = "verifying_replica"
    PROMOTING_REPLICA = "promoting_replica"
    UPDATING_ROUTES = "updating_routes"
    VERIFYING_HEALTH = "verifying_health"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class SyncStatus(str, Enum):
    """Data synchronization status."""

    IN_SYNC = "in_sync"  # Fully synchronized
    SYNCING = "syncing"  # Synchronization in progress
    LAG = "lag"  # Behind but acceptable
    OUT_OF_SYNC = "out_of_sync"  # Critically behind
    FAILED = "failed"  # Sync failure


class FailoverReason(str, Enum):
    """High-level reason for failover."""

    PRIMARY_FAILURE = "primary_failure"
    MAINTENANCE = "maintenance"
    DISASTER = "disaster"
    TESTING = "testing"


# ============================================================================
# Data Models
# ============================================================================


class RecoveryPointObjective(BaseModel):
    """
    Recovery Point Objective (RPO) configuration.

    RPO defines the maximum acceptable amount of data loss
    measured in time (e.g., 5 minutes of data).
    """

    name: str = Field(..., description="Name of the RPO")
    description: str = Field(default="", description="Description")
    max_data_loss_minutes: int = Field(
        ..., ge=0, description="Maximum acceptable data loss in minutes"
    )
    current_lag_minutes: float = Field(
        default=0.0, ge=0.0, description="Current replication lag"
    )
    backup_frequency_minutes: int = Field(
        default=60, ge=1, description="Backup frequency"
    )
    last_backup_at: datetime | None = Field(
        default=None, description="Last successful backup time"
    )
    is_compliant: bool = Field(
        default=True, description="Whether currently meeting RPO"
    )
    violation_count: int = Field(
        default=0, ge=0, description="Number of RPO violations"
    )


class RecoveryTimeObjective(BaseModel):
    """
    Recovery Time Objective (RTO) configuration.

    RTO defines the maximum acceptable downtime
    (e.g., system must be back up within 30 minutes).
    """

    name: str = Field(..., description="Name of the RTO")
    description: str = Field(default="", description="Description")
    max_downtime_minutes: int = Field(
        ..., ge=0, description="Maximum acceptable downtime in minutes"
    )
    estimated_recovery_time_minutes: int = Field(
        default=0, ge=0, description="Estimated time to recover"
    )
    actual_recovery_time_minutes: float | None = Field(
        default=None, ge=0.0, description="Actual recovery time from last event"
    )
    is_achievable: bool = Field(default=True, description="Whether RTO is achievable")
    automated_failover_enabled: bool = Field(
        default=True, description="Whether automated failover is enabled"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="Services this RTO depends on"
    )


class SyncVerificationResult(BaseModel):
    """Result of data synchronization verification."""

    resource: str = Field(..., description="Resource being verified")
    status: SyncStatus = Field(..., description="Sync status")
    lag_seconds: float = Field(default=0.0, ge=0.0, description="Replication lag")
    records_behind: int = Field(default=0, ge=0, description="Records behind")
    last_sync_at: datetime | None = Field(
        default=None, description="Last sync timestamp"
    )
    is_healthy: bool = Field(default=True, description="Whether sync is healthy")
    error: str | None = Field(default=None, description="Error if any")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional details"
    )


class RecoveryMetrics(BaseModel):
    """Metrics tracked during recovery."""

    recovery_id: UUID = Field(default_factory=uuid4)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    duration_seconds: float = Field(default=0.0, ge=0.0)
    rto_target_minutes: int = Field(default=0, ge=0)
    rto_achieved: bool = Field(default=False)
    data_loss_minutes: float = Field(default=0.0, ge=0.0)
    rpo_target_minutes: int = Field(default=0, ge=0)
    rpo_achieved: bool = Field(default=False)
    health_check_passes: int = Field(default=0, ge=0)
    health_check_failures: int = Field(default=0, ge=0)
    rollback_count: int = Field(default=0, ge=0)
    issues_encountered: list[str] = Field(default_factory=list)


@dataclass
class RecoveryStep:
    """A step in a recovery plan."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    order: int = 0
    is_automated: bool = True
    estimated_duration_minutes: int = 5
    is_critical: bool = True
    rollback_possible: bool = True
    dependencies: list[UUID] = field(default_factory=list)
    validation_required: bool = True

    # Execution tracking
    status: RecoveryPlanStatus = RecoveryPlanStatus.DRAFT
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    executed_by: str | None = None
    validation_result: bool | None = None


@dataclass
class RecoveryPlan:
    """Complete disaster recovery plan."""

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated_at: datetime = field(default_factory=datetime.utcnow)
    last_tested_at: datetime | None = None

    # Recovery objectives
    rto_minutes: int = 30
    rpo_minutes: int = 5

    # Plan details
    trigger: FailoverTrigger = FailoverTrigger.MANUAL
    severity: str = "moderate"  # minor, moderate, severe, critical
    steps: list[RecoveryStep] = field(default_factory=list)

    # Status
    status: RecoveryPlanStatus = RecoveryPlanStatus.DRAFT
    approved_by: str | None = None
    approved_at: datetime | None = None

    # Execution history
    execution_count: int = 0
    last_execution_at: datetime | None = None
    last_execution_successful: bool = False
    last_execution_duration_minutes: float = 0.0

    # Documentation
    prerequisites: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    rollback_plan: str = ""
    contact_list: list[dict[str, str]] = field(default_factory=list)


@dataclass
class FailoverEvent:
    """Record of a failover event."""

    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    trigger: FailoverTrigger = FailoverTrigger.MANUAL
    reason: FailoverReason = FailoverReason.TESTING
    status: FailoverStatus = FailoverStatus.NOT_STARTED
    initiated_by: str = "system"

    # Source and target
    source_region: str = "primary"
    target_region: str = "secondary"
    services_affected: list[str] = field(default_factory=list)

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float = 0.0

    # Results
    successful: bool = False
    data_loss_detected: bool = False
    services_restored: list[str] = field(default_factory=list)
    services_failed: list[str] = field(default_factory=list)

    # Metrics
    rto_target_minutes: int = 30
    rto_achieved: bool = False
    actual_downtime_minutes: float = 0.0

    # Issues and resolution
    issues: list[str] = field(default_factory=list)
    resolution_notes: str = ""
    rolled_back: bool = False


@dataclass
class RecoveryConfig:
    """Configuration for disaster recovery service."""

    # RPO/RTO targets
    default_rpo_minutes: int = 5  # 5 minutes max data loss
    default_rto_minutes: int = 30  # 30 minutes max downtime
    critical_rpo_minutes: int = 1  # 1 minute for critical data
    critical_rto_minutes: int = 10  # 10 minutes for critical services

    # Health check settings
    health_check_interval_seconds: int = 60
    health_check_timeout_seconds: int = 10
    max_consecutive_failures: int = 3

    # Failover settings
    auto_failover_enabled: bool = False  # Require manual approval by default
    failover_confirmation_timeout_seconds: int = 300  # 5 minutes
    rollback_on_failure: bool = True

    # Sync settings
    sync_verification_interval_seconds: int = 30
    max_acceptable_lag_seconds: int = 300  # 5 minutes
    sync_timeout_seconds: int = 60

    # Testing
    allow_production_testing: bool = False
    test_mode_enabled: bool = False

    # Notifications
    notify_on_rpo_violation: bool = True
    notify_on_rto_risk: bool = True
    notify_on_failover: bool = True
    notification_recipients: list[str] = field(default_factory=list)


# ============================================================================
# Disaster Recovery Service
# ============================================================================


class DisasterRecoveryService:
    """
    Main disaster recovery service.

    Provides comprehensive disaster recovery capabilities for the
    Residency Scheduler system.

    Usage:
        service = DisasterRecoveryService()
        await service.initialize()

        # Check RPO/RTO compliance
        rpo_status = await service.verify_rpo()
        rto_status = await service.verify_rto()

        # Execute recovery plan
        result = await service.execute_recovery_plan(plan)
    """

    def __init__(self, config: RecoveryConfig | None = None):
        """
        Initialize disaster recovery service.

        Args:
            config: Recovery configuration (uses defaults if not provided)
        """
        self.config = config or RecoveryConfig()

        # Recovery state
        self._current_status = RecoveryStatus.NORMAL
        self._active_recovery: RecoveryMetrics | None = None
        self._failover_in_progress: FailoverEvent | None = None

        # RPO/RTO tracking
        self._rpo_objectives: dict[str, RecoveryPointObjective] = {}
        self._rto_objectives: dict[str, RecoveryTimeObjective] = {}

        # Recovery plans
        self._recovery_plans: dict[UUID, RecoveryPlan] = {}
        self._failover_history: list[FailoverEvent] = []

        # Health monitoring
        self._health_check_failures: dict[str, int] = {}
        self._last_health_check: datetime | None = None

        # Event handlers
        self._event_handlers: dict[str, list[Callable]] = {}

        # Initialize default objectives
        self._initialize_default_objectives()

        logger.info("Disaster Recovery Service initialized")

    def _initialize_default_objectives(self):
        """Initialize default RPO and RTO objectives."""
        # Database RPO/RTO
        self.register_rpo(
            RecoveryPointObjective(
                name="database",
                description="Main PostgreSQL database",
                max_data_loss_minutes=self.config.default_rpo_minutes,
                backup_frequency_minutes=60,
            )
        )

        self.register_rto(
            RecoveryTimeObjective(
                name="database",
                description="Database service availability",
                max_downtime_minutes=self.config.default_rto_minutes,
                estimated_recovery_time_minutes=15,
                automated_failover_enabled=True,
            )
        )

        # Redis cache RPO/RTO
        self.register_rpo(
            RecoveryPointObjective(
                name="redis",
                description="Redis cache and session store",
                max_data_loss_minutes=self.config.default_rpo_minutes,
                backup_frequency_minutes=30,
            )
        )

        self.register_rto(
            RecoveryTimeObjective(
                name="redis",
                description="Redis service availability",
                max_downtime_minutes=self.config.critical_rto_minutes,
                estimated_recovery_time_minutes=5,
                automated_failover_enabled=True,
            )
        )

        # Application RPO/RTO
        self.register_rto(
            RecoveryTimeObjective(
                name="application",
                description="API and frontend services",
                max_downtime_minutes=self.config.critical_rto_minutes,
                estimated_recovery_time_minutes=10,
                automated_failover_enabled=True,
                dependencies=["database", "redis"],
            )
        )

    # ========================================================================
    # RPO Management
    # ========================================================================

    def register_rpo(self, rpo: RecoveryPointObjective):
        """
        Register a Recovery Point Objective.

        Args:
            rpo: RPO configuration to register
        """
        self._rpo_objectives[rpo.name] = rpo
        logger.info(
            f"Registered RPO '{rpo.name}': {rpo.max_data_loss_minutes}min max data loss"
        )

    async def verify_rpo(
        self, name: str | None = None
    ) -> dict[str, RecoveryPointObjective]:
        """
        Verify RPO compliance for all or specific objectives.

        Args:
            name: Specific RPO to check (None = check all)

        Returns:
            Dictionary of RPO name to current status
        """
        results = {}

        objectives_to_check = (
            {name: self._rpo_objectives[name]} if name else self._rpo_objectives
        )

        for rpo_name, rpo in objectives_to_check.items():
            # Check replication lag
            lag = await self._check_replication_lag(rpo_name)
            rpo.current_lag_minutes = lag

            # Check backup freshness
            if rpo.last_backup_at:
                backup_age_minutes = (
                    datetime.utcnow() - rpo.last_backup_at
                ).total_seconds() / 60
                rpo.is_compliant = (
                    backup_age_minutes <= rpo.backup_frequency_minutes
                    and lag <= rpo.max_data_loss_minutes
                )
            else:
                rpo.is_compliant = lag <= rpo.max_data_loss_minutes

            # Track violations
            if not rpo.is_compliant:
                rpo.violation_count += 1
                if self.config.notify_on_rpo_violation:
                    await self._emit_event(
                        "rpo_violation",
                        {
                            "rpo_name": rpo_name,
                            "lag_minutes": lag,
                            "max_allowed": rpo.max_data_loss_minutes,
                        },
                    )

            results[rpo_name] = rpo

        return results

    async def _check_replication_lag(self, resource: str) -> float:
        """
        Check replication lag for a resource.

        Args:
            resource: Resource to check (database, redis, etc.)

        Returns:
            Replication lag in minutes
        """
        # In production, this would query actual replication status
        # For now, simulate with placeholder logic
        try:
            if resource == "database":
                # Check PostgreSQL replication lag
                # SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))
                return 0.5  # Simulated: 30 seconds lag

            elif resource == "redis":
                # Check Redis replication lag
                # INFO replication
                return 0.1  # Simulated: 6 seconds lag

            else:
                return 0.0

        except Exception as e:
            logger.error(f"Error checking replication lag for {resource}: {e}")
            return float("inf")  # Return infinite lag on error

    # ========================================================================
    # RTO Management
    # ========================================================================

    def register_rto(self, rto: RecoveryTimeObjective):
        """
        Register a Recovery Time Objective.

        Args:
            rto: RTO configuration to register
        """
        self._rto_objectives[rto.name] = rto
        logger.info(
            f"Registered RTO '{rto.name}': {rto.max_downtime_minutes}min max downtime"
        )

    async def verify_rto(
        self, name: str | None = None
    ) -> dict[str, RecoveryTimeObjective]:
        """
        Verify RTO achievability for all or specific objectives.

        Args:
            name: Specific RTO to check (None = check all)

        Returns:
            Dictionary of RTO name to current status
        """
        results = {}

        objectives_to_check = (
            {name: self._rto_objectives[name]} if name else self._rto_objectives
        )

        for rto_name, rto in objectives_to_check.items():
            # Check if estimated recovery time is within RTO
            rto.is_achievable = (
                rto.estimated_recovery_time_minutes <= rto.max_downtime_minutes
            )

            # Check dependencies
            for dep in rto.dependencies:
                if dep in self._rto_objectives:
                    dep_rto = self._rto_objectives[dep]
                    if not dep_rto.is_achievable:
                        rto.is_achievable = False
                        logger.warning(
                            f"RTO '{rto_name}' at risk due to dependency '{dep}'"
                        )

            # Notify if RTO at risk
            if not rto.is_achievable and self.config.notify_on_rto_risk:
                await self._emit_event(
                    "rto_at_risk",
                    {
                        "rto_name": rto_name,
                        "estimated_time": rto.estimated_recovery_time_minutes,
                        "target_time": rto.max_downtime_minutes,
                    },
                )

            results[rto_name] = rto

        return results

    # ========================================================================
    # Failover Management
    # ========================================================================

    async def initiate_failover(
        self,
        trigger: FailoverTrigger,
        reason: FailoverReason,
        source_region: str = "primary",
        target_region: str = "secondary",
        services: list[str] | None = None,
        initiated_by: str = "system",
        auto_approve: bool = False,
    ) -> FailoverEvent:
        """
        Initiate a failover operation.

        Args:
            trigger: What triggered the failover
            reason: High-level reason for failover
            source_region: Region to fail over from
            target_region: Region to fail over to
            services: Services to fail over (None = all)
            initiated_by: Who/what initiated the failover
            auto_approve: Whether to auto-approve (requires auto_failover_enabled)

        Returns:
            FailoverEvent tracking the failover

        Raises:
            RuntimeError: If failover already in progress
            PermissionError: If auto-approval attempted without permission
        """
        if self._failover_in_progress:
            raise RuntimeError("Failover already in progress")

        # Check auto-approval permission
        if auto_approve and not self.config.auto_failover_enabled:
            raise PermissionError(
                "Auto-failover not enabled. Manual approval required."
            )

        # Create failover event
        event = FailoverEvent(
            trigger=trigger,
            reason=reason,
            source_region=source_region,
            target_region=target_region,
            services_affected=services or ["database", "redis", "application"],
            initiated_by=initiated_by,
            rto_target_minutes=self.config.default_rto_minutes,
        )

        self._failover_in_progress = event
        self._current_status = RecoveryStatus.FAILOVER_IN_PROGRESS

        logger.warning(
            f"Failover initiated: {reason.value} - {trigger.value} "
            f"from {source_region} to {target_region}"
        )

        await self._emit_event("failover_initiated", event.__dict__)

        # Execute failover if auto-approved
        if auto_approve:
            await self._execute_failover(event)
        else:
            logger.info("Failover waiting for manual approval")
            event.status = FailoverStatus.INITIALIZING

        return event

    async def approve_failover(self, event_id: UUID, approved_by: str) -> bool:
        """
        Approve a pending failover operation.

        Args:
            event_id: ID of the failover event to approve
            approved_by: Who approved the failover

        Returns:
            True if approved and execution started

        Raises:
            ValueError: If no failover pending or wrong event ID
        """
        if not self._failover_in_progress:
            raise ValueError("No failover pending approval")

        if self._failover_in_progress.id != event_id:
            raise ValueError("Event ID does not match pending failover")

        logger.info(f"Failover approved by {approved_by}")
        self._failover_in_progress.initiated_by = approved_by

        await self._execute_failover(self._failover_in_progress)
        return True

    async def _execute_failover(self, event: FailoverEvent):
        """
        Execute the failover operation.

        Args:
            event: Failover event to execute
        """
        event.started_at = datetime.utcnow()
        event.status = FailoverStatus.VERIFYING_REPLICA

        try:
            # Step 1: Verify replica health
            logger.info("Verifying replica health...")
            replica_healthy = await self._verify_replica_health(event.target_region)

            if not replica_healthy:
                raise RuntimeError("Target replica is not healthy")

            # Step 2: Verify data synchronization
            event.status = FailoverStatus.VERIFYING_REPLICA
            logger.info("Verifying data synchronization...")
            sync_results = await self.verify_sync(event.services_affected)

            for service, result in sync_results.items():
                if result.status == SyncStatus.OUT_OF_SYNC:
                    event.data_loss_detected = True
                    logger.warning(
                        f"Data loss detected in {service}: {result.lag_seconds}s lag"
                    )

            # Step 3: Promote replica
            event.status = FailoverStatus.PROMOTING_REPLICA
            logger.info("Promoting replica to primary...")
            await self._promote_replica(event.target_region, event.services_affected)

            # Step 4: Update routes
            event.status = FailoverStatus.UPDATING_ROUTES
            logger.info("Updating traffic routes...")
            await self._update_traffic_routes(event.source_region, event.target_region)

            # Step 5: Verify health
            event.status = FailoverStatus.VERIFYING_HEALTH
            logger.info("Verifying post-failover health...")
            health_ok = await self._verify_post_failover_health(event.target_region)

            if not health_ok:
                raise RuntimeError("Post-failover health checks failed")

            # Success!
            event.status = FailoverStatus.COMPLETED
            event.successful = True
            event.services_restored = event.services_affected.copy()

        except Exception as e:
            logger.error(f"Failover failed: {e}", exc_info=True)
            event.status = FailoverStatus.FAILED
            event.successful = False
            event.issues.append(str(e))

            # Attempt rollback if configured
            if self.config.rollback_on_failure:
                logger.info("Attempting failover rollback...")
                await self._rollback_failover(event)

        finally:
            # Record completion
            event.completed_at = datetime.utcnow()
            if event.started_at:
                event.duration_seconds = (
                    event.completed_at - event.started_at
                ).total_seconds()
                event.actual_downtime_minutes = event.duration_seconds / 60
                event.rto_achieved = (
                    event.actual_downtime_minutes <= event.rto_target_minutes
                )

            # Update state
            self._failover_history.append(event)
            self._failover_in_progress = None
            self._current_status = (
                RecoveryStatus.RECOVERED
                if event.successful
                else RecoveryStatus.RECOVERY_FAILED
            )

            await self._emit_event("failover_completed", event.__dict__)

    async def _verify_replica_health(self, region: str) -> bool:
        """
        Verify replica health before failover.

        Args:
            region: Region to verify

        Returns:
            True if replica is healthy
        """
        # In production, this would check actual replica health
        # For now, simulate
        await asyncio.sleep(1)  # Simulate check
        logger.info(f"Replica in {region} is healthy")
        return True

    async def _promote_replica(self, region: str, services: list[str]):
        """
        Promote replica to primary.

        Args:
            region: Region to promote
            services: Services to promote
        """
        # In production, this would execute actual promotion commands
        await asyncio.sleep(2)  # Simulate promotion
        logger.info(f"Promoted replica in {region} to primary")

    async def _update_traffic_routes(self, from_region: str, to_region: str):
        """
        Update traffic routing from one region to another.

        Args:
            from_region: Source region
            to_region: Target region
        """
        # In production, this would update load balancers, DNS, etc.
        await asyncio.sleep(1)  # Simulate route update
        logger.info(f"Updated traffic routes from {from_region} to {to_region}")

    async def _verify_post_failover_health(self, region: str) -> bool:
        """
        Verify health after failover.

        Args:
            region: Region to verify

        Returns:
            True if healthy
        """
        # In production, this would run comprehensive health checks
        await asyncio.sleep(1)  # Simulate check
        logger.info(f"Post-failover health in {region} verified")
        return True

    async def _rollback_failover(self, event: FailoverEvent):
        """
        Rollback a failed failover.

        Args:
            event: Failed failover event
        """
        try:
            logger.warning("Rolling back failover...")
            event.status = FailoverStatus.FAILED

            # Restore original routing
            await self._update_traffic_routes(event.target_region, event.source_region)

            event.rolled_back = True
            event.resolution_notes = "Failover rolled back due to failure"
            logger.info("Failover rollback completed")

        except Exception as e:
            logger.error(f"Rollback failed: {e}", exc_info=True)
            event.resolution_notes = f"Rollback failed: {e}"

    # ========================================================================
    # Data Synchronization Verification
    # ========================================================================

    async def verify_sync(
        self, resources: list[str] | None = None
    ) -> dict[str, SyncVerificationResult]:
        """
        Verify data synchronization for resources.

        Args:
            resources: Resources to verify (None = all)

        Returns:
            Dictionary of resource to sync verification result
        """
        resources_to_check = resources or ["database", "redis"]
        results = {}

        for resource in resources_to_check:
            result = await self._verify_resource_sync(resource)
            results[resource] = result

            # Log issues
            if not result.is_healthy:
                logger.warning(
                    f"Sync issue for {resource}: {result.status.value} "
                    f"({result.lag_seconds}s lag)"
                )

        return results

    async def _verify_resource_sync(self, resource: str) -> SyncVerificationResult:
        """
        Verify synchronization for a specific resource.

        Args:
            resource: Resource to verify

        Returns:
            Sync verification result
        """
        try:
            # Check replication lag
            lag_minutes = await self._check_replication_lag(resource)
            lag_seconds = lag_minutes * 60

            # Determine status
            if lag_seconds <= self.config.max_acceptable_lag_seconds * 0.1:
                status = SyncStatus.IN_SYNC
            elif lag_seconds <= self.config.max_acceptable_lag_seconds:
                status = SyncStatus.LAG
            else:
                status = SyncStatus.OUT_OF_SYNC

            # Check if healthy
            is_healthy = status in [SyncStatus.IN_SYNC, SyncStatus.LAG]

            return SyncVerificationResult(
                resource=resource,
                status=status,
                lag_seconds=lag_seconds,
                last_sync_at=datetime.utcnow(),
                is_healthy=is_healthy,
                details={"target": "secondary", "method": "streaming_replication"},
            )

        except Exception as e:
            logger.error(f"Sync verification failed for {resource}: {e}")
            return SyncVerificationResult(
                resource=resource,
                status=SyncStatus.FAILED,
                is_healthy=False,
                error=str(e),
            )

    # ========================================================================
    # Recovery Plan Management
    # ========================================================================

    def create_recovery_plan(
        self,
        name: str,
        description: str,
        trigger: FailoverTrigger = FailoverTrigger.MANUAL,
        rto_minutes: int = 30,
        rpo_minutes: int = 5,
    ) -> RecoveryPlan:
        """
        Create a new recovery plan.

        Args:
            name: Plan name
            description: Plan description
            trigger: Failover trigger type
            rto_minutes: Recovery time objective
            rpo_minutes: Recovery point objective

        Returns:
            Created recovery plan
        """
        plan = RecoveryPlan(
            name=name,
            description=description,
            trigger=trigger,
            rto_minutes=rto_minutes,
            rpo_minutes=rpo_minutes,
        )

        self._recovery_plans[plan.id] = plan
        logger.info(f"Created recovery plan: {name}")
        return plan

    def add_recovery_step(
        self,
        plan_id: UUID,
        name: str,
        description: str,
        order: int,
        is_automated: bool = True,
        estimated_duration_minutes: int = 5,
        is_critical: bool = True,
        rollback_possible: bool = True,
        dependencies: list[UUID] | None = None,
    ) -> RecoveryStep:
        """
        Add a step to a recovery plan.

        Args:
            plan_id: Recovery plan ID
            name: Step name
            description: Step description
            order: Execution order
            is_automated: Whether step is automated
            estimated_duration_minutes: Estimated duration
            is_critical: Whether step is critical
            rollback_possible: Whether rollback is possible
            dependencies: Step IDs this depends on

        Returns:
            Created recovery step

        Raises:
            ValueError: If plan not found
        """
        plan = self._recovery_plans.get(plan_id)
        if not plan:
            raise ValueError(f"Recovery plan {plan_id} not found")

        step = RecoveryStep(
            name=name,
            description=description,
            order=order,
            is_automated=is_automated,
            estimated_duration_minutes=estimated_duration_minutes,
            is_critical=is_critical,
            rollback_possible=rollback_possible,
            dependencies=dependencies or [],
        )

        plan.steps.append(step)
        plan.steps.sort(key=lambda s: s.order)
        plan.last_updated_at = datetime.utcnow()

        logger.info(f"Added step '{name}' to plan '{plan.name}'")
        return step

    async def execute_recovery_plan(
        self, plan_id: UUID, executed_by: str = "system"
    ) -> RecoveryMetrics:
        """
        Execute a recovery plan.

        Args:
            plan_id: Recovery plan ID
            executed_by: Who is executing the plan

        Returns:
            Recovery metrics from execution

        Raises:
            ValueError: If plan not found or not approved
            RuntimeError: If recovery already in progress
        """
        plan = self._recovery_plans.get(plan_id)
        if not plan:
            raise ValueError(f"Recovery plan {plan_id} not found")

        if plan.status != RecoveryPlanStatus.APPROVED:
            raise ValueError("Plan must be approved before execution")

        if self._active_recovery:
            raise RuntimeError("Recovery already in progress")

        # Initialize metrics
        metrics = RecoveryMetrics(
            rto_target_minutes=plan.rto_minutes,
            rpo_target_minutes=plan.rpo_minutes,
        )
        self._active_recovery = metrics

        # Update plan status
        plan.status = RecoveryPlanStatus.IN_PROGRESS
        plan.last_execution_at = datetime.utcnow()
        plan.execution_count += 1

        logger.info(f"Executing recovery plan: {plan.name}")

        try:
            # Execute steps in order
            for step in plan.steps:
                await self._execute_recovery_step(step, plan, executed_by)

                # Check if critical step failed
                if not step.validation_result and step.is_critical:
                    raise RuntimeError(f"Critical step '{step.name}' failed")

            # Plan completed successfully
            plan.status = RecoveryPlanStatus.COMPLETED
            plan.last_execution_successful = True
            metrics.rto_achieved = True
            metrics.rpo_achieved = True

        except Exception as e:
            logger.error(f"Recovery plan execution failed: {e}", exc_info=True)
            plan.status = RecoveryPlanStatus.FAILED
            plan.last_execution_successful = False
            metrics.issues_encountered.append(str(e))

            # Attempt rollback of completed steps
            await self._rollback_recovery_steps(plan)

        finally:
            # Record completion
            metrics.completed_at = datetime.utcnow()
            metrics.duration_seconds = (
                metrics.completed_at - metrics.started_at
            ).total_seconds()

            plan.last_execution_duration_minutes = metrics.duration_seconds / 60
            plan.last_updated_at = datetime.utcnow()

            self._active_recovery = None

            await self._emit_event(
                "recovery_plan_completed",
                {
                    "plan_id": str(plan_id),
                    "plan_name": plan.name,
                    "successful": plan.last_execution_successful,
                    "duration_minutes": plan.last_execution_duration_minutes,
                },
            )

        return metrics

    async def _execute_recovery_step(
        self, step: RecoveryStep, plan: RecoveryPlan, executed_by: str
    ):
        """
        Execute a single recovery step.

        Args:
            step: Step to execute
            plan: Parent recovery plan
            executed_by: Who is executing
        """
        step.status = RecoveryPlanStatus.IN_PROGRESS
        step.started_at = datetime.utcnow()
        step.executed_by = executed_by

        logger.info(f"Executing step {step.order}: {step.name}")

        try:
            # Check dependencies
            for dep_id in step.dependencies:
                dep_step = next((s for s in plan.steps if s.id == dep_id), None)
                if dep_step and not dep_step.validation_result:
                    raise RuntimeError(
                        f"Dependency step '{dep_step.name}' not completed successfully"
                    )

            # Execute step (simulated for now)
            await asyncio.sleep(step.estimated_duration_minutes * 0.1)  # Simulate work

            # Validate if required
            if step.validation_required:
                step.validation_result = await self._validate_recovery_step(step)
            else:
                step.validation_result = True

            step.status = RecoveryPlanStatus.COMPLETED
            logger.info(f"Step '{step.name}' completed successfully")

            if self._active_recovery:
                self._active_recovery.health_check_passes += 1

        except Exception as e:
            logger.error(f"Step '{step.name}' failed: {e}", exc_info=True)
            step.status = RecoveryPlanStatus.FAILED
            step.error = str(e)
            step.validation_result = False

            if self._active_recovery:
                self._active_recovery.health_check_failures += 1
                self._active_recovery.issues_encountered.append(f"{step.name}: {e}")

        finally:
            step.completed_at = datetime.utcnow()

    async def _validate_recovery_step(self, step: RecoveryStep) -> bool:
        """
        Validate a recovery step execution.

        Args:
            step: Step to validate

        Returns:
            True if validation passed
        """
        # In production, this would perform actual validation
        # For now, simulate
        await asyncio.sleep(0.5)
        return True

    async def _rollback_recovery_steps(self, plan: RecoveryPlan):
        """
        Rollback completed recovery steps.

        Args:
            plan: Recovery plan to rollback
        """
        logger.warning("Rolling back recovery steps...")

        for step in reversed(plan.steps):
            if step.status == RecoveryPlanStatus.COMPLETED and step.rollback_possible:
                try:
                    logger.info(f"Rolling back step: {step.name}")
                    # In production, execute actual rollback
                    await asyncio.sleep(0.5)

                    if self._active_recovery:
                        self._active_recovery.rollback_count += 1

                except Exception as e:
                    logger.error(f"Rollback of '{step.name}' failed: {e}")

    # ========================================================================
    # Testing
    # ========================================================================

    async def test_recovery_plan(
        self, plan_id: UUID, test_mode: bool = True
    ) -> RecoveryMetrics:
        """
        Test a recovery plan without affecting production.

        Args:
            plan_id: Recovery plan ID to test
            test_mode: Whether to run in test mode (safer)

        Returns:
            Recovery metrics from test execution

        Raises:
            ValueError: If plan not found
            PermissionError: If production testing not allowed
        """
        plan = self._recovery_plans.get(plan_id)
        if not plan:
            raise ValueError(f"Recovery plan {plan_id} not found")

        if not test_mode and not self.config.allow_production_testing:
            raise PermissionError("Production testing not allowed")

        logger.info(f"Testing recovery plan: {plan.name} (test_mode={test_mode})")

        # Save original test mode setting
        original_test_mode = self.config.test_mode_enabled
        self.config.test_mode_enabled = test_mode

        try:
            # Execute plan
            metrics = await self.execute_recovery_plan(plan_id, "test_runner")

            # Update test timestamp
            plan.last_tested_at = datetime.utcnow()

            return metrics

        finally:
            # Restore original setting
            self.config.test_mode_enabled = original_test_mode

    # ========================================================================
    # Health Monitoring
    # ========================================================================

    async def monitor_health(self) -> dict[str, Any]:
        """
        Monitor recovery system health.

        Returns:
            Health status dictionary
        """
        self._last_health_check = datetime.utcnow()

        health = {
            "timestamp": self._last_health_check.isoformat(),
            "overall_status": self._current_status.value,
            "rpo_compliance": {},
            "rto_achievability": {},
            "failover_ready": False,
            "sync_status": {},
            "issues": [],
        }

        try:
            # Check RPO compliance
            rpo_results = await self.verify_rpo()
            health["rpo_compliance"] = {
                name: {
                    "compliant": rpo.is_compliant,
                    "lag_minutes": rpo.current_lag_minutes,
                    "max_allowed": rpo.max_data_loss_minutes,
                }
                for name, rpo in rpo_results.items()
            }

            # Check RTO achievability
            rto_results = await self.verify_rto()
            health["rto_achievability"] = {
                name: {
                    "achievable": rto.is_achievable,
                    "estimated_time": rto.estimated_recovery_time_minutes,
                    "target_time": rto.max_downtime_minutes,
                }
                for name, rto in rto_results.items()
            }

            # Check sync status
            sync_results = await self.verify_sync()
            health["sync_status"] = {
                resource: {
                    "status": result.status.value,
                    "healthy": result.is_healthy,
                    "lag_seconds": result.lag_seconds,
                }
                for resource, result in sync_results.items()
            }

            # Determine failover readiness
            all_synced = all(r.is_healthy for r in sync_results.values())
            all_rto_ok = all(r.is_achievable for r in rto_results.values())
            health["failover_ready"] = all_synced and all_rto_ok

            # Collect issues
            for name, rpo in rpo_results.items():
                if not rpo.is_compliant:
                    health["issues"].append(f"RPO violation: {name}")

            for resource, result in sync_results.items():
                if not result.is_healthy:
                    health["issues"].append(f"Sync issue: {resource}")

        except Exception as e:
            logger.error(f"Health monitoring failed: {e}", exc_info=True)
            health["issues"].append(f"Health check error: {e}")

        return health

    # ========================================================================
    # Documentation Generation
    # ========================================================================

    def generate_recovery_documentation(self, plan_id: UUID) -> str:
        """
        Generate comprehensive recovery plan documentation.

        Args:
            plan_id: Recovery plan ID

        Returns:
            Markdown-formatted documentation

        Raises:
            ValueError: If plan not found
        """
        plan = self._recovery_plans.get(plan_id)
        if not plan:
            raise ValueError(f"Recovery plan {plan_id} not found")

        # Build documentation
        doc = f"""# Disaster Recovery Plan: {plan.name}

**Version:** {plan.version}
**Last Updated:** {plan.last_updated_at.strftime("%Y-%m-%d %H:%M:%S UTC")}
**Status:** {plan.status.value}

## Description

{plan.description}

## Recovery Objectives

- **RTO (Recovery Time Objective):** {plan.rto_minutes} minutes
- **RPO (Recovery Point Objective):** {plan.rpo_minutes} minutes

## Trigger

**Type:** {plan.trigger.value}
**Severity:** {plan.severity}

## Prerequisites

"""
        for prereq in plan.prerequisites:
            doc += f"- {prereq}\n"

        doc += "\n## Recovery Steps\n\n"
        doc += "| Order | Step | Automated | Duration | Critical | Rollback |\n"
        doc += "|-------|------|-----------|----------|----------|----------|\n"

        for step in plan.steps:
            doc += (
                f"| {step.order} | {step.name} | "
                f"{'Yes' if step.is_automated else 'No'} | "
                f"{step.estimated_duration_minutes}m | "
                f"{'Yes' if step.is_critical else 'No'} | "
                f"{'Yes' if step.rollback_possible else 'No'} |\n"
            )

        doc += "\n### Step Details\n\n"
        for step in plan.steps:
            doc += f"""
#### {step.order}. {step.name}

**Description:** {step.description}
**Automated:** {"Yes" if step.is_automated else "No"}
**Estimated Duration:** {step.estimated_duration_minutes} minutes
**Critical:** {"Yes" if step.is_critical else "No"}
**Rollback Possible:** {"Yes" if step.rollback_possible else "No"}
**Validation Required:** {"Yes" if step.validation_required else "No"}

"""
            if step.dependencies:
                doc += "**Dependencies:**\n"
                for dep_id in step.dependencies:
                    dep = next((s for s in plan.steps if s.id == dep_id), None)
                    if dep:
                        doc += f"- {dep.name}\n"
                doc += "\n"

        doc += "## Success Criteria\n\n"
        for criteria in plan.success_criteria:
            doc += f"- {criteria}\n"

        doc += "\n## Rollback Plan\n\n"
        doc += plan.rollback_plan or "No rollback plan specified."

        doc += "\n\n## Emergency Contacts\n\n"
        if plan.contact_list:
            for contact in plan.contact_list:
                doc += f"- **{contact.get('role', 'Unknown')}:** "
                doc += f"{contact.get('name', 'Unknown')} - "
                doc += f"{contact.get('contact', 'No contact info')}\n"
        else:
            doc += "No emergency contacts specified.\n"

        doc += "\n## Execution History\n\n"
        doc += f"**Total Executions:** {plan.execution_count}\n"
        if plan.last_execution_at:
            doc += f"**Last Execution:** {plan.last_execution_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            doc += f"**Last Execution Successful:** {'Yes' if plan.last_execution_successful else 'No'}\n"
            doc += f"**Last Execution Duration:** {plan.last_execution_duration_minutes:.1f} minutes\n"

        if plan.last_tested_at:
            doc += f"**Last Tested:** {plan.last_tested_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"

        return doc

    # ========================================================================
    # Event Handling
    # ========================================================================

    def register_event_handler(
        self, event_type: str, handler: Callable[[dict[str, Any]], Any]
    ):
        """
        Register an event handler.

        Args:
            event_type: Type of event to handle
            handler: Callback function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    async def _emit_event(self, event_type: str, data: dict[str, Any]):
        """
        Emit an event to registered handlers.

        Args:
            event_type: Type of event
            data: Event data
        """
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Event handler error ({event_type}): {e}", exc_info=True)

    # ========================================================================
    # Status and Reporting
    # ========================================================================

    def get_status(self) -> dict[str, Any]:
        """
        Get current disaster recovery system status.

        Returns:
            Status dictionary
        """
        return {
            "recovery_status": self._current_status.value,
            "failover_in_progress": self._failover_in_progress is not None,
            "active_recovery": self._active_recovery is not None,
            "rpo_objectives_count": len(self._rpo_objectives),
            "rto_objectives_count": len(self._rto_objectives),
            "recovery_plans_count": len(self._recovery_plans),
            "failover_history_count": len(self._failover_history),
            "last_health_check": (
                self._last_health_check.isoformat() if self._last_health_check else None
            ),
            "auto_failover_enabled": self.config.auto_failover_enabled,
            "test_mode": self.config.test_mode_enabled,
        }

    def get_failover_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get failover event history.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of failover events (most recent first)
        """
        recent_events = self._failover_history[-limit:]
        return [
            {
                "id": str(event.id),
                "timestamp": event.timestamp.isoformat(),
                "trigger": event.trigger.value,
                "reason": event.reason.value,
                "status": event.status.value,
                "successful": event.successful,
                "duration_seconds": event.duration_seconds,
                "rto_achieved": event.rto_achieved,
                "data_loss_detected": event.data_loss_detected,
            }
            for event in reversed(recent_events)
        ]
