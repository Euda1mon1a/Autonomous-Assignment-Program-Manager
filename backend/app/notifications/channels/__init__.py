"""
Notification channels package.

This package re-exports the core channel implementations from channels_core.py
to maintain backward compatibility with existing imports.
"""

from app.notifications.channels_core import (
    AVAILABLE_CHANNELS,
    DeliveryResult,
    EmailChannel,
    InAppChannel,
    NotificationChannel,
    NotificationPayload,
    WebhookChannel,
    get_channel,
)

__all__ = [
    "AVAILABLE_CHANNELS",
    "DeliveryResult",
    "EmailChannel",
    "InAppChannel",
    "NotificationChannel",
    "NotificationPayload",
    "WebhookChannel",
    "get_channel",
]
