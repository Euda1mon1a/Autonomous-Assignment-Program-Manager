***REMOVED*** Validation Guide

> **Last Updated:** 2025-12-31
> **Purpose:** Comprehensive guide to validation infrastructure in the Residency Scheduler

---

***REMOVED******REMOVED*** Table of Contents

1. [Overview](***REMOVED***overview)
2. [Backend Validation](***REMOVED***backend-validation)
3. [Frontend Validation](***REMOVED***frontend-validation)
4. [Validation Rules](***REMOVED***validation-rules)
5. [Common Patterns](***REMOVED***common-patterns)
6. [Best Practices](***REMOVED***best-practices)

---

***REMOVED******REMOVED*** Overview

The Residency Scheduler uses a comprehensive multi-layer validation approach:

- **Frontend validation**: Immediate feedback using Zod schemas
- **Backend validation**: Pydantic schemas + custom validators
- **Business rules**: Domain-specific validation logic
- **Database constraints**: Referential integrity

***REMOVED******REMOVED******REMOVED*** Validation Layers

```
User Input
    ↓
Frontend Validation (Zod)
    ↓
API Request
    ↓
Pydantic Schema Validation
    ↓
Custom Validators
    ↓
Business Rules
    ↓
Database Constraints
    ↓
Data Persistence
```

---

***REMOVED******REMOVED*** Backend Validation

***REMOVED******REMOVED******REMOVED*** Pydantic Schemas

All API requests and responses use Pydantic schemas for validation.

**Location:** `backend/app/schemas/`

**Example:**

```python
from pydantic import BaseModel, Field, field_validator

class PersonCreate(BaseModel):
    """Schema for creating a person."""

    name: str = Field(..., min_length=2, max_length=255)
    type: str = Field(..., description="Person type (resident, faculty)")
    email: str | None = Field(None, description="Email address")
    pgy_level: int | None = Field(None, ge=1, le=3)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("resident", "faculty"):
            raise ValueError("type must be 'resident' or 'faculty'")
        return v
```

***REMOVED******REMOVED******REMOVED*** Custom Validators

Domain-specific validators for complex validation logic.

**Location:** `backend/app/validators/`

***REMOVED******REMOVED******REMOVED******REMOVED*** Core Validators

- **`acgme_validators.py`** - ACGME compliance rules
- **`assignment_validators.py`** - Assignment validation
- **`credential_validators.py`** - Credential/certification validation
- **`swap_validators.py`** - Swap request validation
- **`date_validators.py`** - Date/time validation
- **`person_validators.py`** - Person data validation
- **`schedule_validators.py`** - Schedule validation

**Example:**

```python
from app.validators.acgme_validators import validate_80_hour_rule

***REMOVED*** Validate ACGME 80-hour rule
violations = await validate_80_hour_rule(
    db=db,
    person_id=person_id,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 28),
)

if violations:
    raise ValidationError(f"ACGME violations detected: {violations}")
```

***REMOVED******REMOVED******REMOVED*** Validation Rules

Reusable business rules and constraints.

**Location:** `backend/app/validators/rules/`

- **`business_rules.py`** - Domain business rules
- **`compliance_rules.py`** - Regulatory compliance
- **`constraint_rules.py`** - Hard and soft constraints
- **`temporal_rules.py`** - Time-based rules
- **`relationship_rules.py`** - Data relationship validation

**Example:**

```python
from app.validators.rules.business_rules import validate_rotation_eligibility

***REMOVED*** Check if person is eligible for rotation
result = await validate_rotation_eligibility(
    db=db,
    person_id=person_id,
    rotation_type="surgery",
    check_date=date(2024, 3, 15),
)

if not result["is_eligible"]:
    raise ValidationError(result["ineligibility_reasons"])
```

***REMOVED******REMOVED******REMOVED*** Validation Utilities

Helper functions for common validation tasks.

**Location:** `backend/app/utils/validation/`

- **`validators.py`** - Reusable validators
- **`sanitizers.py`** - Input sanitization
- **`normalizers.py`** - Data normalization
- **`transformers.py`** - Data transformation

---

***REMOVED******REMOVED*** Frontend Validation

***REMOVED******REMOVED******REMOVED*** Zod Schemas

Type-safe validation schemas for frontend.

**Location:** `frontend/src/lib/validation/schemas.ts`

**Example:**

```typescript
import { z } from "zod";
import { personCreateSchema } from "@/lib/validation/schemas";

// Validate person create data
const result = personCreateSchema.safeParse({
  name: "John Doe",
  type: "resident",
  pgy_level: 2,
});

if (!result.success) {
  console.error(result.error.errors);
}
```

***REMOVED******REMOVED******REMOVED*** Custom Validators

Frontend-specific validation functions.

**Location:** `frontend/src/lib/validation/validators.ts`

**Example:**

```typescript
import { validateFutureDate } from "@/lib/validation/validators";

const result = validateFutureDate("2024-12-31", 7);
if (!result.isValid) {
  console.error(result.error);
}
```

***REMOVED******REMOVED******REMOVED*** Form Validation

React hook utilities for form validation.

**Location:** `frontend/src/lib/validation/form-validation.ts`

**Example:**

```typescript
import { validateForm } from "@/lib/validation/form-validation";
import { personCreateSchema } from "@/lib/validation/schemas";

const handleSubmit = async (values: PersonCreate) => {
  const { isValid, errors } = validateForm(values, personCreateSchema);

  if (!isValid) {
    setFormErrors(errors);
    return;
  }

  // Submit to API
  await createPerson(values);
};
```

***REMOVED******REMOVED******REMOVED*** Error Messages

Standardized error messages for consistent UX.

**Location:** `frontend/src/lib/validation/error-messages.ts`

**Example:**

```typescript
import { validationErrors } from "@/lib/validation/error-messages";

const error = validationErrors.minLength("Name", 2);
// "Name must be at least 2 characters"
```

---

***REMOVED******REMOVED*** Validation Rules

***REMOVED******REMOVED******REMOVED*** ACGME Compliance Rules

1. **80-Hour Weekly Limit**
   - Maximum 80 hours/week averaged over 4 weeks
   - Validator: `validate_80_hour_rule()`

2. **1-in-7 Day Off Rule**
   - One 24-hour period off every 7 days
   - Validator: `validate_one_in_seven_rule()`

3. **24+4 Hour Shift Limit**
   - Maximum 24 hours + 4 hours for handoff
   - Validator: `validate_24_plus_4_rule()`

4. **Supervision Ratios**
   - PGY-1: 1 faculty per 2 residents
   - PGY-2/3: 1 faculty per 4 residents
   - Validator: `validate_supervision_ratio()`

***REMOVED******REMOVED******REMOVED*** Business Rules

1. **Rotation Eligibility**
   - Check person qualifications for rotation
   - Validator: `validate_rotation_eligibility()`

2. **Workload Distribution**
   - Ensure fair workload across team
   - Validator: `validate_workload_distribution()`

3. **Call Equity**
   - Balanced call distribution
   - Validator: `validate_call_equity()`

***REMOVED******REMOVED******REMOVED*** Credential Requirements

1. **Slot Type Requirements**
   - Hard requirements (must have)
   - Soft requirements (preferred)
   - Validator: `validate_slot_type_credentials()`

2. **Expiration Checking**
   - Check credential expiration dates
   - Validator: `validate_person_has_credential()`

---

***REMOVED******REMOVED*** Common Patterns

***REMOVED******REMOVED******REMOVED*** Pattern 1: Pre-Validation Before Create

```python
async def create_assignment(
    db: AsyncSession,
    assignment_data: AssignmentCreate,
) -> Assignment:
    """Create assignment with validation."""

    ***REMOVED*** 1. Validate no conflicts
    conflict_result = await validate_assignment_conflict(
        db=db,
        person_id=assignment_data.person_id,
        block_id=assignment_data.block_id,
    )

    if conflict_result["has_conflict"]:
        raise ValidationError(conflict_result["message"])

    ***REMOVED*** 2. Validate ACGME compliance
    acgme_result = await validate_assignment_acgme_compliance(
        db=db,
        person_id=assignment_data.person_id,
        block_id=assignment_data.block_id,
    )

    if not acgme_result["is_compliant"]:
        raise ValidationError(acgme_result["violations"])

    ***REMOVED*** 3. Create assignment
    assignment = Assignment(**assignment_data.dict())
    db.add(assignment)
    await db.commit()

    return assignment
```

***REMOVED******REMOVED******REMOVED*** Pattern 2: Multi-Layer Validation

```typescript
// Frontend
const handleSubmit = async (values: PersonCreate) => {
  // Layer 1: Schema validation
  const schemaResult = validateForm(values, personCreateSchema);
  if (!schemaResult.isValid) {
    setFormErrors(schemaResult.errors);
    return;
  }

  // Layer 2: Custom validation
  const pgyResult = validatePgyLevel(values.pgy_level, values.type);
  if (!pgyResult.isValid) {
    setFormError("pgy_level", pgyResult.error);
    return;
  }

  // Layer 3: API call (backend validation)
  try {
    await api.createPerson(values);
  } catch (error) {
    const message = getApiErrorMessage(error);
    setFormError("_general", message);
  }
};
```

***REMOVED******REMOVED******REMOVED*** Pattern 3: Bulk Validation

```python
async def validate_bulk_assignments(
    db: AsyncSession,
    assignments: list[AssignmentCreate],
) -> dict:
    """Validate multiple assignments."""

    errors = []

    for idx, assignment in enumerate(assignments):
        ***REMOVED*** Validate each assignment
        result = await validate_assignment_conflict(
            db=db,
            person_id=assignment.person_id,
            block_id=assignment.block_id,
        )

        if result["has_conflict"]:
            errors.append({
                "index": idx,
                "error": result["message"],
            })

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
    }
```

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** 1. Always Validate Early

Validate at the earliest possible point:
- Frontend: Immediate feedback
- API: Before business logic
- Database: Constraints as last resort

***REMOVED******REMOVED******REMOVED*** 2. Use Appropriate Validators

- **Simple checks**: Pydantic field validators
- **Cross-field validation**: Pydantic model validators
- **Complex business logic**: Custom validators
- **Database state**: Async validators

***REMOVED******REMOVED******REMOVED*** 3. Provide Clear Error Messages

```python
***REMOVED*** Bad
raise ValueError("Invalid data")

***REMOVED*** Good
raise ValidationError(
    "Person is already assigned to block on 2024-03-15 PM. "
    "Cannot create duplicate assignment."
)
```

***REMOVED******REMOVED******REMOVED*** 4. Separate Concerns

```python
***REMOVED*** Validator (pure logic)
def validate_pgy_level(pgy_level: int | None, person_type: str) -> int | None:
    """Validate PGY level for person type."""
    if person_type == "resident" and pgy_level is None:
        raise ValidationError("Residents must have a PGY level")
    return pgy_level

***REMOVED*** Schema (API layer)
class PersonCreate(BaseModel):
    pgy_level: int | None

    @field_validator("pgy_level")
    @classmethod
    def validate_pgy(cls, v, info):
        return validate_pgy_level(v, info.data["type"])
```

***REMOVED******REMOVED******REMOVED*** 5. Test Validators Thoroughly

```python
class TestPgyValidator:
    """Test PGY level validation."""

    def test_resident_requires_pgy(self):
        """Residents must have PGY level."""
        with pytest.raises(ValidationError):
            validate_pgy_level(None, "resident")

    def test_faculty_cannot_have_pgy(self):
        """Faculty cannot have PGY level."""
        with pytest.raises(ValidationError):
            validate_pgy_level(2, "faculty")

    def test_valid_pgy_range(self):
        """PGY must be 1-3."""
        assert validate_pgy_level(1, "resident") == 1
        assert validate_pgy_level(3, "resident") == 3

        with pytest.raises(ValidationError):
            validate_pgy_level(0, "resident")

        with pytest.raises(ValidationError):
            validate_pgy_level(4, "resident")
```

---

***REMOVED******REMOVED*** References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Zod Documentation](https://zod.dev/)
- [FastAPI Validation](https://fastapi.tiangolo.com/tutorial/body/)
- [ACGME Requirements](../compliance/acgme-requirements.md)
