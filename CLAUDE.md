***REMOVED*** CLAUDE.md - Project Guidelines for Autonomous Claude Work

> **Last Updated:** 2025-12-25
> **Purpose:** Guidelines for autonomous AI-assisted development on the Residency Scheduler project

---

***REMOVED******REMOVED*** Table of Contents

1. [Project Overview](***REMOVED***project-overview)
2. [Tech Stack](***REMOVED***tech-stack)
3. [Architecture Patterns](***REMOVED***architecture-patterns)
4. [Code Style Guidelines](***REMOVED***code-style-guidelines)
5. [Testing Requirements](***REMOVED***testing-requirements)
6. [Security Requirements](***REMOVED***security-requirements)
7. [Common Commands](***REMOVED***common-commands)
8. [Files and Patterns to Never Modify](***REMOVED***files-and-patterns-to-never-modify)
9. [Development Workflow](***REMOVED***development-workflow)
10. [Debugging & Troubleshooting](***REMOVED***debugging--troubleshooting)
11. [AI Rules of Engagement](***REMOVED***ai-rules-of-engagement)
12. [Key Concepts](***REMOVED***key-concepts)

---

***REMOVED******REMOVED*** Project Overview

***REMOVED******REMOVED******REMOVED*** What This System Does

**Residency Scheduler** is a production-ready, full-stack application for automating and optimizing medical residency program scheduling while ensuring compliance with ACGME (Accreditation Council for Graduate Medical Education) requirements.

***REMOVED******REMOVED******REMOVED*** Core Features

- **Automated Schedule Generation**: Constraint-based algorithm for compliant schedules
- **ACGME Compliance Monitoring**: Real-time validation (80-hour rule, 1-in-7 rule, supervision ratios)
- **Emergency Coverage System**: Handle military deployments, TDY, medical emergencies
- **Swap Management**: Faculty can request schedule swaps with auto-matching
- **Procedure Credentialing**: Track faculty qualifications and certifications
- **Resilience Framework**: Cross-industry best practices (80% utilization threshold, N-1/N-2 contingency, defense in depth)

***REMOVED******REMOVED******REMOVED*** Application Context

This is a **scheduling application** for medical residency programs. All work must consider:
- Data security and privacy
- Audit trails for compliance
- Error handling that doesn't leak sensitive information
- Access control and authorization

---

***REMOVED******REMOVED*** Tech Stack

***REMOVED******REMOVED******REMOVED*** Backend

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

***REMOVED******REMOVED******REMOVED*** Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 14.0.4 | React framework with App Router |
| **React** | 18.2.0 | UI library |
| **TypeScript** | 5.0+ | Type-safe JavaScript |
| **TailwindCSS** | 3.3.0 | Utility-first CSS |
| **TanStack Query** | 5.17.0 | Data fetching and caching |

***REMOVED******REMOVED******REMOVED*** MCP Server (AI Integration)

| Technology | Version | Purpose |
|------------|---------|---------|
| **FastMCP** | 0.2.0+ | Model Context Protocol framework |
| **httpx** | 0.25.0+ | Async HTTP client for API calls |

***REMOVED******REMOVED******REMOVED*** Infrastructure

- **Docker** + **Docker Compose**: Containerization and orchestration
- **MCP Server Container**: AI tool integration (29+ scheduling tools)
- **Prometheus**: Metrics and monitoring
- **Grafana**: Dashboard visualization

---

***REMOVED******REMOVED*** Architecture Patterns

***REMOVED******REMOVED******REMOVED*** Layered Architecture

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

***REMOVED******REMOVED******REMOVED*** Directory Structure

```
backend/app/
├── api/                    ***REMOVED*** API routes (endpoints)
│   ├── deps.py            ***REMOVED*** Dependencies (auth, db session)
│   └── routes/            ***REMOVED*** Route modules
├── controllers/           ***REMOVED*** Request/response handling
├── services/              ***REMOVED*** Business logic layer
├── repositories/          ***REMOVED*** Data access layer (when used)
├── models/                ***REMOVED*** SQLAlchemy ORM models
├── schemas/               ***REMOVED*** Pydantic schemas (request/response)
├── core/                  ***REMOVED*** Config, security, Celery
├── db/                    ***REMOVED*** Database session management
├── scheduling/            ***REMOVED*** Scheduling engine & validator
├── resilience/            ***REMOVED*** Resilience framework
├── notifications/         ***REMOVED*** Alert delivery
└── analytics/             ***REMOVED*** Metrics and reporting
```

***REMOVED******REMOVED******REMOVED*** Key Architectural Rules

1. **Routes should be thin**: Delegate to controllers or services
2. **Business logic belongs in services**: Not in routes or models
3. **Use Pydantic schemas**: For all request/response validation
4. **Async all the way**: Use `async def` for all route handlers and database operations
5. **Dependency injection**: Use FastAPI's `Depends()` for database sessions and auth

---

***REMOVED******REMOVED*** Code Style Guidelines

***REMOVED******REMOVED******REMOVED*** Python (Backend)

***REMOVED******REMOVED******REMOVED******REMOVED*** General Style

- **PEP 8 compliant**: Follow Python style guide
- **Type hints required**: Use type hints for all function signatures
- **Docstrings required**: Use Google-style docstrings for all public functions/classes
- **Line length**: Max 100 characters (not 79)
- **Imports**: Organize as stdlib, third-party, local (separated by blank lines)

***REMOVED******REMOVED******REMOVED******REMOVED*** Example Function

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
    ***REMOVED*** Implementation here
    pass
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Naming Conventions

- **Classes**: `PascalCase` (e.g., `SwapExecutor`, `ACGMEValidator`)
- **Functions/Methods**: `snake_case` (e.g., `create_assignment`, `validate_compliance`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_HOURS_PER_WEEK`, `REDIS_URL`)
- **Private methods**: Prefix with `_` (e.g., `_calculate_utilization`)
- **Database models**: Singular (e.g., `Person`, `Assignment`, not `People`, `Assignments`)

***REMOVED******REMOVED******REMOVED******REMOVED*** Async/Await

```python
***REMOVED*** Always use async/await for database operations
async def get_person(db: AsyncSession, person_id: str) -> Optional[Person]:
    result = await db.execute(
        select(Person).where(Person.id == person_id)
    )
    return result.scalar_one_or_none()
```

***REMOVED******REMOVED******REMOVED*** TypeScript (Frontend)

- **Strict mode enabled**: All TS strict checks active
- **Explicit types**: Avoid `any`, use proper types or `unknown`
- **Component naming**: PascalCase for components
- **Hooks naming**: Start with `use` (e.g., `useScheduleData`)
- **Props interfaces**: Define explicit interfaces for all component props

---

***REMOVED******REMOVED*** Testing Requirements

***REMOVED******REMOVED******REMOVED*** General Testing Philosophy

**ALL code changes must include tests.** Do not commit code without corresponding test coverage.

***REMOVED******REMOVED******REMOVED*** Backend Testing (pytest)

***REMOVED******REMOVED******REMOVED******REMOVED*** Test Organization

```
backend/tests/
├── unit/                   ***REMOVED*** Unit tests (if separated)
├── integration/            ***REMOVED*** Integration tests
├── services/               ***REMOVED*** Service layer tests
├── conftest.py            ***REMOVED*** Pytest fixtures
└── test_*.py              ***REMOVED*** Test modules
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Required Test Coverage

1. **Service layer**: Unit tests for all business logic
2. **API endpoints**: Integration tests for all routes
3. **Models**: Test model relationships and constraints
4. **Edge cases**: Test error conditions, validation failures
5. **ACGME compliance**: All compliance rules must have tests

***REMOVED******REMOVED******REMOVED******REMOVED*** Example Test Structure

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
        ***REMOVED*** Verify database state changed

    async def test_execute_swap_validation_failure(self, db, invalid_swap):
        """Test swap execution fails with invalid request."""
        executor = SwapExecutor()

        with pytest.raises(ValueError, match="Invalid swap request"):
            await executor.execute_swap(db, invalid_swap)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Running Tests

```bash
***REMOVED*** Run all tests
cd backend
pytest

***REMOVED*** Run specific test file
pytest tests/test_swap_executor.py

***REMOVED*** Run with coverage
pytest --cov=app --cov-report=html

***REMOVED*** Run ACGME compliance tests only
pytest -m acgme

***REMOVED*** Run with verbose output
pytest -v
```

***REMOVED******REMOVED******REMOVED*** Frontend Testing (Jest + React Testing Library)

```bash
cd frontend

***REMOVED*** Run all tests
npm test

***REMOVED*** Run with coverage
npm run test:coverage

***REMOVED*** Run tests in CI mode
npm run test:ci

***REMOVED*** Type checking
npm run type-check

***REMOVED*** Linting
npm run lint
npm run lint:fix
```

***REMOVED******REMOVED******REMOVED*** Before Every Commit

**MANDATORY**: Run tests before committing:

```bash
***REMOVED*** Backend
cd backend && pytest

***REMOVED*** Frontend
cd frontend && npm test
```

If tests fail, **DO NOT COMMIT**. Fix the failing tests or the code first.

---

***REMOVED******REMOVED*** Security Requirements

***REMOVED******REMOVED******REMOVED*** Data Protection

Security is important for any application handling user data. Follow standard security best practices.

***REMOVED******REMOVED******REMOVED*** OPSEC/PERSEC Requirements (Military Medical Data)

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
- `*.dump`, `*.sql` - Database dumps
- `.env`, `.env.local` - Credentials

**For Demo/Test Data:**
```python
***REMOVED*** Use synthetic identifiers
residents = ["PGY1-01", "PGY2-01"]  ***REMOVED*** Not real names
faculty = ["FAC-PD", "FAC-APD"]      ***REMOVED*** Role-based IDs
```

See `docs/security/DATA_SECURITY_POLICY.md` for full policy.

***REMOVED******REMOVED******REMOVED*** Authentication & Authorization

1. **JWT-based auth**: httpOnly cookies (XSS-resistant)
2. **Password requirements**: Min 12 chars, complexity rules enforced
3. **Rate limiting**: Enforced on auth endpoints (see `backend/app/core/rate_limit.py`)
4. **Role-based access control (RBAC)**: 8 user roles (Admin, Coordinator, Faculty, Resident, Clinical Staff, RN, LPN, MSA)

***REMOVED******REMOVED******REMOVED*** Security Best Practices

1. **Never log sensitive data**: No passwords, tokens, or personal data in logs
2. **Input validation**: Use Pydantic schemas for all inputs
3. **SQL injection prevention**: Always use SQLAlchemy ORM, never raw SQL
4. **Path traversal prevention**: Validate file paths (see `backend/app/core/file_security.py`)
5. **Secret management**: Never commit secrets, use environment variables
6. **Error handling**: Don't leak information in error messages (use global exception handler)

***REMOVED******REMOVED******REMOVED*** Secret Validation

The application **refuses to start** if `SECRET_KEY` or `WEBHOOK_SECRET` are:
- Empty
- Less than 32 characters
- Using default values

Generate secrets with:
```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

***REMOVED******REMOVED******REMOVED*** File Upload Security

When handling file uploads:
- Validate file size limits
- Validate file types (whitelist, not blacklist)
- Scan file contents, not just extensions
- Prevent path traversal in filenames

---

***REMOVED******REMOVED*** Common Commands

***REMOVED******REMOVED******REMOVED*** Backend Development

```bash
***REMOVED*** Setup virtual environment
cd backend
python -m venv venv
source venv/bin/activate  ***REMOVED*** Windows: venv\Scripts\activate

***REMOVED*** Install dependencies
pip install -r requirements.txt

***REMOVED*** Database migrations
alembic upgrade head                    ***REMOVED*** Apply migrations
alembic downgrade -1                    ***REMOVED*** Rollback one migration
alembic revision --autogenerate -m "description"  ***REMOVED*** Create migration

***REMOVED*** Run development server
uvicorn app.main:app --reload

***REMOVED*** Run tests
pytest
pytest --cov=app --cov-report=html
pytest -m acgme  ***REMOVED*** Only ACGME tests

***REMOVED*** Celery (background tasks)
redis-server                            ***REMOVED*** Start Redis
../scripts/start-celery.sh both         ***REMOVED*** Start worker + beat
../scripts/start-celery.sh worker       ***REMOVED*** Worker only
../scripts/start-celery.sh beat         ***REMOVED*** Scheduler only
python verify_celery.py                 ***REMOVED*** Verify Celery status
```

***REMOVED******REMOVED******REMOVED*** Frontend Development

```bash
cd frontend

***REMOVED*** Install dependencies
npm install

***REMOVED*** Development server
npm run dev

***REMOVED*** Build for production
npm run build

***REMOVED*** Type checking
npm run type-check

***REMOVED*** Linting
npm run lint
npm run lint:fix

***REMOVED*** Testing
npm test
npm run test:coverage
npm run test:e2e  ***REMOVED*** Playwright E2E tests
```

***REMOVED******REMOVED******REMOVED*** Docker

```bash
***REMOVED*** Start all services (includes MCP server)
docker-compose up -d

***REMOVED*** View logs
docker-compose logs -f

***REMOVED*** Stop services
docker-compose down

***REMOVED*** Rebuild after code changes
docker-compose up -d --build

***REMOVED*** Run backend tests in container
docker-compose exec backend pytest

***REMOVED*** Access database
docker-compose exec db psql -U scheduler -d residency_scheduler
```

***REMOVED******REMOVED******REMOVED*** MCP Server (AI Integration)

```bash
***REMOVED*** View MCP server logs
docker-compose logs -f mcp-server

***REMOVED*** Test MCP server health
docker-compose exec mcp-server python -c \
  "from scheduler_mcp.server import mcp; print(f'Tools: {len(mcp.tools)}')"

***REMOVED*** Test API connectivity from MCP container
docker-compose exec mcp-server curl -s http://backend:8000/health

***REMOVED*** Development mode (with HTTP transport on port 8080)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d mcp-server

***REMOVED*** Rebuild MCP server after changes
docker-compose up -d --build mcp-server
```

***REMOVED******REMOVED******REMOVED*** Useful Database Queries

```bash
***REMOVED*** Connect to database
docker-compose exec db psql -U scheduler -d residency_scheduler

***REMOVED*** Common queries
SELECT COUNT(*) FROM assignments;
SELECT * FROM persons WHERE role = 'RESIDENT';
SELECT * FROM blocks WHERE date >= CURRENT_DATE LIMIT 10;
```

***REMOVED******REMOVED******REMOVED*** Load Testing

```bash
***REMOVED*** k6 Load Tests (from load-tests/ directory)
cd load-tests
npm install                           ***REMOVED*** Install dependencies
npm run test:smoke                    ***REMOVED*** Quick validation (1 min)
npm run test:load                     ***REMOVED*** Standard load test (5 min, 50 VUs)
npm run test:stress                   ***REMOVED*** Stress test (10 min, 200 VUs)

***REMOVED*** Run specific k6 scenarios
k6 run scenarios/api-baseline.js      ***REMOVED*** Establish latency baselines
k6 run scenarios/concurrent-users.js  ***REMOVED*** Multi-user simulation
k6 run scenarios/schedule-generation.js  ***REMOVED*** Schedule gen stress
k6 run scenarios/rate-limit-attack.js ***REMOVED*** Security testing

***REMOVED*** Custom k6 options
k6 run --vus 50 --duration 5m scenarios/concurrent-users.js

***REMOVED*** pytest Performance Tests (from backend/ directory)
cd backend
pytest -m performance                 ***REMOVED*** All performance tests
pytest -m "performance and not slow"  ***REMOVED*** Fast performance tests only
pytest tests/performance/test_acgme_load.py -v      ***REMOVED*** ACGME validation
pytest tests/performance/test_connection_pool.py -v ***REMOVED*** DB connection pool
pytest tests/performance/test_idempotency_load.py -v ***REMOVED*** Idempotency
pytest tests/resilience/test_resilience_load.py -v  ***REMOVED*** Resilience framework

***REMOVED*** Docker-based load testing
cd load-tests
npm run test:docker:smoke             ***REMOVED*** Run in container
npm run test:docker:load              ***REMOVED*** Full load test in container
```

---

***REMOVED******REMOVED*** Files and Patterns to Never Modify

***REMOVED******REMOVED******REMOVED*** Critical Files - Never Modify Without Explicit Permission

These files are foundational and changes could break the entire system:

***REMOVED******REMOVED******REMOVED******REMOVED*** Backend Core

- `backend/app/core/config.py` - Application configuration (except adding new config vars)
- `backend/app/core/security.py` - Authentication and password hashing
- `backend/app/db/base.py` - Database base configuration
- `backend/app/db/session.py` - Database session management
- `backend/app/main.py` - FastAPI application initialization

***REMOVED******REMOVED******REMOVED******REMOVED*** Database Models (Modify with Extreme Caution)

- `backend/app/models/*.py` - Any changes require Alembic migration
- **NEVER** modify models without creating a corresponding migration
- **NEVER** drop columns without migration and data backup plan

***REMOVED******REMOVED******REMOVED******REMOVED*** Migrations

- `backend/alembic/versions/*.py` - Never edit existing migrations
- **NEVER** delete or modify applied migrations
- **ONLY** create new migrations to change schema

***REMOVED******REMOVED******REMOVED******REMOVED*** Environment Files

- `.env` - Contains secrets (should never be committed)
- `.env.example` - Template for environment variables (can update)
- `docker-compose.yml` - Production Docker config (changes need careful testing)

***REMOVED******REMOVED******REMOVED*** Patterns to Avoid

1. **Don't bypass authentication**: Never add `allow_anonymous` or skip auth checks
2. **Don't disable rate limiting**: Keep `RATE_LIMIT_ENABLED=true` in production
3. **Don't use synchronous database calls**: Always use `async def` and `await`
4. **Don't hardcode secrets**: Use environment variables
5. **Don't expose sensitive data in API responses**: Use Pydantic schemas to control what's returned
6. **Don't modify ACGME compliance rules**: These are regulatory requirements

***REMOVED******REMOVED******REMOVED*** High-Risk Areas - Extra Caution Required

- **ACGME Compliance**: `backend/app/scheduling/acgme_validator.py`
- **Schedule Generation**: `backend/app/scheduling/engine.py`
- **Authentication**: `backend/app/api/routes/auth.py`
- **Resilience Framework**: `backend/app/resilience/*.py`

---

***REMOVED******REMOVED*** Development Workflow

***REMOVED******REMOVED******REMOVED*** Making Changes

1. **Understand the requirement** fully before coding
2. **Read relevant tests** to understand expected behavior
3. **Follow the layered architecture**: Route → Controller → Service → Repository → Model
4. **Write tests first** (TDD) or alongside implementation
5. **Run tests** before committing
6. **Update documentation** if adding new features

***REMOVED******REMOVED******REMOVED*** Adding a New Feature

Example: Adding a new API endpoint

1. **Create Pydantic schemas** (in `backend/app/schemas/`)
2. **Create/update model** (in `backend/app/models/`) + Alembic migration
3. **Create service** (in `backend/app/services/`)
4. **Create controller** (in `backend/app/controllers/`) if needed
5. **Create route** (in `backend/app/api/routes/`)
6. **Write tests** (in `backend/tests/`)
7. **Update API documentation** (docstrings + `docs/api/`)

***REMOVED******REMOVED******REMOVED*** Database Changes

**Always use Alembic migrations:**

```bash
***REMOVED*** 1. Modify model in backend/app/models/
***REMOVED*** 2. Create migration
cd backend
alembic revision --autogenerate -m "Add new_field to Person model"

***REMOVED*** 3. Review the generated migration in alembic/versions/
***REMOVED*** 4. Edit if needed (autogenerate isn't perfect)
***REMOVED*** 5. Test migration
alembic upgrade head

***REMOVED*** 6. Test rollback
alembic downgrade -1
alembic upgrade head

***REMOVED*** 7. Commit both model change and migration
```

***REMOVED******REMOVED******REMOVED*** Debugging

```bash
***REMOVED*** Backend debugging
import pdb; pdb.set_trace()  ***REMOVED*** Add breakpoint

***REMOVED*** View logs
docker-compose logs -f backend

***REMOVED*** Database inspection
docker-compose exec db psql -U scheduler -d residency_scheduler
\dt  ***REMOVED*** List tables
\d persons  ***REMOVED*** Describe table

***REMOVED*** Redis inspection
docker-compose exec redis redis-cli
KEYS *
GET some_key
```

---

***REMOVED******REMOVED*** Debugging & Troubleshooting

***REMOVED******REMOVED******REMOVED*** Systematic Debugging Workflow

Follow this four-phase approach for complex issues:

**Phase 1: Exploration (DO NOT FIX YET)**
```
"Read the scheduling conflict resolution logic in scheduler.py and examine
the error logs. Don't fix anything yet, just understand the system."
```

**Phase 2: Planning with Extended Thinking**
Use these phrases to trigger deeper reasoning (in order of computational budget):
- `"think"` < `"think hard"` < `"think harder"` < `"ultrathink"`

```
"Think hard about what could cause residents to be double-booked in
overlapping rotations. Create a hypothesis list with root cause analysis."
```

**Phase 3: Implementation**
After approving the plan:
```
"Implement your solution for the rotation overlap bug. After each major
change, verify the logic handles edge cases like overnight shifts."
```

**Phase 4: Commit and Document**
```
"Commit these changes and update CHANGELOG.md with what was fixed and why."
```

***REMOVED******REMOVED******REMOVED*** Test-Driven Debugging (TDD)

For reproducible bugs, use TDD workflow:

1. **Write failing test first**:
   ```
   "Write test cases that reproduce the scheduling conflict bug reported in
   issue ***REMOVED***247. Be explicit that we're doing TDD—don't create mock
   implementations. The tests should fail with the same error."
   ```

2. **Confirm failure**:
   ```
   "Run the tests and confirm they fail. Don't write any implementation code yet."
   ```

3. **Fix until green**:
   ```
   "Now fix the code to make all tests pass. Don't modify the tests.
   Keep iterating until everything passes."
   ```

4. **Verify independently** (optional but recommended):
   ```
   "Use a subagent to verify this implementation isn't overfitting to the
   tests and handles real-world scheduling scenarios."
   ```

***REMOVED******REMOVED******REMOVED*** Debugging Slash Commands

| Command | Purpose |
|---------|---------|
| `/project:debug-scheduling [issue]` | Debug scheduling conflicts and assignment issues |
| `/project:debug-tdd [bug]` | Test-driven debugging workflow |
| `/project:debug-explore [symptom]` | Exploration-first debugging for unclear issues |

***REMOVED******REMOVED******REMOVED*** Context Management for Long Sessions

When debugging spans multiple interactions:

1. **Document & Clear Pattern**:
   ```bash
   ***REMOVED*** When context gets large (check with /context)
   ***REMOVED*** 1. Create debug session notes
   cat > debug-session-notes.md << 'EOF'
   ***REMOVED*** Debug Session: [Issue]
   ***REMOVED******REMOVED*** Bug: [description]
   ***REMOVED******REMOVED*** Hypothesis: [current theory]
   ***REMOVED******REMOVED*** Tried: [what we've done]
   ***REMOVED******REMOVED*** Findings: [what we learned]
   ***REMOVED******REMOVED*** Next Steps: [what to do next]
   EOF

   ***REMOVED*** 2. Use /clear to reset context
   ***REMOVED*** 3. Resume: "Read debug-session-notes.md and continue debugging"
   ```

2. **Avoid `/compact`** - Manual "Document & Clear" is more reliable

***REMOVED******REMOVED******REMOVED*** Strategic Logging Injection

Add diagnostic instrumentation before fixing:

```python
***REMOVED*** Add to relevant function temporarily
import logging
logger = logging.getLogger(__name__)

logger.info(f"DEBUG: Input parameters: {locals()}")
logger.info(f"DEBUG: Validation check result: {result}")
logger.info(f"DEBUG: Assignment decision: {decision}")
```

Run and collect:
```bash
LOG_LEVEL=DEBUG pytest tests/scheduling/test_debug_*.py -v -s 2>&1 | tee debug_output.log
```

***REMOVED******REMOVED******REMOVED*** Known Gotchas (Common Debugging Traps)

| Issue | Cause | Solution |
|-------|-------|----------|
| **Timezone mismatch** | Scheduler runs UTC, displays local (HST) | Always convert times explicitly |
| **Work hour reset** | Limits reset at midnight LOCAL, not UTC | Check `backend/app/services/constraints/acgme.py` |
| **Race conditions** | Missing `with_for_update()` on DB queries | Add row locking for concurrent operations |
| **Double-booking** | Missing overlap check | Check `backend/app/scheduling/conflicts/` |
| **Test isolation** | Tests not using fresh fixtures | Verify `conftest.py` setup |

***REMOVED******REMOVED******REMOVED*** Multi-Claude Parallel Debugging

For complex multi-faceted bugs:

**Terminal 1**: "Investigate why residents are being double-booked"
**Terminal 2**: "Analyze work hour calculation for off-by-one errors"
**Terminal 3**: "Review recent scheduler commits for regressions"

Cycle through terminals to approve permissions and synthesize findings.

***REMOVED******REMOVED******REMOVED*** Checkpoint Commits

Before risky changes:
```bash
git stash push -m "WIP: before debugging [issue]"
```

Restore if needed:
```bash
git stash pop
```

***REMOVED******REMOVED******REMOVED*** Course Correction Tools

- **Escape** - Interrupt mid-execution to redirect
- **Double-tap Escape** - Jump back, edit previous prompt, try different approach
- **"Undo changes"** - Revert and try alternative fix
- **"Make a plan first"** - Stop coding, think through approach

---

***REMOVED******REMOVED*** AI Rules of Engagement

These rules apply to Claude Code, Codex, and any AI agent working in this repo.

> **Full Documentation:**
> - [AI Rules of Engagement](docs/development/AI_RULES_OF_ENGAGEMENT.md) - Complete rules with environment detection
> - [AI Interface Guide](docs/admin-manual/ai-interface-guide.md) - Web vs CLI comparison for clinicians
> - [CI/CD Troubleshooting](docs/development/CI_CD_TROUBLESHOOTING.md) - Error codes, fixes, and LLM-specific patterns
> - [Debugging Workflow Guide](docs/development/DEBUGGING_WORKFLOW.md) - Comprehensive debugging methodology

***REMOVED******REMOVED******REMOVED*** Core Policy

- Full autonomy for local work is allowed.
- All changes destined for GitHub must go through a PR.
- No direct commits or pushes to `main` / `origin/main` unless explicitly approved.

***REMOVED******REMOVED******REMOVED*** Environment Detection (Required)

Before making changes, AI agents MUST:
1. **Identify interface type** (Web App = Suggestion Mode, CLI/IDE = Direct Edit Mode)
2. **Check git context** (`git branch --show-current`, `git status`)
3. **Adapt behavior** - If on main, create a feature branch first

***REMOVED******REMOVED******REMOVED*** Branching and PR Workflow

1) Create a feature branch off `origin/main` for any change.
2) Commit changes on the feature branch only.
3) Push the feature branch to GitHub.
4) Open a PR and wait for approval before merging.

***REMOVED******REMOVED******REMOVED*** Guardrails

- Do not use `--allow-unrelated-histories` unless explicitly approved.
- Avoid merge commits on `main`; use rebase for sync.
- If histories diverge or an orphaned branch is detected, stop and ask.

***REMOVED******REMOVED******REMOVED*** Required Checks

- Run repo-standard linters before PR:
  - Backend: `ruff check . --fix` and `ruff format .`
  - Frontend: `npm run lint:fix`
- Ensure CI passes before merge.

***REMOVED******REMOVED******REMOVED*** Exceptions

- Emergency fixes can be pushed directly to `main` **only** with explicit approval.

---

***REMOVED******REMOVED*** Key Concepts

***REMOVED******REMOVED******REMOVED*** ACGME Compliance Rules

Must be validated for all schedules:

1. **80-Hour Rule**: Maximum 80 hours/week, averaged over rolling 4-week periods
2. **1-in-7 Rule**: One 24-hour period off every 7 days
3. **Supervision Ratios**:
   - PGY-1: 1 faculty per 2 residents
   - PGY-2/3: 1 faculty per 4 residents

***REMOVED******REMOVED******REMOVED*** Schedule Structure

- **Academic Year**: 365 days
- **Blocks**: 730 blocks per year (365 days × AM/PM sessions)
- **Rotations**: Templates (clinic, inpatient, procedures, conference)
- **Assignments**: Person + Block + Rotation

***REMOVED******REMOVED******REMOVED*** Resilience Framework

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
- **Recovery Distance**: Minimum edits to recover from n-1 shocks (operations research)

**Observability & Hardening:**
- **Pre-Solver Validation**: Detects infeasible constraints before solver runs
- **OpenTelemetry Export**: OTLP/Jaeger/Zipkin trace export for distributed tracing
- **Circuit Breaker Health**: Breaker status integrated into `/health` endpoint

See `docs/architecture/cross-disciplinary-resilience.md` for detailed documentation.

***REMOVED******REMOVED******REMOVED*** Swap System

Faculty can request schedule swaps:

- **Types**: One-to-one swap, Absorb (give away shift)
- **Auto-matching**: Find compatible swap candidates
- **Validation**: Ensure swaps maintain ACGME compliance
- **Rollback**: 24-hour window to reverse a swap

***REMOVED******REMOVED******REMOVED*** Background Tasks (Celery)

Used for:
- Resilience health checks (every 15 min)
- N-1/N-2 contingency analysis (every 24 hours)
- Conflict detection after leave approval
- Email notifications
- Schedule metrics calculation

***REMOVED******REMOVED******REMOVED*** Slot-Type Invariants (Credential Requirements)

Convert recurring admin requirements into binary schedule invariants. Each slot type defines hard and soft credential requirements.

**Invariant Structure:**
```python
invariant_catalog = {
    "inpatient_call": {
        "hard": ["HIPAA", "Cyber_Training", "AUP", "Chaperone", "N95_Fit"],
        "soft": [{"name": "expiring_soon", "window_days": 14, "penalty": 3}]
    },
    "peds_clinic": {
        "hard": ["Flu_Vax", "Tdap"]
    },
    "procedures_half_day": {
        "hard": ["BBP_Module", "Sharps_Safety"]
    }
}
```

**Eligibility Logic:**
```python
def is_eligible(person_id: str, slot_type: str, date: date) -> tuple[bool, int]:
    """Check if person meets slot requirements.

    Returns:
        (eligible: bool, penalty: int) - False if hard constraint fails
    """
    reqs = invariant_catalog.get(slot_type, {})

    ***REMOVED*** Hard constraints - must pass all
    for req in reqs.get("hard", []):
        cred = get_credential(person_id, req)
        if not cred or not cred.is_valid or cred.expires_at < date:
            return False, 0

    ***REMOVED*** Soft constraints - accumulate penalties
    penalty = 0
    for soft in reqs.get("soft", []):
        if soft["name"] == "expiring_soon":
            if any_credential_expiring(person_id, soft["window_days"], date):
                penalty += soft["penalty"]

    return True, penalty
```

**Common Credential Categories:**
| Category | Examples | Typical Validity |
|----------|----------|------------------|
| Annual Training | JKO Cyber, HIPAA, AUP | 12 months |
| Immunizations | Flu, Tdap, Hep B | Varies |
| Safety | N95 Fit, BBP, Chaperone | 12-24 months |
| Procedures | BLS, ACLS, PALS, NRP | 24 months |

**Dashboard Integration:**
- "Next block hard failures" - Who can't work scheduled slots
- "Expiring in 30/60/90 days" - Proactive renewal reminders
- "Grace period active" - Track temporary exceptions

---

***REMOVED******REMOVED*** Common Pitfalls and How to Avoid Them

***REMOVED******REMOVED******REMOVED*** 1. N+1 Query Problem

**Bad:**
```python
***REMOVED*** Fetches persons, then queries assignments for each person (N+1 queries)
persons = await db.execute(select(Person))
for person in persons.scalars():
    assignments = await db.execute(
        select(Assignment).where(Assignment.person_id == person.id)
    )
```

**Good:**
```python
***REMOVED*** Single query with join
result = await db.execute(
    select(Person).options(selectinload(Person.assignments))
)
persons = result.scalars().all()
```

***REMOVED******REMOVED******REMOVED*** 2. Missing Type Hints

**Bad:**
```python
def calculate_hours(assignments):  ***REMOVED*** No types
    return sum(a.hours for a in assignments)
```

**Good:**
```python
def calculate_hours(assignments: list[Assignment]) -> float:
    """Calculate total hours from assignments."""
    return sum(a.hours for a in assignments)
```

***REMOVED******REMOVED******REMOVED*** 3. Leaking Sensitive Data in Errors

**Bad:**
```python
raise HTTPException(
    status_code=400,
    detail=f"Person {person_id} has email {person.email}"  ***REMOVED*** Sensitive data leaked!
)
```

**Good:**
```python
raise HTTPException(
    status_code=400,
    detail="Invalid person data"  ***REMOVED*** Generic message
)
***REMOVED*** Log detailed error server-side only
logger.error(f"Validation failed for person {person_id}", exc_info=True)
```

***REMOVED******REMOVED******REMOVED*** 4. Modifying Models Without Migrations

**Bad:**
```python
***REMOVED*** Just changing the model
class Person(Base):
    ***REMOVED*** Added new field but no migration
    middle_name: str = Column(String, nullable=True)
```

**Good:**
```python
***REMOVED*** 1. Change model
class Person(Base):
    middle_name: str = Column(String, nullable=True)

***REMOVED*** 2. Create migration
***REMOVED*** alembic revision --autogenerate -m "Add middle_name to Person"

***REMOVED*** 3. Apply migration
***REMOVED*** alembic upgrade head
```

---

***REMOVED******REMOVED*** Documentation Updates

When making changes, update relevant documentation:

- **API changes**: Update docstrings + `docs/api/*.md`
- **New features**: Update `README.md` + user guide
- **Configuration changes**: Update `.env.example` + `docs/admin-manual/configuration.md`
- **Database changes**: Document in migration message

---

***REMOVED******REMOVED*** Getting Help

***REMOVED******REMOVED******REMOVED*** Documentation

- **README.md**: Project overview and quick start
- **docs/**: Comprehensive documentation
  - `docs/architecture/`: System design
  - `docs/api/`: API reference
  - `docs/user-guide/`: User documentation
  - `docs/development/`: Development guides
  - `docs/admin-manual/`: Administrator guides (includes AI Interface Guide)
- **HUMAN_TODO.md**: Tasks requiring human action

***REMOVED******REMOVED******REMOVED*** AI-Specific Documentation

- **[Agent Skills Reference](docs/development/AGENT_SKILLS.md)**: Complete guide to AI agent skills (12 skills)
- **[AI Agent User Guide](docs/guides/AI_AGENT_USER_GUIDE.md)**: Skills, MCP tools, and Claude Code setup
- **[AI Interface Guide](docs/admin-manual/ai-interface-guide.md)**: Web vs CLI comparison for clinician administrators
- **[AI Rules of Engagement](docs/development/AI_RULES_OF_ENGAGEMENT.md)**: Complete rules with environment detection
- **[CI/CD Troubleshooting](docs/development/CI_CD_TROUBLESHOOTING.md)**: Error codes, auto-fixes, and LLM failure patterns
- **[Git Safe Sync Checklist](docs/development/CLAUDE_GIT_SAFE_SYNC_CHECKLIST.md)**: Daily sync procedures

***REMOVED******REMOVED******REMOVED*** Technical Deep Dives

- **[Solver Algorithm](docs/architecture/SOLVER_ALGORITHM.md)**: Comprehensive scheduling engine documentation (constraints, solvers, optimization)
- **[MCP Placeholder Plan](docs/planning/MCP_PLACEHOLDER_IMPLEMENTATION_PLAN.md)**: Implementation roadmap for MCP tool integrations
- **[Security Pattern Audit](docs/security/SECURITY_PATTERN_AUDIT.md)**: Security architecture review and OWASP compliance
- **[Cross-Disciplinary Resilience](docs/architecture/cross-disciplinary-resilience.md)**: Resilience framework concepts (queuing theory, epidemiology, materials science)

***REMOVED******REMOVED******REMOVED*** Agent Skills (`.claude/skills/`)

AI agents automatically load skills for specialized tasks:

| Skill | Purpose |
|-------|---------|
| `acgme-compliance` | ACGME regulatory expertise |
| `code-review` | Review generated code |
| `constraint-preflight` | Verify constraints are registered before commit |
| `database-migration` | Alembic migration expertise |
| `pr-reviewer` | Pull request review |
| `security-audit` | Healthcare/military security |
| `test-writer` | Generate pytest/Jest tests |

See full list: [Agent Skills Reference](docs/development/AGENT_SKILLS.md)

***REMOVED******REMOVED******REMOVED*** Code References

- Look for similar patterns in existing code
- Check tests to understand expected behavior
- Review `docs/planning/TODO_TRACKER.md` for implementation examples

***REMOVED******REMOVED******REMOVED*** Questions to Ask Yourself

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

***REMOVED******REMOVED*** Summary Checklist for All Work

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
