"""Core notification engine components."""

from app.notifications.engine.notification_engine import NotificationEngine
from app.notifications.engine.dispatcher import NotificationDispatcher
from app.notifications.engine.queue_manager import NotificationQueueManager
from app.notifications.engine.priority_handler import PriorityHandler
from app.notifications.engine.deduplication import DeduplicationEngine
from app.notifications.engine.batching import BatchingEngine
from app.notifications.engine.rate_limiter import NotificationRateLimiter
from app.notifications.engine.retry_handler import RetryHandler
from app.notifications.engine.preference_manager import PreferenceManager

__all__ = [
    "NotificationEngine",
    "NotificationDispatcher",
    "NotificationQueueManager",
    "PriorityHandler",
    "DeduplicationEngine",
    "BatchingEngine",
    "NotificationRateLimiter",
    "RetryHandler",
    "PreferenceManager",
]
