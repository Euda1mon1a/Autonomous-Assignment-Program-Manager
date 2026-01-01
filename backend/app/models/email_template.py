"""Email template model for reusable email content."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class EmailTemplateType(str, enum.Enum):
    """Email template types for different notification scenarios."""

    SCHEDULE_CHANGE = "schedule_change"
    SWAP_NOTIFICATION = "swap_notification"
    CERTIFICATION_EXPIRY = "certification_expiry"
    ABSENCE_REMINDER = "absence_reminder"
    COMPLIANCE_ALERT = "compliance_alert"


class EmailTemplate(Base):
    """
    Stores reusable email templates with variable substitution.

    Templates support Jinja2-style variable substitution for dynamic content.
    Admins can customize templates for different notification types.

    SQLAlchemy Relationships:
        created_by: Many-to-one to User.
            Back-populates User.email_templates (via backref).
            FK ondelete=SET NULL. The user who created this template.
    """

    __tablename__ = "email_templates"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Template identification
    name = Column(String(100), unique=True, nullable=False, index=True)
    template_type = Column(Enum(EmailTemplateType), nullable=False, index=True)

    # Template content (supports Jinja2 variable substitution)
    subject_template = Column(String(500), nullable=False)
    body_html_template = Column(Text, nullable=False)
    body_text_template = Column(Text, nullable=False)

    # Template status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Audit tracking
    created_by_id = Column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship
    created_by = relationship("User", backref="email_templates")

    def __repr__(self) -> str:
        return f"<EmailTemplate(name='{self.name}', type='{self.template_type}', active={self.is_active})>"
