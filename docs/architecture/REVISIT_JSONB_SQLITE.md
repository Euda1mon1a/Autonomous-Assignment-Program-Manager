# Architecture Decision: JSONB vs SQLite Test Infrastructure

**Status:** Open for review
**Date:** 2026-01-18
**Context:** Phase 4 Technical Debt

---

## Summary

The `assignment_backups` table uses PostgreSQL JSONB for storing original assignment data, enabling complete rollback capability. However, tests historically use SQLite for speed, creating a test/production mismatch.

## Background

### Why JSONB was chosen for production

The `assignment_backups.original_data_json` column stores complete assignment state for rollback:

```python
original_data_json = {
    "person_id": "uuid",
    "assignment_date": "2026-01-18",
    "rotation_id": "uuid",
    "time_of_day": "AM",
    # ... all fields needed to recreate the assignment
}
```

**Benefits:**
1. **Schema evolution** - If Assignment model changes, old backups still work
2. **Wholesale restore** - No need to query individual fields, just INSERT the blob
3. **Audit completeness** - Captures exact state, not just foreign keys
4. **Flexibility** - Different assignment types can have different structures

### Why SQLite in tests

SQLite has been used in tests for:
1. **Speed** - No server startup, in-memory execution
2. **Isolation** - Each test gets fresh DB
3. **CI simplicity** - No PostgreSQL container needed for unit tests

### The conflict

SQLite doesn't support JSONB operations. Tests that touch backup functionality fail on SQLite.

## Relationship to CP-SAT Solver

**Key insight:** JSONB is completely irrelevant to CP-SAT performance.

The OR-Tools CP-SAT solver operates entirely in memory on Python objects:

```
PostgreSQL → Python objects → CP-SAT solver → Python solution → PostgreSQL
```

The solver works with:
- `ortools.sat.python.cp_model.CpModel`
- IntVar, BoolVar decision variables
- Constraint objects (AddExactlyOne, AddImplication, etc.)

JSONB is only used for the backup/restore layer, which happens before/after solving.

## Options Analysis

| Approach | Pros | Cons |
|----------|------|------|
| **Skip JSONB tests on SQLite** | Simple, current approach | Reduced coverage for backup code |
| **testcontainers (PG in Docker)** | Full compatibility | Slower CI, more setup complexity |
| **Mock backup layer in unit tests** | Fast unit tests | Doesn't test real backup behavior |
| **Hybrid approach** | Best of both worlds | More test infrastructure to maintain |

## Recommended Approach

**Hybrid approach:**

1. **Unit tests** - Mock the backup layer
   - Fast execution
   - Test business logic in isolation
   - Use SQLite for all non-JSONB operations

2. **Integration tests** - Use testcontainers with PostgreSQL
   - Full compatibility
   - Tests real backup/restore behavior
   - Run in CI with `pytest -m integration`

3. **CI pipeline** - Run both tiers
   - Unit tests first (fast feedback)
   - Integration tests second (thorough validation)

## Implementation Plan

### Phase 1: Add test markers

```python
# conftest.py
import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "requires_postgres: mark test as requiring PostgreSQL"
    )

@pytest.fixture(scope="session")
def postgres_db():
    """Provide PostgreSQL via testcontainers."""
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:15") as postgres:
        yield postgres.get_connection_url()
```

### Phase 2: Mark JSONB-dependent tests

```python
@pytest.mark.requires_postgres
def test_backup_restore_cycle():
    """Test backup and restore with real JSONB."""
    ...
```

### Phase 3: Update CI

```yaml
# .github/workflows/test.yml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest -m "not requires_postgres"

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
    steps:
      - run: pytest -m requires_postgres
```

## Files Affected

- `backend/tests/conftest.py` - Add testcontainers fixture
- `backend/pyproject.toml` - Add testcontainers dependency
- `.github/workflows/test.yml` - Split test jobs
- Tests using `assignment_backups` - Add `requires_postgres` marker

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-18 | Documented for future review | Phase 4 focus was on collection errors |

## Open Questions

1. Should we add testcontainers as a dev dependency now?
2. What's the CI time budget for integration tests?
3. Should we mock JSONB in SQLite tests (using JSON column type)?

---

*This document is part of the Backend Priority Roadmap Phase 4 work.*
