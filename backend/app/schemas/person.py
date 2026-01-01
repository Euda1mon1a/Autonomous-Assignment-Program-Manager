"""Person schemas."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class FacultyRoleSchema(str, Enum):
    """Faculty role types for API schema validation."""

    PD = "pd"
    APD = "apd"
    OIC = "oic"
    DEPT_CHIEF = "dept_chief"
    SPORTS_MED = "sports_med"
    CORE = "core"
    ADJUNCT = "adjunct"


class PersonType(str, Enum):
    """Person type enumeration."""

    RESIDENT = "resident"
    FACULTY = "faculty"


class PersonBase(BaseModel):
    """Base person schema."""

    name: str = Field(
        ..., min_length=1, max_length=100, description="Person's full name"
    )
    type: PersonType = Field(..., description="Person type (resident or faculty)")
    email: EmailStr | None = Field(None, description="Email address")
    pgy_level: int | None = Field(
        None, ge=1, le=3, description="PGY level (1-3) for residents"
    )
    performs_procedures: bool = Field(
        False, description="Whether person performs procedures"
    )
    specialties: list[str] | None = Field(
        None, max_length=10, description="List of specialties (max 10)"
    )
    primary_duty: str | None = Field(
        None, max_length=100, description="Primary duty or role"
    )
    faculty_role: FacultyRoleSchema | None = Field(
        None, description="Faculty role type"
    )

    @field_validator("specialties")
    @classmethod
    def validate_specialties(cls, v: list[str] | None) -> list[str] | None:
        """Validate specialty items are not empty and have max length."""
        if v is not None:
            for specialty in v:
                if not specialty or len(specialty) > 50:
                    raise ValueError(
                        "Each specialty must be between 1 and 50 characters"
                    )
        return v


class PersonCreate(PersonBase):
    """Schema for creating a person."""

    pass


class PersonUpdate(BaseModel):
    """Schema for updating a person."""

    name: str | None = Field(
        None, min_length=1, max_length=100, description="Person's full name"
    )
    email: EmailStr | None = Field(None, description="Email address")
    pgy_level: int | None = Field(
        None, ge=1, le=3, description="PGY level (1-3) for residents"
    )
    performs_procedures: bool | None = Field(
        None, description="Whether person performs procedures"
    )
    specialties: list[str] | None = Field(
        None, max_length=10, description="List of specialties (max 10)"
    )
    primary_duty: str | None = Field(
        None, max_length=100, description="Primary duty or role"
    )
    faculty_role: FacultyRoleSchema | None = Field(
        None, description="Faculty role type"
    )


class PersonResponse(PersonBase):
    """Schema for person response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    # Call and FMIT equity tracking (read-only, managed by system)
    sunday_call_count: int = 0
    weekday_call_count: int = 0
    fmit_weeks_count: int = 0

    class Config:
        from_attributes = True


class PersonListResponse(BaseModel):
    """Schema for list of persons."""

    items: list[PersonResponse]
    total: int
