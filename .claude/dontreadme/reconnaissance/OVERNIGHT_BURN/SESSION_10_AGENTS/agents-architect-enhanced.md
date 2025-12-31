# ARCHITECT Agent - Enhanced Specification
## Comprehensive Design Architecture, Patterns & Decision Frameworks

> **Last Updated:** 2025-12-30 (G2_RECON SEARCH_PARTY)
> **Scope:** Enhanced specification for ARCHITECT agent capabilities
> **Audience:** AI Agents, Faculty Technical Team

---

## Executive Summary

The ARCHITECT agent is the **strategic steward** of system design decisions. This enhanced specification documents:

1. **Design Philosophy & Core Principles** - The foundational thinking behind architecture decisions
2. **Design Patterns Catalog** - 15+ established patterns used throughout the codebase
3. **Decision Frameworks** - Structured approaches for evaluating architectural trade-offs
4. **Database Design Authority** - Complete data architecture governance
5. **API Design Standards** - Comprehensive API contract specifications
6. **Infrastructure & Scalability** - System capacity planning and resilience
7. **Cross-Cutting Concerns** - Security, compliance, observability, error handling
8. **Pattern Evolution & Maintenance** - How architectural decisions age and evolve

---

## Part 1: Design Philosophy & Core Principles

### 1.1 Layered Architecture Paradigm

The Residency Scheduler implements a **strict 5-layer architecture** that separates concerns and enables independent evolution:

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: HTTP Request Entry Points (FastAPI Routes)│
│  - URL parsing, parameter extraction                │
│  - Request/response serialization via Pydantic      │
│  - Middleware attachment (auth, logging)           │
└─────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  Layer 2: Controllers (Input/Output Handling)       │
│  - Request validation and transformation           │
│  - Response formatting and error wrapping          │
│  - Orchestration between multiple services        │
│  - Transaction boundary establishment             │
└─────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  Layer 3: Services (Business Logic)                 │
│  - Constraint validation                           │
│  - ACGME rule application                          │
│  - Scheduling optimization logic                   │
│  - External API calls (Celery, cache)             │
│  - Complex calculations and transformations       │
└─────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  Layer 4: Repositories (Data Access Abstraction)   │
│  - Query construction and execution                │
│  - Entity loading/persistence                      │
│  - Relationship management                        │
│  - Indexing and performance optimization         │
└─────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  Layer 5: Models (Domain Objects via SQLAlchemy)   │
│  - Table definitions with constraints             │
│  - Relationships and foreign keys                 │
│  - Computed properties and business logic        │
│  - Audit trail configuration                     │
└─────────────────────────────────────────────────────┘
```

**Layer Crossing Rules:**
- ✅ Routes → Controllers → Services → Repositories → Models (forward only)
- ❌ Services should NEVER query database directly (use Repository)
- ❌ Routes should NEVER contain business logic
- ❌ Models should NEVER import Services (breaks encapsulation)
- ❌ Controllers should NOT import other Controllers (encourage service reuse)

**Benefits of Layered Architecture:**
- **Testability**: Each layer can be unit-tested independently with mocks
- **Maintainability**: Changes to database don't ripple through business logic
- **Reusability**: Services can be used by multiple routes
- **Onboarding**: New developers understand the flow predictably

### 1.2 Core Design Principles (in priority order)

#### Principle 1: Security First (Non-Negotiable)

No architectural decision overrides security requirements:

1. **Authentication & Authorization**
   - JWT-based auth with httpOnly cookies (XSS-resistant)
   - 8-level RBAC (Admin, Coordinator, Faculty, Resident, Clinical Staff, RN, LPN, MSA)
   - Every endpoint requires explicit role check

2. **Data Protection**
   - No PII/PHI in logs or error messages
   - Sensitive data encrypted at rest (passwords, tokens)
   - SQLAlchemy ORM prevents SQL injection
   - Request signing for webhook callbacks

3. **OPSEC/PERSEC (Military Medical Context)**
   - Schedule assignments reveal duty patterns (OPSEC concern)
   - Resident names and locations (PERSEC concern)
   - Never commit real data to repository
   - Use synthetic identifiers (PGY1-01, FAC-PD) in demos

#### Principle 2: Regulatory Compliance (Immutable)

ACGME rules are regulatory requirements, not suggestions:

1. **Non-Negotiable Constraints**
   - 80-hour weekly work limit (never exceeded)
   - 1-in-7 day off requirement (never violated)
   - Supervision ratios (1 faculty : 2-4 residents)

2. **Audit Trail Requirements**
   - SQLAlchemy-Continuum tracks all changes (who, what, when)
   - Assignment model includes `explain_json` for scheduling rationale
   - All ACGME checks logged for compliance reporting

3. **Escalation Authority**
   - ARCHITECT cannot override ACGME rules
   - SCHEDULER cannot create compliant-violating schedules
   - Faculty/Program Director must approve any exceptions

#### Principle 3: Maintainability (Code Outlasts Features)

Code is read 10x more than written:

1. **Clear Naming Conventions**
   - Classes: `PascalCase` (e.g., `ACGMEValidator`, `SwapExecutor`)
   - Functions: `snake_case` (e.g., `validate_compliance`)
   - Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_HOURS_PER_WEEK`)
   - Private methods: `_snake_case` prefix

2. **Type Hints Everywhere**
   ```python
   # ✅ Good
   async def calculate_work_hours(
       db: AsyncSession,
       person_id: UUID,
       start_date: date,
       end_date: date,
   ) -> float:
       """Calculate total work hours in period."""

   # ❌ Bad
   async def calculate_work_hours(db, person_id, start_date, end_date):
   ```

3. **Documentation Standards**
   - Docstrings: Google-style format for public functions
   - Architecture: ADRs for significant decisions
   - Code comments: WHY not WHAT (code shows what, comments explain why)

#### Principle 4: Performance (P95 Latency Focus)

Optimize for worst-case scenarios, not averages:

1. **Latency Targets**
   - API endpoints: < 200ms (p95)
   - Schedule generation: < 5 minutes for full year (730 blocks)
   - Database queries: < 50ms (p95)

2. **N+1 Query Prevention**
   ```python
   # ❌ Bad (N+1 queries)
   persons = await db.execute(select(Person))
   for person in persons.scalars():
       assignments = await db.execute(
           select(Assignment).where(Assignment.person_id == person.id)
       )  # This runs once per person!

   # ✅ Good (eager loading)
   result = await db.execute(
       select(Person).options(selectinload(Person.assignments))
   )
   persons = result.scalars().all()  # One query with join
   ```

3. **Caching Strategy**
   - Route templates: 24-hour cache (rarely change)
   - Schedule data: 30-minute cache (updated during generation)
   - Rotation templates: 24-hour cache
   - User preferences: Session cache (invalidated on update)

#### Principle 5: Developer Experience

Lower cognitive load accelerates development:

1. **Consistent Patterns**
   - All services follow same initialization pattern
   - All API endpoints follow same structure
   - Error responses use consistent format

2. **Clear Error Messages**
   ```python
   # ❌ Bad
   raise ValueError("Invalid data")

   # ✅ Good
   raise ValidationError(
       field="assignment.person_id",
       message="Person with ID 123e4567-e89b-12d3-a456-426614174000 not found"
   )
   ```

3. **Minimal Surprise**
   - HTTP 200 means success (never use 200 for errors)
   - List endpoints always paginate (never unbounded results)
   - Soft deletes never appear in normal queries

---

## Part 2: Design Patterns Catalog

### 2.1 Established Patterns

#### Pattern 1: Repository Pattern (Data Access Abstraction)

**Purpose**: Decouple business logic from database implementation

**Example**:
```python
# services/person_service.py
class PersonService:
    """Business logic for person management."""

    def __init__(self, repo: PersonRepository):
        self.repo = repo

    async def get_person_workload(self, person_id: UUID) -> float:
        """Calculate person's work hours (doesn't know about DB)."""
        person = await self.repo.get_by_id(person_id)
        if not person:
            raise PersonNotFound(person_id)
        # Business logic here
        return sum(a.hours for a in person.assignments)


# repositories/person_repository.py
class PersonRepository:
    """Data access for persons."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, person_id: UUID) -> Person | None:
        """Query database - repository knows about DB, service doesn't."""
        result = await self.db.execute(
            select(Person).where(Person.id == person_id)
        )
        return result.scalar_one_or_none()
```

**Benefits**:
- Service layer doesn't know about SQL
- Easy to mock repository in tests
- Database changes don't affect business logic

#### Pattern 2: Pydantic Schema Validation (Request/Response Contracts)

**Purpose**: Validate all input/output at system boundaries

**Example**:
```python
# schemas/person.py
class PersonCreate(BaseModel):
    """Request schema for creating person."""
    name: str = Field(..., min_length=1, max_length=255)
    type: Literal["resident", "faculty"]
    email: EmailStr
    pgy_level: Optional[int] = Field(None, ge=1, le=3)

    model_config = ConfigDict(str_strip_whitespace=True)


class PersonResponse(BaseModel):
    """Response schema for person API."""
    id: UUID
    name: str
    type: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # ORM compatible


# routes/people.py
@router.post("/api/v1/people", response_model=PersonResponse)
async def create_person(
    db: AsyncSession = Depends(get_db),
    person_data: PersonCreate = Body(...),
) -> PersonResponse:
    """Create new person. Pydantic validates input automatically."""
    # person_data is guaranteed valid before this line
    created = await PersonService(PersonRepository(db)).create(person_data)
    return PersonResponse.model_validate(created)
```

**Benefits**:
- Type safety at boundaries
- Automatic validation and error messages
- Self-documenting API

#### Pattern 3: Service Layer with Dependency Injection

**Purpose**: Centralize business logic with explicit dependencies

**Example**:
```python
# services/schedule_generation_service.py
class ScheduleGenerationService:
    """Orchestrates schedule generation."""

    def __init__(
        self,
        person_repo: PersonRepository,
        block_repo: BlockRepository,
        constraint_engine: ConstraintEngine,
        resilience_checker: ResilienceHealthCheck,
    ):
        self.person_repo = person_repo
        self.block_repo = block_repo
        self.constraint_engine = constraint_engine
        self.resilience_checker = resilience_checker

    async def generate_schedule(
        self,
        academic_year: int,
    ) -> Schedule:
        """Generate compliant schedule."""
        # Check resilience first
        health = await self.resilience_checker.check()
        if health.score < 0.7:
            raise ResilienceViolation("System not healthy for generation")

        # Load data
        persons = await self.person_repo.get_all_residents()
        blocks = await self.block_repo.get_for_year(academic_year)

        # Generate
        return await self.constraint_engine.solve(persons, blocks)
```

**Benefits**:
- Easy to test (inject mocks)
- Explicit dependencies visible
- No hidden globals

#### Pattern 4: Async/Await Throughout (Concurrency)

**Purpose**: Non-blocking database and I/O operations

**Rule**: Every database operation must be `async def` with `await`

```python
# ❌ Bad (blocking)
def get_person_assignments(person_id: UUID) -> list[Assignment]:
    result = db.execute(select(Assignment).where(...))
    return result.scalars().all()

# ✅ Good (async)
async def get_person_assignments(
    db: AsyncSession,
    person_id: UUID,
) -> list[Assignment]:
    result = await db.execute(
        select(Assignment).where(Assignment.person_id == person_id)
    )
    return result.scalars().all()
```

#### Pattern 5: Audit Trail with SQLAlchemy-Continuum

**Purpose**: Track all changes for compliance and debugging

```python
# models/assignment.py
class Assignment(Base):
    """Schedule assignment with audit trail."""
    __tablename__ = "assignments"
    __versioned__ = {}  # Enable change tracking

    id = Column(GUID(), primary_key=True)
    person_id = Column(GUID(), ForeignKey("people.id"))
    block_id = Column(GUID(), ForeignKey("blocks.id"))
    # ... other fields ...


# Usage: Automatic tracking
# Every change to an Assignment is saved to the versions table
# Access history: assignment.versions (queryset of historical states)
```

#### Pattern 6: Cross-Database Type Decorators

**Purpose**: Write database-agnostic code (PostgreSQL + SQLite)

```python
# db/types.py - Platform-independent types
class GUID(TypeDecorator):
    """UUID that works on both PostgreSQL and SQLite."""
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))


# models/person.py
class Person(Base):
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    # Works on PostgreSQL (native UUID) AND SQLite (CHAR)
```

#### Pattern 7: Constraint-Based Validation (Domain Rules)

**Purpose**: Enforce business rules in the database

```python
# models/person.py
class Person(Base):
    __tablename__ = "people"

    # ... columns ...

    __table_args__ = (
        CheckConstraint(
            "type IN ('resident', 'faculty')",
            name="check_person_type"
        ),
        CheckConstraint(
            "pgy_level IS NULL OR pgy_level BETWEEN 1 AND 3",
            name="check_pgy_level"
        ),
        UniqueConstraint("email", name="unique_person_email"),
    )

# Benefits:
# - Constraints enforced at database level (no garbage data)
# - Clear intent in model definition
# - Automatic migration generation
```

#### Pattern 8: Connection Pool Management

**Purpose**: Efficient database connection reuse

```python
# db/session.py
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,           # Verify connection before use
    pool_size=10,                 # Base connections
    max_overflow=20,              # Burst connections allowed
    pool_timeout=30,              # Wait time for connection
    pool_recycle=1800,            # Lifetime: 30 minutes
)
```

**Settings Analysis**:
- `pool_size=10`: Keep 10 connections ready
- `max_overflow=20`: Allow up to 30 total during peaks
- `pool_recycle=1800`: Refresh every 30 min (prevents stale DB connections)
- `pool_pre_ping=True`: Verify connection health before reuse

#### Pattern 9: Transaction Scope Management

**Purpose**: Explicit transaction control

```python
# For HTTP requests (explicit commit)
@router.post("/api/v1/people")
async def create_person(
    db: AsyncSession = Depends(get_db),
    data: PersonCreate = Body(...),
) -> PersonResponse:
    person = Person(**data.model_dump())
    db.add(person)
    await db.commit()  # Explicit commit
    return PersonResponse.model_validate(person)


# For background tasks (auto-commit on success)
@app.task
def process_schedule():
    with task_session_scope() as session:
        # Work happens here
        session.commit()  # Auto-commit on normal exit
        # Auto-rollback on exception
```

#### Pattern 10: Error Handling with Custom Exceptions

**Purpose**: Meaningful error responses

```python
# core/exceptions.py
class SchedulingError(Exception):
    """Base exception for scheduling domain."""
    pass

class ACGMEViolation(SchedulingError):
    """ACGME compliance rule violated."""
    def __init__(self, rule: str, reason: str):
        self.rule = rule
        self.reason = reason
        super().__init__(f"{rule}: {reason}")


# Usage in service
async def assign_person_to_block(person_id: UUID, block_id: UUID) -> None:
    work_hours = await calculate_hours(person_id, block_id)
    if work_hours > 80:
        raise ACGMEViolation(
            rule="80-hour-limit",
            reason=f"Would result in {work_hours} hours (max 80)"
        )
```

#### Pattern 11: Health Check Pattern (Resilience Framework)

**Purpose**: Monitor system readiness before operations

```python
# core/health.py
class HealthCheck:
    """System health status for operations."""

    async def check_schedule_generation_readiness(self) -> ResilienceStatus:
        """Can we safely generate a schedule?"""
        checks = {
            "resilience_score": await self._check_resilience(),
            "database_available": await self._check_db(),
            "solver_available": await self._check_solver(),
            "n1_contingency": await self._check_n1_contingency(),
        }

        if any(not v for v in checks.values()):
            raise SystemNotReady("Schedule generation blocked", checks)

        return ResilienceStatus.HEALTHY


# Usage
async def generate_schedule(...) -> Schedule:
    await health.check_schedule_generation_readiness()  # Guard clause
    # Proceed safely
```

#### Pattern 12: Feature Flags (Progressive Rollout)

**Purpose**: Control feature visibility without deployment

```python
# models/feature_flag.py
class FeatureFlag(Base):
    __tablename__ = "feature_flags"

    name = Column(String(255), unique=True)
    enabled = Column(Boolean, default=False)
    rollout_percentage = Column(Integer, default=0)  # 0-100


# services/feature_service.py
async def is_feature_enabled(flag_name: str, user_id: UUID) -> bool:
    """Check if feature is enabled for user."""
    flag = await get_flag(flag_name)
    if not flag:
        return False

    if flag.rollout_percentage == 100:
        return True

    # Deterministic rollout (same user always same result)
    return hash(user_id) % 100 < flag.rollout_percentage


# Usage in routes
@router.get("/api/v1/schedule/experimental")
async def get_experimental_schedule(...):
    if not await is_feature_enabled("new_solver", user_id):
        raise FeatureNotEnabled()
    # New code here
```

#### Pattern 13: Request Idempotency (Safe Retries)

**Purpose**: Safe to retry failed requests

```python
# models/idempotency.py
class IdempotencyRequest(Base):
    __tablename__ = "idempotency_requests"

    idempotency_key = Column(String(255), unique=True)
    request_method = Column(String(10))
    request_path = Column(String(2048))
    response_status = Column(Integer)
    response_body = Column(JSONType())
    created_at = Column(DateTime, default=datetime.utcnow)


# middleware/idempotency.py
async def idempotency_middleware(request: Request) -> Response:
    """Handle idempotent request deduplication."""
    idempotency_key = request.headers.get("Idempotency-Key")

    if idempotency_key:
        existing = await db.execute(
            select(IdempotencyRequest).where(...)
        )
        if existing:
            return existing.response_body  # Return cached response

    # Process normally, store result for future identical requests
```

#### Pattern 14: Slot-Type Invariants (Credential Requirements)

**Purpose**: Declarative credential requirements for scheduling slots

```python
# scheduling/slot_invariants.py
INVARIANT_CATALOG = {
    "inpatient_call": {
        "hard": ["HIPAA", "Cyber_Training", "AUP", "N95_Fit"],
        "soft": [
            {"name": "expiring_soon", "window_days": 14, "penalty": 3}
        ]
    },
    "peds_clinic": {
        "hard": ["Flu_Vax", "Tdap"],
    },
}


# Usage
async def is_eligible(person_id: UUID, slot_type: str, date: date) -> bool:
    """Check if person meets slot requirements."""
    reqs = INVARIANT_CATALOG.get(slot_type, {})

    for req in reqs.get("hard", []):
        cred = await get_credential(person_id, req)
        if not cred or not cred.is_valid:
            return False  # Hard constraint failed

    return True  # All hard constraints satisfied
```

#### Pattern 15: Explainability in Schedule Assignments

**Purpose**: Transparency in scheduling decisions

```python
# models/assignment.py
class Assignment(Base):
    # ... other fields ...

    explain_json = Column(JSONType())  # DecisionExplanation as JSON
    confidence = Column(Float)  # 0-1 confidence score
    score = Column(Float)  # Objective score for assignment
    alternatives_json = Column(JSONType())  # Top alternatives


# schemas/assignment.py
class DecisionExplanation(BaseModel):
    """Why was this assignment made?"""
    algorithm: str  # 'greedy', 'cp_sat', 'pulp'
    primary_reason: str
    constraints_satisfied: list[str]
    constraints_violated: list[str]
    objective_value: float
    runtime_seconds: float


# Usage
assignment = Assignment(
    person_id=person_id,
    block_id=block_id,
    explain_json=DecisionExplanation(
        algorithm="cp_sat",
        primary_reason="Minimizes conflicts while satisfying constraints",
        constraints_satisfied=["acgme_80h", "supervision", "coverage"],
        constraints_violated=[],
        objective_value=0.95,
        runtime_seconds=12.5,
    ).model_dump(),
    confidence=0.95,
)
```

---

## Part 3: Decision Frameworks

### 3.1 API Design Decision Tree

```
Is this exposing data or triggering an action?
├─ EXPOSE DATA
│  └─ GET /api/v1/{resource}
│     Is it a collection or single item?
│     ├─ Collection: GET /api/v1/people?page=1&size=25
│     └─ Single: GET /api/v1/people/{id}
│
├─ TRIGGER ACTION (CREATE)
│  └─ POST /api/v1/{resource}
│     Payload? Yes → Body with Pydantic schema
│
├─ TRIGGER ACTION (FULL UPDATE)
│  └─ PUT /api/v1/{resource}/{id}
│     Replaces entire resource
│
├─ TRIGGER ACTION (PARTIAL UPDATE)
│  └─ PATCH /api/v1/{resource}/{id}
│     Updates only provided fields
│
├─ TRIGGER ACTION (DELETE)
│  └─ DELETE /api/v1/{resource}/{id}
│     Hard delete or soft delete?
│     ├─ Hard: Removed from database
│     └─ Soft: Marked deleted, still queryable with is_deleted filter
│
└─ TRIGGER ACTION (CUSTOM)
   └─ POST /api/v1/{resource}/{action}
      Examples: POST /api/v1/schedule/generate
                POST /api/v1/swap/{id}/execute
```

### 3.2 Database Design Decision Tree

```
Is this a new data model?
├─ YES: Create new table in models/
│  ├─ Does it track changes? → Add __versioned__ = {}
│  ├─ Does it need audit? → Add created_by, created_at, updated_at
│  ├─ Does it need soft delete? → Add deleted_at field + filter by IS NULL
│  ├─ What are the unique constraints?
│  │  └─ Example: unique(email), unique(person_id, block_id)
│  ├─ What are the foreign keys?
│  │  └─ Always use ondelete="CASCADE" or "SET NULL" (explicit)
│  └─ What are the check constraints?
│     └─ Example: CHECK(pgy_level BETWEEN 1 AND 3)
│
└─ NO: Modifying existing table
   ├─ Schema change? → Create Alembic migration
   │  └─ alembic revision --autogenerate -m "description"
   ├─ Dropping column? → Add migration + rollback plan
   ├─ Renaming column? → Add migration with data copy
   └─ Adding constraint? → Add migration (safer than direct ALTER)
```

### 3.3 Constraint Implementation Decision Framework

**When adding a new constraint to the scheduling engine:**

```
Constraint Type Assessment:
├─ HARD CONSTRAINT (must satisfy, never violated)
│  Examples: ACGME 80-hour limit, supervision ratios
│  └─ Implementation: constraint_engine.hard_constraints list
│     - Solver fails if unsatisfiable
│     - Explicit error to user
│
├─ SOFT CONSTRAINT (prefer to satisfy, can trade-off)
│  Examples: Minimize consecutive call days, prefer Wed for PD
│  └─ Implementation: constraint_engine.soft_constraints list
│     - Weighted in objective function
│     - Solver may violate if necessary
│
├─ PREFERENCE CONSTRAINT (nice-to-have)
│  Examples: Resident prefers morning clinic
│  └─ Implementation: RotationPreference weights
│     - Low weight in objective (easy to override)
│     - Used for fairness tie-breaking
│
└─ BUSINESS RULE (enforced by application)
   Examples: Only faculty can assign to supervise role
   └─ Implementation: Service layer validation
      - Check before persisting to database
      - Custom exception with clear message
```

### 3.4 Technology Evaluation Framework

**When evaluating new dependencies or libraries:**

```
Step 1: Problem Analysis
├─ What problem does it solve?
├─ Can existing stack solve it? (prefer yes)
├─ What's the cost of NOT adopting?
└─ Is this strategic or tactical?

Step 2: Evaluation Criteria (weighted)
├─ Maturity (20%): Community size, GitHub stars, production usage
├─ Security (20%): CVE history, patch frequency, ownership
├─ Performance (15%): Benchmarks relevant to our use case
├─ Maintenance (15%): Update frequency, responsiveness
├─ Compatibility (15%): License, Python 3.11+, async support
├─ Learning Curve (10%): Documentation quality, team ramp-up time
└─ Lock-in Risk (5%): Can we replace it later?

Step 3: Decision Matrix
├─ Score each criterion (1-10)
├─ Apply weights
├─ Threshold: ≥ 7.5/10 for adoption
└─ If adopted: Create ADR documenting decision

Step 4: Integration Planning
├─ Proof of concept (1-2 days)
├─ Performance testing in target environment
├─ Dependency tree analysis (does it bring 50 subdeps?)
└─ Migration effort estimate
```

---

## Part 4: Database Design Authority

### 4.1 Current Database Schema Structure

The system manages **80+ models** organized in layers:

```
Core Scheduling Models
├─ Person (residents, faculty, staff)
├─ Block (730 time slots per year)
├─ Assignment (person × block → role)
├─ RotationTemplate (activity definitions)
├─ Absence (leave, TDY, medical)
└─ CallAssignment (call schedule tracking)

Credentialing & Compliance
├─ Procedure (medical procedures)
├─ ProcedureCredential (person qualifications)
├─ PersonCertification (training completions)
└─ Certification (training definitions)

Resilience Framework (Tier 1-3)
├─ ResilienceHealthCheck (system status)
├─ VulnerabilityRecord (N-1 analysis)
├─ AllostasisRecord (equilibrium tracking)
├─ CognitiveDecisionRecord (decision complexity)
└─ HubProtectionPlanRecord (critical resource protection)

Clinical Operations
├─ ClinicSession (clinic scheduling)
├─ ClinicType (ambulatory, ED, etc.)
└─ StaffingStatus (coverage tracking)

Management & Configuration
├─ FeatureFlag (progressive rollout)
├─ ApplicationSettings (system config)
├─ ScheduledJob (background tasks)
└─ ExportJob (schedule exports)

Audit & Compliance
├─ User (application users)
├─ TokenBlacklist (logout tracking)
├─ EmailLog (notification audit)
└─ ConflictAlert (constraint violations)

External Integrations
├─ Webhook (event delivery)
├─ CalendarSubscription (iCal exports)
└─ OAuth2Client (OIDC integration)
```

### 4.2 Design Patterns in Models

#### Pattern: Audit Timestamps

Every mutable entity has:
```python
created_by = Column(String(255))  # Who created it
created_at = Column(DateTime, default=datetime.utcnow)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Pattern: Soft Deletes

For entities that shouldn't be truly deleted:
```python
deleted_at = Column(DateTime, nullable=True, default=None)

# Query pattern:
active_items = await db.execute(
    select(Item).where(Item.deleted_at.is_(None))
)
```

#### Pattern: Explicit Relationships

Define both sides of relationship:
```python
# In Person model:
assignments = relationship("Assignment", back_populates="person")

# In Assignment model:
person = relationship("Person", back_populates="assignments")

# Benefits:
# - Bi-directional traversal: person.assignments or assignment.person
# - SQLAlchemy maintains referential integrity
```

#### Pattern: Check Constraints for Enums

Instead of relying on application validation:
```python
class Person(Base):
    type = Column(String(50), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "type IN ('resident', 'faculty')",
            name="check_person_type"
        ),
    )
```

### 4.3 Indexing Strategy

**Query Performance Optimization:**

```python
# Indexes on foreign keys (automatic for FK columns in PostgreSQL)
person_id = Column(GUID(), ForeignKey("people.id"))  # Auto-indexed

# Indexes on frequently filtered columns:
created_at = Column(DateTime, index=True)
deleted_at = Column(DateTime, index=True)  # For soft delete queries
email = Column(String(255), unique=True)  # Unique implies index

# Composite indexes for common query patterns:
__table_args__ = (
    Index('idx_assignments_person_block', 'person_id', 'block_id'),
    Index('idx_assignments_block_role', 'block_id', 'role'),
)
```

### 4.4 Connection Pool Configuration

**Current settings in config.py:**

| Setting | Value | Rationale |
|---------|-------|-----------|
| `pool_size` | 10 | Base connections (1 per request handler) |
| `max_overflow` | 20 | Allow burst to 30 total |
| `pool_timeout` | 30s | Don't wait > 30s for connection |
| `pool_recycle` | 1800s | Refresh every 30 min (prevent stale) |
| `pool_pre_ping` | True | Verify connection before reuse |

**Scaling Strategy:**

- **Small deployment** (< 100 users): pool_size=5, max_overflow=10
- **Medium deployment** (100-500 users): pool_size=15, max_overflow=30
- **Large deployment** (> 500 users): Consider connection pooler (PgBouncer)

---

## Part 5: API Design Standards

### 5.1 Response Format Standard

**Success Response (2xx):**
```json
{
  "status": "success",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "John Doe",
    "type": "resident"
  },
  "metadata": {
    "timestamp": "2025-12-30T12:34:56Z",
    "request_id": "req-123"
  }
}
```

**Error Response (4xx/5xx):**
```json
{
  "status": "error",
  "error": {
    "code": "ACGME_VIOLATION",
    "message": "Cannot assign: would exceed 80-hour limit",
    "details": {
      "rule": "80-hour-weekly-limit",
      "current_hours": 75.5,
      "proposed_hours": 82.0
    }
  },
  "metadata": {
    "timestamp": "2025-12-30T12:34:56Z",
    "request_id": "req-123"
  }
}
```

### 5.2 Standard HTTP Status Codes

| Code | Usage | Example |
|------|-------|---------|
| **200** | Successful GET/PUT/PATCH | Get person details |
| **201** | Created resource via POST | Create new person |
| **204** | No content (DELETE success) | Delete person |
| **400** | Bad request (validation error) | Invalid email format |
| **401** | Unauthorized (auth missing/invalid) | Missing JWT token |
| **403** | Forbidden (insufficient permissions) | Non-admin accessing admin endpoint |
| **404** | Resource not found | Person ID doesn't exist |
| **409** | Conflict (duplicate/constraint) | Duplicate email |
| **422** | Unprocessable entity (business logic) | ACGME violation |
| **429** | Too many requests (rate limited) | Exceeded API quota |
| **500** | Server error (unhandled exception) | Database crash |
| **503** | Service unavailable | Maintenance mode |

### 5.3 Pagination Standard

**All list endpoints paginate:**

```
GET /api/v1/people?page=1&page_size=25
```

**Response:**
```json
{
  "status": "success",
  "data": [
    { "id": "...", "name": "..." },
    { "id": "...", "name": "..." }
  ],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total_count": 150,
    "total_pages": 6,
    "has_next": true,
    "has_previous": false
  }
}
```

**Rationale:**
- Prevents unbounded queries (malicious or accidental)
- Enables UI pagination
- Reduces response size

### 5.4 Rate Limiting

**Per-endpoint configuration:**

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /auth/login` | 5 | 15 minutes |
| `POST /schedule/generate` | 10 | 1 hour |
| `GET /api/v1/*` | 1000 | 1 hour |
| `POST /api/v1/*` | 100 | 1 hour |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1704048000
```

---

## Part 6: Infrastructure & Scalability

### 6.1 Deployment Architecture

```
┌────────────────────────────────────┐
│        Client Layer                │
│  (Web, Mobile, AI Agents)          │
└────────────┬───────────────────────┘
             │
┌────────────▼───────────────────────┐
│      Nginx (Reverse Proxy)         │
│  - SSL/TLS termination             │
│  - Rate limiting                   │
│  - Static file serving             │
│  - Request routing                 │
└────────────┬───────────────────────┘
             │
        ┌────┴────┐
        │          │
    ┌───▼──┐  ┌───▼──┐
    │FastAPI│  │FastAPI│  (Multiple instances)
    │Backend│  │Backend│
    └───┬──┘  └───┬──┘
        │          │
        └────┬─────┘
             │
    ┌────────▼─────────────┐
    │  PostgreSQL (primary)│  (Read/write)
    │  + Read Replicas     │  (Read-only)
    └──────────────────────┘
             │
    ┌────────▼─────────────┐
    │   Redis Cache        │  (Session, cache, Celery)
    └──────────────────────┘
```

### 6.2 Celery Background Tasks

**Long-running operations off HTTP path:**

```python
@celery_app.task(bind=True, max_retries=3)
def generate_schedule_async(self, academic_year: int) -> dict:
    """Generate schedule in background."""
    try:
        with task_session_scope() as db:
            schedule = ScheduleGenerationService(db).generate(academic_year)
            return {"status": "complete", "schedule_id": str(schedule.id)}
    except Exception as exc:
        # Exponential backoff retry
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

**Celery Beat Scheduled Tasks:**

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'health-check-every-15-min': {
        'task': 'app.tasks.health_checks.check_resilience',
        'schedule': crontab(minute='*/15'),
    },
    'n1-contingency-daily': {
        'task': 'app.tasks.resilience.analyze_n1_contingency',
        'schedule': crontab(hour=2, minute=0),  # 2 AM
    },
}
```

### 6.3 Caching Strategy

**Layered caching from fastest to slowest:**

```
L1: In-Memory (Request scoped) - 0ms
└─ Single request context (no cache miss)

L2: Redis Cache - 10-50ms
└─ Shared across processes
    - Schedule templates: 24 hours
    - User preferences: 1 hour
    - Rotation data: 4 hours

L3: Database - 50-200ms
└─ Indexed queries
    - Assignment queries: With indexes < 50ms
    - Complex aggregations: 50-200ms

L4: Solver Cache - 1-300s
└─ Cached solver results
    - Yesterday's schedule → reuse today
    - Pattern templates → reuse structure
```

**Cache Invalidation Pattern:**

```python
async def update_person_preference(person_id: UUID, pref: dict) -> None:
    """Update preference and invalidate cache."""
    # Update database
    await PersonRepository(db).update_preference(person_id, pref)

    # Invalidate related caches
    cache.invalidate(f"person:{person_id}:assignments")
    cache.invalidate(f"person:{person_id}:preferences")
    cache.invalidate(f"schedule:*")  # Wildcard invalidation
```

---

## Part 7: Cross-Cutting Concerns

### 7.1 Security Architecture

**Defense in Depth (5 Layers):**

```
Layer 1: Transport Security
├─ HTTPS/TLS 1.3 mandatory
├─ HSTS headers (Strict-Transport-Security)
└─ Certificate pinning (mobile clients)

Layer 2: Authentication
├─ JWT in httpOnly cookies (XSS-resistant)
├─ 12-character minimum password complexity
├─ MFA optional (2FA via authenticator apps)
└─ OAuth2 PKCE for public clients

Layer 3: Authorization
├─ 8-level RBAC (Admin, Coordinator, Faculty, ...)
├─ Endpoint-level permission checks (@require_role("admin"))
├─ Data-level access control (can only see own assignments)
└─ Resource-level filtering (can only modify own schedule)

Layer 4: Input Validation
├─ Pydantic schemas validate all input
├─ SQLAlchemy ORM prevents SQL injection
├─ File upload scanning (size, type, content)
└─ Path traversal prevention in file operations

Layer 5: Audit & Logging
├─ All changes logged with user/timestamp
├─ Sensitive operations logged (not values, just actions)
├─ Access logs for compliance reporting
└─ Alert on suspicious patterns (failed login attempts)
```

### 7.2 Compliance & Audit

**ACGME Compliance Tracking:**

```python
# models/assignment.py
class Assignment(Base):
    # ... fields ...

    # Explainability for audit
    explain_json = Column(JSONType())  # Why assigned here?
    confidence = Column(Float)  # 0-1 confidence

    # Audit trail via SQLAlchemy-Continuum
    __versioned__ = {}


# Usage: Generate compliance report
async def generate_compliance_report(academic_year: int) -> dict:
    """Report all ACGME violations and their justification."""

    assignments = await db.execute(
        select(Assignment).where(Assignment.year == academic_year)
    )

    violations = []
    for assignment in assignments.scalars():
        if not await ACGMEValidator.is_compliant(assignment):
            violations.append({
                "assignment_id": assignment.id,
                "violation": "...",
                "explanation": json.loads(assignment.explain_json),
                "version_history": assignment.versions,  # Full audit trail
            })

    return {"academic_year": academic_year, "violations": violations}
```

### 7.3 Error Handling Philosophy

**Never expose internal details in error messages:**

```python
# ❌ Bad (leaks information)
try:
    person = await db.execute(select(Person).where(...))
except DatabaseError as e:
    raise HTTPException(status_code=500, detail=str(e))
    # Client sees: "duplicate key value violates unique constraint"

# ✅ Good (generic to client, detailed server-side)
try:
    person = await db.execute(select(Person).where(...))
except IntegrityError as e:
    logger.error(f"Integrity error creating person: {e}", exc_info=True)
    raise HTTPException(
        status_code=409,
        detail="Person with this email already exists"
    )
    # Client sees: descriptive but non-leaking message
    # Server logs: full technical details for debugging
```

### 7.4 Observability & Monitoring

**Instrumentation Pattern:**

```python
# Use structured logging
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)

# Log with structure
logger.info(
    "Schedule generation started",
    extra={
        "event": "schedule_generation_start",
        "academic_year": 2026,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat(),
    }
)

# Metrics
from prometheus_client import Counter, Histogram

schedule_generation_counter = Counter(
    'schedule_generation_total',
    'Total schedule generations',
    ['status']  # success, failure
)

generation_duration = Histogram(
    'schedule_generation_seconds',
    'Schedule generation duration'
)

# Usage
with generation_duration.time():
    schedule = await generate()
schedule_generation_counter.labels(status='success').inc()
```

---

## Part 8: Pattern Evolution & Maintenance

### 8.1 How Patterns Age

**Pattern Lifecycle:**

```
1. PROPOSED (New idea)
   ├─ Created via ADR
   ├─ Peer review
   └─ Decision made (adopt/reject)

2. ADOPTED (Actively used)
   ├─ Documentation updated in CLAUDE.md
   ├─ Examples added to codebase
   └─ Team trained

3. MATURE (Proven pattern)
   ├─ Used consistently across codebase
   ├─ No breaking changes in 6+ months
   └─ Low defect rate

4. DEPRECATED (Replaced by better pattern)
   ├─ New pattern approved
   ├─ Migration guide published
   ├─ Gradual replacement (not all-at-once)
   └─ Old pattern removed in next major version

5. OBSOLETE (Removed)
   └─ No instances remain in codebase
```

### 8.2 When to Break Architectural Patterns

**ONLY if:**

1. Clear evidence of pattern failure (not preference)
   - Bug patterns tied to specific architecture
   - Performance measurement shows bottleneck
   - Team consensus on specific issue

2. Proposed alternative is proven better
   - Implementation in feature branch
   - Comparison testing
   - Migration path defined

3. ARCHITECT approval with ADR
   - Document old pattern's deficiency
   - Document new pattern benefits
   - Define rollout timeline

**Never break patterns for:**
- Personal style preference
- Trendy new framework
- "Cleaner looking code"
- Premature optimization

### 8.3 Architecture Review Cycle

**Quarterly Architecture Review (Q4 focus):**

```
1. Pattern Audit (2 weeks)
   ├─ List all patterns used
   ├─ Count usage (high/medium/low)
   └─ Assess health (stable/fragile)

2. Technical Debt Assessment (1 week)
   ├─ Identify aging patterns
   ├─ Estimate refactoring cost
   └─ Prioritize by impact

3. Future Planning (1 week)
   ├─ Assess upcoming feature complexity
   ├─ Identify pattern gaps
   └─ Plan new patterns if needed

4. Team Alignment (1 week)
   ├─ Present findings to agents
   ├─ Discuss proposed changes
   └─ Publish updated CLAUDE.md
```

---

## Part 9: Decision Authority Matrix

### 9.1 What ARCHITECT Decides Independently

| Decision Type | Autonomy | Documentation |
|---------------|----------|----------------|
| New service layer | Full | ADR if significant |
| API endpoint design | Full | Endpoint specs in code |
| Database schema | Full* | Alembic migration + explanation |
| Performance optimization | Full | ADR if non-obvious |
| New dependency | Full | Evaluation documented |
| Error handling patterns | Full | CLAUDE.md update |
| Caching strategy | Full | Architecture doc |
| Testing patterns | Full | Test examples |
| Code organization | Full | CLAUDE.md section |
| Internal refactoring | Full | No external impact |

*Database schema changes require migrations, not direct ALTER

### 9.2 What Requires Escalation

| Decision Type | Escalate To | Reason |
|---------------|-------------|--------|
| ACGME rule changes | Faculty + SCHEDULER | Regulatory (non-negotiable) |
| Auth changes | Security Auditor + Faculty | Security critical |
| Breaking API changes | API_DEVELOPER + Faculty | Affects clients |
| Data migration risk | DBA + Resilience Engineer | Potential data loss |
| Major refactor > 3 months | ORCHESTRATOR | Timeline visibility |
| Removing tested features | QA_TESTER + Faculty | Risk of regression |
| Performance SLA changes | RESILIENCE_ENGINEER | System guarantees |

### 9.3 What ARCHITECT Absolutely Cannot Do

```
❌ NEVER:
├─ Override ACGME compliance rules
├─ Disable security checks
├─ Skip database backups before writes
├─ Bypass audit requirements
├─ Use deprecated unsupported libraries
├─ Accept tech debt without plan
├─ Push directly to main (use PR)
├─ Modify .env files in commits
├─ Store secrets in code
└─ Deploy without testing
```

---

## Part 10: High-Level Design Decisions (Historical)

### Foundational ADRs

| ADR | Decision | Status |
|-----|----------|--------|
| ADR-0001 | Layered architecture (Route→Controller→Service→Repository→Model) | Accepted |
| ADR-0002 | SQLAlchemy ORM (prevent SQL injection) | Accepted |
| ADR-0003 | Async/await throughout (concurrency) | Accepted |
| ADR-0004 | Pydantic schemas for validation (type safety) | Accepted |
| ADR-0005 | PostgreSQL + SQLite support (type decorators) | Accepted |
| ADR-0006 | SQLAlchemy-Continuum for audit trails | Accepted |
| ADR-0007 | Connection pooling (prevent exhaustion) | Accepted |
| ADR-0008 | Redis caching (performance) | Accepted |
| ADR-0009 | Celery background tasks (non-blocking) | Accepted |
| ADR-0010 | Feature flags (progressive rollout) | Accepted |

### Resilience Framework ADRs

| ADR | Decision | Status |
|-----|----------|--------|
| ADR-0050 | SPC monitoring (statistical control) | Accepted |
| ADR-0051 | SIR epidemiology models (burnout spread) | Accepted |
| ADR-0052 | Erlang C queuing (staffing levels) | Accepted |
| ADR-0053 | Seismic precursor detection (burnout early warning) | Accepted |
| ADR-0054 | N-1/N-2 contingency analysis | Accepted |
| ADR-0055 | Sacrifice hierarchy for cascade failures | Accepted |

---

## Summary: ARCHITECT's Role in Decisions

```
ARCHITECT = Strategic Steward of Design

Responsibilities:
├─ Maintain architectural integrity (patterns consistent)
├─ Evaluate technology decisions (good ROI)
├─ Review data schema evolution (sound design)
├─ Approve cross-cutting concerns (security, performance)
├─ Document significant decisions (ADRs)
├─ Guide system evolution (long-term vision)
└─ Coordinate with specialized agents (SCHEDULER, QA_TESTER, etc)

Authority:
├─ Autonomous on architecture decisions
├─ Escalates ACGME, security, breaking changes
├─ Documents all decisions for team learning
└─ Maintains CLAUDE.md as living document

Philosophy:
├─ Security > Features
├─ Compliance > Convenience
├─ Maintainability > Cleverness
├─ Measured > Gut-feel
└─ Long-term > Quick-fix
```

---

## Appendix A: Architecture Documentation Map

**Location of key architectural documents:**

```
/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/
├─ CLAUDE.md (Project guidelines - start here)
├─ docs/architecture/
│  ├─ overview.md (System architecture diagram)
│  ├─ api-design.md (API standards)
│  ├─ SOLVER_ALGORITHM.md (Scheduling engine internals)
│  ├─ cross-disciplinary-resilience.md (Resilience framework)
│  ├─ BLOCK_SCHEDULE_ARCHITECTURE.md (Block structure)
│  ├─ CONTROL_THEORY_TUNING_GUIDE.md (System tuning)
│  └─ CONSULTATION_LOG.md (Design decision history)
├─ backend/app/
│  ├─ models/ (SQLAlchemy ORM definitions)
│  ├─ services/ (Business logic)
│  ├─ api/routes/ (HTTP endpoints)
│  ├─ core/config.py (Configuration management)
│  └─ db/ (Database session, types, migration)
└─ .claude/Agents/ARCHITECT.md (This specification)
```

---

**End of Enhanced ARCHITECT Specification**

This document serves as the authoritative reference for architectural decisions, design patterns, and decision frameworks used throughout the Residency Scheduler system. Last reviewed by G2_RECON SEARCH_PARTY on 2025-12-30.
