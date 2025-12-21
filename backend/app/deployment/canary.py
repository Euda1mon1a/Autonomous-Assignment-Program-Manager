"""
Canary release system for progressive deployment and automatic rollback.

This module implements a production-grade canary release system that:
- Controls traffic percentage to new deployment versions
- Segments users for targeted canary releases
- Collects and compares metrics between canary and baseline
- Automatically rolls back on error rate spikes or metric degradation
- Gradually ramps up traffic based on success criteria
- Provides A/B metric comparison and analysis
- Implements a state machine for release progression

Architecture:
- CanaryReleaseManager: Orchestrates the entire canary process
- UserSegment: Defines user groups for targeting
- TrafficSplit: Controls routing between baseline and canary
- CanaryMetrics: Tracks performance and error metrics
- State machine: PREPARING → RAMPING → MONITORING → COMPLETE/ROLLED_BACK
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class CanaryState(str, Enum):
    """
    State of a canary release in the deployment state machine.

    Progression:
    PREPARING → RAMPING → MONITORING → COMPLETE (success)
                     ↓
                ROLLING_BACK → ROLLED_BACK (failure)
    """
    PREPARING = "preparing"  # Initial setup, pre-flight checks
    RAMPING = "ramping"  # Gradually increasing traffic
    MONITORING = "monitoring"  # At target traffic, observing metrics
    ROLLING_BACK = "rolling_back"  # Reverting to baseline
    ROLLED_BACK = "rolled_back"  # Rollback complete
    COMPLETE = "complete"  # Successfully deployed
    PAUSED = "paused"  # Manually paused for investigation


class CanaryOutcome(str, Enum):
    """Final outcome of a canary release."""
    SUCCESS = "success"  # Canary passed all checks
    AUTOMATIC_ROLLBACK = "automatic_rollback"  # Auto-rolled back due to metrics
    MANUAL_ROLLBACK = "manual_rollback"  # Manually rolled back
    TIMEOUT = "timeout"  # Release exceeded max duration
    ERROR = "error"  # System error during release
    IN_PROGRESS = "in_progress"  # Still ongoing


class RollbackReason(str, Enum):
    """Reason for rolling back a canary release."""
    ERROR_RATE_SPIKE = "error_rate_spike"  # Error rate exceeded threshold
    LATENCY_DEGRADATION = "latency_degradation"  # Response time increased
    AVAILABILITY_DROP = "availability_drop"  # Service availability decreased
    MANUAL = "manual"  # Manual intervention
    TIMEOUT = "timeout"  # Release took too long
    METRIC_COMPARISON_FAILED = "metric_comparison_failed"  # A/B test failed
    HEALTHCHECK_FAILED = "healthcheck_failed"  # Health check failed
    EXCEPTION_RATE = "exception_rate"  # Too many exceptions


@dataclass
class UserSegment:
    """
    User segment definition for targeted canary releases.

    Segments allow testing new versions with specific user groups
    before full rollout (e.g., internal users, beta testers, specific regions).
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""

    # Segment criteria
    user_ids: list[UUID] = field(default_factory=list)  # Specific users
    user_roles: list[str] = field(default_factory=list)  # By role (e.g., "admin")
    organizations: list[UUID] = field(default_factory=list)  # By organization
    percentage: float = 0.0  # Random percentage of all users

    # Geographic or time-based
    regions: list[str] = field(default_factory=list)  # Geographic regions
    time_zones: list[str] = field(default_factory=list)  # Time zones

    # Feature flags
    required_flags: dict[str, bool] = field(default_factory=dict)  # Feature flags

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

    def matches(self, user_id: UUID, user_role: str = None,
                organization_id: UUID = None, user_hash: int = None) -> bool:
        """
        Check if a user matches this segment criteria.

        Args:
            user_id: User's ID
            user_role: User's role
            organization_id: User's organization
            user_hash: Hash of user_id for percentage-based matching

        Returns:
            True if user matches segment criteria
        """
        if not self.is_active:
            return False

        # Check specific user IDs
        if self.user_ids and user_id in self.user_ids:
            return True

        # Check role
        if self.user_roles and user_role in self.user_roles:
            return True

        # Check organization
        if self.organizations and organization_id in self.organizations:
            return True

        # Check percentage-based assignment
        if self.percentage > 0.0 and user_hash is not None:
            threshold = int(self.percentage * 100)
            if (user_hash % 100) < threshold:
                return True

        return False


@dataclass
class TrafficSplit:
    """
    Traffic routing configuration for canary releases.

    Controls what percentage of traffic goes to canary vs baseline.
    """
    canary_percentage: float = 0.0  # 0.0 to 100.0
    baseline_percentage: float = 100.0  # Should be (100 - canary_percentage)

    # Ramp-up schedule
    ramp_increment: float = 10.0  # Increase by this much each step
    ramp_interval_minutes: int = 15  # Wait this long between increases
    target_percentage: float = 100.0  # Final target percentage

    # Safety limits
    max_ramp_percentage: float = 50.0  # Don't go above this during ramp

    def __post_init__(self):
        """Validate percentages sum to 100."""
        total = self.canary_percentage + self.baseline_percentage
        if not (99.9 <= total <= 100.1):  # Allow small floating point error
            raise ValueError(
                f"Traffic percentages must sum to 100, got {total}"
            )

    def can_ramp_up(self) -> bool:
        """Check if we can increase canary traffic."""
        return (
            self.canary_percentage < self.target_percentage and
            self.canary_percentage < self.max_ramp_percentage
        )

    def ramp_up(self) -> "TrafficSplit":
        """
        Increase canary traffic by one increment.

        Returns:
            New TrafficSplit with increased canary percentage
        """
        new_canary = min(
            self.canary_percentage + self.ramp_increment,
            self.target_percentage,
            self.max_ramp_percentage
        )
        new_baseline = 100.0 - new_canary

        return TrafficSplit(
            canary_percentage=new_canary,
            baseline_percentage=new_baseline,
            ramp_increment=self.ramp_increment,
            ramp_interval_minutes=self.ramp_interval_minutes,
            target_percentage=self.target_percentage,
            max_ramp_percentage=self.max_ramp_percentage,
        )


@dataclass
class CanaryMetrics:
    """
    Metrics collected during canary release for comparison.

    Tracks both canary and baseline metrics to detect regressions.
    """
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Request metrics
    canary_request_count: int = 0
    baseline_request_count: int = 0

    # Error metrics
    canary_error_count: int = 0
    baseline_error_count: int = 0
    canary_error_rate: float = 0.0
    baseline_error_rate: float = 0.0

    # Latency metrics (milliseconds)
    canary_p50_latency: float = 0.0
    canary_p95_latency: float = 0.0
    canary_p99_latency: float = 0.0
    baseline_p50_latency: float = 0.0
    baseline_p95_latency: float = 0.0
    baseline_p99_latency: float = 0.0

    # Availability metrics
    canary_availability: float = 100.0  # Percentage
    baseline_availability: float = 100.0

    # Exception metrics
    canary_exception_count: int = 0
    baseline_exception_count: int = 0

    # Custom metrics
    custom_metrics: dict[str, float] = field(default_factory=dict)

    def calculate_error_rates(self):
        """Calculate error rates from counts."""
        if self.canary_request_count > 0:
            self.canary_error_rate = (
                self.canary_error_count / self.canary_request_count * 100.0
            )
        if self.baseline_request_count > 0:
            self.baseline_error_rate = (
                self.baseline_error_count / self.baseline_request_count * 100.0
            )


@dataclass
class MetricComparison:
    """
    A/B comparison of canary vs baseline metrics.

    Determines if canary is performing acceptably compared to baseline.
    """
    metric_name: str
    canary_value: float
    baseline_value: float
    threshold: float  # Maximum acceptable difference
    is_acceptable: bool = True
    difference: float = 0.0
    difference_percentage: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Calculate differences and acceptability."""
        self.difference = self.canary_value - self.baseline_value

        if self.baseline_value != 0:
            self.difference_percentage = (
                abs(self.difference) / self.baseline_value * 100.0
            )
        else:
            self.difference_percentage = 0.0 if self.canary_value == 0 else float('inf')

        self.is_acceptable = self.difference_percentage <= self.threshold


@dataclass
class CanaryConfig:
    """Configuration for a canary release."""

    # Release identification
    release_name: str = ""
    canary_version: str = ""
    baseline_version: str = ""

    # Traffic control
    initial_traffic_percentage: float = 5.0  # Start with 5%
    target_traffic_percentage: float = 100.0
    ramp_increment: float = 10.0  # Increase by 10% each step
    ramp_interval_minutes: int = 15  # Wait 15 min between increases

    # Metric thresholds for automatic rollback
    max_error_rate_increase: float = 2.0  # Max 2% increase in error rate
    max_latency_increase_percentage: float = 20.0  # Max 20% latency increase
    max_availability_decrease: float = 1.0  # Max 1% availability decrease
    max_exception_rate: float = 5.0  # Max 5% exception rate

    # Timing
    minimum_observation_minutes: int = 30  # Observe at each level for 30 min
    maximum_release_duration_hours: int = 24  # Auto-rollback after 24 hours

    # User segmentation
    target_segments: list[UserSegment] = field(default_factory=list)

    # Automatic rollback
    auto_rollback_enabled: bool = True
    rollback_on_error_spike: bool = True
    rollback_on_latency_degradation: bool = True
    rollback_on_availability_drop: bool = True

    # Notifications
    notification_recipients: list[str] = field(default_factory=list)
    slack_channel: str = ""

    # Feature flags
    feature_flags: dict[str, bool] = field(default_factory=dict)


@dataclass
class CanaryRelease:
    """
    State of an active canary release.

    Tracks the entire lifecycle of a canary deployment.
    """
    id: UUID = field(default_factory=uuid4)
    config: CanaryConfig = field(default_factory=CanaryConfig)

    # State tracking
    state: CanaryState = CanaryState.PREPARING
    outcome: CanaryOutcome = CanaryOutcome.IN_PROGRESS

    # Traffic management
    current_traffic: TrafficSplit = field(default_factory=lambda: TrafficSplit(
        canary_percentage=5.0,
        baseline_percentage=95.0
    ))

    # Metrics
    metrics_history: list[CanaryMetrics] = field(default_factory=list)
    current_metrics: CanaryMetrics = field(default_factory=CanaryMetrics)

    # Comparison results
    metric_comparisons: list[MetricComparison] = field(default_factory=list)

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_ramp_at: datetime | None = None

    # Rollback tracking
    rollback_reason: RollbackReason | None = None
    rollback_message: str = ""

    # Health checks
    canary_healthy: bool = True
    baseline_healthy: bool = True
    last_health_check: datetime | None = None

    # Event log
    events: list[dict[str, Any]] = field(default_factory=list)

    def log_event(self, event_type: str, message: str, metadata: dict = None):
        """
        Log an event in the release timeline.

        Args:
            event_type: Type of event (e.g., "ramp_up", "rollback", "metric_check")
            message: Human-readable message
            metadata: Additional event data
        """
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "message": message,
            "state": self.state.value,
            "canary_traffic": self.current_traffic.canary_percentage,
            "metadata": metadata or {},
        }
        self.events.append(event)
        logger.info(f"Canary {self.id} [{event_type}]: {message}")

    def is_expired(self) -> bool:
        """Check if release has exceeded maximum duration."""
        if not self.started_at:
            return False

        elapsed = datetime.utcnow() - self.started_at
        max_duration = timedelta(hours=self.config.maximum_release_duration_hours)
        return elapsed > max_duration

    def can_ramp_up(self) -> bool:
        """Check if we can increase canary traffic."""
        if self.state != CanaryState.RAMPING:
            return False

        if not self.current_traffic.can_ramp_up():
            return False

        # Check minimum observation time
        if self.last_ramp_at:
            min_interval = timedelta(minutes=self.config.ramp_interval_minutes)
            if datetime.utcnow() - self.last_ramp_at < min_interval:
                return False

        return True


class CanaryReleaseManager:
    """
    Manages canary releases with automatic rollback and metric tracking.

    This service orchestrates the entire canary release process:
    1. Initialize release with configuration
    2. Start with low traffic percentage
    3. Monitor metrics continuously
    4. Compare canary vs baseline performance
    5. Automatically rollback on degradation
    6. Gradually ramp up traffic on success
    7. Complete release or rollback

    Usage:
        manager = CanaryReleaseManager()

        # Create release
        config = CanaryConfig(
            release_name="api-v2.1.0",
            canary_version="v2.1.0",
            baseline_version="v2.0.0",
        )
        release = manager.create_release(config)

        # Start release
        manager.start_release(release.id)

        # Collect metrics
        manager.record_request(release.id, is_canary=True, error=False, latency_ms=45)

        # Check health and potentially ramp up
        manager.check_and_ramp(release.id)

        # Get status
        status = manager.get_release_status(release.id)
    """

    def __init__(self):
        self.releases: dict[UUID, CanaryRelease] = {}
        self._event_handlers: dict[str, list[Callable]] = {}
        self._metric_collectors: list[Callable] = []

    def create_release(self, config: CanaryConfig) -> CanaryRelease:
        """
        Create a new canary release.

        Args:
            config: Canary release configuration

        Returns:
            New CanaryRelease instance
        """
        traffic = TrafficSplit(
            canary_percentage=config.initial_traffic_percentage,
            baseline_percentage=100.0 - config.initial_traffic_percentage,
            ramp_increment=config.ramp_increment,
            ramp_interval_minutes=config.ramp_interval_minutes,
            target_percentage=config.target_traffic_percentage,
        )

        release = CanaryRelease(
            config=config,
            current_traffic=traffic,
        )

        self.releases[release.id] = release
        release.log_event("created", f"Created canary release {config.release_name}")

        self._emit_event("release_created", release)

        return release

    def start_release(self, release_id: UUID) -> bool:
        """
        Start a canary release, beginning metric collection.

        Args:
            release_id: ID of the release to start

        Returns:
            True if started successfully
        """
        release = self.releases.get(release_id)
        if not release:
            logger.error(f"Release {release_id} not found")
            return False

        if release.state != CanaryState.PREPARING:
            logger.warning(f"Release {release_id} already started")
            return False

        release.state = CanaryState.RAMPING
        release.started_at = datetime.utcnow()
        release.last_ramp_at = datetime.utcnow()
        release.log_event(
            "started",
            f"Started canary at {release.current_traffic.canary_percentage}% traffic"
        )

        self._emit_event("release_started", release)

        return True

    def record_request(
        self,
        release_id: UUID,
        is_canary: bool,
        error: bool = False,
        latency_ms: float = 0.0,
        exception: bool = False,
    ):
        """
        Record a request to either canary or baseline.

        Args:
            release_id: ID of the release
            is_canary: True if request went to canary, False for baseline
            error: Whether the request resulted in an error
            latency_ms: Request latency in milliseconds
            exception: Whether an exception was raised
        """
        release = self.releases.get(release_id)
        if not release:
            return

        metrics = release.current_metrics

        if is_canary:
            metrics.canary_request_count += 1
            if error:
                metrics.canary_error_count += 1
            if exception:
                metrics.canary_exception_count += 1
            # Update latency percentiles (simplified - use proper percentile tracking)
            metrics.canary_p50_latency = max(metrics.canary_p50_latency, latency_ms)
        else:
            metrics.baseline_request_count += 1
            if error:
                metrics.baseline_error_count += 1
            if exception:
                metrics.baseline_exception_count += 1
            metrics.baseline_p50_latency = max(metrics.baseline_p50_latency, latency_ms)

        metrics.calculate_error_rates()

    def collect_metrics(self, release_id: UUID) -> CanaryMetrics:
        """
        Collect current metrics and save snapshot.

        Args:
            release_id: ID of the release

        Returns:
            Current CanaryMetrics snapshot
        """
        release = self.releases.get(release_id)
        if not release:
            raise ValueError(f"Release {release_id} not found")

        # Call registered metric collectors
        for collector in self._metric_collectors:
            try:
                collector(release)
            except Exception as e:
                logger.error(f"Metric collector error: {e}")

        # Save current metrics to history
        metrics_snapshot = CanaryMetrics(
            timestamp=datetime.utcnow(),
            canary_request_count=release.current_metrics.canary_request_count,
            baseline_request_count=release.current_metrics.baseline_request_count,
            canary_error_count=release.current_metrics.canary_error_count,
            baseline_error_count=release.current_metrics.baseline_error_count,
            canary_error_rate=release.current_metrics.canary_error_rate,
            baseline_error_rate=release.current_metrics.baseline_error_rate,
            canary_p50_latency=release.current_metrics.canary_p50_latency,
            canary_p95_latency=release.current_metrics.canary_p95_latency,
            canary_p99_latency=release.current_metrics.canary_p99_latency,
            baseline_p50_latency=release.current_metrics.baseline_p50_latency,
            baseline_p95_latency=release.current_metrics.baseline_p95_latency,
            baseline_p99_latency=release.current_metrics.baseline_p99_latency,
        )

        release.metrics_history.append(metrics_snapshot)

        return metrics_snapshot

    def compare_metrics(self, release_id: UUID) -> list[MetricComparison]:
        """
        Compare canary vs baseline metrics.

        Args:
            release_id: ID of the release

        Returns:
            List of metric comparisons
        """
        release = self.releases.get(release_id)
        if not release:
            raise ValueError(f"Release {release_id} not found")

        metrics = release.current_metrics
        config = release.config
        comparisons = []

        # Compare error rates
        error_rate_comp = MetricComparison(
            metric_name="error_rate",
            canary_value=metrics.canary_error_rate,
            baseline_value=metrics.baseline_error_rate,
            threshold=config.max_error_rate_increase,
        )
        comparisons.append(error_rate_comp)

        # Compare latency
        if metrics.baseline_p50_latency > 0:
            latency_increase = (
                (metrics.canary_p50_latency - metrics.baseline_p50_latency) /
                metrics.baseline_p50_latency * 100.0
            )
            latency_comp = MetricComparison(
                metric_name="p50_latency",
                canary_value=metrics.canary_p50_latency,
                baseline_value=metrics.baseline_p50_latency,
                threshold=config.max_latency_increase_percentage,
            )
            latency_comp.difference_percentage = abs(latency_increase)
            latency_comp.is_acceptable = latency_increase <= config.max_latency_increase_percentage
            comparisons.append(latency_comp)

        # Compare availability
        availability_comp = MetricComparison(
            metric_name="availability",
            canary_value=metrics.canary_availability,
            baseline_value=metrics.baseline_availability,
            threshold=config.max_availability_decrease,
        )
        comparisons.append(availability_comp)

        release.metric_comparisons = comparisons

        return comparisons

    def check_rollback_conditions(self, release_id: UUID) -> tuple[bool, RollbackReason | None]:
        """
        Check if canary should be rolled back based on metrics.

        Args:
            release_id: ID of the release

        Returns:
            Tuple of (should_rollback, reason)
        """
        release = self.releases.get(release_id)
        if not release:
            return False, None

        if not release.config.auto_rollback_enabled:
            return False, None

        metrics = release.current_metrics
        config = release.config

        # Check if we have enough data
        if metrics.canary_request_count < 10:
            return False, None

        # Check error rate spike
        if config.rollback_on_error_spike:
            error_rate_diff = metrics.canary_error_rate - metrics.baseline_error_rate
            if error_rate_diff > config.max_error_rate_increase:
                return True, RollbackReason.ERROR_RATE_SPIKE

        # Check latency degradation
        if config.rollback_on_latency_degradation and metrics.baseline_p50_latency > 0:
            latency_increase = (
                (metrics.canary_p50_latency - metrics.baseline_p50_latency) /
                metrics.baseline_p50_latency * 100.0
            )
            if latency_increase > config.max_latency_increase_percentage:
                return True, RollbackReason.LATENCY_DEGRADATION

        # Check availability drop
        if config.rollback_on_availability_drop:
            availability_drop = metrics.baseline_availability - metrics.canary_availability
            if availability_drop > config.max_availability_decrease:
                return True, RollbackReason.AVAILABILITY_DROP

        # Check exception rate
        if metrics.canary_request_count > 0:
            exception_rate = (
                metrics.canary_exception_count / metrics.canary_request_count * 100.0
            )
            if exception_rate > config.max_exception_rate:
                return True, RollbackReason.EXCEPTION_RATE

        # Check timeout
        if release.is_expired():
            return True, RollbackReason.TIMEOUT

        # Check metric comparisons
        for comparison in release.metric_comparisons:
            if not comparison.is_acceptable:
                return True, RollbackReason.METRIC_COMPARISON_FAILED

        return False, None

    def rollback(
        self,
        release_id: UUID,
        reason: RollbackReason,
        message: str = "",
    ) -> bool:
        """
        Rollback a canary release to baseline.

        Args:
            release_id: ID of the release to rollback
            reason: Reason for rollback
            message: Additional context

        Returns:
            True if rollback successful
        """
        release = self.releases.get(release_id)
        if not release:
            logger.error(f"Release {release_id} not found")
            return False

        release.state = CanaryState.ROLLING_BACK
        release.rollback_reason = reason
        release.rollback_message = message

        # Set traffic to 100% baseline
        release.current_traffic = TrafficSplit(
            canary_percentage=0.0,
            baseline_percentage=100.0,
        )

        release.log_event(
            "rollback_initiated",
            f"Rolling back due to {reason.value}: {message}",
            {"reason": reason.value}
        )

        # Complete rollback
        release.state = CanaryState.ROLLED_BACK
        release.outcome = (
            CanaryOutcome.AUTOMATIC_ROLLBACK
            if reason != RollbackReason.MANUAL
            else CanaryOutcome.MANUAL_ROLLBACK
        )
        release.completed_at = datetime.utcnow()

        release.log_event(
            "rollback_complete",
            "Rollback complete, all traffic routed to baseline"
        )

        self._emit_event("release_rolled_back", release)

        return True

    def ramp_up(self, release_id: UUID) -> bool:
        """
        Increase canary traffic by one increment.

        Args:
            release_id: ID of the release

        Returns:
            True if ramp up successful
        """
        release = self.releases.get(release_id)
        if not release:
            logger.error(f"Release {release_id} not found")
            return False

        if not release.can_ramp_up():
            return False

        old_percentage = release.current_traffic.canary_percentage
        release.current_traffic = release.current_traffic.ramp_up()
        release.last_ramp_at = datetime.utcnow()
        new_percentage = release.current_traffic.canary_percentage

        release.log_event(
            "ramp_up",
            f"Ramped up canary traffic from {old_percentage}% to {new_percentage}%"
        )

        # Check if we've reached target
        if new_percentage >= release.config.target_traffic_percentage:
            release.state = CanaryState.MONITORING
            release.log_event(
                "target_reached",
                f"Reached target traffic of {new_percentage}%"
            )

        self._emit_event("traffic_ramped", release)

        return True

    def check_and_ramp(self, release_id: UUID) -> dict[str, Any]:
        """
        Check metrics and ramp up if healthy, rollback if not.

        Args:
            release_id: ID of the release

        Returns:
            Dict with action taken and status
        """
        release = self.releases.get(release_id)
        if not release:
            return {"error": "Release not found"}

        # Collect current metrics
        self.collect_metrics(release_id)

        # Compare metrics
        comparisons = self.compare_metrics(release_id)

        # Check rollback conditions
        should_rollback, reason = self.check_rollback_conditions(release_id)

        if should_rollback:
            self.rollback(release_id, reason, "Automatic rollback triggered")
            return {
                "action": "rollback",
                "reason": reason.value,
                "state": release.state.value,
            }

        # Check if we can ramp up
        if release.can_ramp_up():
            # Verify minimum observation time
            if release.last_ramp_at:
                min_observation = timedelta(
                    minutes=release.config.minimum_observation_minutes
                )
                if datetime.utcnow() - release.last_ramp_at < min_observation:
                    return {
                        "action": "waiting",
                        "message": "Observing current traffic level",
                        "state": release.state.value,
                    }

            # All checks passed, ramp up
            self.ramp_up(release_id)
            return {
                "action": "ramp_up",
                "new_percentage": release.current_traffic.canary_percentage,
                "state": release.state.value,
            }

        # Check if monitoring is complete
        if release.state == CanaryState.MONITORING:
            min_observation = timedelta(
                minutes=release.config.minimum_observation_minutes
            )
            if release.last_ramp_at and datetime.utcnow() - release.last_ramp_at > min_observation:
                self.complete_release(release_id)
                return {
                    "action": "complete",
                    "state": release.state.value,
                }

        return {
            "action": "monitoring",
            "state": release.state.value,
        }

    def complete_release(self, release_id: UUID) -> bool:
        """
        Mark a canary release as successfully completed.

        Args:
            release_id: ID of the release

        Returns:
            True if completed successfully
        """
        release = self.releases.get(release_id)
        if not release:
            return False

        release.state = CanaryState.COMPLETE
        release.outcome = CanaryOutcome.SUCCESS
        release.completed_at = datetime.utcnow()

        release.log_event(
            "complete",
            f"Canary release completed successfully at 100% traffic"
        )

        self._emit_event("release_completed", release)

        return True

    def pause_release(self, release_id: UUID, reason: str = "") -> bool:
        """
        Pause a canary release for manual investigation.

        Args:
            release_id: ID of the release
            reason: Reason for pausing

        Returns:
            True if paused successfully
        """
        release = self.releases.get(release_id)
        if not release:
            return False

        release.state = CanaryState.PAUSED
        release.log_event("paused", f"Release paused: {reason}")

        self._emit_event("release_paused", release)

        return True

    def resume_release(self, release_id: UUID) -> bool:
        """
        Resume a paused canary release.

        Args:
            release_id: ID of the release

        Returns:
            True if resumed successfully
        """
        release = self.releases.get(release_id)
        if not release or release.state != CanaryState.PAUSED:
            return False

        release.state = CanaryState.RAMPING
        release.log_event("resumed", "Release resumed")

        self._emit_event("release_resumed", release)

        return True

    def get_release_status(self, release_id: UUID) -> dict[str, Any]:
        """
        Get current status of a canary release.

        Args:
            release_id: ID of the release

        Returns:
            Dict with release status and metrics
        """
        release = self.releases.get(release_id)
        if not release:
            return {"error": "Release not found"}

        return {
            "release_id": str(release.id),
            "release_name": release.config.release_name,
            "state": release.state.value,
            "outcome": release.outcome.value,
            "canary_version": release.config.canary_version,
            "baseline_version": release.config.baseline_version,
            "traffic": {
                "canary_percentage": release.current_traffic.canary_percentage,
                "baseline_percentage": release.current_traffic.baseline_percentage,
            },
            "metrics": {
                "canary_requests": release.current_metrics.canary_request_count,
                "baseline_requests": release.current_metrics.baseline_request_count,
                "canary_error_rate": release.current_metrics.canary_error_rate,
                "baseline_error_rate": release.current_metrics.baseline_error_rate,
                "canary_p50_latency": release.current_metrics.canary_p50_latency,
                "baseline_p50_latency": release.current_metrics.baseline_p50_latency,
            },
            "comparisons": [
                {
                    "metric": c.metric_name,
                    "canary": c.canary_value,
                    "baseline": c.baseline_value,
                    "acceptable": c.is_acceptable,
                    "difference": c.difference_percentage,
                }
                for c in release.metric_comparisons
            ],
            "health": {
                "canary_healthy": release.canary_healthy,
                "baseline_healthy": release.baseline_healthy,
            },
            "timing": {
                "created_at": release.created_at.isoformat(),
                "started_at": release.started_at.isoformat() if release.started_at else None,
                "completed_at": release.completed_at.isoformat() if release.completed_at else None,
                "elapsed_minutes": (
                    (datetime.utcnow() - release.started_at).total_seconds() / 60.0
                    if release.started_at else 0
                ),
            },
            "rollback": {
                "reason": release.rollback_reason.value if release.rollback_reason else None,
                "message": release.rollback_message,
            } if release.rollback_reason else None,
        }

    def get_active_releases(self) -> list[CanaryRelease]:
        """
        Get all active (non-completed) canary releases.

        Returns:
            List of active CanaryRelease instances
        """
        return [
            r for r in self.releases.values()
            if r.state not in (CanaryState.COMPLETE, CanaryState.ROLLED_BACK)
        ]

    def register_event_handler(
        self,
        event_type: str,
        handler: Callable[[CanaryRelease], Any],
    ):
        """
        Register a handler for canary events.

        Event types:
        - release_created
        - release_started
        - traffic_ramped
        - release_rolled_back
        - release_completed
        - release_paused
        - release_resumed

        Args:
            event_type: Type of event to handle
            handler: Callable that takes a CanaryRelease
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def register_metric_collector(self, collector: Callable[[CanaryRelease], None]):
        """
        Register a custom metric collector.

        Collectors are called during collect_metrics() to gather
        custom metrics from external sources.

        Args:
            collector: Callable that takes a CanaryRelease and updates its metrics
        """
        self._metric_collectors.append(collector)

    def _emit_event(self, event_type: str, release: CanaryRelease):
        """Emit event to registered handlers."""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(release)
            except Exception as e:
                logger.error(f"Event handler error ({event_type}): {e}")

    def cleanup_old_releases(self, days: int = 7) -> int:
        """
        Remove completed releases older than specified days.

        Args:
            days: Remove releases older than this many days

        Returns:
            Number of releases removed
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        to_remove = [
            release_id
            for release_id, release in self.releases.items()
            if release.completed_at and release.completed_at < cutoff
        ]

        for release_id in to_remove:
            del self.releases[release_id]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old canary releases")

        return len(to_remove)

    def route_request(
        self,
        release_id: UUID,
        user_id: UUID,
        user_role: str = None,
        organization_id: UUID = None,
    ) -> str:
        """
        Determine if a request should go to canary or baseline.

        Args:
            release_id: ID of the release
            user_id: User making the request
            user_role: User's role
            organization_id: User's organization

        Returns:
            "canary" or "baseline"
        """
        release = self.releases.get(release_id)
        if not release or release.state in (CanaryState.COMPLETE, CanaryState.ROLLED_BACK):
            return "baseline"

        # Check if user matches any target segment
        user_hash = hash(user_id) % 100
        for segment in release.config.target_segments:
            if segment.matches(user_id, user_role, organization_id, user_hash):
                return "canary"

        # Use traffic percentage for general population
        if user_hash < int(release.current_traffic.canary_percentage):
            return "canary"

        return "baseline"
