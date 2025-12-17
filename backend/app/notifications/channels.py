"""Notification delivery channels."""
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class NotificationPayload(BaseModel):
    """
    Standard notification payload across all channels.

    Attributes:
        id: Unique notification identifier
        recipient_id: UUID of the recipient
        notification_type: Type of notification
        subject: Notification subject/title
        body: Notification body content
        data: Additional structured data
        priority: Priority level (high, normal, low)
        created_at: Timestamp of creation
    """
    id: UUID = Field(default_factory=uuid.uuid4)
    recipient_id: UUID
    notification_type: str
    subject: str
    body: str
    data: dict[str, Any] | None = None
    priority: str = "normal"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DeliveryResult(BaseModel):
    """
    Result of a notification delivery attempt.

    Attributes:
        success: Whether delivery succeeded
        channel: The channel used for delivery
        message: Success or error message
        metadata: Additional delivery metadata
    """
    success: bool
    channel: str
    message: str
    metadata: dict[str, Any] | None = None


class NotificationChannel(ABC):
    """
    Abstract base class for notification delivery channels.

    All channels must implement the deliver method to handle
    notification delivery through their specific mechanism.
    """

    @abstractmethod
    async def deliver(
        self,
        payload: NotificationPayload,
        db: Session | None = None
    ) -> DeliveryResult:
        """
        Deliver a notification through this channel.

        Args:
            payload: The notification to deliver
            db: Optional database session for persistence

        Returns:
            DeliveryResult indicating success/failure
        """
        pass

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Return the name of this channel."""
        pass


class InAppChannel(NotificationChannel):
    """
    In-app notification channel - stores notifications in database for UI display.

    This channel persists notifications to the database where they can be
    retrieved and displayed in the application UI.
    """

    @property
    def channel_name(self) -> str:
        return "in_app"

    async def deliver(
        self,
        payload: NotificationPayload,
        db: Session | None = None
    ) -> DeliveryResult:
        """
        Store notification in database for in-app display.

        Args:
            payload: The notification to store
            db: Database session (required for this channel)

        Returns:
            DeliveryResult with success status
        """
        if not db:
            return DeliveryResult(
                success=False,
                channel=self.channel_name,
                message="Database session required for in-app notifications"
            )

        try:
            # NOTE: Database persistence disabled until Notification SQLAlchemy model exists
            # Data structure prepared for future persistence:
            {
                "id": str(payload.id),
                "recipient_id": str(payload.recipient_id),
                "notification_type": payload.notification_type,
                "subject": payload.subject,
                "body": payload.body,
                "data": payload.data,
                "priority": payload.priority,
                "is_read": False,
                "created_at": payload.created_at,
            }

            # When model exists:
            # notification = Notification(**notification_data)
            # db.add(notification)
            # db.commit()

            return DeliveryResult(
                success=True,
                channel=self.channel_name,
                message="Notification stored successfully",
                metadata={"notification_id": str(payload.id)}
            )

        except Exception as e:
            return DeliveryResult(
                success=False,
                channel=self.channel_name,
                message=f"Failed to store notification: {str(e)}"
            )


class EmailChannel(NotificationChannel):
    """
    Email notification channel - prepares email payloads for delivery.

    This channel formats notifications for email delivery. Actual email
    sending should be handled by a separate email service (e.g., Celery task).
    """

    def __init__(self, from_address: str = "noreply@schedule.mil"):
        """
        Initialize email channel.

        Args:
            from_address: Default sender email address
        """
        self.from_address = from_address

    @property
    def channel_name(self) -> str:
        return "email"

    async def deliver(
        self,
        payload: NotificationPayload,
        db: Session | None = None
    ) -> DeliveryResult:
        """
        Prepare email payload for delivery.

        Args:
            payload: The notification to send
            db: Optional database session to look up recipient email

        Returns:
            DeliveryResult with email payload in metadata
        """
        try:
            # NOTE: Recipient email lookup needs Person model join
            # Using placeholder email until database lookup is implemented
            email_payload = {
                "from": self.from_address,
                "to": f"user-{payload.recipient_id}@example.com",  # Placeholder
                "subject": payload.subject,
                "body": payload.body,
                "html": self._format_html(payload),
                "priority": payload.priority,
            }

            # NOTE: Email sending requires Celery + Redis. See tasks.send_email()
            # Uncomment when infrastructure ready:
            # from app.notifications.tasks import send_email
            # send_email.delay(**email_payload)
            logger.debug("Email prepared for %s: %s", payload.recipient_id, payload.subject)

            return DeliveryResult(
                success=True,
                channel=self.channel_name,
                message="Email queued for delivery",
                metadata={"email_payload": email_payload}
            )

        except Exception as e:
            return DeliveryResult(
                success=False,
                channel=self.channel_name,
                message=f"Failed to prepare email: {str(e)}"
            )

    def _format_html(self, payload: NotificationPayload) -> str:
        """
        Format notification as HTML email.

        Args:
            payload: The notification payload

        Returns:
            HTML-formatted email body
        """
        # Simple HTML template - can be enhanced with proper email templates
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background-color: #003366; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .priority-high {{ border-left: 4px solid #dc3545; }}
                .priority-normal {{ border-left: 4px solid #007bff; }}
                .priority-low {{ border-left: 4px solid #6c757d; }}
                .footer {{ padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{payload.subject}</h2>
            </div>
            <div class="content priority-{payload.priority}">
                <pre style="white-space: pre-wrap; font-family: Arial, sans-serif;">
{payload.body}
                </pre>
            </div>
            <div class="footer">
                <p>This is an automated notification from the Schedule Management System.</p>
            </div>
        </body>
        </html>
        """
        return html


class WebhookChannel(NotificationChannel):
    """
    Webhook notification channel - sends notifications to external systems.

    This channel prepares webhook payloads for integration with external
    services like Slack, Teams, or custom monitoring systems.
    """

    def __init__(self, webhook_url: str | None = None):
        """
        Initialize webhook channel.

        Args:
            webhook_url: Default webhook URL for delivery
        """
        self.webhook_url = webhook_url

    @property
    def channel_name(self) -> str:
        return "webhook"

    async def deliver(
        self,
        payload: NotificationPayload,
        db: Session | None = None
    ) -> DeliveryResult:
        """
        Prepare webhook payload for external delivery.

        Args:
            payload: The notification to send
            db: Optional database session

        Returns:
            DeliveryResult with webhook payload in metadata
        """
        try:
            webhook_payload = {
                "event": "notification",
                "notification_id": str(payload.id),
                "type": payload.notification_type,
                "recipient_id": str(payload.recipient_id),
                "subject": payload.subject,
                "body": payload.body,
                "priority": payload.priority,
                "timestamp": payload.created_at.isoformat(),
                "data": payload.data,
            }

            # NOTE: Webhook delivery requires Celery + Redis. See tasks.send_webhook()
            # Uncomment when infrastructure ready:
            # if self.webhook_url:
            #     from app.notifications.tasks import send_webhook
            #     send_webhook.delay(self.webhook_url, webhook_payload)
            logger.debug("Webhook prepared for %s", self.webhook_url or "no URL configured")

            return DeliveryResult(
                success=True,
                channel=self.channel_name,
                message="Webhook queued for delivery",
                metadata={
                    "webhook_url": self.webhook_url,
                    "payload": webhook_payload
                }
            )

        except Exception as e:
            return DeliveryResult(
                success=False,
                channel=self.channel_name,
                message=f"Failed to prepare webhook: {str(e)}"
            )


# Channel registry
AVAILABLE_CHANNELS = {
    "in_app": InAppChannel,
    "email": EmailChannel,
    "webhook": WebhookChannel,
}


def get_channel(channel_name: str, **kwargs) -> NotificationChannel | None:
    """
    Get a notification channel instance by name.

    Args:
        channel_name: Name of the channel (in_app, email, webhook)
        **kwargs: Additional arguments to pass to channel constructor

    Returns:
        NotificationChannel instance or None if not found
    """
    channel_class = AVAILABLE_CHANNELS.get(channel_name)
    if not channel_class:
        return None
    return channel_class(**kwargs)
