"""Email-specific queue management."""

from collections import deque
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class QueuedEmail(BaseModel):
    """Queued email item."""

    id: UUID = Field(default_factory=uuid4)
    to_address: str
    subject: str
    body: str
    html_body: str | None = None
    priority: int = 0
    queued_at: datetime = Field(default_factory=datetime.utcnow)
    retry_count: int = 0


class EmailQueue:
    """
    Email-specific queue with priority handling.

    Provides separate queues for different priority levels
    and implements FIFO within each priority.
    """

    def __init__(self) -> None:
        """Initialize email queue."""
        self._high: deque[QueuedEmail] = deque()
        self._normal: deque[QueuedEmail] = deque()
        self._low: deque[QueuedEmail] = deque()

    def enqueue(
        self,
        to_address: str,
        subject: str,
        body: str,
        html_body: str | None = None,
        priority: int = 0,
    ) -> UUID:
        """
        Add email to queue.

        Args:
            to_address: Recipient email
            subject: Email subject
            body: Email body
            html_body: Optional HTML body
            priority: Priority score

        Returns:
            Queued email ID
        """
        email = QueuedEmail(
            to_address=to_address,
            subject=subject,
            body=body,
            html_body=html_body,
            priority=priority,
        )

        if priority >= 75:
            self._high.append(email)
        elif priority >= 25:
            self._normal.append(email)
        else:
            self._low.append(email)

        logger.debug("Enqueued email to %s (priority: %d)", to_address, priority)

        return email.id

    def dequeue(self) -> QueuedEmail | None:
        """Dequeue highest priority email."""
        if self._high:
            return self._high.popleft()
        elif self._normal:
            return self._normal.popleft()
        elif self._low:
            return self._low.popleft()

        return None

    def size(self) -> int:
        """Get total queue size."""
        return len(self._high) + len(self._normal) + len(self._low)
