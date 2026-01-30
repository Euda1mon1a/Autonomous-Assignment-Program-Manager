"""Circuit breaker for channel failures."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit breaker for notification channels.

    Prevents cascading failures by temporarily disabling
    channels that are experiencing high error rates.

    States:
    - CLOSED: Normal operation
    - OPEN: Too many failures, reject all requests
    - HALF_OPEN: Testing if channel recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
        success_threshold: int = 2,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout_seconds: Time before attempting recovery
            success_threshold: Successes needed to close circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout_seconds)
        self.success_threshold = success_threshold

        # Per-channel state
        self._channels: dict[str, dict[str, Any]] = {}

    def record_success(self, channel: str) -> None:
        """Record a successful delivery."""
        if channel not in self._channels:
            self._init_channel(channel)

        state = self._channels[channel]

        if state["state"] == CircuitState.HALF_OPEN:
            state["success_count"] += 1
            if state["success_count"] >= self.success_threshold:
                self._close_circuit(channel)
                logger.info("Circuit breaker closed for channel: %s", channel)

                # Reset failure count on success
        state["failure_count"] = 0

    def record_failure(self, channel: str) -> None:
        """Record a failed delivery."""
        if channel not in self._channels:
            self._init_channel(channel)

        state = self._channels[channel]

        if state["state"] == CircuitState.HALF_OPEN:
            # Failed during recovery, reopen circuit
            self._open_circuit(channel)
            logger.warning("Circuit breaker reopened for channel: %s", channel)
        elif state["state"] == CircuitState.CLOSED:
            state["failure_count"] += 1
            if state["failure_count"] >= self.failure_threshold:
                self._open_circuit(channel)
                logger.warning("Circuit breaker opened for channel: %s", channel)

    def can_execute(self, channel: str) -> bool:
        """Check if channel can execute requests."""
        if channel not in self._channels:
            self._init_channel(channel)

        state = self._channels[channel]

        if state["state"] == CircuitState.CLOSED:
            return True

        if state["state"] == CircuitState.OPEN:
            # Check if recovery timeout elapsed
            if datetime.utcnow() >= state["open_until"]:
                self._half_open_circuit(channel)
                logger.info("Circuit breaker half-open for channel: %s", channel)
                return True
            return False

        if state["state"] == CircuitState.HALF_OPEN:
            return True

        return False

    def _init_channel(self, channel: str) -> None:
        """Initialize channel state."""
        self._channels[channel] = {
            "state": CircuitState.CLOSED,
            "failure_count": 0,
            "success_count": 0,
            "open_until": None,
        }

    def _open_circuit(self, channel: str) -> None:
        """Open circuit for a channel."""
        self._channels[channel]["state"] = CircuitState.OPEN
        self._channels[channel]["open_until"] = (
            datetime.utcnow() + self.recovery_timeout
        )
        self._channels[channel]["success_count"] = 0

    def _half_open_circuit(self, channel: str) -> None:
        """Move circuit to half-open state."""
        self._channels[channel]["state"] = CircuitState.HALF_OPEN
        self._channels[channel]["failure_count"] = 0
        self._channels[channel]["success_count"] = 0

    def _close_circuit(self, channel: str) -> None:
        """Close circuit for a channel."""
        self._channels[channel]["state"] = CircuitState.CLOSED
        self._channels[channel]["failure_count"] = 0
        self._channels[channel]["success_count"] = 0

    def get_state(self, channel: str) -> CircuitState:
        """Get circuit state for a channel."""
        if channel not in self._channels:
            return CircuitState.CLOSED
        return self._channels[channel]["state"]

    def reset(self, channel: str | None = None) -> None:
        """Reset circuit breaker state."""
        if channel:
            if channel in self._channels:
                self._close_circuit(channel)
                logger.info("Reset circuit breaker for channel: %s", channel)
        else:
            self._channels.clear()
            logger.info("Reset all circuit breakers")
