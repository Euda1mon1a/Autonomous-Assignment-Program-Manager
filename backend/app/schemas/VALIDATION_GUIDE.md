# API Validation Enhancement Guide

**Created:** 2025-12-31
**Purpose:** Comprehensive guide for enhancing Pydantic schema validation

---

## Table of Contents

1. [Validation Principles](#validation-principles)
2. [Field-Level Validation](#field-level-validation)
3. [Cross-Field Validation](#cross-field-validation)
4. [Custom Validators](#custom-validators)
5. [Request/Response Examples](#requestresponse-examples)
6. [Error Messages](#error-messages)
7. [Testing Validation](#testing-validation)
8. [Best Practices](#best-practices)

---

## Validation Principles

### 1. **Fail Fast**
Validate at the schema level before data reaches business logic.

### 2. **Clear Error Messages**
Provide actionable error messages that tell users what's wrong and how to fix it.

### 3. **Consistent Patterns**
Use the same validation patterns across all schemas for consistency.

### 4. **Security First**
Validate to prevent injection attacks, XSS, and data leaks.

### 5. **Document Constraints**
Include field descriptions that explain validation rules.

---

## Field-Level Validation

### String Validation

```python
from pydantic import BaseModel, Field, field_validator
import re

class PersonCreate(BaseModel):
    """Create person with comprehensive string validation."""

    # Basic string with length constraints
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Person's full name (2-100 characters)",
        examples=["Dr. Jane Smith", "John Doe"]
    )

    # Email validation (using EmailStr)
    email: EmailStr = Field(
        ...,
        description="Valid email address",
        examples=["user@example.com"]
    )

    # String with pattern validation (regex)
    phone: str | None = Field(
        None,
        pattern=r'^\+?1?\d{10,15}$',
        description="Phone number (10-15 digits, optional +1 prefix)",
        examples=["+15551234567", "5551234567"]
    )

    # Enum-like string (limited values)
    person_type: str = Field(
        ...,
        pattern="^(resident|faculty)$",
        description="Person type: 'resident' or 'faculty'",
        examples=["resident"]
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name doesn't contain special characters."""
        if not re.match(r"^[a-zA-Z\s\-\.\']+$", v):
            raise ValueError(
                "Name can only contain letters, spaces, hyphens, "
                "periods, and apostrophes"
            )
        return v.strip()

    @field_validator("person_type")
    @classmethod
    def validate_person_type(cls, v: str) -> str:
        """Validate person type is allowed value."""
        allowed = {"resident", "faculty"}
        if v not in allowed:
            raise ValueError(
                f"person_type must be one of: {', '.join(allowed)}"
            )
        return v
```

### Numeric Validation

```python
from pydantic import BaseModel, Field, field_validator

class AssignmentCreate(BaseModel):
    """Create assignment with numeric validation."""

    # Integer with range
    pgy_level: int | None = Field(
        None,
        ge=1,
        le=3,
        description="PGY level (1-3)",
        examples=[2]
    )

    # Float with range and precision
    confidence_score: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0)",
        examples=[0.85]
    )

    # Positive integer
    duration_hours: int = Field(
        ...,
        gt=0,
        le=168,  # Max 1 week
        description="Duration in hours (1-168)",
        examples=[12]
    )

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence_precision(cls, v: float | None) -> float | None:
        """Validate confidence score has max 2 decimal places."""
        if v is not None:
            rounded = round(v, 2)
            if abs(rounded - v) > 1e-9:
                raise ValueError(
                    "Confidence score must have at most 2 decimal places"
                )
        return v
```

### Date and DateTime Validation

```python
from datetime import date, datetime, timedelta
from pydantic import BaseModel, Field, field_validator

class DateRangeFilter(BaseModel):
    """Date range filter with comprehensive validation."""

    start_date: date = Field(
        ...,
        description="Start date (inclusive, ISO 8601 format: YYYY-MM-DD)",
        examples=["2025-01-01"]
    )

    end_date: date = Field(
        ...,
        description="End date (inclusive, ISO 8601 format: YYYY-MM-DD)",
        examples=["2025-01-31"]
    )

    @field_validator("start_date")
    @classmethod
    def validate_start_date_not_too_old(cls, v: date) -> date:
        """Prevent queries for dates too far in the past."""
        min_date = date.today() - timedelta(days=730)  # 2 years
        if v < min_date:
            raise ValueError(
                f"start_date cannot be before {min_date.isoformat()} "
                "(2 years ago)"
            )
        return v

    @field_validator("end_date")
    @classmethod
    def validate_end_date_not_too_far_future(cls, v: date) -> date:
        """Prevent queries for dates too far in the future."""
        max_date = date.today() + timedelta(days=730)  # 2 years
        if v > max_date:
            raise ValueError(
                f"end_date cannot be after {max_date.isoformat()} "
                "(2 years from now)"
            )
        return v
```

### List and Collection Validation

```python
from pydantic import BaseModel, Field, field_validator

class ScheduleGenerateRequest(BaseModel):
    """Schedule generation request with list validation."""

    resident_ids: list[UUID] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of resident IDs (1-100)",
        examples=[
            [
                "550e8400-e29b-41d4-a716-446655440000",
                "660e8400-e29b-41d4-a716-446655440001"
            ]
        ]
    )

    excluded_dates: list[date] = Field(
        default_factory=list,
        max_length=50,
        description="Dates to exclude from schedule (max 50)",
        examples=[["2025-12-25", "2025-01-01"]]
    )

    preferences: dict[str, int] = Field(
        default_factory=dict,
        description="Preference weights (key: preference_type, value: weight)",
        examples=[{"weekend_off": 5, "clinic_preferred": 3}]
    )

    @field_validator("resident_ids")
    @classmethod
    def validate_no_duplicate_ids(cls, v: list[UUID]) -> list[UUID]:
        """Ensure no duplicate resident IDs."""
        if len(v) != len(set(v)):
            raise ValueError("resident_ids must not contain duplicates")
        return v

    @field_validator("preferences")
    @classmethod
    def validate_preference_weights(cls, v: dict[str, int]) -> dict[str, int]:
        """Validate preference weights are in valid range."""
        for pref_type, weight in v.items():
            if not (0 <= weight <= 10):
                raise ValueError(
                    f"Preference weight for '{pref_type}' must be 0-10, "
                    f"got {weight}"
                )
        return v
```

---

## Cross-Field Validation

### Model Validator (After)

```python
from pydantic import BaseModel, Field, model_validator

class AbsenceCreate(BaseModel):
    """Absence request with cross-field validation."""

    person_id: UUID = Field(..., description="Person requesting absence")
    start_date: date = Field(..., description="Absence start date")
    end_date: date = Field(..., description="Absence end date")
    absence_type: str = Field(
        ...,
        description="Type: 'vacation', 'sick_leave', 'tdy', 'deployment'"
    )
    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Reason for absence (10-500 characters)"
    )

    @model_validator(mode="after")
    def validate_date_range(self):
        """Validate end_date is after start_date."""
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")

        # Validate date range is reasonable
        days = (self.end_date - self.start_date).days + 1
        if days > 365:
            raise ValueError(
                f"Absence duration ({days} days) exceeds maximum (365 days)"
            )

        return self

    @model_validator(mode="after")
    def validate_deployment_requires_long_duration(self):
        """Deployment absences must be at least 30 days."""
        if self.absence_type == "deployment":
            days = (self.end_date - self.start_date).days + 1
            if days < 30:
                raise ValueError(
                    "Deployment absences must be at least 30 days, "
                    f"got {days} days"
                )
        return self

    @model_validator(mode="after")
    def validate_vacation_not_too_far_future(self):
        """Vacation requests must be within 1 year."""
        if self.absence_type == "vacation":
            if self.start_date > date.today() + timedelta(days=365):
                raise ValueError(
                    "Vacation requests cannot be more than 1 year in advance"
                )
        return self
```

### Conditional Field Requirements

```python
from pydantic import BaseModel, Field, model_validator

class SwapRequest(BaseModel):
    """Swap request with conditional field validation."""

    requester_id: UUID
    requester_assignment_id: UUID
    swap_type: str = Field(..., pattern="^(one_to_one|absorb)$")

    # Optional fields (required for one_to_one)
    target_id: UUID | None = None
    target_assignment_id: UUID | None = None

    reason: str = Field(..., min_length=10, max_length=500)

    @model_validator(mode="after")
    def validate_swap_type_requirements(self):
        """Validate required fields based on swap type."""
        if self.swap_type == "one_to_one":
            if self.target_id is None:
                raise ValueError(
                    "target_id is required for one_to_one swaps"
                )
            if self.target_assignment_id is None:
                raise ValueError(
                    "target_assignment_id is required for one_to_one swaps"
                )
            if self.requester_id == self.target_id:
                raise ValueError("Cannot swap with yourself")

        elif self.swap_type == "absorb":
            if self.target_id is not None:
                raise ValueError(
                    "target_id must be None for absorb swaps"
                )
            if self.target_assignment_id is not None:
                raise ValueError(
                    "target_assignment_id must be None for absorb swaps"
                )

        return self
```

---

## Custom Validators

### Reusable Validators Module

Create `backend/app/validators/common_validators.py`:

```python
"""Reusable validation functions for Pydantic schemas."""

import re
from datetime import date, datetime, timedelta
from uuid import UUID


def validate_uuid_format(value: str, field_name: str = "id") -> UUID:
    """
    Validate string is a valid UUID.

    Args:
        value: String to validate
        field_name: Name of field (for error messages)

    Returns:
        UUID object

    Raises:
        ValueError: If string is not a valid UUID
    """
    try:
        return UUID(value)
    except (ValueError, AttributeError):
        raise ValueError(
            f"{field_name} must be a valid UUID, got: {value}"
        )


def validate_date_range(
    start_date: date,
    end_date: date,
    max_days: int = 365,
    field_name: str = "date range"
) -> tuple[date, date]:
    """
    Validate date range is logical.

    Args:
        start_date: Start date
        end_date: End date
        max_days: Maximum allowed days in range
        field_name: Name of field (for error messages)

    Returns:
        Tuple of (start_date, end_date)

    Raises:
        ValueError: If date range is invalid
    """
    if end_date < start_date:
        raise ValueError(
            f"{field_name}: end_date must be on or after start_date"
        )

    days = (end_date - start_date).days + 1
    if days > max_days:
        raise ValueError(
            f"{field_name}: duration ({days} days) exceeds "
            f"maximum ({max_days} days)"
        )

    return start_date, end_date


def validate_iso_datetime(value: str, field_name: str = "datetime") -> datetime:
    """
    Validate string is ISO 8601 datetime.

    Args:
        value: String to validate
        field_name: Name of field (for error messages)

    Returns:
        datetime object

    Raises:
        ValueError: If string is not a valid ISO datetime
    """
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise ValueError(
            f"{field_name} must be ISO 8601 format (YYYY-MM-DDTHH:MM:SS), "
            f"got: {value}"
        )


def validate_alphanumeric_with_dash(
    value: str,
    field_name: str = "value"
) -> str:
    """
    Validate string contains only alphanumeric characters and dashes.

    Args:
        value: String to validate
        field_name: Name of field (for error messages)

    Returns:
        Validated string

    Raises:
        ValueError: If string contains invalid characters
    """
    if not re.match(r'^[a-zA-Z0-9\-]+$', value):
        raise ValueError(
            f"{field_name} can only contain letters, numbers, and dashes"
        )
    return value


def validate_no_sql_injection(value: str, field_name: str = "value") -> str:
    """
    Basic SQL injection prevention.

    Args:
        value: String to validate
        field_name: Name of field (for error messages)

    Returns:
        Validated string

    Raises:
        ValueError: If string contains SQL keywords
    """
    sql_keywords = [
        "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
        "ALTER", "EXEC", "EXECUTE", "--", "/*", "*/", "xp_", "sp_"
    ]

    value_upper = value.upper()
    for keyword in sql_keywords:
        if keyword in value_upper:
            raise ValueError(
                f"{field_name} contains prohibited SQL keyword: {keyword}"
            )

    return value
```

### Usage in Schemas

```python
from app.validators.common_validators import (
    validate_date_range,
    validate_alphanumeric_with_dash,
)

class ProjectCreate(BaseModel):
    """Project creation with custom validators."""

    project_code: str = Field(..., max_length=50)
    start_date: date
    end_date: date

    @field_validator("project_code")
    @classmethod
    def validate_project_code_format(cls, v: str) -> str:
        """Validate project code is alphanumeric with dashes."""
        return validate_alphanumeric_with_dash(v, "project_code")

    @model_validator(mode="after")
    def validate_project_dates(self):
        """Validate project date range."""
        validate_date_range(
            self.start_date,
            self.end_date,
            max_days=730,  # 2 years max
            field_name="project"
        )
        return self
```

---

## Request/Response Examples

### Adding Examples to Schemas

```python
from pydantic import BaseModel, Field

class AssignmentCreate(BaseModel):
    """Assignment creation request."""

    block_id: UUID = Field(..., description="Block ID")
    person_id: UUID = Field(..., description="Person ID")
    rotation_template_id: UUID | None = Field(
        None,
        description="Rotation template ID"
    )
    role: str = Field(
        ...,
        pattern="^(primary|supervising|backup)$",
        description="Assignment role"
    )
    notes: str | None = Field(
        None,
        max_length=1000,
        description="Assignment notes"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "block_id": "550e8400-e29b-41d4-a716-446655440000",
                    "person_id": "660e8400-e29b-41d4-a716-446655440001",
                    "rotation_template_id": "770e8400-e29b-41d4-a716-446655440002",
                    "role": "primary",
                    "notes": "Regular clinic rotation"
                },
                {
                    "block_id": "550e8400-e29b-41d4-a716-446655440000",
                    "person_id": "660e8400-e29b-41d4-a716-446655440001",
                    "rotation_template_id": None,
                    "role": "backup",
                    "notes": "Backup coverage for procedures"
                }
            ]
        }
    }
```

### Multiple Examples for Different Scenarios

```python
class SwapRequest(BaseModel):
    """Swap request with scenario-specific examples."""

    requester_id: UUID
    target_id: UUID | None = None
    swap_type: str
    reason: str = Field(..., min_length=10, max_length=500)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "One-to-One Swap",
                    "description": "Trading shifts with another faculty member",
                    "value": {
                        "requester_id": "550e8400-e29b-41d4-a716-446655440000",
                        "target_id": "660e8400-e29b-41d4-a716-446655440001",
                        "swap_type": "one_to_one",
                        "reason": "Need to attend family event that weekend"
                    }
                },
                {
                    "title": "Absorb Swap",
                    "description": "Giving away a shift without receiving one",
                    "value": {
                        "requester_id": "550e8400-e29b-41d4-a716-446655440000",
                        "target_id": None,
                        "swap_type": "absorb",
                        "reason": "Medical emergency - need someone to cover"
                    }
                }
            ]
        }
    }
```

---

## Error Messages

### Clear, Actionable Error Messages

```python
@field_validator("email")
@classmethod
def validate_email_domain(cls, v: str) -> str:
    """Validate email is from allowed domain."""
    allowed_domains = ["example.com", "test.com"]

    if "@" not in v:
        raise ValueError("Email must contain @ symbol")

    domain = v.split("@")[1].lower()
    if domain not in allowed_domains:
        raise ValueError(
            f"Email domain must be one of: {', '.join(allowed_domains)}. "
            f"Got: {domain}"
        )

    return v
```

### Error Message Best Practices

1. **Be Specific:** Tell user exactly what's wrong
2. **Show Allowed Values:** List valid options
3. **Show Actual Value:** Include what was provided
4. **Suggest Fix:** Tell user how to correct it

**Bad:**
```python
raise ValueError("Invalid value")
```

**Good:**
```python
raise ValueError(
    f"role must be one of: primary, supervising, backup. "
    f"Got: {v}"
)
```

---

## Testing Validation

### Test Structure

```python
"""Tests for assignment schema validation."""

import pytest
from uuid import uuid4
from app.schemas.assignment import AssignmentCreate

class TestAssignmentCreateValidation:
    """Test assignment creation validation."""

    def test_valid_assignment_passes(self):
        """Test valid assignment passes validation."""
        assignment = AssignmentCreate(
            block_id=uuid4(),
            person_id=uuid4(),
            rotation_template_id=uuid4(),
            role="primary",
            notes="Test assignment"
        )
        assert assignment.role == "primary"

    def test_invalid_role_rejected(self):
        """Test invalid role is rejected."""
        with pytest.raises(ValueError, match="role must be"):
            AssignmentCreate(
                block_id=uuid4(),
                person_id=uuid4(),
                role="invalid_role"
            )

    def test_notes_too_long_rejected(self):
        """Test notes exceeding max length are rejected."""
        with pytest.raises(ValueError):
            AssignmentCreate(
                block_id=uuid4(),
                person_id=uuid4(),
                role="primary",
                notes="x" * 1001  # Over 1000 char limit
            )

    def test_empty_notes_accepted(self):
        """Test empty notes (None) is accepted."""
        assignment = AssignmentCreate(
            block_id=uuid4(),
            person_id=uuid4(),
            role="primary",
            notes=None
        )
        assert assignment.notes is None

    @pytest.mark.parametrize("role", ["primary", "supervising", "backup"])
    def test_all_valid_roles_accepted(self, role):
        """Test all valid roles are accepted."""
        assignment = AssignmentCreate(
            block_id=uuid4(),
            person_id=uuid4(),
            role=role
        )
        assert assignment.role == role
```

### Test Cross-Field Validation

```python
from datetime import date, timedelta

class TestDateRangeValidation:
    """Test date range validation."""

    def test_end_before_start_rejected(self):
        """Test end_date before start_date is rejected."""
        with pytest.raises(ValueError, match="end_date must be"):
            DateRangeFilter(
                start_date=date(2025, 1, 31),
                end_date=date(2025, 1, 1)
            )

    def test_range_too_large_rejected(self):
        """Test date range exceeding limit is rejected."""
        start = date(2025, 1, 1)
        end = start + timedelta(days=366)  # Over 365 day limit

        with pytest.raises(ValueError, match="cannot exceed"):
            DateRangeFilter(start_date=start, end_date=end)

    def test_valid_range_accepted(self):
        """Test valid date range is accepted."""
        start = date(2025, 1, 1)
        end = date(2025, 1, 31)

        filter = DateRangeFilter(start_date=start, end_date=end)
        assert filter.start_date == start
        assert filter.end_date == end
```

---

## Best Practices

### 1. **Use Field Constraints Over Validators When Possible**

**Prefer:**
```python
name: str = Field(..., min_length=2, max_length=100)
```

**Over:**
```python
name: str

@field_validator("name")
@classmethod
def validate_name_length(cls, v):
    if len(v) < 2 or len(v) > 100:
        raise ValueError("name must be 2-100 characters")
    return v
```

### 2. **Use Enums for Fixed Value Sets**

**Prefer:**
```python
from enum import Enum

class RoleSchema(str, Enum):
    PRIMARY = "primary"
    SUPERVISING = "supervising"
    BACKUP = "backup"

class Assignment(BaseModel):
    role: RoleSchema
```

**Over:**
```python
role: str

@field_validator("role")
@classmethod
def validate_role(cls, v):
    if v not in ["primary", "supervising", "backup"]:
        raise ValueError("Invalid role")
    return v
```

### 3. **Validate Business Rules in Services, Not Schemas**

**Schema validation should focus on:**
- Data format and type
- Field constraints (length, range)
- Cross-field consistency
- Input sanitization

**Service validation should handle:**
- Database lookups (does person exist?)
- Business logic (is person qualified?)
- ACGME compliance
- Schedule conflicts

### 4. **Document All Constraints**

```python
pgy_level: int | None = Field(
    None,
    ge=1,
    le=3,
    description=(
        "Post-Graduate Year level for residents (1, 2, or 3). "
        "Required for residents, must be None for faculty."
    ),
    examples=[2]
)
```

### 5. **Provide Helpful Examples**

Include examples that show:
- Typical use case
- Edge cases
- Optional fields as None
- Lists/arrays with multiple items

### 6. **Sanitize User Input**

```python
@field_validator("notes")
@classmethod
def sanitize_notes(cls, v: str | None) -> str | None:
    """Sanitize notes to prevent XSS."""
    if v is not None:
        # Remove HTML tags
        v = re.sub(r'<[^>]*>', '', v)
        # Strip whitespace
        v = v.strip()
    return v
```

### 7. **Use Consistent Patterns**

Create reusable patterns for common validation:
- Date ranges
- UUID validation
- String sanitization
- Pagination parameters
- Sorting/filtering

---

## Summary Checklist

For each schema, ensure:

- [ ] All string fields have `min_length`/`max_length`
- [ ] All numeric fields have `ge`/`le`/`gt`/`lt` constraints
- [ ] All fields have clear descriptions
- [ ] Enums are used for fixed value sets
- [ ] Cross-field validation uses `@model_validator(mode="after")`
- [ ] Custom validators have clear error messages
- [ ] Request/response examples are provided
- [ ] Security validations are in place (XSS, SQL injection)
- [ ] Tests cover valid inputs, invalid inputs, and edge cases
- [ ] Documentation explains validation rules

---

## Resources

- **Pydantic Documentation:** https://docs.pydantic.dev/latest/
- **Field Constraints:** https://docs.pydantic.dev/latest/concepts/fields/
- **Validators:** https://docs.pydantic.dev/latest/concepts/validators/
- **JSON Schema:** https://docs.pydantic.dev/latest/concepts/json_schema/

---

**Next Steps:**
1. Apply these patterns to all request schemas
2. Add comprehensive tests for all validators
3. Update OpenAPI documentation with examples
4. Review error messages for clarity
