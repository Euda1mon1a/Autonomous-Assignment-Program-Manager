# CLAUDE.md - Project Guidelines for Autonomous Claude Work

> **Last Updated:** 2025-12-18
> **Purpose:** Guidelines for autonomous AI-assisted development on the Residency Scheduler project

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Architecture Patterns](#architecture-patterns)
4. [Code Style Guidelines](#code-style-guidelines)
5. [Testing Requirements](#testing-requirements)
6. [Security Requirements](#security-requirements)
7. [Common Commands](#common-commands)
8. [Files and Patterns to Never Modify](#files-and-patterns-to-never-modify)
9. [Development Workflow](#development-workflow)
10. [Key Concepts](#key-concepts)

---

## Project Overview

### What This System Does

**Residency Scheduler** is a production-ready, full-stack application for automating and optimizing medical residency program scheduling while ensuring compliance with ACGME (Accreditation Council for Graduate Medical Education) requirements.

### Core Features

- **Automated Schedule Generation**: Constraint-based algorithm for compliant schedules
- **ACGME Compliance Monitoring**: Real-time validation (80-hour rule, 1-in-7 rule, supervision ratios)
- **Emergency Coverage System**: Handle military deployments, TDY, medical emergencies
- **Swap Management**: Faculty can request schedule swaps with auto-matching
- **Procedure Credentialing**: Track faculty qualifications and certifications
- **Resilience Framework**: Cross-industry best practices (80% utilization threshold, N-1/N-2 contingency, defense in depth)

### Application Context

This is a **scheduling application** for medical residency programs. All work must consider:
- Data security and privacy
- Audit trails for compliance
- Error handling that doesn't leak sensitive information
- Access control and authorization

---

## Tech Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Core language |
| **FastAPI** | 0.109.0 | High-performance web framework |
| **SQLAlchemy** | 2.0.25 | ORM with async support |
| **Pydantic** | 2.5.3 | Data validation and serialization |
| **Alembic** | 1.13.1 | Database migrations |
| **PostgreSQL** | 15 | Primary database |
| **Redis** | Latest | Celery broker, rate limiting, caching |
| **Celery** | 5.x | Background task processing |
| **pytest** | Latest | Testing framework |
| **NetworkX** | 3.0+ | Graph analysis for resilience |
| **SciPy** | 1.11+ | Scientific computing (Erlang C, statistics) |
| **NDlib** | 5.1+ | Network epidemiology (SIR models) |
| **pyspc** | 0.1+ | Statistical Process Control charts |
| **pyworkforce** | 0.2+ | Erlang C queuing optimization |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 14.0.4 | React framework with App Router |
| **React** | 18.2.0 | UI library |
| **TypeScript** | 5.0+ | Type-safe JavaScript |
| **TailwindCSS** | 3.3.0 | Utility-first CSS |
| **TanStack Query** | 5.17.0 | Data fetching and caching |

### Infrastructure

- **Docker** + **Docker Compose**: Containerization and orchestration
- **Prometheus**: Metrics and monitoring
- **Grafana**: Dashboard visualization

---

## Architecture Patterns

### Layered Architecture

The backend follows a strict layered architecture. **Always respect these boundaries:**

```
API Route (FastAPI endpoint)
    ↓
Controller (request/response handling, validation)
    ↓
Service (business logic)
    ↓
Repository (data access, if used)
    ↓
Model (SQLAlchemy ORM)
```

### Directory Structure

```
backend/app/
├── api/                    # API routes (endpoints)
│   ├── deps.py            # Dependencies (auth, db session)
│   └── routes/            # Route modules
├── controllers/           # Request/response handling
├── services/              # Business logic layer
├── repositories/          # Data access layer (when used)
├── models/                # SQLAlchemy ORM models
├── schemas/               # Pydantic schemas (request/response)
├── core/                  # Config, security, Celery
├── db/                    # Database session management
├── scheduling/            # Scheduling engine & validator
├── resilience/            # Resilience framework
├── notifications/         # Alert delivery
└── analytics/             # Metrics and reporting
```

### Key Architectural Rules

1. **Routes should be thin**: Delegate to controllers or services
2. **Business logic belongs in services**: Not in routes or models
3. **Use Pydantic schemas**: For all request/response validation
4. **Async all the way**: Use `async def` for all route handlers and database operations
5. **Dependency injection**: Use FastAPI's `Depends()` for database sessions and auth

---

## Code Style Guidelines

### Python (Backend)

#### General Style

- **PEP 8 compliant**: Follow Python style guide
- **Type hints required**: Use type hints for all function signatures
- **Docstrings required**: Use Google-style docstrings for all public functions/classes
- **Line length**: Max 100 characters (not 79)
- **Imports**: Organize as stdlib, third-party, local (separated by blank lines)

#### Example Function

```python
"""Service for managing schedule assignments."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate


async def create_assignment(
    db: Session,
    assignment_data: AssignmentCreate,
    created_by: str
) -> Assignment:
    """
    Create a new schedule assignment.

    Args:
        db: Database session
        assignment_data: Validated assignment data
        created_by: ID of user creating the assignment

    Returns:
        Assignment: Created assignment instance

    Raises:
        ValueError: If assignment conflicts with existing assignments
        ConflictError: If ACGME compliance would be violated
    """
    # Implementation here
    pass
```

#### Naming Conventions

- **Classes**: `PascalCase` (e.g., `SwapExecutor`, `ACGMEValidator`)
- **Functions/Methods**: `snake_case` (e.g., `create_assignment`, `validate_compliance`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_HOURS_PER_WEEK`, `REDIS_URL`)
- **Private methods**: Prefix with `_` (e.g., `_calculate_utilization`)
- **Database models**: Singular (e.g., `Person`, `Assignment`, not `People`, `Assignments`)

#### Async/Await

```python
# Always use async/await for database operations
async def get_person(db: AsyncSession, person_id: str) -> Optional[Person]:
    result = await db.execute(
        select(Person).where(Person.id == person_id)
    )
    return result.scalar_one_or_none()
```

### TypeScript (Frontend)

- **Strict mode enabled**: All TS strict checks active
- **Explicit types**: Avoid `any`, use proper types or `unknown`
- **Component naming**: PascalCase for components
- **Hooks naming**: Start with `use` (e.g., `useScheduleData`)
- **Props interfaces**: Define explicit interfaces for all component props

---

## Testing Requirements

### General Testing Philosophy

**ALL code changes must include tests.** Do not commit code without corresponding test coverage.

### Backend Testing (pytest)

#### Test Organization

```
backend/tests/
├── unit/                   # Unit tests (if separated)
├── integration/            # Integration tests
├── services/               # Service layer tests
├── conftest.py            # Pytest fixtures
└── test_*.py              # Test modules
```

#### Required Test Coverage

1. **Service layer**: Unit tests for all business logic
2. **API endpoints**: Integration tests for all routes
3. **Models**: Test model relationships and constraints
4. **Edge cases**: Test error conditions, validation failures
5. **ACGME compliance**: All compliance rules must have tests

#### Example Test Structure

```python
"""Tests for swap executor service."""
import pytest
from datetime import date

from app.services.swap_executor import SwapExecutor
from app.models.swap import SwapRequest, SwapType


class TestSwapExecutor:
    """Test suite for swap execution logic."""

    async def test_execute_one_to_one_swap(self, db, swap_request):
        """Test successful execution of one-to-one swap."""
        executor = SwapExecutor()
        result = await executor.execute_swap(db, swap_request)

        assert result.status == "completed"
        assert result.executed_at is not None
        # Verify database state changed

    async def test_execute_swap_validation_failure(self, db, invalid_swap):
        """Test swap execution fails with invalid request."""
        executor = SwapExecutor()

        with pytest.raises(ValueError, match="Invalid swap request"):
            await executor.execute_swap(db, invalid_swap)
```

#### Running Tests

```bash
# Run all tests
cd backend
pytest

# Run specific test file
pytest tests/test_swap_executor.py

# Run with coverage
pytest --cov=app --cov-report=html

# Run ACGME compliance tests only
pytest -m acgme

# Run with verbose output
pytest -v
```

### Frontend Testing (Jest + React Testing Library)

```bash
cd frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run tests in CI mode
npm run test:ci

# Type checking
npm run type-check

# Linting
npm run lint
npm run lint:fix
```

### Before Every Commit

**MANDATORY**: Run tests before committing:

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

If tests fail, **DO NOT COMMIT**. Fix the failing tests or the code first.

---

## Security Requirements

### Data Protection

Security is important for any application handling user data. Follow standard security best practices.

### OPSEC/PERSEC Requirements (Military Medical Data)

This system handles military medical residency schedules. **Never commit to the repository:**

| Data Type | Risk | Handling |
|-----------|------|----------|
| **Resident/Faculty Names** | PERSEC | Local only, sanitize for demos |
| **Schedule Assignments** | OPSEC | Local only, reveals duty patterns |
| **Absence/Leave Records** | OPSEC/PERSEC | Local only, reveals movements |
| **TDY/Deployment Data** | OPSEC | Never in repo or logs |

**Gitignored Files:**
- `docs/data/*_export.json` - Airtable exports with real data
- `docs/data/*.json` - Any schedule data
- `.env`, `.env.local` - Credentials

**For Demo/Test Data:**
```python
# Use synthetic identifiers
residents = ["PGY1-01", "PGY2-01"]  # Not real names
faculty = ["FAC-PD", "FAC-APD"]      # Role-based IDs
```

See `docs/security/DATA_SECURITY_POLICY.md` for full policy.

### Authentication & Authorization

1. **JWT-based auth**: httpOnly cookies (XSS-resistant)
2. **Password requirements**: Min 12 chars, complexity rules enforced
3. **Rate limiting**: Enforced on auth endpoints (see `backend/app/core/rate_limit.py`)
4. **Role-based access control (RBAC)**: 8 user roles (Admin, Coordinator, Faculty, Resident, Clinical Staff, RN, LPN, MSA)

### Security Best Practices

1. **Never log sensitive data**: No passwords, tokens, or personal data in logs
2. **Input validation**: Use Pydantic schemas for all inputs
3. **SQL injection prevention**: Always use SQLAlchemy ORM, never raw SQL
4. **Path traversal prevention**: Validate file paths (see `backend/app/core/file_security.py`)
5. **Secret management**: Never commit secrets, use environment variables
6. **Error handling**: Don't leak information in error messages (use global exception handler)

### Secret Validation

The application **refuses to start** if `SECRET_KEY` or `WEBHOOK_SECRET` are:
- Empty
- Less than 32 characters
- Using default values

Generate secrets with:
```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

### File Upload Security

When handling file uploads:
- Validate file size limits
- Validate file types (whitelist, not blacklist)
- Scan file contents, not just extensions
- Prevent path traversal in filenames

---

## Common Commands

### Backend Development

```bash
# Setup virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Database migrations
alembic upgrade head                    # Apply migrations
alembic downgrade -1                    # Rollback one migration
alembic revision --autogenerate -m "description"  # Create migration

# Run development server
uvicorn app.main:app --reload

# Run tests
pytest
pytest --cov=app --cov-report=html
pytest -m acgme  # Only ACGME tests

# Celery (background tasks)
redis-server                            # Start Redis
../scripts/start-celery.sh both         # Start worker + beat
../scripts/start-celery.sh worker       # Worker only
../scripts/start-celery.sh beat         # Scheduler only
python verify_celery.py                 # Verify Celery status
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check

# Linting
npm run lint
npm run lint:fix

# Testing
npm test
npm run test:coverage
npm run test:e2e  # Playwright E2E tests
```

### Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Run backend tests in container
docker-compose exec backend pytest

# Access database
docker-compose exec db psql -U scheduler -d residency_scheduler
```

### Useful Database Queries

```bash
# Connect to database
docker-compose exec db psql -U scheduler -d residency_scheduler

# Common queries
SELECT COUNT(*) FROM assignments;
SELECT * FROM persons WHERE role = 'RESIDENT';
SELECT * FROM blocks WHERE date >= CURRENT_DATE LIMIT 10;
```

### Load Testing

```bash
# k6 Load Tests (from load-tests/ directory)
cd load-tests
npm install                           # Install dependencies
npm run test:smoke                    # Quick validation (1 min)
npm run test:load                     # Standard load test (5 min, 50 VUs)
npm run test:stress                   # Stress test (10 min, 200 VUs)

# Run specific k6 scenarios
k6 run scenarios/api-baseline.js      # Establish latency baselines
k6 run scenarios/concurrent-users.js  # Multi-user simulation
k6 run scenarios/schedule-generation.js  # Schedule gen stress
k6 run scenarios/rate-limit-attack.js # Security testing

# Custom k6 options
k6 run --vus 50 --duration 5m scenarios/concurrent-users.js

# pytest Performance Tests (from backend/ directory)
cd backend
pytest -m performance                 # All performance tests
pytest -m "performance and not slow"  # Fast performance tests only
pytest tests/performance/test_acgme_load.py -v      # ACGME validation
pytest tests/performance/test_connection_pool.py -v # DB connection pool
pytest tests/performance/test_idempotency_load.py -v # Idempotency
pytest tests/resilience/test_resilience_load.py -v  # Resilience framework

# Docker-based load testing
cd load-tests
npm run test:docker:smoke             # Run in container
npm run test:docker:load              # Full load test in container
```

---

## Files and Patterns to Never Modify

### Critical Files - Never Modify Without Explicit Permission

These files are foundational and changes could break the entire system:

#### Backend Core

- `backend/app/core/config.py` - Application configuration (except adding new config vars)
- `backend/app/core/security.py` - Authentication and password hashing
- `backend/app/db/base.py` - Database base configuration
- `backend/app/db/session.py` - Database session management
- `backend/app/main.py` - FastAPI application initialization

#### Database Models (Modify with Extreme Caution)

- `backend/app/models/*.py` - Any changes require Alembic migration
- **NEVER** modify models without creating a corresponding migration
- **NEVER** drop columns without migration and data backup plan

#### Migrations

- `backend/alembic/versions/*.py` - Never edit existing migrations
- **NEVER** delete or modify applied migrations
- **ONLY** create new migrations to change schema

#### Environment Files

- `.env` - Contains secrets (should never be committed)
- `.env.example` - Template for environment variables (can update)
- `docker-compose.yml` - Production Docker config (changes need careful testing)

### Patterns to Avoid

1. **Don't bypass authentication**: Never add `allow_anonymous` or skip auth checks
2. **Don't disable rate limiting**: Keep `RATE_LIMIT_ENABLED=true` in production
3. **Don't use synchronous database calls**: Always use `async def` and `await`
4. **Don't hardcode secrets**: Use environment variables
5. **Don't expose sensitive data in API responses**: Use Pydantic schemas to control what's returned
6. **Don't modify ACGME compliance rules**: These are regulatory requirements

### High-Risk Areas - Extra Caution Required

- **ACGME Compliance**: `backend/app/scheduling/acgme_validator.py`
- **Schedule Generation**: `backend/app/scheduling/engine.py`
- **Authentication**: `backend/app/api/routes/auth.py`
- **Resilience Framework**: `backend/app/resilience/*.py`

---

## Development Workflow

### Making Changes

1. **Understand the requirement** fully before coding
2. **Read relevant tests** to understand expected behavior
3. **Follow the layered architecture**: Route → Controller → Service → Repository → Model
4. **Write tests first** (TDD) or alongside implementation
5. **Run tests** before committing
6. **Update documentation** if adding new features

### Adding a New Feature

Example: Adding a new API endpoint

1. **Create Pydantic schemas** (in `backend/app/schemas/`)
2. **Create/update model** (in `backend/app/models/`) + Alembic migration
3. **Create service** (in `backend/app/services/`)
4. **Create controller** (in `backend/app/controllers/`) if needed
5. **Create route** (in `backend/app/api/routes/`)
6. **Write tests** (in `backend/tests/`)
7. **Update API documentation** (docstrings + `docs/api/`)

### Database Changes

**Always use Alembic migrations:**

```bash
# 1. Modify model in backend/app/models/
# 2. Create migration
cd backend
alembic revision --autogenerate -m "Add new_field to Person model"

# 3. Review the generated migration in alembic/versions/
# 4. Edit if needed (autogenerate isn't perfect)
# 5. Test migration
alembic upgrade head

# 6. Test rollback
alembic downgrade -1
alembic upgrade head

# 7. Commit both model change and migration
```

### Debugging

```bash
# Backend debugging
import pdb; pdb.set_trace()  # Add breakpoint

# View logs
docker-compose logs -f backend

# Database inspection
docker-compose exec db psql -U scheduler -d residency_scheduler
\dt  # List tables
\d persons  # Describe table

# Redis inspection
docker-compose exec redis redis-cli
KEYS *
GET some_key
```

---

## Key Concepts

### ACGME Compliance Rules

Must be validated for all schedules:

1. **80-Hour Rule**: Maximum 80 hours/week, averaged over rolling 4-week periods
2. **1-in-7 Rule**: One 24-hour period off every 7 days
3. **Supervision Ratios**:
   - PGY-1: 1 faculty per 2 residents
   - PGY-2/3: 1 faculty per 4 residents

### Schedule Structure

- **Academic Year**: 365 days
- **Blocks**: 730 blocks per year (365 days × AM/PM sessions)
- **Rotations**: Templates (clinic, inpatient, procedures, conference)
- **Assignments**: Person + Block + Rotation

### Resilience Framework

Cross-industry best practices organized in tiers:

**Tier 1 - Core Concepts:**
- **80% Utilization Threshold**: Queuing theory prevents cascade failures
- **N-1/N-2 Contingency**: Power grid-style vulnerability detection
- **Defense in Depth**: 5 safety levels (GREEN → YELLOW → ORANGE → RED → BLACK)
- **Static Stability**: Pre-computed fallback schedules
- **Sacrifice Hierarchy**: Triage-based load shedding

**Tier 2 - Strategic Concepts:**
- **Homeostasis**: Biological feedback loops for schedule balance
- **Blast Radius Isolation**: Zone-based containment from AWS
- **Le Chatelier's Principle**: Equilibrium shifts from chemistry

**Tier 3+ - Cross-Disciplinary Analytics:**
- **SPC Monitoring**: Western Electric rules from semiconductor manufacturing
- **Process Capability**: Cp/Cpk Six Sigma metrics for schedule quality
- **Burnout Epidemiology**: SIR models and Rt reproduction number
- **Erlang Coverage**: Telecommunications queuing for specialist staffing
- **Seismic Detection**: STA/LTA algorithm for burnout precursors
- **Burnout Fire Index**: Multi-temporal danger rating from forestry CFFDRS
- **Creep/Fatigue**: Larson-Miller parameter from materials science

See `docs/architecture/cross-disciplinary-resilience.md` for detailed documentation.

### Swap System

Faculty can request schedule swaps:

- **Types**: One-to-one swap, Absorb (give away shift)
- **Auto-matching**: Find compatible swap candidates
- **Validation**: Ensure swaps maintain ACGME compliance
- **Rollback**: 24-hour window to reverse a swap

### Background Tasks (Celery)

Used for:
- Resilience health checks (every 15 min)
- N-1/N-2 contingency analysis (every 24 hours)
- Conflict detection after leave approval
- Email notifications
- Schedule metrics calculation

---

## Common Pitfalls and How to Avoid Them

### 1. N+1 Query Problem

**Bad:**
```python
# Fetches persons, then queries assignments for each person (N+1 queries)
persons = await db.execute(select(Person))
for person in persons.scalars():
    assignments = await db.execute(
        select(Assignment).where(Assignment.person_id == person.id)
    )
```

**Good:**
```python
# Single query with join
result = await db.execute(
    select(Person).options(selectinload(Person.assignments))
)
persons = result.scalars().all()
```

### 2. Missing Type Hints

**Bad:**
```python
def calculate_hours(assignments):  # No types
    return sum(a.hours for a in assignments)
```

**Good:**
```python
def calculate_hours(assignments: list[Assignment]) -> float:
    """Calculate total hours from assignments."""
    return sum(a.hours for a in assignments)
```

### 3. Leaking Sensitive Data in Errors

**Bad:**
```python
raise HTTPException(
    status_code=400,
    detail=f"Person {person_id} has email {person.email}"  # Sensitive data leaked!
)
```

**Good:**
```python
raise HTTPException(
    status_code=400,
    detail="Invalid person data"  # Generic message
)
# Log detailed error server-side only
logger.error(f"Validation failed for person {person_id}", exc_info=True)
```

### 4. Modifying Models Without Migrations

**Bad:**
```python
# Just changing the model
class Person(Base):
    # Added new field but no migration
    middle_name: str = Column(String, nullable=True)
```

**Good:**
```python
# 1. Change model
class Person(Base):
    middle_name: str = Column(String, nullable=True)

# 2. Create migration
# alembic revision --autogenerate -m "Add middle_name to Person"

# 3. Apply migration
# alembic upgrade head
```

---

## Documentation Updates

When making changes, update relevant documentation:

- **API changes**: Update docstrings + `docs/api/*.md`
- **New features**: Update `README.md` + user guide
- **Configuration changes**: Update `.env.example` + `docs/admin-manual/configuration.md`
- **Database changes**: Document in migration message

---

## Getting Help

### Documentation

- **README.md**: Project overview and quick start
- **docs/**: Comprehensive documentation
  - `docs/architecture/`: System design
  - `docs/api/`: API reference
  - `docs/user-guide/`: User documentation
  - `docs/development/`: Development guides
- **HUMAN_TODO.md**: Tasks requiring human action

### Code References

- Look for similar patterns in existing code
- Check tests to understand expected behavior
- Review `docs/planning/TODO_TRACKER.md` for implementation examples

### Questions to Ask Yourself

Before implementing a feature:

1. Does this maintain ACGME compliance?
2. Is this secure?
3. Have I written tests?
4. Does this follow the layered architecture?
5. Are all database operations async?
6. Have I validated all inputs with Pydantic?
7. Does this need a database migration?
8. Could this leak sensitive information in errors?

---

## Summary Checklist for All Work

- [ ] Code follows layered architecture (Route → Controller → Service → Model)
- [ ] All functions have type hints and docstrings
- [ ] All new code has corresponding tests
- [ ] Tests pass: `pytest` (backend) and `npm test` (frontend)
- [ ] Database changes have Alembic migrations
- [ ] No secrets hardcoded (use environment variables)
- [ ] No sensitive data leaked in error messages or logs
- [ ] Input validation uses Pydantic schemas
- [ ] All database operations are async
- [ ] ACGME compliance maintained (if touching scheduling)
- [ ] Documentation updated if needed
- [ ] Security best practices followed

---

**Remember**: This is a scheduling application. Data security and ACGME compliance are important. When in doubt, ask before making changes to critical systems.

---

*This document is maintained as a living guide. Update it when patterns or requirements change.*
