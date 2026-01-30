"""Real-time notification aggregation."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


class NotificationAggregator:
    """
    Aggregates similar notifications in real-time.

    Aggregation rules:
    - Multiple assignment changes -> Single summary
    - Multiple ACGME warnings -> Combined alert
    - Reduce notification fatigue
    """

    def __init__(self, aggregation_window_minutes: int = 5) -> None:
        """
        Initialize aggregator.

        Args:
            aggregation_window_minutes: Time window for aggregation
        """
        self._window = timedelta(minutes=aggregation_window_minutes)
        self._pending: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._last_aggregation: dict[str, datetime] = {}

    def add(
        self,
        recipient_id: UUID,
        notification_type: str,
        data: dict[str, Any],
    ) -> bool:
        """
        Add notification for aggregation.

        Args:
            recipient_id: Recipient UUID
            notification_type: Type of notification
            data: Notification data

        Returns:
            True if aggregated, False if should send immediately
        """
        key = f"{recipient_id}:{notification_type}"

        # Check if aggregation window active
        if key in self._last_aggregation:
            last_time = self._last_aggregation[key]
            if datetime.utcnow() - last_time < self._window:
                # Add to pending
                self._pending[key].append(data)
                logger.debug("Added to aggregation: %s", key)
                return True

                # Start new aggregation window
        self._pending[key] = [data]
        self._last_aggregation[key] = datetime.utcnow()

        return False

    def get_aggregated(
        self, recipient_id: UUID, notification_type: str
    ) -> list[dict[str, Any]]:
        """Get aggregated notifications for sending."""
        key = f"{recipient_id}:{notification_type}"

        if key in self._pending:
            notifications = self._pending[key]
            del self._pending[key]
            return notifications

        return []
