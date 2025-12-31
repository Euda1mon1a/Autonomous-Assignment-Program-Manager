# Schema Validation Checklist

**Quick reference for creating or enhancing Pydantic schemas**

---

## Before You Start

- [ ] Read `VALIDATION_GUIDE.md` for detailed patterns
- [ ] Review `block_enhanced_example.py` for complete example
- [ ] Check existing schemas for similar patterns

---

## Field-Level Validation

### String Fields

- [ ] Add `min_length` and `max_length` constraints
- [ ] Add `pattern` for regex validation (if applicable)
- [ ] Add field `description` explaining constraints
- [ ] Add `examples` showing valid values
- [ ] Add validator for special characters/sanitization (if needed)
- [ ] Use `EmailStr` for email fields
- [ ] Use Enum for fixed value sets

**Example:**
```python
name: str = Field(
    ...,
    min_length=2,
    max_length=100,
    description="Person's full name (2-100 characters)",
    examples=["Dr. Jane Smith"]
)
```

### Numeric Fields

- [ ] Add range constraints (`ge`, `le`, `gt`, `lt`)
- [ ] Add field `description` explaining range
- [ ] Add `examples` showing valid values
- [ ] Add validator for precision (if needed)

**Example:**
```python
pgy_level: int = Field(
    ...,
    ge=1,
    le=3,
    description="PGY level (1-3)",
    examples=[2]
)
```

### Date/DateTime Fields

- [ ] Add date range validation
- [ ] Add field `description` with format info
- [ ] Add `examples` in ISO 8601 format
- [ ] Validate academic year bounds (if applicable)
- [ ] Validate not too far past/future (if applicable)

**Example:**
```python
start_date: date = Field(
    ...,
    description="Start date (ISO 8601: YYYY-MM-DD)",
    examples=["2025-01-15"]
)

@field_validator("start_date")
@classmethod
def validate_start_date(cls, v: date) -> date:
    if v < date.today() - timedelta(days=730):
        raise ValueError("start_date cannot be >2 years ago")
    return v
```

### List/Collection Fields

- [ ] Add `min_length` and `max_length` constraints
- [ ] Add field `description`
- [ ] Add `examples` with multiple items
- [ ] Add validator to check for duplicates (if needed)
- [ ] Add validator to check item values (if needed)

**Example:**
```python
resident_ids: list[UUID] = Field(
    ...,
    min_length=1,
    max_length=100,
    description="List of resident IDs (1-100)",
    examples=[[uuid1, uuid2]]
)
```

### Optional Fields

- [ ] Set appropriate default (None or default_factory)
- [ ] Add field `description` explaining when to use
- [ ] Include None in `examples`

**Example:**
```python
notes: str | None = Field(
    None,
    max_length=1000,
    description="Optional notes (max 1000 chars)",
    examples=["Some notes", None]
)
```

---

## Cross-Field Validation

### Date Ranges

- [ ] Add `@model_validator(mode="after")` to check end >= start
- [ ] Validate total range duration (if applicable)
- [ ] Provide clear error message with actual values

**Example:**
```python
@model_validator(mode="after")
def validate_date_range(self):
    if self.end_date < self.start_date:
        raise ValueError("end_date must be >= start_date")
    return self
```

### Conditional Requirements

- [ ] Add `@model_validator(mode="after")` for conditional logic
- [ ] Check all conditional field requirements
- [ ] Provide clear error message explaining requirement

**Example:**
```python
@model_validator(mode="after")
def validate_swap_requirements(self):
    if self.swap_type == "one_to_one" and self.target_id is None:
        raise ValueError("target_id required for one_to_one swaps")
    return self
```

### Business Rules

- [ ] Document business rule in validator docstring
- [ ] Add clear error message
- [ ] Consider if rule belongs in service layer instead

---

## Request/Response Examples

### model_config

- [ ] Add `model_config` with `json_schema_extra`
- [ ] Include at least one complete example
- [ ] Include multiple examples for different scenarios
- [ ] Use real-looking data (not foo/bar)
- [ ] Include optional fields as None in at least one example

**Example:**
```python
model_config = {
    "json_schema_extra": {
        "examples": [
            {
                "field1": "value1",
                "field2": 123,
                "optional_field": None
            },
            {
                "field1": "value2",
                "field2": 456,
                "optional_field": "present"
            }
        ]
    }
}
```

### Multiple Scenario Examples

- [ ] Add `title` to each example
- [ ] Add `description` explaining scenario
- [ ] Provide `value` with complete data

**Example:**
```python
"examples": [
    {
        "title": "Standard Case",
        "description": "Typical usage scenario",
        "value": {...}
    },
    {
        "title": "Edge Case",
        "description": "Unusual but valid scenario",
        "value": {...}
    }
]
```

---

## Error Messages

- [ ] Messages are clear and specific
- [ ] Messages show what was expected
- [ ] Messages show what was received (when safe)
- [ ] Messages suggest how to fix
- [ ] Messages don't leak sensitive data

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

## Security

### Input Sanitization

- [ ] Remove HTML tags from user input
- [ ] Trim whitespace
- [ ] Check for SQL injection patterns (if applicable)
- [ ] Validate file paths don't traverse (if applicable)
- [ ] Validate URLs are safe (if applicable)

**Example:**
```python
@field_validator("notes")
@classmethod
def sanitize_notes(cls, v: str | None) -> str | None:
    if v is not None:
        import re
        v = re.sub(r'<[^>]*>', '', v)  # Remove HTML
        v = v.strip()  # Trim whitespace
    return v
```

### Sensitive Data

- [ ] Don't log sensitive field values
- [ ] Don't include sensitive data in error messages
- [ ] Use appropriate field types (SecretStr for passwords)

---

## Documentation

### Field Descriptions

- [ ] All fields have `description`
- [ ] Descriptions explain constraints
- [ ] Descriptions explain format (for dates, etc.)
- [ ] Descriptions explain when to use (for optional fields)

### Class Docstrings

- [ ] Schema has clear docstring
- [ ] Docstring explains purpose
- [ ] Docstring mentions key validation rules (if complex)

### Validator Docstrings

- [ ] All validators have docstrings
- [ ] Docstrings explain what is validated
- [ ] Docstrings document Args, Returns, Raises

---

## Testing

### Unit Tests

- [ ] Test valid input passes
- [ ] Test invalid input rejected with correct error
- [ ] Test missing required fields rejected
- [ ] Test field constraints enforced (length, range)
- [ ] Test cross-field validation enforced
- [ ] Test edge cases (boundary values, null, empty)
- [ ] Use `@pytest.mark.parametrize` for multiple test cases

**Example:**
```python
def test_invalid_role_rejected(self):
    with pytest.raises(ValueError, match="role must be"):
        AssignmentCreate(
            block_id=uuid4(),
            person_id=uuid4(),
            role="invalid_role"
        )
```

### Coverage

- [ ] All validators have tests
- [ ] All error paths are tested
- [ ] Coverage >95% for schema file

---

## Code Style

- [ ] Follow PEP 8
- [ ] Use type hints
- [ ] Import Field from pydantic
- [ ] Import validators from pydantic
- [ ] Use appropriate field validator decorator
- [ ] Validators are classmethod with @classmethod decorator
- [ ] Model validators use mode="after"
- [ ] Consistent ordering: field definition → field validator → model validator

---

## Final Checks

- [ ] All checklist items completed
- [ ] Tests written and passing
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Examples tested in FastAPI docs
- [ ] Error messages tested

---

## Common Patterns

### UUID Fields
```python
from uuid import UUID

person_id: UUID = Field(
    ...,
    description="Person identifier (UUID)",
    examples=["550e8400-e29b-41d4-a716-446655440000"]
)
```

### Email Fields
```python
from pydantic import EmailStr

email: EmailStr = Field(
    ...,
    description="Valid email address",
    examples=["user@example.com"]
)
```

### Enum Fields
```python
from enum import Enum

class RoleEnum(str, Enum):
    PRIMARY = "primary"
    SUPERVISING = "supervising"
    BACKUP = "backup"

role: RoleEnum = Field(
    ...,
    description="Assignment role"
)
```

### Date Range
```python
from datetime import date

start_date: date = Field(..., description="Start date")
end_date: date = Field(..., description="End date")

@model_validator(mode="after")
def validate_date_range(self):
    if self.end_date < self.start_date:
        raise ValueError("end_date must be >= start_date")
    return self
```

### Pagination
```python
page: int = Field(
    1,
    ge=1,
    description="Page number (1-indexed)"
)

page_size: int = Field(
    100,
    ge=1,
    le=500,
    description="Items per page (max 500)"
)
```

---

## Quick Reference

| Type | Constraints | Example |
|------|-------------|---------|
| str | min_length, max_length, pattern | `Field(..., min_length=2, max_length=100)` |
| int | ge, le, gt, lt | `Field(..., ge=1, le=10)` |
| float | ge, le, gt, lt | `Field(..., ge=0.0, le=1.0)` |
| date | Custom validator | `@field_validator("date")` |
| list | min_length, max_length | `Field(..., min_length=1, max_length=100)` |
| UUID | Native type validation | `field: UUID` |
| Email | EmailStr type | `field: EmailStr` |
| Enum | Enum class | `field: MyEnum` |

---

## Resources

- **Full Guide:** `VALIDATION_GUIDE.md`
- **Complete Example:** `block_enhanced_example.py`
- **Pydantic Docs:** https://docs.pydantic.dev/latest/
- **Project Guidelines:** `/CLAUDE.md`

---

**Last Updated:** 2025-12-31
**Version:** 1.0
