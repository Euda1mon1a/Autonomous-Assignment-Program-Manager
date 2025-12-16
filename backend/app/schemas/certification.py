"""Certification schemas for API validation."""
from datetime import datetime, date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, field_validator


# ============================================================================
# Certification Type Schemas
# ============================================================================


class CertificationTypeBase(BaseModel):
    """Base certification type schema."""
    name: str
    full_name: Optional[str] = None
    description: Optional[str] = None
    renewal_period_months: int = 24
    required_for_residents: bool = True
    required_for_faculty: bool = True
    required_for_specialties: Optional[str] = None
    reminder_days_180: bool = True
    reminder_days_90: bool = True
    reminder_days_30: bool = True
    reminder_days_14: bool = True
    reminder_days_7: bool = True
    is_active: bool = True


class CertificationTypeCreate(CertificationTypeBase):
    """Schema for creating a certification type."""
    pass


class CertificationTypeUpdate(BaseModel):
    """Schema for updating a certification type."""
    name: Optional[str] = None
    full_name: Optional[str] = None
    description: Optional[str] = None
    renewal_period_months: Optional[int] = None
    required_for_residents: Optional[bool] = None
    required_for_faculty: Optional[bool] = None
    required_for_specialties: Optional[str] = None
    reminder_days_180: Optional[bool] = None
    reminder_days_90: Optional[bool] = None
    reminder_days_30: Optional[bool] = None
    reminder_days_14: Optional[bool] = None
    reminder_days_7: Optional[bool] = None
    is_active: Optional[bool] = None


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
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# Person Certification Schemas
# ============================================================================


class PersonCertificationBase(BaseModel):
    """Base person certification schema."""
    certification_number: Optional[str] = None
    issued_date: date
    expiration_date: date
    status: str = 'current'
    verified_by: Optional[str] = None
    verified_date: Optional[date] = None
    document_url: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = ('current', 'expiring_soon', 'expired', 'pending')
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v


class PersonCertificationCreate(PersonCertificationBase):
    """Schema for creating a person certification."""
    person_id: UUID
    certification_type_id: UUID


class PersonCertificationUpdate(BaseModel):
    """Schema for updating a person certification."""
    certification_number: Optional[str] = None
    issued_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: Optional[str] = None
    verified_by: Optional[str] = None
    verified_date: Optional[date] = None
    document_url: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid_statuses = ('current', 'expiring_soon', 'expired', 'pending')
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
    email: Optional[str] = None

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
