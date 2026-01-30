"""Health monitoring for notification system."""

from datetime import datetime, timedelta
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class HealthMonitor:
    """
    Monitors notification system health.

    Health checks:
    - Channel availability
    - Queue depth
    - Error rates
    - Latency thresholds
    - Dead letter queue size
    """

    # Health thresholds
    MAX_QUEUE_SIZE = 1000
    MAX_ERROR_RATE_PERCENT = 10.0
    MAX_LATENCY_SECONDS = 60.0
    MAX_DEAD_LETTER_SIZE = 100

    def __init__(self) -> None:
        """Initialize health monitor."""
        self._last_check = datetime.utcnow()
        self._health_status = "healthy"
        self._issues: list[str] = []

    async def check_health(self, engine: Any) -> dict[str, Any]:
        """
        Perform health check on notification engine.

        Args:
            engine: NotificationEngine instance

        Returns:
            Health check results
        """
        self._issues = []
        issues = []

        # Check queue size
        queue_size = await engine.queue_manager.get_queue_size()
        if queue_size > self.MAX_QUEUE_SIZE:
            issues.append(f"Queue size critical: {queue_size}")

            # Check retry/dead letter
        retry_count = await engine.retry_handler.get_pending_count()
        dead_letter_count = await engine.retry_handler.get_dead_letter_count()

        if dead_letter_count > self.MAX_DEAD_LETTER_SIZE:
            issues.append(f"Dead letter queue critical: {dead_letter_count}")

            # Determine overall status
        if issues:
            self._health_status = "unhealthy"
            self._issues = issues
        else:
            self._health_status = "healthy"
            self._issues = []

        self._last_check = datetime.utcnow()

        return {
            "status": self._health_status,
            "timestamp": self._last_check.isoformat(),
            "queue_size": queue_size,
            "retry_count": retry_count,
            "dead_letter_count": dead_letter_count,
            "issues": self._issues,
        }

    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self._health_status == "healthy"

    def get_issues(self) -> list[str]:
        """Get current health issues."""
        return self._issues
