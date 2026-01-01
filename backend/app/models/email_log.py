"""Email log model for tracking email notifications."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class EmailStatus(str, enum.Enum):
    """Email delivery status."""

    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


class EmailLog(Base):
    """
    Tracks email notifications sent from the system.

    This model maintains a complete audit trail of all emails sent,
    including delivery status, retry attempts, and error tracking.

    SQLAlchemy Relationships:
        notification: Many-to-one to Notification.
            Back-populates Notification.email_logs.
            FK ondelete=SET NULL. The in-app notification (if any).

        template: Many-to-one to EmailTemplate.
            Back-populates EmailTemplate.email_logs (via backref).
            FK ondelete=SET NULL. The template used for this email.
    """

    __tablename__ = "email_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Optional link to notification (for in-app notifications that also send email)
    notification_id = Column(
        GUID(),
        ForeignKey("notifications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Optional link to email template used
    template_id = Column(
        GUID(),
        ForeignKey("email_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Email details
    recipient_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)

    # Delivery tracking
    status = Column(
        Enum(EmailStatus), default=EmailStatus.QUEUED, nullable=False, index=True
    )
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    notification = relationship("Notification", back_populates="email_logs")
    template = relationship("EmailTemplate", backref="email_logs")

    def __repr__(self) -> str:
        return f"<EmailLog(id={self.id}, recipient='{self.recipient_email}', status='{self.status}')>"
