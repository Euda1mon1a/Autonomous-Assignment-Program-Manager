# Claude Code Skills Testing Patterns - Part 1 of 3: Foundations

**Document Purpose:** Comprehensive reference for testing Claude Code skills in the Residency Scheduler project.

**Last Updated:** 2025-12-30
**Author:** G2_RECON (SEARCH_PARTY Operation)

**Part 1 of 3:** Executive Summary, Current Testing Landscape, and Framework Overview
**See Also:** [Part 2 - Patterns](skills-testing-patterns-02-patterns.md) | [Part 3 - Implementation](skills-testing-patterns-03-implementation.md)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Testing Landscape](#current-testing-landscape)
3. [Skill Categories & Testing Approaches](#skill-categories--testing-approaches)
4. [Testing Framework Overview](#testing-framework-overview)

---

## Executive Summary

### Key Findings (PERCEPTION + INVESTIGATION)

**Project Testing Maturity:** HIGH
- 175+ test files across `backend/tests/`
- Comprehensive pytest infrastructure with fixtures and parametrization
- CI/CD integration with GitHub Actions (13 workflows)
- Coverage reporting via Codecov
- Segregated test organization (unit, integration, performance, resilience, scenarios)

**Skills Testing Coverage:** PARTIAL
- 15 skills with dedicated testing frameworks (test-writer, python-testing-patterns, etc.)
- Pre-flight validation for constraints (constraint-preflight skill)
- Scenario-based testing for complex operations (test-scenario-framework)
- NO dedicated skill execution tests (skills themselves are not being tested)
- Missing: Skill composition validation, MCP tool integration tests

**Critical Gaps Identified:**
1. **Skill Execution Tests** - Skills are documented but not tested for correctness
2. **MCP Tool Integration** - No tests verifying MCP tools work correctly with skills
3. **Skill Composition** - No tests for parallel/serialized skill execution
4. **Error Handling** - Missing tests for skill failure scenarios
5. **CI Integration** - Skills not validated in CI/CD pipeline

---

## Current Testing Landscape

### (PERCEPTION Lens)

#### Test Directory Structure

```
backend/tests/
├── conftest.py                      # Shared pytest fixtures (100+ lines)
├── __init__.py
├── TEST_SUMMARY.md
├── TEST_EXPANSION_SUMMARY.md
├── api/                            # API endpoint tests
├── auth/                           # Authentication tests
├── autonomous/                     # Autonomous operation tests (NEW)
├── constraints/                    # Constraint validation tests
├── factories/                      # Test data factories
├── health/                         # Health check tests
├── integration/                    # Integration tests (27 modules)
├── performance/                    # Performance & load tests
├── resilience/                     # Resilience framework tests
├── routes/                         # API route tests
├── scenarios/                      # Scenario-based tests
├── e2e/                           # End-to-end tests
└── [140+ individual test files]

```

#### Test Markers (pytest.ini)

```ini
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    acgme: marks tests related to ACGME compliance
    performance: marks tests as performance/load tests
```

#### Available Fixtures (conftest.py)

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `db` | function | Fresh in-memory SQLite for each test |
| `client` | function | TestClient with DB override |
| `admin_user` | function | Pre-authenticated admin user |
| `auth_headers` | function | Bearer token headers |
| `sample_resident` | function | Test resident person |
| `sample_faculty` | function | Test faculty person |

#### CI/CD Workflow Integration

```yaml
# .github/workflows/ci.yml - Primary testing pipeline
Backend Tests:
  - Python 3.11
  - PostgreSQL 15 service
  - Coverage reporting to Codecov
  - Artifact upload (HTML reports)

Frontend Tests:
  - Node 20
  - Jest with coverage
  - Jest XML reports

Triggers:
  - Pull requests to main/master/develop
  - Pushes to main/master/claude/** branches
```

---

## Skill Categories & Testing Approaches

### (INVESTIGATION + ARCANA Lenses)

#### Skill Type Matrix

| Skill Category | Count | Testing Approach | Examples |
|---|---|---|---|
| **Knowledge Skills** | 12 | Documentation, reference validation | acgme-compliance, code-review, docker-containerization |
| **Workflow Skills** | 8 | Scenario + integration tests | COMPLIANCE_VALIDATION, SCHEDULING, SWAP_EXECUTION |
| **Framework Skills** | 5 | Pattern validation + examples | test-scenario-framework, python-testing-patterns, test-writer |
| **Development Skills** | 10 | Pre-flight checks + code analysis | constraint-preflight, automated-code-fixer, lint-monorepo |
| **Meta Skills** | 4 | Context management + orchestration | MCP_ORCHESTRATION, CORE, context-aware-delegation, startup |

#### Knowledge Skills (Reference-Based)

**Examples:** `acgme-compliance`, `code-review`, `docker-containerization`, `security-audit`

**How They're Currently Tested:**
1. By human review of documentation correctness
2. By application of recommendations in actual code review
3. By CI validation when rules are enforced

**Testing Gaps:**
- No automated validation that knowledge is current
- No test that recommendations are correct
- No verification that examples compile/execute

**Testing Strategy:**
```python
# Example: Test that ACGME compliance knowledge is current
@pytest.mark.skill
def test_acgme_compliance_skill_knowledge():
    """Verify ACGME compliance skill references are current."""
    from .claude.skills.acgme_compliance import SKILL

    # Load skill documentation
    skill_doc = read_skill_doc("acgme-compliance")

    # Validate: 80-hour rule cited correctly
    assert "80 hours" in skill_doc
    assert "4-week rolling average" in skill_doc

    # Validate: 1-in-7 rule present
    assert "one 24-hour period" in skill_doc or "1-in-7" in skill_doc

    # Validate: supervision ratios documented
    assert "PGY-1" in skill_doc and ("1:2" in skill_doc or "2:1" in skill_doc)
```

#### Workflow Skills (Execution-Based)

**Examples:** `COMPLIANCE_VALIDATION`, `SCHEDULING`, `SWAP_EXECUTION`

**How They're Currently Tested:**
1. By running actual backend operations they orchestrate
2. By scenario-based testing (test-scenario-framework)
3. By integration tests validating API operations

**Testing Gaps:**
- No tests that skills are invoked correctly
- No validation of skill error handling
- Missing rollback/recovery tests

**Testing Strategy:**
```python
# Example: Test workflow skill execution
@pytest.mark.skill
async def test_swap_execution_workflow(db_session):
    """Verify SWAP_EXECUTION skill orchestrates swap correctly."""
    from app.skills.swap_execution import SwapExecutionWorkflow

    # Setup: Create valid swap request
    swap = create_test_swap(db_session, ...)

    # Execute: Run the skill workflow
    workflow = SwapExecutionWorkflow(db_session)
    result = await workflow.execute(swap)

    # Validate: Verify workflow outputs
    assert result.status == "completed"
    assert result.audit_trail is not None
    assert result.rollback_capability is not None
```

#### Framework Skills (Pattern + Template Validation)

**Examples:** `test-scenario-framework`, `python-testing-patterns`, `test-writer`

**How They're Currently Tested:**
1. Through examples in skill documentation
2. By observing if generated tests pass
3. Manual verification of generated code patterns

**Testing Gaps:**
- No tests that generated tests are syntactically correct
- No validation of test coverage targets
- Missing scenario composition validation

**Testing Strategy:**
```python
# Example: Test framework skill generates valid tests
@pytest.mark.skill
def test_test_writer_generates_valid_pytest():
    """Verify test-writer skill generates correct pytest code."""
    from .claude.skills.test_writer import TestWriter

    # Define source code to test
    source = """
    def calculate_hours(assignments: list[Assignment]) -> float:
        return sum(a.hours for a in assignments)
    """

    # Generate tests using skill
    writer = TestWriter()
    tests = writer.generate_tests(source)

    # Validate: Tests are syntactically correct
    compile(tests, '<string>', 'exec')

    # Validate: Tests include happy path
    assert "def test_" in tests
    assert "calculate_hours" in tests
```

#### Development Skills (Pre-Flight / Analysis)

**Examples:** `constraint-preflight`, `automated-code-fixer`, `lint-monorepo`

**How They're Currently Tested:**
1. By running verification scripts
2. By checking CI/CD output
3. By manual inspection of fixes

**Testing Gaps:**
- No automated validation of pre-flight checks
- Missing test for all error detection scenarios
- No regression tests for fixes

**Testing Strategy:**
```python
# Example: Test constraint-preflight detects unregistered constraints
@pytest.mark.skill
def test_constraint_preflight_detects_unregistered():
    """Verify constraint-preflight skill detects missing registrations."""
    from .claude.skills.constraint_preflight import ConstraintPreflight

    # Create unregistered constraint scenario
    create_unregistered_constraint()

    # Run pre-flight check
    preflight = ConstraintPreflight()
    results = preflight.verify_all_constraints()

    # Validate: Error detected
    assert any("not registered" in r.message for r in results if r.severity == "error")
```

---

## Testing Framework Overview

### Testing Infrastructure

#### Backend (Python/pytest)

**Configuration File:** `backend/pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
minversion = 7.0

addopts =
    -v
    --tb=short
    --strict-markers
    -ra

markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    acgme: marks tests related to ACGME compliance
    performance: marks tests as performance/load tests

asyncio_mode = auto
```

**Key Dependencies:**
- `pytest` 7.0+ - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-xdist` - Parallel execution

**Database Setup:**
```python
# Using in-memory SQLite for speed
TEST_DATABASE_URL = "sqlite:///:memory:"

# With StaticPool to prevent threading issues
poolclass=StaticPool
```

#### Frontend (TypeScript/Jest)

**Configuration:** Inferred from `frontend/jest.config.js`

```javascript
// Expected configuration
{
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.ts?(x)', '**/?(*.)+(spec|test).ts?(x)'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1'
  },
  collectCoverageFrom: ['src/**/*.ts(x)', '!src/**/*.d.ts']
}
```

**Key Dependencies:**
- `jest` - Test framework
- `@testing-library/react` - React component testing
- `@testing-library/jest-dom` - DOM matchers
- `jest-junit` - JUnit XML reports
- `ts-jest` - TypeScript support

#### Test Database Strategy

**In-Memory SQLite (Fast)**
```python
@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create isolated DB per test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
```

**PostgreSQL Service (CI/CD)**
```yaml
services:
  postgres:
    image: postgres:15-alpine
    env:
      POSTGRES_DB: test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
```

---

**Next Section:** [Part 2 - Backend Testing Patterns through Integration & E2E Testing](skills-testing-patterns-02-patterns.md)

**Updated:** 2025-12-31 | **Part 1 of 3**
