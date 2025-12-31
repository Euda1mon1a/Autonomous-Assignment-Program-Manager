***REMOVED*** Schema Conventions

> **Last Updated:** 2025-12-31
> **Purpose:** Naming conventions and patterns for Pydantic schemas and Zod schemas

---

***REMOVED******REMOVED*** Table of Contents

1. [Overview](***REMOVED***overview)
2. [Naming Conventions](***REMOVED***naming-conventions)
3. [Schema Patterns](***REMOVED***schema-patterns)
4. [Field Conventions](***REMOVED***field-conventions)
5. [Validation Patterns](***REMOVED***validation-patterns)

---

***REMOVED******REMOVED*** Overview

Consistent schema naming and structure improves code maintainability and developer experience.

***REMOVED******REMOVED******REMOVED*** Key Principles

1. **Clarity**: Schema names should clearly indicate their purpose
2. **Consistency**: Follow established patterns throughout the codebase
3. **Type Safety**: Leverage Pydantic/Zod type inference
4. **Reusability**: Create base schemas for common patterns

---

***REMOVED******REMOVED*** Naming Conventions

***REMOVED******REMOVED******REMOVED*** Backend (Pydantic)

***REMOVED******REMOVED******REMOVED******REMOVED*** Schema Suffixes

- **`Base`**: Shared fields across CRUD operations
  - Example: `PersonBase`, `AssignmentBase`

- **`Create`**: Fields required for creation
  - Example: `PersonCreate`, `AssignmentCreate`

- **`Update`**: Fields allowed for updates (typically partial)
  - Example: `PersonUpdate`, `AssignmentUpdate`

- **`Response`**: API response schema (includes computed fields, timestamps)
  - Example: `PersonResponse`, `AssignmentResponse`

- **`Filter`**: Query filter parameters
  - Example: `PersonFilter`, `AssignmentFilter`

- **`Sort`**: Sorting parameters
  - Example: `PersonSort`, `AssignmentSort`

***REMOVED******REMOVED******REMOVED******REMOVED*** Examples

```python
***REMOVED*** Base schema (shared fields)
class PersonBase(BaseModel):
    name: str
    type: str
    email: str | None = None

***REMOVED*** Create schema (inherits base)
class PersonCreate(PersonBase):
    pass

***REMOVED*** Update schema (partial base)
class PersonUpdate(BaseModel):
    name: str | None = None
    email: str | None = None

***REMOVED*** Response schema (adds metadata)
class PersonResponse(PersonBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

***REMOVED******REMOVED******REMOVED*** Frontend (Zod/TypeScript)

***REMOVED******REMOVED******REMOVED******REMOVED*** Schema Suffixes

- **`Schema`**: Zod schema definition
  - Example: `personBaseSchema`, `assignmentCreateSchema`

- **Type Export**: TypeScript type inferred from schema
  - Example: `PersonBase`, `AssignmentCreate`

***REMOVED******REMOVED******REMOVED******REMOVED*** Examples

```typescript
// Schema definition
export const personBaseSchema = z.object({
  name: z.string().min(2).max(255),
  type: z.enum(["resident", "faculty"]),
  email: z.string().email().optional().nullable(),
});

// Type export
export type PersonBase = z.infer<typeof personBaseSchema>;

// Create schema (extends base)
export const personCreateSchema = personBaseSchema;

// Update schema (partial base)
export const personUpdateSchema = personBaseSchema.partial();
```

---

***REMOVED******REMOVED*** Schema Patterns

***REMOVED******REMOVED******REMOVED*** Pattern 1: CRUD Schema Family

Every entity should have a family of related schemas:

```python
***REMOVED*** backend/app/schemas/person.py

class PersonBase(BaseModel):
    """Base person schema."""
    name: str
    type: str
    email: EmailStr | None = None

class PersonCreate(PersonBase):
    """Schema for creating a person."""
    pass

class PersonUpdate(BaseModel):
    """Schema for updating a person."""
    name: str | None = None
    email: EmailStr | None = None

class PersonResponse(PersonBase):
    """Schema for person response."""
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PersonListResponse(BaseModel):
    """Schema for paginated person list."""
    items: list[PersonResponse]
    total: int
```

***REMOVED******REMOVED******REMOVED*** Pattern 2: Nested Schemas

For complex objects with relationships:

```python
class AssignmentResponse(BaseModel):
    """Assignment with nested person and block."""
    id: UUID
    person: PersonResponse
    block: BlockResponse
    rotation_template: RotationTemplateResponse | None
    role: str
```

***REMOVED******REMOVED******REMOVED*** Pattern 3: Mixins for Common Fields

```python
class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    created_at: datetime
    updated_at: datetime

class AuditMixin(TimestampMixin):
    """Mixin for audit fields."""
    created_by: str | None
    updated_by: str | None

class PersonResponse(PersonBase, AuditMixin):
    """Person with audit fields."""
    id: UUID
```

***REMOVED******REMOVED******REMOVED*** Pattern 4: Filters and Pagination

```python
class PersonFilter(BaseModel):
    """Filter parameters for person queries."""
    person_type: str | None = None
    pgy_level: int | None = None
    search: str | None = None

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=1000)

class PersonListRequest(BaseModel):
    """Request for person list with filters."""
    filters: PersonFilter = Field(default_factory=PersonFilter)
    pagination: PaginationParams = Field(default_factory=PaginationParams)
    sort: PersonSort | None = None
```

---

***REMOVED******REMOVED*** Field Conventions

***REMOVED******REMOVED******REMOVED*** Field Names

- **Use snake_case**: `first_name`, `pgy_level`, `created_at`
- **Boolean fields**: Prefix with `is_`, `has_`, `can_`
  - Example: `is_active`, `has_email`, `can_supervise`
- **Timestamp fields**: Suffix with `_at`
  - Example: `created_at`, `updated_at`, `executed_at`
- **Count fields**: Suffix with `_count`
  - Example: `sunday_call_count`, `total_count`

***REMOVED******REMOVED******REMOVED*** Field Types

```python
***REMOVED*** Strings
name: str = Field(..., min_length=1, max_length=255)

***REMOVED*** Optional strings
email: str | None = Field(None, description="Email address")

***REMOVED*** Enums
type: Literal["resident", "faculty"]

***REMOVED*** Dates
date: date
created_at: datetime

***REMOVED*** UUIDs
id: UUID
person_id: UUID

***REMOVED*** Lists
specialties: list[str] = Field(default_factory=list)

***REMOVED*** Nested objects
person: PersonResponse

***REMOVED*** Discriminated unions
assignment: Union[PrimaryAssignment, SupervisingAssignment]
```

***REMOVED******REMOVED******REMOVED*** Field Descriptions

Always provide descriptions for non-obvious fields:

```python
class PersonCreate(BaseModel):
    name: str = Field(..., description="Full name of the person")
    type: str = Field(..., description="Person type (resident or faculty)")
    pgy_level: int | None = Field(None, description="Post-graduate year (1-3 for residents)")
```

---

***REMOVED******REMOVED*** Validation Patterns

***REMOVED******REMOVED******REMOVED*** Pattern 1: Field Validators

```python
class PersonCreate(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not v or "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower()
```

***REMOVED******REMOVED******REMOVED*** Pattern 2: Model Validators

For cross-field validation:

```python
class PersonCreate(BaseModel):
    type: str
    pgy_level: int | None

    @model_validator(mode="after")
    def validate_pgy_level(self) -> "PersonCreate":
        """Validate PGY level based on person type."""
        if self.type == "resident" and self.pgy_level is None:
            raise ValueError("Residents must have a PGY level")
        if self.type == "faculty" and self.pgy_level is not None:
            raise ValueError("Faculty cannot have a PGY level")
        return self
```

***REMOVED******REMOVED******REMOVED*** Pattern 3: Custom Validators

```python
from app.validators.person_validators import validate_pgy_level

class PersonCreate(BaseModel):
    type: str
    pgy_level: int | None

    @field_validator("pgy_level")
    @classmethod
    def validate_pgy(cls, v: int | None, info) -> int | None:
        """Validate PGY level."""
        return validate_pgy_level(v, info.data["type"])
```

***REMOVED******REMOVED******REMOVED*** Pattern 4: Async Validators (Custom)

For database-dependent validation:

```python
***REMOVED*** Not in Pydantic schema - use custom validator
async def validate_assignment_create(
    db: AsyncSession,
    assignment: AssignmentCreate,
) -> None:
    """Validate assignment before creation."""
    ***REMOVED*** Check for conflicts
    conflict = await validate_assignment_conflict(
        db, assignment.person_id, assignment.block_id
    )
    if conflict["has_conflict"]:
        raise ValidationError(conflict["message"])
```

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** 1. Keep Schemas Focused

Each schema should have a single, clear purpose:

```python
***REMOVED*** Good: Separate schemas for different operations
class PersonCreate(BaseModel):
    name: str
    email: str

class PersonUpdate(BaseModel):
    name: str | None = None
    email: str | None = None

***REMOVED*** Bad: One schema for everything
class Person(BaseModel):
    id: UUID | None = None  ***REMOVED*** Only for responses
    name: str | None = None  ***REMOVED*** Required for create
    email: str | None = None
```

***REMOVED******REMOVED******REMOVED*** 2. Use Config Appropriately

```python
class PersonResponse(BaseModel):
    id: UUID
    name: str

    class Config:
        ***REMOVED*** Enable ORM mode for SQLAlchemy models
        from_attributes = True

        ***REMOVED*** Validate on assignment
        validate_assignment = True

        ***REMOVED*** JSON schema examples
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "John Doe"
            }
        }
```

***REMOVED******REMOVED******REMOVED*** 3. Document Complex Validation

```python
class AssignmentCreate(BaseModel):
    """
    Schema for creating an assignment.

    Validation rules:
    - Person and block must exist
    - No duplicate assignments (same person/block)
    - Must maintain ACGME supervision ratios
    - Cannot violate 1-in-7 rule
    """
    person_id: UUID
    block_id: UUID
    role: str
```

***REMOVED******REMOVED******REMOVED*** 4. Leverage Type Inference

```python
***REMOVED*** Define schema once
personCreateSchema = z.object({
  name: z.string().min(2),
  type: z.enum(["resident", "faculty"]),
});

// Infer TypeScript type
type PersonCreate = z.infer<typeof personCreateSchema>;

// Use in function signatures
function createPerson(data: PersonCreate): Promise<PersonResponse> {
  return personCreateSchema.parse(data);
}
```

---

***REMOVED******REMOVED*** References

- [Pydantic Field Types](https://docs.pydantic.dev/latest/concepts/fields/)
- [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [Zod Documentation](https://zod.dev/)
- [TypeScript Type Inference](https://www.typescriptlang.org/docs/handbook/type-inference.html)
