# Automated Code Fixer - Reference Guide

## Quick Diagnostic Commands

```bash
# Backend diagnostics
cd /home/user/Autonomous-Assignment-Program-Manager/backend
pytest --tb=short -q                    # Quick test run
pytest --lf                              # Re-run last failures
ruff check app/ tests/ --fix            # Auto-fix linting
black app/ tests/ --check               # Format check
mypy app/ --python-version 3.11         # Type check

# Frontend diagnostics
cd /home/user/Autonomous-Assignment-Program-Manager/frontend
npm test                                 # Jest tests
npm run type-check                      # TypeScript check
npm run lint                            # ESLint check
```

## Common Fix Patterns

### Pattern 1: Async/Await Fixes

**Problem:**
```python
# Missing await on async function
def get_person(db: Session, person_id: str):
    result = db.execute(select(Person).where(Person.id == person_id))
    return result.scalar_one_or_none()
```

**Fix:**
```python
async def get_person(db: AsyncSession, person_id: str) -> Optional[Person]:
    result = await db.execute(select(Person).where(Person.id == person_id))
    return result.scalar_one_or_none()
```

### Pattern 2: Type Annotation Fixes

**Problem:**
```python
def calculate_hours(assignments):
    return sum(a.hours for a in assignments)
```

**Fix:**
```python
def calculate_hours(assignments: list[Assignment]) -> float:
    """Calculate total hours from assignments."""
    return sum(a.hours for a in assignments)
```

### Pattern 3: N+1 Query Fixes

**Problem:**
```python
persons = await db.execute(select(Person))
for person in persons.scalars():
    assignments = await db.execute(
        select(Assignment).where(Assignment.person_id == person.id)
    )
```

**Fix:**
```python
result = await db.execute(
    select(Person).options(selectinload(Person.assignments))
)
persons = result.scalars().all()
```

### Pattern 4: Security Fixes

**Problem - Hardcoded Secrets:**
```python
SECRET_KEY = "hardcoded-secret-123"
```

**Fix:**
```python
from app.core.config import settings
SECRET_KEY = settings.SECRET_KEY
```

**Problem - SQL Injection:**
```python
query = f"SELECT * FROM users WHERE id = '{user_id}'"
```

**Fix:**
```python
result = await db.execute(
    select(User).where(User.id == user_id)
)
```

### Pattern 5: Error Handling Fixes

**Problem - Leaking Sensitive Data:**
```python
raise HTTPException(
    status_code=400,
    detail=f"Person {person_id} has email {person.email}"
)
```

**Fix:**
```python
logger.error(f"Validation failed for person {person_id}", exc_info=True)
raise HTTPException(
    status_code=400,
    detail="Invalid person data"
)
```

### Pattern 6: Import Organization

**Problem:**
```python
from app.models import Person
import os
from sqlalchemy import select
from datetime import date
```

**Fix:**
```python
import os
from datetime import date

from sqlalchemy import select

from app.models import Person
```

### Pattern 7: Test Fixture Fixes

**Problem:**
```python
def test_create_person():
    person = Person(name="Test", email="test@test.com")
    db.add(person)
    db.commit()
```

**Fix:**
```python
@pytest.fixture
def test_person(db: AsyncSession):
    person = Person(name="Test", email="test@test.com")
    db.add(person)
    db.commit()
    yield person
    db.delete(person)
    db.commit()

async def test_create_person(test_person):
    assert test_person.id is not None
```

## Quality Gate Thresholds

| Gate | Threshold | Action on Fail |
|------|-----------|----------------|
| Test Pass Rate | 100% | Block fix |
| Code Coverage | >= 70% | Block fix |
| Type Coverage | 100% public APIs | Block fix |
| Security Warnings | 0 critical | Block fix |
| Linting Errors | 0 | Block fix |
| Linting Warnings | < 10 new | Warning |

## Escalation Decision Tree

```
Is the fix...
├── Changing database models? → ESCALATE
├── Touching auth/security? → ESCALATE
├── Affecting ACGME logic? → ESCALATE
├── Requiring new dependencies? → ESCALATE (if production)
├── Taking > 30 minutes? → ESCALATE
├── Unclear on requirements? → ESCALATE
└── Otherwise → PROCEED with fix
```

## File Patterns by Issue Type

| Issue Type | Files to Check |
|------------|----------------|
| Test Failures | `tests/`, corresponding `app/` code |
| Type Errors | File mentioned in mypy output |
| Import Errors | Check `__init__.py` files |
| Async Issues | Service layer files |
| Security | `app/core/`, `app/api/routes/` |
| Linting | Auto-fixable in most cases |

## Commit Message Format

```
fix: Brief description of what was fixed

- Root cause: [what was wrong]
- Solution: [what was changed]
- Tests: [added/modified/unchanged]
```

## Emergency Rollback

If a fix causes cascading failures:

```bash
# Revert last commit
git revert HEAD --no-commit

# Check status
git status

# Run tests to confirm rollback worked
pytest --tb=short

# If tests pass, commit the revert
git commit -m "revert: Rollback failed fix for [issue]"
```
