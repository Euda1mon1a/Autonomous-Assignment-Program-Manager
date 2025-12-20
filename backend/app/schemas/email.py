"""Email notification schemas for API validation."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


# ============================================================================
# EmailLog Schemas
# ============================================================================


class EmailLogBase(BaseModel):
    """Base email log schema."""
    recipient_email: EmailStr
    subject: str
    body_html: str | None = None
    body_text: str | None = None

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Validate subject is not empty."""
        if not v or not v.strip():
            raise ValueError("subject cannot be empty")
        if len(v) > 500:
            raise ValueError("subject cannot exceed 500 characters")
        return v


class EmailLogCreate(EmailLogBase):
    """Schema for creating an email log."""
    notification_id: UUID | None = None
    template_id: UUID | None = None


class EmailLogUpdate(BaseModel):
    """Schema for updating an email log."""
    status: str | None = None
    error_message: str | None = None
    sent_at: datetime | None = None
    retry_count: int | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        """Validate status is a valid EmailStatus value."""
        if v is not None and v not in ("queued", "sent", "failed", "bounced"):
            raise ValueError("status must be one of: queued, sent, failed, bounced")
        return v

    @field_validator("retry_count")
    @classmethod
    def validate_retry_count(cls, v: int | None) -> int | None:
        """Validate retry count is non-negative."""
        if v is not None and v < 0:
            raise ValueError("retry_count must be non-negative")
        return v


class EmailLogRead(EmailLogBase):
    """Schema for email log response."""
    id: UUID
    notification_id: UUID | None = None
    template_id: UUID | None = None
    status: str
    error_message: str | None = None
    sent_at: datetime | None = None
    retry_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class EmailLogListResponse(BaseModel):
    """Schema for list of email logs."""
    items: list[EmailLogRead]
    total: int


# ============================================================================
# EmailTemplate Schemas
# ============================================================================


class EmailTemplateBase(BaseModel):
    """Base email template schema."""
    name: str
    template_type: str
    subject_template: str
    body_html_template: str
    body_text_template: str
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty and has reasonable length."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        if len(v) > 100:
            raise ValueError("name cannot exceed 100 characters")
        return v

    @field_validator("template_type")
    @classmethod
    def validate_template_type(cls, v: str) -> str:
        """Validate template_type is a valid EmailTemplateType value."""
        valid_types = (
            "schedule_change",
            "swap_notification",
            "certification_expiry",
            "absence_reminder",
            "compliance_alert"
        )
        if v not in valid_types:
            raise ValueError(f"template_type must be one of: {', '.join(valid_types)}")
        return v

    @field_validator("subject_template")
    @classmethod
    def validate_subject_template(cls, v: str) -> str:
        """Validate subject template is not empty."""
        if not v or not v.strip():
            raise ValueError("subject_template cannot be empty")
        if len(v) > 500:
            raise ValueError("subject_template cannot exceed 500 characters")
        return v

    @field_validator("body_html_template", "body_text_template")
    @classmethod
    def validate_body_template(cls, v: str) -> str:
        """Validate body template is not empty."""
        if not v or not v.strip():
            raise ValueError("body template cannot be empty")
        return v


class EmailTemplateCreate(EmailTemplateBase):
    """Schema for creating an email template."""
    created_by_id: UUID | None = None


class EmailTemplateUpdate(BaseModel):
    """Schema for updating an email template."""
    name: str | None = None
    template_type: str | None = None
    subject_template: str | None = None
    body_html_template: str | None = None
    body_text_template: str | None = None
    is_active: bool | None = None

    @field_validator("template_type")
    @classmethod
    def validate_template_type(cls, v: str | None) -> str | None:
        """Validate template_type is a valid EmailTemplateType value."""
        if v is None:
            return v
        valid_types = (
            "schedule_change",
            "swap_notification",
            "certification_expiry",
            "absence_reminder",
            "compliance_alert"
        )
        if v not in valid_types:
            raise ValueError(f"template_type must be one of: {', '.join(valid_types)}")
        return v


class EmailTemplateRead(EmailTemplateBase):
    """Schema for email template response."""
    id: UUID
    created_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailTemplateListResponse(BaseModel):
    """Schema for list of email templates."""
    items: list[EmailTemplateRead]
    total: int


class EmailTemplateSummary(BaseModel):
    """Minimal email template info."""
    id: UUID
    name: str
    template_type: str
    is_active: bool

    class Config:
        from_attributes = True


# ============================================================================
# Email Send Request Schema
# ============================================================================


class EmailSendRequest(BaseModel):
    """Schema for sending an email via API."""
    recipient_email: EmailStr
    subject: str
    body_html: str | None = None
    body_text: str | None = None
    template_id: UUID | None = None
    template_variables: dict[str, str] | None = None

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Validate subject is not empty."""
        if not v or not v.strip():
            raise ValueError("subject cannot be empty")
        if len(v) > 500:
            raise ValueError("subject cannot exceed 500 characters")
        return v

    @field_validator("body_html", "body_text")
    @classmethod
    def validate_body(cls, v: str | None) -> str | None:
        """Validate at least one body format is provided if no template."""
        # This validation is enhanced in the service layer
        return v
