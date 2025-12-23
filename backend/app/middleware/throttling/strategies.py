"""
Throttling strategies for request handling.

Implements different strategies for handling requests when
capacity is reached, including queuing, rejection, and degradation.
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.middleware.throttling.config import (
    DEGRADATION_THRESHOLDS,
    ThrottleConfig,
    ThrottlePriority,
)
from app.middleware.throttling.storage import ThrottleMetrics, ThrottleStorage

logger = logging.getLogger(__name__)


class ThrottleAction(str, Enum):
    """Actions to take when throttling."""

    ALLOW = "allow"  # Allow request immediately
    QUEUE = "queue"  # Queue request for later processing
    REJECT = "reject"  # Reject request immediately
    DEGRADE = "degrade"  # Allow but mark as degraded


class ThrottleDecision:
    """Decision result from throttling strategy."""

    def __init__(
        self,
        action: ThrottleAction,
        reason: str | None = None,
        wait_time: float | None = None,
        retry_after: int | None = None,
    ):
        """
        Initialize throttle decision.

        Args:
            action: Action to take
            reason: Reason for the decision
            wait_time: Time to wait before retry (seconds)
            retry_after: Retry-After header value (seconds)
        """
        self.action = action
        self.reason = reason or ""
        self.wait_time = wait_time or 0.0
        self.retry_after = retry_after or 0


class ThrottleStrategy(ABC):
    """Base class for throttling strategies."""

    def __init__(self, storage: ThrottleStorage):
        """
        Initialize strategy.

        Args:
            storage: Throttle storage instance
        """
        self.storage = storage

    @abstractmethod
    async def decide(
        self,
        request: Request,
        config: ThrottleConfig,
        metrics: ThrottleMetrics,
        priority: ThrottlePriority,
    ) -> ThrottleDecision:
        """
        Decide what to do with a request.

        Args:
            request: FastAPI request
            config: Throttle configuration
            metrics: Current throttle metrics
            priority: Request priority

        Returns:
            ThrottleDecision with action to take
        """
        pass


class SimpleThrottleStrategy(ThrottleStrategy):
    """
    Simple throttling strategy.

    - Allow if capacity available
    - Reject if capacity full
    - No queuing or degradation
    """

    async def decide(
        self,
        request: Request,
        config: ThrottleConfig,
        metrics: ThrottleMetrics,
        priority: ThrottlePriority,
    ) -> ThrottleDecision:
        """Decide based on simple capacity check."""
        if metrics.utilization < 1.0:
            return ThrottleDecision(
                action=ThrottleAction.ALLOW,
                reason="Capacity available",
            )
        else:
            return ThrottleDecision(
                action=ThrottleAction.REJECT,
                reason="Maximum concurrent requests reached",
                retry_after=5,
            )


class QueuedThrottleStrategy(ThrottleStrategy):
    """
    Queued throttling strategy.

    - Allow if capacity available
    - Queue if capacity full but queue has space
    - Reject if both capacity and queue are full
    """

    async def decide(
        self,
        request: Request,
        config: ThrottleConfig,
        metrics: ThrottleMetrics,
        priority: ThrottlePriority,
    ) -> ThrottleDecision:
        """Decide with queuing support."""
        # Allow if capacity available
        if metrics.utilization < 1.0:
            return ThrottleDecision(
                action=ThrottleAction.ALLOW,
                reason="Capacity available",
            )

        # Queue if space available
        if metrics.queue_utilization < 1.0:
            # Estimate wait time based on queue position
            wait_time = metrics.queued_requests * 0.5  # Assume 0.5s per request
            return ThrottleDecision(
                action=ThrottleAction.QUEUE,
                reason="Queued due to capacity limit",
                wait_time=wait_time,
                retry_after=int(wait_time) + 1,
            )

        # Reject if both full
        return ThrottleDecision(
            action=ThrottleAction.REJECT,
            reason="Maximum capacity and queue size reached",
            retry_after=10,
        )


class PriorityThrottleStrategy(ThrottleStrategy):
    """
    Priority-based throttling strategy.

    - Critical/High priority: Always try to allow or queue
    - Normal priority: Standard throttling
    - Low/Background: Reject earlier to preserve capacity
    """

    async def decide(
        self,
        request: Request,
        config: ThrottleConfig,
        metrics: ThrottleMetrics,
        priority: ThrottlePriority,
    ) -> ThrottleDecision:
        """Decide based on priority and utilization."""
        utilization = metrics.utilization

        # Critical priority - always try to allow
        if priority == ThrottlePriority.CRITICAL:
            if utilization < 0.98:  # Allow up to 98% for critical
                return ThrottleDecision(
                    action=ThrottleAction.ALLOW,
                    reason="Critical priority request",
                )
            elif metrics.queue_utilization < 0.9:
                return ThrottleDecision(
                    action=ThrottleAction.QUEUE,
                    reason="Critical priority queued",
                    wait_time=1.0,
                    retry_after=2,
                )
            else:
                return ThrottleDecision(
                    action=ThrottleAction.REJECT,
                    reason="System at critical capacity",
                    retry_after=5,
                )

        # High priority - generous limits
        if priority == ThrottlePriority.HIGH:
            if utilization < 0.95:
                return ThrottleDecision(
                    action=ThrottleAction.ALLOW,
                    reason="High priority request",
                )
            elif metrics.queue_utilization < 0.8:
                wait_time = metrics.queued_requests * 0.3
                return ThrottleDecision(
                    action=ThrottleAction.QUEUE,
                    reason="High priority queued",
                    wait_time=wait_time,
                    retry_after=int(wait_time) + 1,
                )
            else:
                return ThrottleDecision(
                    action=ThrottleAction.REJECT,
                    reason="High priority capacity reached",
                    retry_after=10,
                )

        # Normal priority - standard throttling
        if priority == ThrottlePriority.NORMAL:
            if utilization < 0.85:
                return ThrottleDecision(
                    action=ThrottleAction.ALLOW,
                    reason="Normal priority allowed",
                )
            elif metrics.queue_utilization < 0.7:
                wait_time = metrics.queued_requests * 0.5
                return ThrottleDecision(
                    action=ThrottleAction.QUEUE,
                    reason="Normal priority queued",
                    wait_time=wait_time,
                    retry_after=int(wait_time) + 1,
                )
            else:
                return ThrottleDecision(
                    action=ThrottleAction.REJECT,
                    reason="Normal priority capacity reached",
                    retry_after=15,
                )

        # Low priority - conservative limits
        if priority == ThrottlePriority.LOW:
            if utilization < 0.70:
                return ThrottleDecision(
                    action=ThrottleAction.ALLOW,
                    reason="Low priority allowed",
                )
            elif utilization < 0.80 and metrics.queue_utilization < 0.5:
                wait_time = metrics.queued_requests * 0.8
                return ThrottleDecision(
                    action=ThrottleAction.QUEUE,
                    reason="Low priority queued",
                    wait_time=wait_time,
                    retry_after=int(wait_time) + 5,
                )
            else:
                return ThrottleDecision(
                    action=ThrottleAction.REJECT,
                    reason="Low priority rejected to preserve capacity",
                    retry_after=30,
                )

        # Background priority - strictest limits
        if utilization < 0.60:
            return ThrottleDecision(
                action=ThrottleAction.ALLOW,
                reason="Background request allowed",
            )
        else:
            return ThrottleDecision(
                action=ThrottleAction.REJECT,
                reason="Background requests rejected to preserve capacity",
                retry_after=60,
            )


class AdaptiveThrottleStrategy(ThrottleStrategy):
    """
    Adaptive throttling strategy with graceful degradation.

    Adapts behavior based on system utilization:
    - < 70%: Normal operation
    - 70-80%: Start warning, queue low priority
    - 80-90%: Aggressive throttling, reject low priority
    - 90-95%: Reject normal priority, only high/critical
    - > 95%: Emergency mode, minimal requests
    """

    async def decide(
        self,
        request: Request,
        config: ThrottleConfig,
        metrics: ThrottleMetrics,
        priority: ThrottlePriority,
    ) -> ThrottleDecision:
        """Decide with adaptive degradation based on utilization."""
        utilization = metrics.utilization

        # Normal operation (< 70% utilization)
        if utilization < DEGRADATION_THRESHOLDS["warning"]:
            if utilization < 1.0:
                return ThrottleDecision(
                    action=ThrottleAction.ALLOW,
                    reason="Normal operation",
                )
            elif metrics.queue_utilization < 1.0:
                wait_time = metrics.queued_requests * 0.5
                return ThrottleDecision(
                    action=ThrottleAction.QUEUE,
                    reason="Normal queuing",
                    wait_time=wait_time,
                    retry_after=int(wait_time) + 1,
                )

        # Warning level (70-80% utilization)
        elif utilization < DEGRADATION_THRESHOLDS["throttle"]:
            # Allow critical and high
            if priority in [ThrottlePriority.CRITICAL, ThrottlePriority.HIGH]:
                if utilization < 1.0:
                    return ThrottleDecision(
                        action=ThrottleAction.ALLOW,
                        reason="High/Critical priority in warning state",
                    )
                elif metrics.queue_utilization < 0.8:
                    return ThrottleDecision(
                        action=ThrottleAction.QUEUE,
                        reason="High/Critical queued in warning state",
                        wait_time=2.0,
                        retry_after=3,
                    )

            # Queue normal priority
            elif priority == ThrottlePriority.NORMAL:
                if utilization < 0.75 and metrics.utilization < 1.0:
                    return ThrottleDecision(
                        action=ThrottleAction.ALLOW,
                        reason="Normal priority allowed in warning state",
                    )
                elif metrics.queue_utilization < 0.6:
                    return ThrottleDecision(
                        action=ThrottleAction.QUEUE,
                        reason="Normal queued in warning state",
                        wait_time=5.0,
                        retry_after=10,
                    )

            # Reject low/background
            return ThrottleDecision(
                action=ThrottleAction.REJECT,
                reason="Low priority rejected in warning state",
                retry_after=30,
            )

        # Throttle level (80-90% utilization)
        elif utilization < DEGRADATION_THRESHOLDS["reject"]:
            # Critical: Allow or queue
            if priority == ThrottlePriority.CRITICAL:
                if utilization < 0.95:
                    return ThrottleDecision(
                        action=ThrottleAction.ALLOW,
                        reason="Critical priority in throttle state",
                    )
                elif metrics.queue_utilization < 0.9:
                    return ThrottleDecision(
                        action=ThrottleAction.QUEUE,
                        reason="Critical queued in throttle state",
                        wait_time=1.0,
                        retry_after=2,
                    )

            # High: Allow with limits
            elif priority == ThrottlePriority.HIGH:
                if utilization < 0.85:
                    return ThrottleDecision(
                        action=ThrottleAction.ALLOW,
                        reason="High priority allowed in throttle state",
                    )
                elif metrics.queue_utilization < 0.7:
                    return ThrottleDecision(
                        action=ThrottleAction.QUEUE,
                        reason="High queued in throttle state",
                        wait_time=3.0,
                        retry_after=5,
                    )

            # Reject normal and lower
            return ThrottleDecision(
                action=ThrottleAction.REJECT,
                reason="System in throttle state - high priority only",
                retry_after=20,
            )

        # Reject level (90-95% utilization)
        elif utilization < DEGRADATION_THRESHOLDS["critical"]:
            # Only critical and high priority
            if priority == ThrottlePriority.CRITICAL:
                if utilization < 0.98:
                    return ThrottleDecision(
                        action=ThrottleAction.ALLOW,
                        reason="Critical priority in reject state",
                    )
            elif priority == ThrottlePriority.HIGH:
                if utilization < 0.92 and metrics.queue_utilization < 0.5:
                    return ThrottleDecision(
                        action=ThrottleAction.QUEUE,
                        reason="High priority queued in reject state",
                        wait_time=5.0,
                        retry_after=10,
                    )

            return ThrottleDecision(
                action=ThrottleAction.REJECT,
                reason="System in reject state - critical priority only",
                retry_after=30,
            )

        # Critical/Emergency level (> 95% utilization)
        else:
            # Only critical priority allowed
            if priority == ThrottlePriority.CRITICAL and utilization < 0.99:
                return ThrottleDecision(
                    action=ThrottleAction.ALLOW,
                    reason="Critical priority in emergency state",
                )

            return ThrottleDecision(
                action=ThrottleAction.REJECT,
                reason="System in emergency state - critical maintenance required",
                retry_after=60,
            )


def create_throttle_response(decision: ThrottleDecision) -> JSONResponse:
    """
    Create HTTP response for throttle decision.

    Args:
        decision: Throttle decision

    Returns:
        JSONResponse with appropriate status and headers
    """
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "Service Throttled",
            "message": decision.reason,
            "retry_after": decision.retry_after,
        },
        headers={
            "Retry-After": str(decision.retry_after),
            "X-Throttle-Action": decision.action.value,
        },
    )
