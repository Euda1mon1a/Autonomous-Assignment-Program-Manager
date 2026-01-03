"""Person schemas."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


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

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

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

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate name is not empty."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("name cannot be empty")
        return v.strip() if v else v

    @field_validator("pgy_level")
    @classmethod
    def validate_pgy_level(cls, v: int | None) -> int | None:
        """Validate PGY level is within valid range."""
        if v is not None and (v < 1 or v > 3):
            raise ValueError("pgy_level must be between 1 and 3")
        return v


class PersonResponse(PersonBase):
    """Schema for person response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    # Call and FMIT equity tracking (read-only, managed by system)
    sunday_call_count: int = 0
    weekday_call_count: int = 0
    fmit_weeks_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_masked(cls, person: object, user_role: str) -> "PersonResponse":  # type: ignore
        """Return masked version for non-admin users.

        Args:
            person: The person ORM object or dictionary
            user_role: The role of the requesting user

        Returns:
            PersonResponse with masked fields if user is not admin
        """
        # If it's an ORM object, convert to dict-like access for consistency
        # or access attributes directly.

        # Helper to get attribute safely
        def get_attr(obj, name, default=None):
            return getattr(obj, name, default)

        is_admin = user_role == "admin"

        data = {
            "id": get_attr(person, "id"),
            "name": (
                get_attr(person, "name")
                if is_admin
                else f"Person-{str(get_attr(person, 'id'))[:8]}"
            ),
            "email": get_attr(person, "email") if is_admin else None,
            "type": get_attr(person, "type"),
            "pgy_level": get_attr(person, "pgy_level"),
            "performs_procedures": get_attr(person, "performs_procedures", False),
            "specialties": get_attr(person, "specialties"),
            "primary_duty": get_attr(person, "primary_duty"),
            "faculty_role": get_attr(person, "faculty_role"),
            "created_at": get_attr(person, "created_at"),
            "updated_at": get_attr(person, "updated_at"),
            "sunday_call_count": get_attr(person, "sunday_call_count", 0),
            "weekday_call_count": get_attr(person, "weekday_call_count", 0),
            "fmit_weeks_count": get_attr(person, "fmit_weeks_count", 0),
        }
        return cls(**data)


class PersonListResponse(BaseModel):
    """Schema for list of persons."""

    items: list[PersonResponse]
    total: int
