"""ProcedureCredential schemas."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator

from app.schemas.procedure import ProcedureSummary
from app.validators.date_validators import validate_date_range


class CredentialBase(BaseModel):
    """Base credential schema."""
    status: str = 'active'
    competency_level: str = 'qualified'
    issued_date: date | None = None
    expiration_date: date | None = None
    last_verified_date: date | None = None
    max_concurrent_residents: int | None = None
    max_per_week: int | None = None
    max_per_academic_year: int | None = None
    notes: str | None = None

    @field_validator("issued_date", "expiration_date", "last_verified_date")
    @classmethod
    def validate_dates_in_range(cls, v: date | None) -> date | None:
        """Validate dates are within reasonable bounds."""
        if v is not None:
            return validate_date_range(v, field_name="date")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = ('active', 'expired', 'suspended', 'pending')
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v

    @field_validator("competency_level")
    @classmethod
    def validate_competency(cls, v: str) -> str:
        valid_levels = ('trainee', 'qualified', 'expert', 'master')
        if v not in valid_levels:
            raise ValueError(f"competency_level must be one of {valid_levels}")
        return v

    @model_validator(mode="after")
    def validate_expiration_after_issue(self):
        """Ensure expiration_date is after issued_date if both are set."""
        if self.issued_date and self.expiration_date:
            if self.expiration_date <= self.issued_date:
                raise ValueError(
                    f"expiration_date ({self.expiration_date.isoformat()}) must be after "
                    f"issued_date ({self.issued_date.isoformat()})"
                )
        return self


class CredentialCreate(CredentialBase):
    """Schema for creating a credential."""
    person_id: UUID
    procedure_id: UUID


class CredentialUpdate(BaseModel):
    """Schema for updating a credential."""
    status: str | None = None
    competency_level: str | None = None
    expiration_date: date | None = None
    last_verified_date: date | None = None
    max_concurrent_residents: int | None = None
    max_per_week: int | None = None
    max_per_academic_year: int | None = None
    notes: str | None = None

    @field_validator("expiration_date", "last_verified_date")
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
        valid_statuses = ('active', 'expired', 'suspended', 'pending')
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v

    @field_validator("competency_level")
    @classmethod
    def validate_competency(cls, v: str | None) -> str | None:
        if v is None:
            return v
        valid_levels = ('trainee', 'qualified', 'expert', 'master')
        if v not in valid_levels:
            raise ValueError(f"competency_level must be one of {valid_levels}")
        return v


class CredentialResponse(CredentialBase):
    """Schema for credential response."""
    id: UUID
    person_id: UUID
    procedure_id: UUID
    created_at: datetime
    updated_at: datetime
    is_valid: bool  # Computed property

    class Config:
        from_attributes = True


class CredentialWithProcedureResponse(CredentialResponse):
    """Credential response including procedure details."""
    procedure: ProcedureSummary

    class Config:
        from_attributes = True


class CredentialListResponse(BaseModel):
    """Schema for list of credentials."""
    items: list[CredentialResponse]
    total: int


class CredentialWithProcedureListResponse(BaseModel):
    """Schema for list of credentials with procedure details."""
    items: list[CredentialWithProcedureResponse]
    total: int


class PersonSummary(BaseModel):
    """Minimal person info for embedding in credential responses."""
    id: UUID
    name: str
    type: str

    class Config:
        from_attributes = True


class CredentialWithPersonResponse(CredentialResponse):
    """Credential response including person details."""
    person: PersonSummary

    class Config:
        from_attributes = True


class QualifiedFacultyResponse(BaseModel):
    """Response for listing faculty qualified for a procedure."""
    procedure_id: UUID
    procedure_name: str
    qualified_faculty: list[PersonSummary]
    total: int


class FacultyCredentialSummary(BaseModel):
    """Summary of a faculty member's credentials."""
    person_id: UUID
    person_name: str
    total_credentials: int
    active_credentials: int
    expiring_soon: int  # Credentials expiring in next 30 days
    procedures: list[ProcedureSummary]
