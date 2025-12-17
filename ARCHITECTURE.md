# Architecture Overview

This document describes the layered architecture of the Residency Scheduler application.

## Backend Architecture (FastAPI + SQLAlchemy)

The backend follows a layered architecture pattern that separates concerns and reduces code duplication:

```
HTTP Request
     │
     ▼
┌─────────────┐
│   Router    │  ← URL path mapping, HTTP method binding
└─────────────┘
     │
     ▼
┌─────────────┐
│ Controller  │  ← Request validation, response formatting, HTTP status codes
└─────────────┘
     │
     ▼
┌─────────────┐
│   Service   │  ← Business logic, orchestration, domain rules
└─────────────┘
     │
     ▼
┌─────────────┐
│ Repository  │  ← Database CRUD operations, queries
└─────────────┘
     │
     ▼
┌─────────────┐
│    Model    │  ← Database schema definitions (SQLAlchemy ORM)
└─────────────┘
```

### Layer Responsibilities

#### Models (`app/models/`)
Define database table schemas using SQLAlchemy ORM.

```python
# app/models/person.py
class Person(Base):
    __tablename__ = "people"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    # ...
```

#### Repositories (`app/repositories/`)
Pure database operations. No business logic - just CRUD and queries.

```python
# app/repositories/person_repository.py
class PersonRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, person_id: UUID) -> Person | None:
        return self.db.query(Person).filter(Person.id == person_id).first()

    def get_active_residents(self) -> list[Person]:
        return self.db.query(Person).filter(
            Person.role == "resident",
            Person.is_active == True
        ).all()
```

#### Services (`app/services/`)
Business logic layer. Uses repositories as building blocks to implement domain rules.

```python
# app/services/schedule_service.py
class ScheduleService:
    def __init__(self, db: Session):
        self.person_repo = PersonRepository(db)
        self.assignment_repo = AssignmentRepository(db)

    def generate_schedule(self, start_date: date, end_date: date) -> ScheduleRun:
        residents = self.person_repo.get_active_residents()
        # Apply business rules, constraints, optimization...
        assignments = self._optimize_assignments(residents, start_date, end_date)
        return self.assignment_repo.bulk_create(assignments)
```

#### Controllers (`app/controllers/`)
Handle HTTP concerns: request validation, response building, status codes.

```python
# app/controllers/schedule_controller.py
class ScheduleController:
    def __init__(self, db: Session):
        self.service = ScheduleService(db)

    def generate(self, request: GenerateScheduleRequest) -> GenerateScheduleResponse:
        try:
            schedule = self.service.generate_schedule(request.start_date, request.end_date)
            return GenerateScheduleResponse(
                schedule_id=schedule.id,
                assignments_created=len(schedule.assignments)
            )
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))
```

#### Routers (`app/api/routes/`)
Map URL paths to controller methods. Minimal logic here.

```python
# app/api/routes/schedule.py
router = APIRouter(prefix="/schedules", tags=["schedules"])

@router.post("/generate", response_model=GenerateScheduleResponse)
def generate_schedule(
    request: GenerateScheduleRequest,
    db: Session = Depends(get_db)
):
    controller = ScheduleController(db)
    return controller.generate(request)
```

#### Schemas (`app/schemas/`)
Pydantic models for request/response validation. Separate from database models.

```python
# app/schemas/schedule.py
class GenerateScheduleRequest(BaseModel):
    start_date: date
    end_date: date

class GenerateScheduleResponse(BaseModel):
    schedule_id: UUID
    assignments_created: int
```

#### Middleware (`app/middleware/`)
Functions applied to every request. Good for cross-cutting concerns.

```python
# app/middleware/auth.py
async def verify_token(request: Request, call_next):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401)
    # Validate token...
    response = await call_next(request)
    return response
```

### Domain-Specific Modules

Beyond the standard layers, the codebase has domain modules:

| Module | Purpose |
|--------|---------|
| `app/scheduling/` | OR-Tools constraint solver for schedule optimization |
| `app/analytics/` | Reporting engines (coverage, fairness, workload) |
| `app/notifications/` | Alert delivery system (email, in-app) |
| `app/maintenance/` | Backup, restore, and data retention |
| `app/validators/` | ACGME compliance rule validation |
| `app/resilience/` | Circuit breakers, rate limiting, retry logic |

### Infrastructure

| Directory | Purpose |
|-----------|---------|
| `app/core/` | Configuration, settings, shared dependencies |
| `app/db/` | Database session factory, connection pooling |
| `app/cli/` | Command-line tools for admin tasks |
| `alembic/` | Database migrations |

---

## Frontend Architecture (Next.js + React)

```
frontend/src/
├── app/              ← Next.js App Router (pages)
├── components/       ← Reusable UI components
├── hooks/            ← Custom React hooks
├── lib/              ← Utilities, API client
├── types/            ← TypeScript type definitions
└── mocks/            ← MSW handlers for testing
```

### Data Flow

```
User Interaction
       │
       ▼
┌──────────────┐
│   Page/View  │  ← app/[route]/page.tsx
└──────────────┘
       │
       ▼
┌──────────────┐
│    Hooks     │  ← useSchedule(), usePeople() - data fetching
└──────────────┘
       │
       ▼
┌──────────────┐
│  API Client  │  ← lib/api.ts - axios wrapper
└──────────────┘
       │
       ▼
   Backend API
```

### Key Patterns

- **React Query** for server state management and caching
- **Tailwind CSS** for styling
- **MSW** for API mocking in tests
- **TypeScript** throughout for type safety

---

## Request Lifecycle Example

A complete example: Creating a new absence record.

```
1. User submits absence form in frontend

2. Frontend: POST /api/absences with JSON body
   → hooks/useAbsences.ts calls api.post('/absences', data)

3. Backend Router: app/api/routes/absences.py
   @router.post("/")
   def create_absence(request: CreateAbsenceRequest, db: Session)

4. Backend Controller: app/controllers/absence_controller.py
   - Validates request fields
   - Calls service layer
   - Returns 201 with created resource

5. Backend Service: app/services/absence_service.py
   - Checks for conflicts with existing schedule
   - Applies business rules (blocking vs partial)
   - Calls repository to persist

6. Backend Repository: app/repositories/absence_repository.py
   - Executes INSERT query
   - Returns created Absence model

7. Response flows back up the stack
   → Controller formats response
   → Router returns HTTP 201
   → Frontend receives response
   → React Query invalidates cache
   → UI updates
```

---

## Database Schema

Core entities and relationships:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Person    │────<│ Assignment  │>────│    Block    │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                       │
       │            ┌─────────────┐            │
       └───────────<│   Absence   │            │
                    └─────────────┘            │
                                               │
┌─────────────┐     ┌─────────────┐            │
│ScheduleRun  │────<│ CallAssign. │>───────────┘
└─────────────┘     └─────────────┘
```

See `app/models/` for complete schema definitions.

---

## Adding New Features

1. **New entity**: Model → Repository → Service → Controller → Router → Schema
2. **New business rule**: Service layer (keep repositories pure)
3. **New API endpoint**: Router → Controller (reuse existing services)
4. **New validation**: Validators module or Pydantic schema
5. **New background job**: Celery task in `app/tasks/`

---

## Testing Strategy

| Layer | Test Type | Location |
|-------|-----------|----------|
| Models | Unit tests | `tests/models/` |
| Repositories | Integration tests (needs DB) | `tests/repositories/` |
| Services | Unit tests (mock repos) | `tests/services/` |
| Controllers | Unit tests (mock services) | `tests/controllers/` |
| Routes | Integration tests (TestClient) | `tests/api/` |
| Frontend | Jest + RTL | `frontend/__tests__/` |
| E2E | Playwright | `frontend/e2e/` |
