"""Certification schemas for API validation."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator

from app.validators.date_validators import validate_date_range

# ============================================================================
# Certification Type Schemas
# ============================================================================


class CertificationTypeBase(BaseModel):
    """Base certification type schema."""

    name: str = Field(..., min_length=1, max_length=100, description="Certification name")
    full_name: str | None = Field(
        None, min_length=1, max_length=200, description="Full certification name"
    )
    description: str | None = Field(
        None, min_length=1, max_length=1000, description="Certification description"
    )
    renewal_period_months: int = Field(
        24, ge=1, le=120, description="Renewal period in months (1-120)"
    )
    required_for_residents: bool = Field(
        True, description="Whether required for residents"
    )
    required_for_faculty: bool = Field(True, description="Whether required for faculty")
    required_for_specialties: str | None = Field(
        None, min_length=1, max_length=500, description="Comma-separated specialty list"
    )
    reminder_days_180: bool = Field(True, description="Send reminder at 180 days")
    reminder_days_90: bool = Field(True, description="Send reminder at 90 days")
    reminder_days_30: bool = Field(True, description="Send reminder at 30 days")
    reminder_days_14: bool = Field(True, description="Send reminder at 14 days")
    reminder_days_7: bool = Field(True, description="Send reminder at 7 days")
    is_active: bool = Field(True, description="Whether certification type is active")


class CertificationTypeCreate(CertificationTypeBase):
    """Schema for creating a certification type."""

    pass


class CertificationTypeUpdate(BaseModel):
    """Schema for updating a certification type."""

    name: str | None = None
    full_name: str | None = None
    description: str | None = None
    renewal_period_months: int | None = None
    required_for_residents: bool | None = None
    required_for_faculty: bool | None = None
    required_for_specialties: str | None = None
    reminder_days_180: bool | None = None
    reminder_days_90: bool | None = None
    reminder_days_30: bool | None = None
    reminder_days_14: bool | None = None
    reminder_days_7: bool | None = None
    is_active: bool | None = None


class CertificationTypeResponse(CertificationTypeBase):
    """Schema for certification type response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CertificationTypeListResponse(BaseModel):
    """Schema for list of certification types."""

    items: list[CertificationTypeResponse]
    total: int


class CertificationTypeSummary(BaseModel):
    """Minimal certification type info."""

    id: UUID
    name: str
    full_name: str | None = None

    class Config:
        from_attributes = True


# ============================================================================
# Person Certification Schemas
# ============================================================================


class PersonCertificationBase(BaseModel):
    """Base person certification schema."""

    certification_number: str | None = Field(
        None, min_length=1, max_length=100, description="Certification number or ID"
    )
    issued_date: date = Field(..., description="Date certification was issued")
    expiration_date: date = Field(..., description="Date certification expires")
    status: str = Field(
        "current",
        pattern="^(current|expiring_soon|expired|pending)$",
        description="Certification status",
    )
    verified_by: str | None = Field(
        None, min_length=1, max_length=200, description="Person who verified certification"
    )
    verified_date: date | None = Field(None, description="Date certification was verified")
    document_url: str | None = Field(
        None, min_length=1, max_length=500, description="URL to certification document"
    )
    notes: str | None = Field(
        None, min_length=1, max_length=2000, description="Additional notes"
    )

    @field_validator("issued_date", "expiration_date", "verified_date")
    @classmethod
    def validate_dates_in_range(cls, v: date | None) -> date | None:
        """Validate dates are within reasonable bounds."""
        if v is not None:
            return validate_date_range(v, field_name="date")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = ("current", "expiring_soon", "expired", "pending")
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v

    @model_validator(mode="after")
    def validate_expiration_after_issue(self):
        """Ensure expiration_date is after issued_date."""
        if self.expiration_date <= self.issued_date:
            raise ValueError(
                f"expiration_date ({self.expiration_date.isoformat()}) must be after "
                f"issued_date ({self.issued_date.isoformat()})"
            )
        return self


class PersonCertificationCreate(PersonCertificationBase):
    """Schema for creating a person certification."""

    person_id: UUID
    certification_type_id: UUID


class PersonCertificationUpdate(BaseModel):
    """Schema for updating a person certification."""

    certification_number: str | None = None
    issued_date: date | None = None
    expiration_date: date | None = None
    status: str | None = None
    verified_by: str | None = None
    verified_date: date | None = None
    document_url: str | None = None
    notes: str | None = None

    @field_validator("issued_date", "expiration_date", "verified_date")
    @classmethod
    def validate_dates_in_range(cls, v: date | None) -> date | None:
        """Validate dates are within reasonable bounds."""
        if v is not None:
            return validate_date_range(v, field_name="date")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid_statuses = ("current", "expiring_soon", "expired", "pending")
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v


class PersonCertificationResponse(PersonCertificationBase):
    """Schema for person certification response."""

    id: UUID
    person_id: UUID
    certification_type_id: UUID
    days_until_expiration: int
    is_expired: bool
    is_expiring_soon: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PersonCertificationWithTypeResponse(PersonCertificationResponse):
    """Certification response with type details."""

    certification_type: CertificationTypeSummary

    class Config:
        from_attributes = True


class PersonCertificationListResponse(BaseModel):
    """Schema for list of certifications."""

    items: list[PersonCertificationResponse]
    total: int


class PersonCertificationWithTypeListResponse(BaseModel):
    """Schema for list of certifications with type details."""

    items: list[PersonCertificationWithTypeResponse]
    total: int


# ============================================================================
# Summary and Dashboard Schemas
# ============================================================================


class PersonSummary(BaseModel):
    """Minimal person info for certification reports."""

    id: UUID
    name: str
    type: str
    email: str | None = None

    class Config:
        from_attributes = True


class ExpiringCertificationResponse(BaseModel):
    """Certification that's expiring soon."""

    id: UUID
    person: PersonSummary
    certification_type: CertificationTypeSummary
    expiration_date: date
    days_until_expiration: int
    status: str


class ExpiringCertificationsListResponse(BaseModel):
    """List of expiring certifications."""

    items: list[ExpiringCertificationResponse]
    total: int
    days_threshold: int


class ComplianceSummaryResponse(BaseModel):
    """Overall certification compliance summary."""

    total: int
    current: int
    expiring_soon: int
    expired: int
    compliance_rate: float


class PersonComplianceResponse(BaseModel):
    """Certification compliance for a single person."""

    person: PersonSummary
    total_required: int
    total_current: int
    expired: int
    expiring_soon: int
    missing: list[CertificationTypeSummary]
    is_compliant: bool


class ReminderQueueResponse(BaseModel):
    """Certifications that need reminder emails."""

    days_threshold: int
    certifications: list[ExpiringCertificationResponse]
    total: int
