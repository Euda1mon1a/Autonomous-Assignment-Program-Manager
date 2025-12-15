# Code Style and Conventions

This document defines the coding standards and conventions for the Residency Scheduler project to ensure consistency, readability, and maintainability.

## Table of Contents

1. [Python Style Guide](#python-style-guide)
2. [TypeScript Style Guide](#typescript-style-guide)
3. [CSS/Styling Conventions](#cssstyling-conventions)
4. [Git Conventions](#git-conventions)
5. [Documentation Standards](#documentation-standards)
6. [Code Organization](#code-organization)

---

## Python Style Guide

### General Principles

We follow [PEP 8](https://pep8.org/) with some project-specific conventions.

### Formatting Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| Black | Code formatting | `pyproject.toml` |
| Ruff | Linting | `pyproject.toml` |
| mypy | Type checking | `pyproject.toml` |
| isort | Import sorting | Via Ruff |

### Running Formatters

```bash
cd backend

# Format code
black .

# Lint code
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Type check
mypy app
```

### Line Length

- Maximum **88 characters** (Black default)
- Long strings can exceed for readability

### Imports

Organize imports in this order:
1. Standard library
2. Third-party packages
3. Local application imports

```python
# Standard library
from datetime import date, timedelta
from typing import Optional, List

# Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Local
from app.db.session import get_db
from app.models import Person
from app.schemas.person import PersonCreate, PersonResponse
```

### Type Hints

**Required** for all function parameters and return types:

```python
# Good
def calculate_hours(
    assignments: list[Assignment],
    start_date: date,
    end_date: date,
) -> float:
    """Calculate total hours for a date range."""
    ...

# Bad - missing type hints
def calculate_hours(assignments, start_date, end_date):
    ...
```

### Docstrings

Use Google-style docstrings for public functions and classes:

```python
def generate_schedule(
    start_date: date,
    end_date: date,
    algorithm: str = "greedy",
) -> ScheduleResult:
    """Generate a schedule for the specified date range.

    Uses the specified algorithm to generate assignments while
    respecting ACGME compliance rules and absence constraints.

    Args:
        start_date: Beginning of the scheduling period.
        end_date: End of the scheduling period.
        algorithm: Scheduling algorithm to use. Options are
            "greedy", "min_conflicts", or "cp_sat".

    Returns:
        ScheduleResult containing assignments and any violations.

    Raises:
        ValueError: If end_date is before start_date.
        SchedulingError: If no valid schedule can be generated.

    Example:
        >>> engine = SchedulingEngine()
        >>> result = engine.generate_schedule(
        ...     date(2024, 1, 1),
        ...     date(2024, 1, 31)
        ... )
        >>> print(f"Generated {len(result.assignments)} assignments")
    """
    ...
```

### Class Definitions

```python
class Person(Base):
    """SQLAlchemy model for residents and faculty.

    Attributes:
        id: Primary key.
        name: Full name of the person.
        email: Unique email address.
        type: Either "resident" or "faculty".
        pgy_level: PGY level (1-7) for residents, None for faculty.
        is_active: Whether the person is currently active.
    """

    __tablename__ = "people"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    type: Mapped[PersonType] = mapped_column(Enum(PersonType), nullable=False)
    pgy_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="person")
    absences: Mapped[list["Absence"]] = relationship(back_populates="person")

    def __repr__(self) -> str:
        return f"<Person(id={self.id}, name='{self.name}', type='{self.type}')>"
```

### Pydantic Schemas

```python
from pydantic import BaseModel, Field, EmailStr, model_validator

class PersonCreate(BaseModel):
    """Schema for creating a new person."""

    name: str = Field(..., min_length=1, max_length=100, description="Full name")
    email: EmailStr = Field(..., description="Unique email address")
    type: PersonType = Field(..., description="Person type (resident or faculty)")
    pgy_level: Optional[int] = Field(
        None,
        ge=1,
        le=7,
        description="PGY level (required for residents)"
    )

    @model_validator(mode="after")
    def validate_pgy_for_resident(self) -> "PersonCreate":
        """Ensure residents have a PGY level."""
        if self.type == PersonType.RESIDENT and self.pgy_level is None:
            raise ValueError("PGY level is required for residents")
        return self

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Dr. Jane Smith",
                    "email": "jane.smith@hospital.org",
                    "type": "resident",
                    "pgy_level": 2,
                }
            ]
        }
    }
```

### FastAPI Routes

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Person
from app.schemas.person import PersonCreate, PersonResponse, PersonUpdate

router = APIRouter(prefix="/api/people", tags=["People"])


@router.post(
    "/",
    response_model=PersonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new person",
    description="Create a new resident or faculty member.",
)
async def create_person(
    person: PersonCreate,
    db: Session = Depends(get_db),
) -> Person:
    """Create a new person (resident or faculty).

    - **name**: Full name (1-100 characters)
    - **email**: Unique email address
    - **type**: Either "resident" or "faculty"
    - **pgy_level**: Required for residents (1-7)
    """
    # Check for duplicate email
    existing = db.query(Person).filter(Person.email == person.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Person with email {person.email} already exists",
        )

    db_person = Person(**person.model_dump())
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person


@router.get(
    "/{person_id}",
    response_model=PersonResponse,
    summary="Get a person by ID",
)
async def get_person(
    person_id: int,
    db: Session = Depends(get_db),
) -> Person:
    """Retrieve a person by their ID."""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person with ID {person_id} not found",
        )
    return person
```

### Error Handling

```python
from fastapi import HTTPException, status

# Use specific HTTP status codes
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Person not found",
)

raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid date range: end_date must be after start_date",
)

raise HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Cannot generate schedule: no available residents",
)
```

---

## TypeScript Style Guide

### Formatting Tools

| Tool | Purpose | Configuration |
|------|---------|---------------|
| ESLint | Linting | `.eslintrc.js` |
| Prettier | Formatting | `.prettierrc` |
| TypeScript | Type checking | `tsconfig.json` |

### Running Formatters

```bash
cd frontend

# Lint
npm run lint

# Format with Prettier
npx prettier --write .

# Type check
npx tsc --noEmit
```

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Components | PascalCase | `UserProfile.tsx` |
| Hooks | camelCase with "use" | `usePeople.ts` |
| Utilities | camelCase | `formatDate.ts` |
| Constants | UPPER_SNAKE_CASE | `API_BASE_URL` |
| Types/Interfaces | PascalCase | `PersonCreate` |
| Files | Component name or kebab-case | `UserProfile.tsx`, `api-client.ts` |

### Type Definitions

```typescript
// types/index.ts

// Use interfaces for object shapes
interface Person {
  id: number;
  name: string;
  email: string;
  type: PersonType;
  pgy_level: number | null;
  is_active: boolean;
}

// Use type for unions, intersections, and simple types
type PersonType = 'resident' | 'faculty';

// Use enums sparingly, prefer union types
type AbsenceType =
  | 'vacation'
  | 'deployment'
  | 'tdy'
  | 'medical'
  | 'family_emergency'
  | 'conference';

// Request/Response types
interface PersonCreate {
  name: string;
  email: string;
  type: PersonType;
  pgy_level?: number;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

// Component props
interface UserCardProps {
  user: Person;
  onSelect: (userId: number) => void;
  isActive?: boolean;
  className?: string;
}
```

### React Components

```typescript
// components/UserCard.tsx
import { cn } from '@/lib/utils';

interface UserCardProps {
  user: Person;
  onSelect: (userId: number) => void;
  isActive?: boolean;
  className?: string;
}

export function UserCard({
  user,
  onSelect,
  isActive = false,
  className,
}: UserCardProps) {
  const handleClick = () => {
    onSelect(user.id);
  };

  return (
    <div
      className={cn(
        'rounded-lg border p-4 transition-colors',
        isActive && 'border-blue-500 bg-blue-50',
        className
      )}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && handleClick()}
    >
      <h3 className="font-medium">{user.name}</h3>
      <p className="text-sm text-gray-500">{user.email}</p>
      {user.type === 'resident' && (
        <span className="text-xs text-blue-600">PGY-{user.pgy_level}</span>
      )}
    </div>
  );
}
```

### React Hooks

```typescript
// lib/hooks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, post, put, del } from './api';

// Query keys as constants
export const queryKeys = {
  people: ['people'] as const,
  person: (id: number) => ['people', id] as const,
  schedule: (start: string, end: string) => ['schedule', start, end] as const,
};

// Read hook
export function usePeople(params?: { type?: PersonType; active?: boolean }) {
  return useQuery({
    queryKey: [...queryKeys.people, params],
    queryFn: () => get<PaginatedResponse<Person>>('/api/people', { params }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Single item hook
export function usePerson(id: number) {
  return useQuery({
    queryKey: queryKeys.person(id),
    queryFn: () => get<Person>(`/api/people/${id}`),
    enabled: id > 0,
  });
}

// Mutation hook
export function useCreatePerson() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PersonCreate) => post<Person>('/api/people', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.people });
    },
  });
}

// Update hook
export function useUpdatePerson() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<PersonCreate> }) =>
      put<Person>(`/api/people/${id}`, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.people });
      queryClient.invalidateQueries({ queryKey: queryKeys.person(id) });
    },
  });
}

// Delete hook
export function useDeletePerson() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => del(`/api/people/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.people });
    },
  });
}
```

### Error Handling

```typescript
// Handle API errors consistently
import { AxiosError } from 'axios';

interface ApiError {
  detail: string;
  status_code?: number;
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data as ApiError | undefined;
    return data?.detail || error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
}

// Usage in components
function PeopleList() {
  const { data, error, isLoading } = usePeople();

  if (error) {
    return (
      <Alert variant="error">
        {getErrorMessage(error)}
      </Alert>
    );
  }

  // ...
}
```

---

## CSS/Styling Conventions

### TailwindCSS Usage

Use Tailwind utility classes as the primary styling approach:

```tsx
// Good - Tailwind utilities
<button className="rounded-md bg-blue-500 px-4 py-2 text-white hover:bg-blue-600">
  Submit
</button>

// Avoid - Inline styles
<button style={{ backgroundColor: 'blue', padding: '8px 16px' }}>
  Submit
</button>
```

### Class Organization

Order Tailwind classes consistently:

1. Layout (display, position)
2. Box model (width, padding, margin)
3. Typography
4. Visual (colors, borders)
5. Interactive (hover, focus)

```tsx
<div className="
  flex items-center justify-between
  w-full p-4 mb-2
  text-sm font-medium
  bg-white border rounded-lg shadow-sm
  hover:bg-gray-50 focus:ring-2
">
```

### Component Variants

Use a utility function for conditional classes:

```typescript
// lib/utils.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Usage
<button
  className={cn(
    'rounded-md px-4 py-2 font-medium',
    variant === 'primary' && 'bg-blue-500 text-white',
    variant === 'secondary' && 'bg-gray-200 text-gray-800',
    variant === 'danger' && 'bg-red-500 text-white',
    disabled && 'opacity-50 cursor-not-allowed'
  )}
>
```

### Responsive Design

Use mobile-first approach:

```tsx
<div className="
  grid grid-cols-1 gap-4
  sm:grid-cols-2
  lg:grid-cols-3
  xl:grid-cols-4
">
```

---

## Git Conventions

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation |
| `style` | Formatting (no code change) |
| `refactor` | Code restructuring |
| `test` | Adding/updating tests |
| `chore` | Maintenance tasks |
| `perf` | Performance improvements |
| `ci` | CI/CD changes |

**Examples:**

```bash
feat(scheduling): add support for holiday blocks
fix(auth): resolve token refresh race condition
docs(api): update endpoint documentation
test(compliance): add 80-hour rule validation tests
refactor(models): extract common validation logic
chore(deps): update FastAPI to 0.110.0
perf(query): optimize people list query
```

### Branch Names

```
<type>/<description>

feature/add-export-pdf
bugfix/fix-assignment-overlap
docs/update-api-reference
refactor/simplify-validation
```

---

## Documentation Standards

### Code Comments

```python
# Use comments to explain "why", not "what"

# Good - explains reasoning
# Skip weekends as they use a different scheduling algorithm
if day.weekday() >= 5:
    continue

# Bad - just restates the code
# If day is weekend, continue
if day.weekday() >= 5:
    continue
```

### TODO Comments

```python
# TODO: Implement caching for better performance
# TODO(#123): Fix race condition in concurrent updates
# FIXME: This calculation is incorrect for leap years
```

### API Documentation

FastAPI auto-generates docs from:
- Function docstrings
- Pydantic schema descriptions
- Route decorators

```python
@router.post(
    "/generate",
    response_model=ScheduleResponse,
    summary="Generate schedule",
    description="Generate a new schedule for the specified date range.",
    responses={
        200: {"description": "Schedule generated successfully"},
        400: {"description": "Invalid date range"},
        422: {"description": "Cannot generate schedule"},
    },
)
async def generate_schedule(
    request: ScheduleRequest,
    db: Session = Depends(get_db),
) -> ScheduleResponse:
    """Generate a schedule for the specified date range.

    - **start_date**: Beginning of the scheduling period
    - **end_date**: End of the scheduling period
    - **algorithm**: Scheduling algorithm (greedy, min_conflicts, cp_sat)
    """
    ...
```

---

## Code Organization

### Backend Structure

```
app/
├── api/routes/           # One file per resource
│   ├── __init__.py       # Router aggregation
│   ├── people.py
│   ├── schedule.py
│   └── ...
├── models/               # One file per model
│   ├── __init__.py       # Export all models
│   ├── person.py
│   └── ...
├── schemas/              # One file per resource
│   ├── __init__.py
│   ├── person.py
│   └── ...
├── scheduling/           # Scheduling logic
│   ├── engine.py
│   ├── validator.py
│   └── constraints.py
└── services/             # Business logic
    └── emergency_coverage.py
```

### Frontend Structure

```
src/
├── app/                  # Pages (Next.js App Router)
│   ├── layout.tsx
│   ├── page.tsx
│   └── [feature]/
│       └── page.tsx
├── components/           # Reusable components
│   ├── ui/               # Base UI components
│   ├── forms/            # Form components
│   └── [feature]/        # Feature-specific components
├── lib/                  # Utilities and hooks
│   ├── api.ts
│   ├── hooks.ts
│   └── utils.ts
└── types/                # TypeScript definitions
    └── index.ts
```

### Import Order

**Python:**
```python
# 1. Standard library
from datetime import date
from typing import Optional

# 2. Third-party
from fastapi import APIRouter
from pydantic import BaseModel

# 3. Local
from app.models import Person
```

**TypeScript:**
```typescript
// 1. React
import { useState, useEffect } from 'react';

// 2. Third-party
import { useQuery } from '@tanstack/react-query';

// 3. Local (absolute paths)
import { usePeople } from '@/lib/hooks';
import { Button } from '@/components/ui/Button';

// 4. Relative imports
import { PersonCard } from './PersonCard';
```

---

## Linting Configuration

### Backend (`pyproject.toml`)

```toml
[tool.black]
line-length = 88
target-version = ["py311"]

[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "ARG", "SIM"]
ignore = ["E501", "B008"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
disallow_untyped_defs = true
```

### Frontend (`.eslintrc.js`)

```javascript
module.exports = {
  extends: ['next/core-web-vitals', 'prettier'],
  rules: {
    'react/prop-types': 'off',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'prefer-const': 'error',
    'no-console': ['warn', { allow: ['warn', 'error'] }],
  },
};
```

---

*Last Updated: December 2024*
