"""
Circuit Breaker State Machine.

Implements the three-state circuit breaker pattern:

CLOSED (Normal):
- All requests pass through
- Failures are counted
- When failure threshold reached, transition to OPEN

OPEN (Tripped):
- All requests fail immediately (fail-fast)
- No load on downstream service
- After timeout, transition to HALF_OPEN

HALF_OPEN (Testing):
- Limited requests pass through to test recovery
- Success threshold must be met to return to CLOSED
- Any failure returns to OPEN
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """The three states of a circuit breaker."""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Failing, reject requests
    HALF_OPEN = "half_open"    # Testing recovery


@dataclass
class StateTransition:
    """Record of a state transition."""
    from_state: CircuitState
    to_state: CircuitState
    timestamp: datetime
    reason: str
    failure_count: int = 0
    success_count: int = 0


@dataclass
class CircuitMetrics:
    """Metrics for circuit breaker monitoring."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_transitions: list[StateTransition] = field(default_factory=list)

    @property
    def failure_rate(self) -> float:
        """Calculate current failure rate (0.0 - 1.0)."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests

    @property
    def success_rate(self) -> float:
        """Calculate current success rate (0.0 - 1.0)."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    def reset_consecutive_counters(self):
        """Reset consecutive failure/success counters."""
        self.consecutive_failures = 0
        self.consecutive_successes = 0


class StateMachine:
    """
    State machine for circuit breaker transitions.

    Manages state transitions based on thresholds and timeouts.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        """
        Initialize state machine.

        Args:
            failure_threshold: Failures before opening circuit
            success_threshold: Successes needed to close from half-open
            timeout_seconds: Time to wait before trying half-open
            half_open_max_calls: Max concurrent calls in half-open state
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.half_open_max_calls = half_open_max_calls

        self.current_state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self.opened_at: Optional[datetime] = None
        self.half_open_calls_in_flight = 0

    def record_success(self) -> CircuitState:
        """
        Record a successful call.

        Returns:
            Current state after processing success
        """
        self.metrics.total_requests += 1
        self.metrics.successful_requests += 1
        self.metrics.consecutive_successes += 1
        self.metrics.consecutive_failures = 0
        self.metrics.last_success_time = datetime.utcnow()

        if self.current_state == CircuitState.HALF_OPEN:
            # In half-open, successes count toward recovery
            if self.metrics.consecutive_successes >= self.success_threshold:
                self._transition_to_closed("Success threshold met")

        return self.current_state

    def record_failure(self) -> CircuitState:
        """
        Record a failed call.

        Returns:
            Current state after processing failure
        """
        self.metrics.total_requests += 1
        self.metrics.failed_requests += 1
        self.metrics.consecutive_failures += 1
        self.metrics.consecutive_successes = 0
        self.metrics.last_failure_time = datetime.utcnow()

        if self.current_state == CircuitState.CLOSED:
            # In closed state, check if we should open
            if self.metrics.consecutive_failures >= self.failure_threshold:
                self._transition_to_open("Failure threshold exceeded")
        elif self.current_state == CircuitState.HALF_OPEN:
            # In half-open, any failure returns to open
            self._transition_to_open("Failure during recovery test")

        return self.current_state

    def record_rejection(self):
        """Record a rejected call (circuit open)."""
        self.metrics.rejected_requests += 1

    def should_allow_request(self) -> bool:
        """
        Determine if a request should be allowed.

        Returns:
            True if request should proceed, False if rejected
        """
        if self.current_state == CircuitState.CLOSED:
            return True

        if self.current_state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self._should_attempt_reset():
                self._transition_to_half_open("Timeout elapsed, testing recovery")
                return True
            return False

        if self.current_state == CircuitState.HALF_OPEN:
            # Allow limited concurrent calls
            return self.half_open_calls_in_flight < self.half_open_max_calls

        return False

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.opened_at:
            return False
        return datetime.utcnow() >= self.opened_at + self.timeout

    def _transition_to_closed(self, reason: str):
        """Transition to CLOSED state."""
        old_state = self.current_state
        self.current_state = CircuitState.CLOSED
        self.opened_at = None
        self.metrics.reset_consecutive_counters()

        transition = StateTransition(
            from_state=old_state,
            to_state=CircuitState.CLOSED,
            timestamp=datetime.utcnow(),
            reason=reason,
            success_count=self.metrics.consecutive_successes,
        )
        self.metrics.state_transitions.append(transition)

        logger.info(
            f"Circuit breaker transitioned: {old_state.value} -> CLOSED. "
            f"Reason: {reason}"
        )

    def _transition_to_open(self, reason: str):
        """Transition to OPEN state."""
        old_state = self.current_state
        self.current_state = CircuitState.OPEN
        self.opened_at = datetime.utcnow()

        transition = StateTransition(
            from_state=old_state,
            to_state=CircuitState.OPEN,
            timestamp=datetime.utcnow(),
            reason=reason,
            failure_count=self.metrics.consecutive_failures,
        )
        self.metrics.state_transitions.append(transition)

        logger.warning(
            f"Circuit breaker OPENED: {old_state.value} -> OPEN. "
            f"Reason: {reason}. Consecutive failures: {self.metrics.consecutive_failures}"
        )

    def _transition_to_half_open(self, reason: str):
        """Transition to HALF_OPEN state."""
        old_state = self.current_state
        self.current_state = CircuitState.HALF_OPEN
        self.metrics.reset_consecutive_counters()
        self.half_open_calls_in_flight = 0

        transition = StateTransition(
            from_state=old_state,
            to_state=CircuitState.HALF_OPEN,
            timestamp=datetime.utcnow(),
            reason=reason,
        )
        self.metrics.state_transitions.append(transition)

        logger.info(
            f"Circuit breaker transitioned: {old_state.value} -> HALF_OPEN. "
            f"Reason: {reason}"
        )

    def force_open(self, reason: str = "Manual override"):
        """
        Manually force circuit to OPEN state.

        Args:
            reason: Reason for manual override
        """
        if self.current_state != CircuitState.OPEN:
            self._transition_to_open(reason)

    def force_closed(self, reason: str = "Manual override"):
        """
        Manually force circuit to CLOSED state.

        Args:
            reason: Reason for manual override
        """
        if self.current_state != CircuitState.CLOSED:
            self._transition_to_closed(reason)

    def reset(self):
        """Reset circuit breaker to initial state."""
        self.current_state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self.opened_at = None
        self.half_open_calls_in_flight = 0
        logger.info("Circuit breaker reset to initial state")

    def get_status(self) -> dict:
        """
        Get current status of the circuit breaker.

        Returns:
            Dictionary with state and metrics
        """
        return {
            "state": self.current_state.value,
            "failure_rate": self.metrics.failure_rate,
            "success_rate": self.metrics.success_rate,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "rejected_requests": self.metrics.rejected_requests,
            "consecutive_failures": self.metrics.consecutive_failures,
            "consecutive_successes": self.metrics.consecutive_successes,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "last_failure_time": (
                self.metrics.last_failure_time.isoformat()
                if self.metrics.last_failure_time else None
            ),
            "last_success_time": (
                self.metrics.last_success_time.isoformat()
                if self.metrics.last_success_time else None
            ),
            "recent_transitions": [
                {
                    "from": t.from_state.value,
                    "to": t.to_state.value,
                    "timestamp": t.timestamp.isoformat(),
                    "reason": t.reason,
                }
                for t in self.metrics.state_transitions[-10:]  # Last 10 transitions
            ],
        }
