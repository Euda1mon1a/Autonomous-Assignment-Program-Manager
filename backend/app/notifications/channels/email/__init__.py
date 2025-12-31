"""Email notification channel implementation."""

from app.notifications.channels.email.email_sender import EmailSender
from app.notifications.channels.email.template_engine import EmailTemplateEngine
from app.notifications.channels.email.html_builder import HTMLEmailBuilder
from app.notifications.channels.email.attachment_handler import AttachmentHandler
from app.notifications.channels.email.tracking import EmailTracker
from app.notifications.channels.email.bounce_handler import BounceHandler
from app.notifications.channels.email.unsubscribe import UnsubscribeManager

__all__ = [
    "EmailSender",
    "EmailTemplateEngine",
    "HTMLEmailBuilder",
    "AttachmentHandler",
    "EmailTracker",
    "BounceHandler",
    "UnsubscribeManager",
]
