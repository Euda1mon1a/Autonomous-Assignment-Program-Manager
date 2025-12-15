# Code Architecture Overview

This document provides a detailed overview of the Residency Scheduler codebase architecture, design patterns, and component interactions.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Backend Architecture](#backend-architecture)
3. [Frontend Architecture](#frontend-architecture)
4. [Database Design](#database-design)
5. [Scheduling Engine](#scheduling-engine)
6. [Authentication System](#authentication-system)
7. [Design Patterns](#design-patterns)
8. [Data Flow](#data-flow)

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Next.js Frontend                       │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐     │    │
│  │  │ React Query  │ │  Components  │ │ React Hooks  │     │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘     │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   FastAPI Backend                        │    │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────────┐       │    │
│  │  │   Routes   │ │  Services  │ │   Scheduling   │       │    │
│  │  │   (REST)   │ │ (Business) │ │     Engine     │       │    │
│  │  └────────────┘ └────────────┘ └────────────────┘       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ SQLAlchemy ORM
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                 PostgreSQL Database                      │    │
│  │  ┌────────┐ ┌────────┐ ┌─────────────┐ ┌─────────────┐  │    │
│  │  │ People │ │ Blocks │ │ Assignments │ │  Templates  │  │    │
│  │  └────────┘ └────────┘ └─────────────┘ └─────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**: Clear boundaries between presentation, business logic, and data access
2. **ACGME Compliance**: Built-in validation for medical residency regulations
3. **RESTful API Design**: Standard HTTP methods and status codes
4. **Type Safety**: TypeScript frontend, Pydantic backend schemas
5. **Test-Driven Development**: Comprehensive test coverage requirements

---

## Backend Architecture

### Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # Application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/                 # API endpoint handlers
│   │       ├── __init__.py         # Router aggregation
│   │       ├── auth.py             # Authentication endpoints
│   │       ├── people.py           # People CRUD
│   │       ├── blocks.py           # Block CRUD
│   │       ├── assignments.py      # Assignment CRUD
│   │       ├── absences.py         # Absence CRUD
│   │       ├── rotation_templates.py  # Template CRUD
│   │       ├── schedule.py         # Schedule generation/validation
│   │       ├── settings.py         # Application settings
│   │       └── export.py           # Data export (Excel)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Application configuration
│   │   └── security.py             # JWT and password handling
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                 # SQLAlchemy declarative base
│   │   ├── session.py              # Database session management
│   │   └── types.py                # Custom database types
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── person.py
│   │   ├── block.py
│   │   ├── assignment.py
│   │   ├── absence.py
│   │   ├── rotation_template.py
│   │   ├── user.py
│   │   ├── call_assignment.py
│   │   └── schedule_run.py
│   ├── schemas/                    # Pydantic validation schemas
│   │   ├── __init__.py
│   │   ├── person.py
│   │   ├── block.py
│   │   ├── assignment.py
│   │   ├── absence.py
│   │   ├── rotation_template.py
│   │   ├── schedule.py
│   │   ├── auth.py
│   │   └── settings.py
│   ├── scheduling/                 # Scheduling engine
│   │   ├── __init__.py
│   │   ├── engine.py               # Main scheduling algorithm
│   │   ├── validator.py            # ACGME compliance validation
│   │   ├── constraints.py          # Constraint definitions
│   │   └── solvers.py              # Algorithm implementations
│   └── services/                   # Business logic services
│       ├── __init__.py
│       ├── emergency_coverage.py
│       └── xlsx_export.py
├── alembic/                        # Database migrations
│   ├── env.py
│   ├── versions/                   # Migration files
│   └── alembic.ini
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Test fixtures
│   ├── test_api.py
│   ├── test_people_api.py
│   ├── test_schedule_api.py
│   ├── test_assignments_api.py
│   ├── test_scheduling_engine.py
│   ├── test_solvers.py
│   └── test_constraints.py
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

### Layer Responsibilities

#### Routes Layer (`app/api/routes/`)

Handles HTTP request/response:
- Input validation via Pydantic schemas
- Authentication/authorization checks
- Response formatting
- Error handling

```python
# Example: app/api/routes/people.py
@router.post("/", response_model=PersonResponse, status_code=201)
async def create_person(
    person: PersonCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new person (resident or faculty)."""
    db_person = Person(**person.model_dump())
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person
```

#### Models Layer (`app/models/`)

Database table definitions:
- SQLAlchemy ORM mappings
- Relationship definitions
- Column constraints

```python
# Example: app/models/person.py
class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    type = Column(Enum(PersonType), nullable=False)
    pgy_level = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    assignments = relationship("Assignment", back_populates="person")
    absences = relationship("Absence", back_populates="person")
```

#### Schemas Layer (`app/schemas/`)

Request/response validation:
- Pydantic data models
- Type coercion
- Validation rules

```python
# Example: app/schemas/person.py
class PersonCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    type: PersonType
    pgy_level: Optional[int] = Field(None, ge=1, le=7)

    @model_validator(mode='after')
    def validate_pgy_for_resident(self):
        if self.type == PersonType.RESIDENT and self.pgy_level is None:
            raise ValueError("PGY level required for residents")
        return self
```

#### Scheduling Layer (`app/scheduling/`)

Core scheduling logic:
- Schedule generation algorithms
- ACGME compliance validation
- Constraint satisfaction

```python
# Example: app/scheduling/engine.py
class SchedulingEngine:
    def generate_schedule(
        self,
        start_date: date,
        end_date: date,
        algorithm: str = "greedy"
    ) -> ScheduleResult:
        # Load constraints
        constraints = self._load_constraints()

        # Get available people and blocks
        people = self._get_available_people(start_date, end_date)
        blocks = self._get_blocks(start_date, end_date)

        # Run selected algorithm
        if algorithm == "cp_sat":
            assignments = self._solve_cp_sat(people, blocks, constraints)
        else:
            assignments = self._solve_greedy(people, blocks, constraints)

        # Validate result
        violations = self.validator.validate(assignments)

        return ScheduleResult(assignments=assignments, violations=violations)
```

---

## Frontend Architecture

### Directory Structure

```
frontend/
├── src/
│   ├── app/                        # Next.js App Router
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # Home/dashboard page
│   │   ├── login/
│   │   │   └── page.tsx            # Login page
│   │   ├── schedule/
│   │   │   ├── page.tsx            # Schedule overview
│   │   │   └── [personId]/
│   │   │       └── page.tsx        # Individual schedule view
│   │   ├── people/
│   │   │   └── page.tsx            # People management
│   │   ├── absences/
│   │   │   └── page.tsx            # Absence management
│   │   ├── compliance/
│   │   │   └── page.tsx            # ACGME compliance view
│   │   ├── templates/
│   │   │   └── page.tsx            # Rotation templates
│   │   ├── settings/
│   │   │   └── page.tsx            # Application settings
│   │   └── help/
│   │       └── page.tsx            # Help/documentation
│   ├── components/                 # React components
│   │   ├── ui/                     # Base UI components
│   │   ├── forms/                  # Form components
│   │   ├── schedule/               # Schedule-specific components
│   │   ├── dashboard/              # Dashboard widgets
│   │   └── skeletons/              # Loading skeletons
│   ├── contexts/                   # React Context providers
│   │   └── AuthContext.tsx
│   ├── lib/
│   │   ├── api.ts                  # API client (Axios)
│   │   └── hooks.ts                # React Query hooks
│   ├── types/
│   │   └── index.ts                # TypeScript type definitions
│   └── mocks/                      # MSW API mocks for testing
├── __tests__/                      # Jest unit tests
│   ├── hooks/
│   ├── components/
│   └── utils/
├── e2e/                            # Playwright E2E tests
├── public/                         # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── Dockerfile
```

### Component Architecture

#### Page Components

Located in `src/app/`, these are Next.js App Router pages:

```typescript
// src/app/people/page.tsx
export default function PeoplePage() {
  const { data: people, isLoading, error } = usePeople();

  if (isLoading) return <PeopleSkeleton />;
  if (error) return <ErrorDisplay error={error} />;

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">People</h1>
      <PeopleTable people={people?.items ?? []} />
    </div>
  );
}
```

#### Reusable Components

Located in `src/components/`:

```typescript
// src/components/ui/Button.tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
}

export function Button({
  variant = 'primary',
  size = 'md',
  children,
  ...props
}: ButtonProps) {
  const classes = cn(
    'rounded font-medium transition-colors',
    variantClasses[variant],
    sizeClasses[size]
  );

  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
}
```

### Data Layer

#### API Client

The API client (`src/lib/api.ts`) provides typed HTTP methods:

```typescript
// src/lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor for auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function get<T>(url: string): Promise<T> {
  const { data } = await api.get<T>(url);
  return data;
}

export async function post<T>(url: string, body: unknown): Promise<T> {
  const { data } = await api.post<T>(url, body);
  return data;
}
```

#### React Query Hooks

Custom hooks for data fetching (`src/lib/hooks.ts`):

```typescript
// src/lib/hooks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export function usePeople(params?: PeopleParams) {
  return useQuery({
    queryKey: ['people', params],
    queryFn: () => get<PaginatedResponse<Person>>('/api/people', { params }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCreatePerson() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: PersonCreate) => post<Person>('/api/people', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['people'] });
    },
  });
}
```

---

## Database Design

### Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│     Person      │       │     Block       │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ name            │       │ date            │
│ email           │       │ shift_type      │
│ type            │       │ location        │
│ pgy_level       │       │ required_staff  │
│ is_active       │       │ is_holiday      │
└────────┬────────┘       └────────┬────────┘
         │                         │
         │ 1                       │ 1
         │                         │
         ▼ *                       ▼ *
┌─────────────────┐       ┌─────────────────┐
│   Assignment    │       │    Absence      │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ person_id (FK)  │───────│ person_id (FK)  │
│ block_id (FK)   │       │ start_date      │
│ rotation_id(FK) │       │ end_date        │
│ role            │       │ absence_type    │
│ is_chief        │       │ deployment_info │
└─────────────────┘       └─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│RotationTemplate │       │      User       │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ name            │       │ email           │
│ activity_type   │       │ hashed_password │
│ duration_weeks  │       │ role            │
│ min_residents   │       │ is_active       │
│ max_residents   │       │ created_at      │
│ allows_pgy1     │       └─────────────────┘
│ requires_faculty│
└─────────────────┘
```

### Key Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `people` | Residents and faculty | name, email, type, pgy_level |
| `blocks` | Schedulable time slots | date, shift_type, location |
| `assignments` | Links people to blocks | person_id, block_id, role |
| `absences` | Leave/deployment tracking | person_id, dates, type |
| `rotation_templates` | Reusable activity patterns | name, capacity, requirements |
| `users` | Authentication accounts | email, password_hash, role |

---

## Scheduling Engine

### Algorithm Overview

The scheduling engine uses a greedy algorithm with constraint satisfaction:

```
┌───────────────────┐
│ Load Constraints  │
│ - ACGME rules     │
│ - Absences        │
│ - Preferences     │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Sort Blocks by    │
│ Priority/Date     │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ For Each Block:   │
│ Find Best Match   │
└────────┬──────────┘
         │
         ▼
┌───────────────────────────────────────┐
│ Candidate Passes    NO→ Try Next     │
│ All Constraints?       Candidate     │
└────────┬──────────────────────────────┘
         │ YES
         ▼
┌───────────────────┐
│ Assign & Update   │
│ Running Totals    │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ Validate Final    │
│ Schedule          │
└───────────────────┘
```

### ACGME Constraints

| Rule | Limit | Measurement |
|------|-------|-------------|
| Weekly Hours | ≤ 80 hours | 4-week rolling average |
| Continuous Duty | ≤ 24 hours | Per shift |
| Day Off | ≥ 1 day | Per 7 days |
| Night Float | ≤ 6 consecutive | Per rotation |
| Supervision | Required | PGY-1 procedures |

### Solver Implementations

1. **Greedy Solver**: Fast, good for initial assignments
2. **Min-Conflicts Solver**: Local search for optimization
3. **CP-SAT Solver**: Constraint programming for optimal solutions

---

## Authentication System

### JWT Flow

```
┌──────────┐    1. Login     ┌──────────┐    2. Verify    ┌──────────┐
│  Client  │ ──────────────▶ │   API    │ ──────────────▶ │    DB    │
└──────────┘   credentials   └──────────┘   password      └──────────┘
     ▲                            │
     │                            │ 3. Generate JWT
     │                            ▼
     │                       ┌──────────┐
     └───────────────────────│  Return  │
         4. Store token      │   JWT    │
                             └──────────┘
```

### Token Structure

```json
{
  "sub": "user@example.com",
  "exp": 1703980800,
  "iat": 1703894400,
  "type": "access",
  "role": "admin"
}
```

### Security Measures

- **Password Hashing**: bcrypt with automatic salt
- **Token Expiration**: 24-hour access tokens
- **CORS**: Restricted to configured origins
- **Input Validation**: Pydantic schemas
- **SQL Injection Prevention**: SQLAlchemy ORM
- **XSS Prevention**: React automatic escaping

---

## Design Patterns

### Backend Patterns

| Pattern | Usage | Example |
|---------|-------|---------|
| Dependency Injection | Database sessions, auth | `Depends(get_db)` |
| Repository Pattern | Data access abstraction | Models layer |
| Factory Pattern | Schema validation | Pydantic models |
| Strategy Pattern | Scheduling algorithms | Solver selection |

### Frontend Patterns

| Pattern | Usage | Example |
|---------|-------|---------|
| Compound Components | Complex UI structures | Form groups |
| Custom Hooks | Reusable logic | `usePeople()` |
| Context | Global state | `AuthContext` |
| Container/Presenter | Data/UI separation | Pages/Components |

---

## Data Flow

### Create Person Flow

```
┌─────────┐    1. POST /api/people     ┌─────────┐
│ Frontend│ ─────────────────────────▶ │  Route  │
│ Form    │    {name, email, type}     │ Handler │
└─────────┘                            └────┬────┘
                                            │
                                            │ 2. Validate
                                            ▼
                                       ┌─────────┐
                                       │ Pydantic│
                                       │ Schema  │
                                       └────┬────┘
                                            │
                                            │ 3. Create model
                                            ▼
                                       ┌─────────┐
                                       │SQLAlchemy│
                                       │  Model  │
                                       └────┬────┘
                                            │
                                            │ 4. Persist
                                            ▼
                                       ┌─────────┐
                                       │ Database│
                                       └────┬────┘
                                            │
                                            │ 5. Return
                                            ▼
┌─────────┐    6. Response JSON        ┌─────────┐
│ Frontend│ ◀───────────────────────── │  Route  │
│ Update  │    PersonResponse          │ Handler │
└─────────┘                            └─────────┘
```

### Schedule Generation Flow

```
┌─────────┐    1. POST /api/schedule/generate
│ Frontend│ ─────────────────────────────────▶ ┌───────────┐
└─────────┘    {start_date, end_date}          │   Route   │
                                               └─────┬─────┘
                                                     │
                                                     ▼
                                               ┌───────────┐
                                               │ Scheduling│
                                               │  Engine   │
                                               └─────┬─────┘
                                                     │
                         ┌───────────────────────────┼───────────────────────────┐
                         ▼                           ▼                           ▼
                   ┌───────────┐               ┌───────────┐               ┌───────────┐
                   │   Load    │               │   Load    │               │   Load    │
                   │  People   │               │  Blocks   │               │Constraints│
                   └─────┬─────┘               └─────┬─────┘               └─────┬─────┘
                         │                           │                           │
                         └───────────────────────────┼───────────────────────────┘
                                                     │
                                                     ▼
                                               ┌───────────┐
                                               │   Solver  │
                                               │ Algorithm │
                                               └─────┬─────┘
                                                     │
                                                     ▼
                                               ┌───────────┐
                                               │ ACGME     │
                                               │ Validator │
                                               └─────┬─────┘
                                                     │
                                                     ▼
┌─────────┐    6. ScheduleResult               ┌───────────┐
│ Frontend│ ◀────────────────────────────────  │  Return   │
└─────────┘    {assignments, violations}       │  Result   │
                                               └───────────┘
```

---

## Further Reading

- [Environment Setup](./environment-setup.md) - Development environment configuration
- [Workflow](./workflow.md) - Development process and branching
- [Testing](./testing.md) - Testing strategies and tools
- [Code Style](./code-style.md) - Coding conventions

---

*Last Updated: December 2024*
