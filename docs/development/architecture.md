***REMOVED*** Code Architecture Overview

This document provides a detailed overview of the Residency Scheduler codebase architecture, design patterns, and component interactions.

***REMOVED******REMOVED*** Table of Contents

1. [System Architecture](***REMOVED***system-architecture)
2. [Backend Architecture](***REMOVED***backend-architecture)
3. [Frontend Architecture](***REMOVED***frontend-architecture)
4. [Database Design](***REMOVED***database-design)
5. [Scheduling Engine](***REMOVED***scheduling-engine)
6. [Authentication System](***REMOVED***authentication-system)
7. [Design Patterns](***REMOVED***design-patterns)
8. [Data Flow](***REMOVED***data-flow)

---

***REMOVED******REMOVED*** System Architecture

***REMOVED******REMOVED******REMOVED*** High-Level Overview

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

***REMOVED******REMOVED******REMOVED*** Design Principles

1. **Separation of Concerns**: Clear boundaries between presentation, business logic, and data access
2. **ACGME Compliance**: Built-in validation for medical residency regulations
3. **RESTful API Design**: Standard HTTP methods and status codes
4. **Type Safety**: TypeScript frontend, Pydantic backend schemas
5. **Test-Driven Development**: Comprehensive test coverage requirements

---

***REMOVED******REMOVED*** Backend Architecture

***REMOVED******REMOVED******REMOVED*** Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     ***REMOVED*** Application entry point
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/                 ***REMOVED*** API endpoint handlers
│   │       ├── __init__.py         ***REMOVED*** Router aggregation
│   │       ├── auth.py             ***REMOVED*** Authentication endpoints
│   │       ├── people.py           ***REMOVED*** People CRUD
│   │       ├── blocks.py           ***REMOVED*** Block CRUD
│   │       ├── assignments.py      ***REMOVED*** Assignment CRUD
│   │       ├── absences.py         ***REMOVED*** Absence CRUD
│   │       ├── rotation_templates.py  ***REMOVED*** Template CRUD
│   │       ├── schedule.py         ***REMOVED*** Schedule generation/validation
│   │       ├── settings.py         ***REMOVED*** Application settings
│   │       └── export.py           ***REMOVED*** Data export (Excel)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               ***REMOVED*** Application configuration
│   │   └── security.py             ***REMOVED*** JWT and password handling
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                 ***REMOVED*** SQLAlchemy declarative base
│   │   ├── session.py              ***REMOVED*** Database session management
│   │   └── types.py                ***REMOVED*** Custom database types
│   ├── models/                     ***REMOVED*** SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── person.py
│   │   ├── block.py
│   │   ├── assignment.py
│   │   ├── absence.py
│   │   ├── rotation_template.py
│   │   ├── user.py
│   │   ├── call_assignment.py
│   │   └── schedule_run.py
│   ├── schemas/                    ***REMOVED*** Pydantic validation schemas
│   │   ├── __init__.py
│   │   ├── person.py
│   │   ├── block.py
│   │   ├── assignment.py
│   │   ├── absence.py
│   │   ├── rotation_template.py
│   │   ├── schedule.py
│   │   ├── auth.py
│   │   └── settings.py
│   ├── scheduling/                 ***REMOVED*** Scheduling engine
│   │   ├── __init__.py
│   │   ├── engine.py               ***REMOVED*** Main scheduling algorithm
│   │   ├── validator.py            ***REMOVED*** ACGME compliance validation
│   │   ├── constraints.py          ***REMOVED*** Constraint definitions
│   │   └── solvers.py              ***REMOVED*** Algorithm implementations
│   └── services/                   ***REMOVED*** Business logic services
│       ├── __init__.py
│       ├── emergency_coverage.py
│       └── xlsx_export.py
├── alembic/                        ***REMOVED*** Database migrations
│   ├── env.py
│   ├── versions/                   ***REMOVED*** Migration files
│   └── alembic.ini
├── tests/                          ***REMOVED*** Test suite
│   ├── __init__.py
│   ├── conftest.py                 ***REMOVED*** Test fixtures
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

***REMOVED******REMOVED******REMOVED*** Layer Responsibilities

***REMOVED******REMOVED******REMOVED******REMOVED*** Routes Layer (`app/api/routes/`)

Handles HTTP request/response:
- Input validation via Pydantic schemas
- Authentication/authorization checks
- Response formatting
- Error handling

```python
***REMOVED*** Example: app/api/routes/people.py
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

***REMOVED******REMOVED******REMOVED******REMOVED*** Models Layer (`app/models/`)

Database table definitions:
- SQLAlchemy ORM mappings
- Relationship definitions
- Column constraints

```python
***REMOVED*** Example: app/models/person.py
class Person(Base):
    __tablename__ = "people"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    type = Column(Enum(PersonType), nullable=False)
    pgy_level = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)

    ***REMOVED*** Relationships
    assignments = relationship("Assignment", back_populates="person")
    absences = relationship("Absence", back_populates="person")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Schemas Layer (`app/schemas/`)

Request/response validation:
- Pydantic data models
- Type coercion
- Validation rules

```python
***REMOVED*** Example: app/schemas/person.py
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

***REMOVED******REMOVED******REMOVED******REMOVED*** Scheduling Layer (`app/scheduling/`)

Core scheduling logic:
- Schedule generation algorithms
- ACGME compliance validation
- Constraint satisfaction

```python
***REMOVED*** Example: app/scheduling/engine.py
class SchedulingEngine:
    def generate_schedule(
        self,
        start_date: date,
        end_date: date,
        algorithm: str = "greedy"
    ) -> ScheduleResult:
        ***REMOVED*** Load constraints
        constraints = self._load_constraints()

        ***REMOVED*** Get available people and blocks
        people = self._get_available_people(start_date, end_date)
        blocks = self._get_blocks(start_date, end_date)

        ***REMOVED*** Run selected algorithm
        if algorithm == "cp_sat":
            assignments = self._solve_cp_sat(people, blocks, constraints)
        else:
            assignments = self._solve_greedy(people, blocks, constraints)

        ***REMOVED*** Validate result
        violations = self.validator.validate(assignments)

        return ScheduleResult(assignments=assignments, violations=violations)
```

---

***REMOVED******REMOVED*** Frontend Architecture

***REMOVED******REMOVED******REMOVED*** Directory Structure

```
frontend/
├── src/
│   ├── app/                        ***REMOVED*** Next.js App Router
│   │   ├── layout.tsx              ***REMOVED*** Root layout
│   │   ├── page.tsx                ***REMOVED*** Home/dashboard page
│   │   ├── login/
│   │   │   └── page.tsx            ***REMOVED*** Login page
│   │   ├── schedule/
│   │   │   ├── page.tsx            ***REMOVED*** Schedule overview
│   │   │   └── [personId]/
│   │   │       └── page.tsx        ***REMOVED*** Individual schedule view
│   │   ├── people/
│   │   │   └── page.tsx            ***REMOVED*** People management
│   │   ├── absences/
│   │   │   └── page.tsx            ***REMOVED*** Absence management
│   │   ├── compliance/
│   │   │   └── page.tsx            ***REMOVED*** ACGME compliance view
│   │   ├── templates/
│   │   │   └── page.tsx            ***REMOVED*** Rotation templates
│   │   ├── settings/
│   │   │   └── page.tsx            ***REMOVED*** Application settings
│   │   └── help/
│   │       └── page.tsx            ***REMOVED*** Help/documentation
│   ├── components/                 ***REMOVED*** React components
│   │   ├── ui/                     ***REMOVED*** Base UI components
│   │   ├── forms/                  ***REMOVED*** Form components
│   │   ├── schedule/               ***REMOVED*** Schedule-specific components
│   │   ├── dashboard/              ***REMOVED*** Dashboard widgets
│   │   └── skeletons/              ***REMOVED*** Loading skeletons
│   ├── contexts/                   ***REMOVED*** React Context providers
│   │   └── AuthContext.tsx
│   ├── lib/
│   │   ├── api.ts                  ***REMOVED*** API client (Axios)
│   │   └── hooks.ts                ***REMOVED*** React Query hooks
│   ├── types/
│   │   └── index.ts                ***REMOVED*** TypeScript type definitions
│   └── mocks/                      ***REMOVED*** MSW API mocks for testing
├── __tests__/                      ***REMOVED*** Jest unit tests
│   ├── hooks/
│   ├── components/
│   └── utils/
├── e2e/                            ***REMOVED*** Playwright E2E tests
├── public/                         ***REMOVED*** Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── Dockerfile
```

***REMOVED******REMOVED******REMOVED*** Component Architecture

***REMOVED******REMOVED******REMOVED******REMOVED*** Page Components

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

***REMOVED******REMOVED******REMOVED******REMOVED*** Reusable Components

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

***REMOVED******REMOVED******REMOVED*** Data Layer

***REMOVED******REMOVED******REMOVED******REMOVED*** API Client

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

***REMOVED******REMOVED******REMOVED******REMOVED*** React Query Hooks

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

***REMOVED******REMOVED*** Database Design

***REMOVED******REMOVED******REMOVED*** Entity Relationship Diagram

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

***REMOVED******REMOVED******REMOVED*** Key Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `people` | Residents and faculty | name, email, type, pgy_level |
| `blocks` | Schedulable time slots | date, shift_type, location |
| `assignments` | Links people to blocks | person_id, block_id, role |
| `absences` | Leave/deployment tracking | person_id, dates, type |
| `rotation_templates` | Reusable activity patterns | name, capacity, requirements |
| `users` | Authentication accounts | email, password_hash, role |

---

***REMOVED******REMOVED*** Scheduling Engine

***REMOVED******REMOVED******REMOVED*** Algorithm Overview

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

***REMOVED******REMOVED******REMOVED*** ACGME Constraints

| Rule | Limit | Measurement |
|------|-------|-------------|
| Weekly Hours | ≤ 80 hours | 4-week rolling average |
| Continuous Duty | ≤ 24 hours | Per shift |
| Day Off | ≥ 1 day | Per 7 days |
| Night Float | ≤ 6 consecutive | Per rotation |
| Supervision | Required | PGY-1 procedures |

***REMOVED******REMOVED******REMOVED*** Solver Implementations

1. **Greedy Solver**: Fast, good for initial assignments
2. **Min-Conflicts Solver**: Local search for optimization
3. **CP-SAT Solver**: Constraint programming for optimal solutions

---

***REMOVED******REMOVED*** Authentication System

***REMOVED******REMOVED******REMOVED*** JWT Flow

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

***REMOVED******REMOVED******REMOVED*** Token Structure

```json
{
  "sub": "user@example.com",
  "exp": 1703980800,
  "iat": 1703894400,
  "type": "access",
  "role": "admin"
}
```

***REMOVED******REMOVED******REMOVED*** Security Measures

- **Password Hashing**: bcrypt with automatic salt
- **Token Expiration**: 24-hour access tokens
- **CORS**: Restricted to configured origins
- **Input Validation**: Pydantic schemas
- **SQL Injection Prevention**: SQLAlchemy ORM
- **XSS Prevention**: React automatic escaping

---

***REMOVED******REMOVED*** Design Patterns

***REMOVED******REMOVED******REMOVED*** Backend Patterns

| Pattern | Usage | Example |
|---------|-------|---------|
| Dependency Injection | Database sessions, auth | `Depends(get_db)` |
| Repository Pattern | Data access abstraction | Models layer |
| Factory Pattern | Schema validation | Pydantic models |
| Strategy Pattern | Scheduling algorithms | Solver selection |

***REMOVED******REMOVED******REMOVED*** Frontend Patterns

| Pattern | Usage | Example |
|---------|-------|---------|
| Compound Components | Complex UI structures | Form groups |
| Custom Hooks | Reusable logic | `usePeople()` |
| Context | Global state | `AuthContext` |
| Container/Presenter | Data/UI separation | Pages/Components |

---

***REMOVED******REMOVED*** Data Flow

***REMOVED******REMOVED******REMOVED*** Create Person Flow

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

***REMOVED******REMOVED******REMOVED*** Schedule Generation Flow

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

***REMOVED******REMOVED*** Further Reading

- [Environment Setup](./environment-setup.md) - Development environment configuration
- [Workflow](./workflow.md) - Development process and branching
- [Testing](./testing.md) - Testing strategies and tools
- [Code Style](./code-style.md) - Coding conventions

---

*Last Updated: December 2024*
