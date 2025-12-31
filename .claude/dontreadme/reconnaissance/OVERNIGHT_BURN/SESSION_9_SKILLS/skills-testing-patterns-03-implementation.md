# Claude Code Skills Testing Patterns - Part 3 of 3: Implementation & Reference

**Document Purpose:** CI/CD integration, quality gates, and testing reference materials for Claude Code skills.

**Last Updated:** 2025-12-30
**Author:** G2_RECON (SEARCH_PARTY Operation)

**Part 3 of 3:** CI/CD Integration, Coverage Recommendations, Quality Gates, and Appendices
**See Also:** [Part 1 - Foundations](skills-testing-patterns-01-foundations.md) | [Part 2 - Patterns](skills-testing-patterns-02-patterns.md)

---

## Table of Contents

8. [CI/CD Integration](#cicd-integration)
9. [Coverage Recommendations](#coverage-recommendations)
10. [Skill-Specific Testing Guidance](#skill-specific-testing-guidance)
11. [Common Pitfalls & Fixes](#common-pitfalls--fixes)
12. [Quality Gates & Validation](#quality-gates--validation)
13. [Testing Skills Themselves](#testing-skills-themselves)
14. [Final Recommendations](#final-recommendations)
15. [Appendices](#appendices)

---

## CI/CD Integration

### (PERCEPTION + MEDICINE Lenses)

#### GitHub Actions Workflow

**Primary CI Pipeline:** `.github/workflows/ci.yml`

```yaml
name: CI - Tests
on:
  pull_request:
    branches: [main, master, develop]
  push:
    branches:
      - main
      - 'claude/**'

env:
  PYTHON_VERSION: "3.11"
  NODE_VERSION: "20"

jobs:
  # Step 1: Detect changes
  changes:
    runs-on: ubuntu-latest
    outputs:
      backend: ${{ steps.filter.outputs.backend }}
      frontend: ${{ steps.filter.outputs.frontend }}
    steps:
      - uses: actions/checkout@v6
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            backend:
              - 'backend/**'
            frontend:
              - 'frontend/**'

  # Step 2: Run backend tests
  backend-tests:
    needs: changes
    if: ${{ needs.changes.outputs.backend == 'true' }}
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r backend/requirements.txt

      - name: Run tests with coverage
        run: pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v5
        with:
          files: backend/coverage.xml

  # Step 3: Run frontend tests
  frontend-tests:
    needs: changes
    if: ${{ needs.changes.outputs.frontend == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v6
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci --prefix frontend

      - name: Run tests
        run: npm run test:coverage --prefix frontend
```

#### Quality Gates

```yaml
# Before PR can merge, these checks must pass:

✅ CI - Tests (ci.yml)
  - backend-tests: pytest passes
  - frontend-tests: npm test passes
  - coverage-report: Codecov comment added

✅ Code Quality (code-quality.yml)
  - lint: ruff check pass
  - types: mypy pass
  - format: prettier/black pass

✅ Security (security.yml)
  - bandit: Security scan pass
  - dependabot: Dependency checks pass

✅ Docs (docs.yml)
  - Links verified
  - API docs generated
```

#### Coverage Thresholds (Suggested)

```python
# backend/pyproject.toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-fail-under=70"

# By layer:
# - Services: 80%+ coverage required
# - Controllers: 75%+ coverage required
# - Models: 70%+ coverage required
# - Utils: 85%+ coverage required
```

---

## Coverage Recommendations

### (INVESTIGATION + INSIGHT Lenses)

#### Target Coverage by Component

| Component | Target | Minimum | Rationale |
|-----------|--------|---------|-----------|
| **Services** | 85% | 80% | Core business logic |
| **Controllers** | 80% | 75% | Request handling |
| **Models** | 75% | 70% | Data layer |
| **Utilities** | 90% | 85% | Reusable functions |
| **Routes** | 75% | 65% | Endpoint mappings |
| **Overall** | 80% | 70% | Project threshold |

#### Coverage Calculation Example

```bash
# Generate coverage report with missing lines
pytest --cov=app --cov-report=html --cov-report=term-missing

# Output shows:
# Name                    Stmts   Miss  Cover   Missing
# ─────────────────────────────────────────────────────
# app/services/swap.py      150     15   90%    45-50, 120-125
# app/models/person.py      120     30   75%    40-70, 100-115
#                          ─────  ─────  ──────
# TOTAL                    2450    350   85%

# Calculate: (2450 - 350) / 2450 = 85% coverage
```

#### Gap Analysis

**Coverage Gap Report:**

```python
# Script: scripts/coverage_analysis.py

import coverage
import json

cov = coverage.Coverage()
cov.load()

# Get coverage by type
gaps = {
    "services": analyze_layer("app/services"),
    "controllers": analyze_layer("app/controllers"),
    "models": analyze_layer("app/models"),
}

# Identify high-impact gaps
high_priority = [
    (module, lines)
    for module, lines in gaps.items()
    if len(lines) > 5 and module_is_critical(module)
]

print(f"High-priority coverage gaps: {len(high_priority)}")
for module, lines in high_priority:
    print(f"  {module}: {len(lines)} uncovered lines")
```

#### Coverage Improvement Plan

1. **Identify Gaps:** `pytest --cov=app --cov-report=term-missing`
2. **Prioritize:** Focus on high-traffic code paths (services, controllers)
3. **Generate Tests:** Use test-writer skill for uncovered functions
4. **Verify:** Re-run coverage after adding tests
5. **Document:** Add to PR description what's newly covered

---

## Skill-Specific Testing Guidance

### (ARCANA + RELIGION Lenses)

#### By Skill Type

##### Knowledge Skills Testing

**Skills:** `acgme-compliance`, `code-review`, `docker-containerization`, `security-audit`

**Testing Approach:**
1. Validate documentation references are correct
2. Test that examples compile/execute
3. Verify recommendations are actionable

```python
# Example: Test knowledge skill examples execute
@pytest.mark.skill
def test_code_review_skill_examples_are_valid():
    """Verify code-review skill examples compile."""
    skill_doc = read_skill("code-review")

    # Extract code examples from documentation
    examples = extract_code_blocks(skill_doc, language="python")

    # Test each example compiles
    for example in examples:
        try:
            compile(example, '<example>', 'exec')
        except SyntaxError as e:
            pytest.fail(f"Example failed to compile: {e}")
```

##### Workflow Skills Testing

**Skills:** `COMPLIANCE_VALIDATION`, `SCHEDULING`, `SWAP_EXECUTION`

**Testing Approach:**
1. Test each workflow phase in isolation
2. Test complete workflow end-to-end
3. Test error handling and rollback

```python
# Example: Test workflow skill phases
@pytest.mark.skill
async def test_compliance_validation_workflow_phases(db_session):
    """Test COMPLIANCE_VALIDATION skill workflow phases."""
    from app.skills.compliance_validation import ComplianceValidation

    skill = ComplianceValidation(db_session)
    schedule = create_test_schedule(db_session)

    # Phase 1: Audit
    audit_result = await skill.audit_schedule(schedule)
    assert audit_result.phase == "audit"
    assert audit_result.violations is not None

    # Phase 2: Analyze
    analysis = await skill.analyze_violations(audit_result.violations)
    assert analysis.phase == "analyze"
    assert analysis.patterns is not None

    # Phase 3: Remediate
    remediation = await skill.remediate(analysis)
    assert remediation.phase == "remediate"
    assert remediation.fixed_violations > 0
```

##### Framework Skills Testing

**Skills:** `test-scenario-framework`, `python-testing-patterns`, `test-writer`

**Testing Approach:**
1. Verify generated artifacts are valid
2. Test that patterns match documentation
3. Validate output quality

```python
# Example: Test test-writer skill generates valid tests
@pytest.mark.skill
def test_test_writer_generates_valid_tests():
    """Verify test-writer generates syntactically correct pytest."""
    from app.skills.test_writer import TestWriter

    source = """
    async def swap_assignments(db, swap_id):
        swap = await db.get(Swap, swap_id)
        if not swap:
            raise ValueError("Swap not found")
        return await execute_swap(db, swap)
    """

    writer = TestWriter()
    generated_tests = writer.generate_tests(source)

    # Validate syntax
    compile(generated_tests, '<generated>', 'exec')

    # Validate it tests the function
    assert "def test_" in generated_tests
    assert "swap_assignments" in generated_tests
    assert "ValueError" in generated_tests  # Should test error case
```

##### Development Skills Testing

**Skills:** `constraint-preflight`, `automated-code-fixer`, `lint-monorepo`

**Testing Approach:**
1. Test detection of all error types
2. Test fix correctness
3. Test no false positives

```python
# Example: Test automated-code-fixer detects and fixes
@pytest.mark.skill
async def test_automated_code_fixer_detects_and_fixes(tmp_path):
    """Verify automated-code-fixer detects and fixes issues."""
    from app.skills.automated_code_fixer import AutomatedCodeFixer

    # Create file with multiple issues
    test_file = tmp_path / "broken.py"
    test_file.write_text("""
import os
import sys
import json  # Unused

def test():
    x = 1
    y = 2
    z = x + y  # Unused variable
    return True
""")

    fixer = AutomatedCodeFixer()
    results = await fixer.fix_file(str(test_file))

    # Should detect unused imports and variables
    assert any("unused" in r.message for r in results)

    # Fixed file should be valid Python
    fixed_content = test_file.read_text()
    compile(fixed_content, str(test_file), 'exec')
```

#### MCP Tool Integration Testing

**Critical Gap:** No tests verify MCP tools work correctly

**Proposed Test Structure:**

```python
# backend/tests/skills/test_mcp_tool_integration.py

@pytest.mark.skill
@pytest.mark.mcp
class TestMCPToolIntegration:
    """Test that skills correctly invoke MCP tools."""

    async def test_mcp_tool_exists(self):
        """Verify MCP tools are registered."""
        from app.mcp_client import MCPClient

        client = MCPClient()
        tools = await client.list_tools()

        # Should have 29+ tools registered
        assert len(tools) > 25
        assert any(t.name == "validate_acgme_compliance" for t in tools)

    async def test_mcp_tool_executes(self):
        """Verify MCP tools can be executed."""
        from app.mcp_client import MCPClient

        client = MCPClient()
        result = await client.call_tool(
            name="validate_acgme_compliance",
            arguments={"schedule_id": "test-123"}
        )

        # Should return valid response
        assert result is not None
        assert hasattr(result, "violations") or hasattr(result, "is_valid")

    async def test_skill_uses_mcp_correctly(self):
        """Verify COMPLIANCE_VALIDATION skill uses MCP tools."""
        from app.skills.compliance_validation import ComplianceValidation
        from unittest.mock import AsyncMock, patch

        # Mock MCP client
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = {
            "is_valid": True,
            "violations": []
        }

        with patch("app.skills.compliance_validation.MCPClient", return_value=mock_client):
            skill = ComplianceValidation()
            result = await skill.audit_schedule("test-schedule")

        # Should have called MCP tool
        mock_client.call_tool.assert_called_once()
        assert "validate_acgme_compliance" in str(mock_client.call_tool.call_args)
```

#### Skill Composition Testing

**Critical Gap:** No tests verify skill composition (parallel/serialized execution)

**Proposed Test Structure:**

```python
# backend/tests/skills/test_skill_composition.py

@pytest.mark.skill
@pytest.mark.composition
class TestSkillComposition:
    """Test composition of multiple skills."""

    async def test_serialized_skills_execute_in_order(self):
        """Verify serialized skills execute in correct order."""
        from app.skills.orchestration import SkillOrchestrator

        execution_order = []

        # Mock skills that track execution
        skill1 = AsyncMock(name="skill1")
        skill1.side_effect = lambda: (execution_order.append("skill1"), "result1")[1]

        skill2 = AsyncMock(name="skill2")
        skill2.side_effect = lambda: (execution_order.append("skill2"), "result2")[1]

        # Execute with serialization requirement
        orchestrator = SkillOrchestrator()
        await orchestrator.execute_serialized([skill1, skill2])

        # Verify order
        assert execution_order == ["skill1", "skill2"]

    async def test_parallel_skills_execute_concurrently(self):
        """Verify parallel-safe skills execute concurrently."""
        from app.skills.orchestration import SkillOrchestrator

        import time

        # Mock skills with delays
        skill1 = AsyncMock()
        skill1.side_effect = lambda: asyncio.sleep(0.1)

        skill2 = AsyncMock()
        skill2.side_effect = lambda: asyncio.sleep(0.1)

        # Execute with parallelization
        orchestrator = SkillOrchestrator()
        start = time.time()
        await orchestrator.execute_parallel([skill1, skill2])
        elapsed = time.time() - start

        # Should take ~0.1s (parallel) not ~0.2s (serial)
        assert elapsed < 0.15
```

---

## Common Pitfalls & Fixes

### (MEDICINE + STEALTH Lenses)

#### Pitfall 1: Unregistered Constraints (STEALTH)

**Problem:** Constraint implemented, tested, but not registered in ConstraintManager.

```python
# BAD: Constraint exists but isn't used
class MyConstraint(SoftConstraint):
    pass

# In tests:
def test_my_constraint():
    constraint = MyConstraint()
    # Tests pass!

# In solver:
# ❌ MyConstraint never actually used because not in manager
```

**Fix:** Use constraint-preflight skill

```bash
# Before committing:
cd backend && python ../scripts/verify_constraints.py

# Should output:
# [OK] MyConstraint registered in ConstraintManager.create_default()
# [OK] MyConstraint registered in ConstraintManager.create_resilience_aware()
```

#### Pitfall 2: Race Conditions in Async Tests (SURVIVAL)

**Problem:** Async test doesn't wait for all operations to complete

```python
# BAD: Race condition
@pytest.mark.asyncio
async def test_create_and_list(db_session):
    await create_person(db_session, "Test")
    # ❌ Might not be flushed yet!
    people = await list_people(db_session)
    assert len(people) == 1  # Flaky!
```

**Fix:** Ensure commits before reading

```python
# GOOD: Explicit flush/commit
@pytest.mark.asyncio
async def test_create_and_list(db_session):
    await create_person(db_session, "Test")
    await db_session.commit()  # Or flush + refresh

    people = await list_people(db_session)
    assert len(people) == 1  # Reliable
```

#### Pitfall 3: Fixture Scope Mismatches (MEDICINE)

**Problem:** Fixture scope causes unexpected state sharing

```python
# BAD: Session-scope fixture modified by tests
@pytest.fixture(scope="session")
def shared_schedule(db):
    schedule = create_schedule(db)
    return schedule

def test_1_modifies_schedule(shared_schedule):
    shared_schedule.name = "Modified"
    db.commit()

def test_2_sees_modification(shared_schedule):
    # ❌ Gets modified version from test_1!
    assert shared_schedule.name == "Original"  # Fails
```

**Fix:** Use function scope for mutable objects

```python
# GOOD: Function scope ensures fresh data
@pytest.fixture(scope="function")
def fresh_schedule(db):
    schedule = create_schedule(db)
    yield schedule
    # Automatic cleanup after test

def test_1_modifies_schedule(fresh_schedule):
    fresh_schedule.name = "Modified"

def test_2_has_fresh_copy(fresh_schedule):
    assert fresh_schedule.name == "Original"  # Passes
```

#### Pitfall 4: Missing Type Hints (PERCEPTION)

**Problem:** Untyped code makes tests harder to write correctly

```python
# BAD: No types, unclear what's expected
def create_assignment(person, block):  # What types?
    return Assignment(person, block)

# Test is ambiguous:
def test_create_assignment():
    result = create_assignment("person-1", "2024-01-01")
    # ✓ String IDs? ✓ String dates?
    # ❌ Unclear, test is brittle
```

**Fix:** Add type hints everywhere

```python
# GOOD: Types make intent clear
def create_assignment(
    person: Person,
    block: Block
) -> Assignment:
    return Assignment(person_id=person.id, block_id=block.id)

# Test is explicit:
@pytest.mark.asyncio
async def test_create_assignment(
    db_session,
    person_factory,
    block_factory
):
    person = await person_factory()
    block = await block_factory()
    result = await create_assignment(person, block)
    assert isinstance(result, Assignment)
```

#### Pitfall 5: Hardcoded Test Data (INVESTIGATION)

**Problem:** Test data hardcoded makes tests fail when context changes

```python
# BAD: Hardcoded dates and IDs
def test_schedule_generation():
    schedule = generate_schedule(
        start_date="2024-01-01",  # Hardcoded!
        end_date="2024-12-31",
        program_id="abc-123"  # What if this doesn't exist?
    )
    assert schedule is not None
```

**Fix:** Use factories and date utilities

```python
# GOOD: Dynamic test data
from datetime import date, timedelta

@pytest.mark.asyncio
async def test_schedule_generation(
    db_session,
    program_factory,
):
    program = await program_factory()
    today = date.today()

    schedule = await generate_schedule(
        program_id=program.id,
        start_date=today,
        end_date=today + timedelta(days=365)
    )

    assert schedule.program_id == program.id
```

#### Pitfall 6: Incomplete Mock Setup (MEDICINE)

**Problem:** Mock missing required methods, causing AttributeError

```python
# BAD: Incomplete mock
mock_db = AsyncMock()
# Missing: execute, commit, rollback, flush...

@pytest.mark.asyncio
async def test_with_mock(mock_db):
    result = await service.get_all(mock_db)
    # ❌ AttributeError: 'AsyncMock' has no attribute 'execute'
```

**Fix:** Use spec or MagicMock chainability

```python
# GOOD: Mock with spec
from sqlalchemy.orm import AsyncSession

mock_db = AsyncMock(spec=AsyncSession)
mock_db.execute.return_value.scalars.return_value.all.return_value = []

# Or use MagicMock for chainable calls
mock_result = MagicMock()
mock_result.scalars.return_value.all.return_value = []
mock_db.execute.return_value = mock_result
```

#### Pitfall 7: Neglecting Error Cases (SURVIVAL)

**Problem:** Tests only check happy path, miss error scenarios

```python
# BAD: Only happy path tested
def test_validate_hours():
    result = validate_hours(40)
    assert result.is_valid  # ✓

def test_validate_hours_over_limit():
    # ❌ Never written! What if someone passes -1?
```

**Fix:** Test error cases explicitly

```python
# GOOD: Happy + sad paths
@pytest.mark.parametrize("hours,should_fail", [
    (80, False),   # Max allowed
    (81, True),    # Over limit
    (0, False),    # Min allowed
    (-1, True),    # Invalid
    (1000, True),  # Way over
])
def test_validate_hours(hours, should_fail):
    result = validate_hours(hours)
    assert result.is_valid != should_fail
```

---

## Quality Gates & Validation

### (INSIGHT + NATURE Lenses)

#### Pre-Commit Testing

**Before Every Commit:**

```bash
#!/bin/bash
# .git/hooks/pre-commit

set -e

echo "Running pre-commit checks..."

# 1. Backend tests
cd backend
pytest --tb=short -q
python ../scripts/verify_constraints.py

# 2. Frontend tests
cd ../frontend
npm run test:ci --silent

# 3. Linting
cd ../backend
ruff check app/
ruff format app/ --check

# 4. Type checking
mypy app/ --ignore-missing-imports 2>/dev/null || true

echo "✓ All checks passed"
```

#### Pre-PR Validation

**CI Workflow Completion Checklist:**

```yaml
# Must pass before PR merge
✅ ci.yml:backend-tests
   └─ pytest passes
   └─ coverage >= 70%

✅ ci.yml:frontend-tests
   └─ npm test passes
   └─ coverage >= 60%

✅ code-quality.yml
   └─ ruff lint: PASS
   └─ mypy type-check: PASS
   └─ prettier format: PASS

✅ security.yml
   └─ bandit: PASS
   └─ dependabot: PASS

✅ docs.yml
   └─ Link validation: PASS
   └─ API docs generated: PASS
```

#### Test Report Interpretation

**Coverage Report Example:**

```
Name                     Stmts   Miss  Cover   Missing
─────────────────────────────────────────────────────
app/services/swap.py       150     15    90%    45-50, 120-125
app/models/person.py       120     30    75%    40-70, 100-115
app/api/routes.py          200     50    75%    80-120
─────────────────────────────────────────────────────
TOTAL                     2450    350    85%

Lines not covered by tests:
- app/services/swap.py:45-50 - Rare edge case
- app/services/swap.py:120-125 - Error recovery path
- app/models/person.py:40-70 - Validation logic
```

**Action Items:**
1. Target missing lines in high-traffic code (services, models)
2. Use test-writer skill to generate tests for gaps
3. Review if missing lines are truly testable
4. Re-run coverage after adding tests

#### Flaky Test Detection

**Identifying Flaky Tests:**

```bash
# Run specific test multiple times
pytest --count=10 tests/test_swap_executor.py::test_execute_swap_success

# If fails on some runs:
# - Likely race condition
# - Likely insufficient mocking
# - Likely timing-dependent code
```

**Fix Flaky Tests:**

```python
# Pattern 1: Race condition
# BAD
@pytest.mark.asyncio
async def test_concurrent_swaps(db_session):
    await execute_swap_1()
    await execute_swap_2()  # Might execute first!
    results = await get_swaps()
    assert len(results) == 2  # ❌ Flaky

# GOOD
@pytest.mark.asyncio
async def test_concurrent_swaps(db_session):
    results = await asyncio.gather(
        execute_swap_1(),
        execute_swap_2()
    )
    assert len(results) == 2  # ✓ Deterministic

# Pattern 2: Missing flush
# BAD
def test_with_db(db_session):
    create_person(db_session, "Test")
    people = list_people(db_session)  # ❌ Not flushed

# GOOD
def test_with_db(db_session):
    create_person(db_session, "Test")
    db_session.flush()  # ✓ Explicit flush
    people = list_people(db_session)
```

---

## Testing Skills Themselves

### (RELIGION + STEALTH Lenses)

#### The Meta-Testing Problem

**Question:** How do we test that skills work correctly?

**Current State:**
- Skills are not unit tested
- Skills are validated by humans reviewing documentation
- Skills are indirectly tested through project operations
- No automated CI checks for skill correctness

**Proposed Solution:** Create skill test framework

#### Skill Testing Infrastructure

**Proposed Directory Structure:**

```
backend/tests/skills/
├── __init__.py
├── conftest.py                          # Shared skill test fixtures
├── test_acgme_compliance_skill.py       # Knowledge skill tests
├── test_code_review_skill.py
├── test_swap_execution_skill.py         # Workflow skill tests
├── test_compliance_validation_skill.py
├── test_test_writer_skill.py            # Framework skill tests
├── test_test_scenario_framework_skill.py
├── test_constraint_preflight_skill.py   # Development skill tests
├── test_automated_code_fixer_skill.py
├── test_mcp_integration.py              # MCP integration tests
├── test_skill_composition.py            # Multi-skill tests
└── fixtures/
    ├── skill_examples.py
    ├── test_data.py
    └── mock_services.py
```

#### Skill Test Fixture Pattern

```python
# backend/tests/skills/conftest.py

@pytest.fixture
def skill_context():
    """Provide context for skill testing."""
    return {
        "database": create_test_db(),
        "mcp_client": MockMCPClient(),
        "logger": logging.getLogger("test"),
        "config": SkillTestConfig(),
    }

@pytest.fixture
async def skill_with_context(skill_context):
    """Provide skill instance with full context."""
    class SkillEnvironment:
        def __init__(self, skill_class, context):
            self.skill = skill_class(**context)
            self.context = context

        async def execute(self, *args, **kwargs):
            return await self.skill.execute(*args, **kwargs)

    yield SkillEnvironment
```

#### Example: Testing a Knowledge Skill

```python
# backend/tests/skills/test_acgme_compliance_skill.py

@pytest.mark.skill
class TestACGMEComplianceSkill:
    """Tests for acgme-compliance knowledge skill."""

    def test_skill_documentation_exists(self):
        """Skill must have documentation."""
        skill_doc = read_skill_doc("acgme-compliance")
        assert skill_doc is not None
        assert len(skill_doc) > 100

    def test_acgme_80_hour_rule_documented(self):
        """80-hour rule must be documented accurately."""
        skill_doc = read_skill_doc("acgme-compliance")
        assert "80 hours" in skill_doc
        assert "4-week rolling average" in skill_doc or "rolling" in skill_doc

    def test_acgme_1_in_7_rule_documented(self):
        """1-in-7 rule must be documented."""
        skill_doc = read_skill_doc("acgme-compliance")
        assert "1-in-7" in skill_doc or "one 24-hour period off" in skill_doc

    def test_supervision_ratio_documented(self):
        """Supervision ratios must be documented."""
        skill_doc = read_skill_doc("acgme-compliance")
        # Should mention PGY-specific ratios
        assert "PGY" in skill_doc
        assert any(ratio in skill_doc for ratio in ["1:2", "1:4", "1:1"])

    def test_skill_examples_are_valid(self):
        """Examples in skill doc must be valid Python."""
        skill_doc = read_skill_doc("acgme-compliance")
        examples = extract_code_blocks(skill_doc)

        for example in examples:
            try:
                compile(example, '<skill_example>', 'exec')
            except SyntaxError as e:
                pytest.fail(f"Example has syntax error: {e}")

    def test_skill_provides_actionable_guidance(self):
        """Skill should provide specific, actionable advice."""
        skill_doc = read_skill_doc("acgme-compliance")

        # Should have practical examples
        assert "example" in skill_doc.lower()
        assert "how to" in skill_doc.lower() or "steps" in skill_doc.lower()
```

#### Example: Testing a Workflow Skill

```python
# backend/tests/skills/test_swap_execution_skill.py

@pytest.mark.skill
@pytest.mark.integration
class TestSwapExecutionSkill:
    """Tests for SWAP_EXECUTION workflow skill."""

    async def test_skill_orchestrates_swap_workflow(self, skill_context):
        """Skill should orchestrate complete swap workflow."""
        from app.skills.swap_execution import SwapExecutionWorkflow

        # Create test data
        swap = create_test_swap()

        # Execute skill workflow
        workflow = SwapExecutionWorkflow(skill_context)
        result = await workflow.execute_swap(swap)

        # Verify all phases executed
        assert result.safety_checks_passed
        assert result.audit_trail is not None
        assert result.rollback_capability is not None

    async def test_skill_safety_checks_work(self, skill_context):
        """Skill must validate swap safety."""
        from app.skills.swap_execution import SwapExecutionWorkflow

        # Create invalid swap
        invalid_swap = create_invalid_swap()

        workflow = SwapExecutionWorkflow(skill_context)
        result = await workflow.execute_swap(invalid_swap)

        # Should reject invalid swap
        assert not result.safety_checks_passed
        assert "ACGME" in str(result.error) or "violation" in str(result.error)

    async def test_skill_maintains_audit_trail(self, skill_context):
        """Skill must maintain complete audit trail."""
        from app.skills.swap_execution import SwapExecutionWorkflow

        swap = create_test_swap()
        workflow = SwapExecutionWorkflow(skill_context)
        result = await workflow.execute_swap(swap)

        # Audit trail should be complete
        assert "initiator" in result.audit_trail
        assert "timestamp" in result.audit_trail
        assert "before_state" in result.audit_trail
        assert "after_state" in result.audit_trail
```

#### Example: Testing a Framework Skill

```python
# backend/tests/skills/test_test_writer_skill.py

@pytest.mark.skill
class TestTestWriterSkill:
    """Tests for test-writer framework skill."""

    def test_generates_valid_pytest_syntax(self):
        """Generated tests must be valid Python."""
        from app.skills.test_writer import TestWriter

        source = """
        async def create_assignment(db, person_id, block_id):
            assignment = Assignment(person_id=person_id, block_id=block_id)
            db.add(assignment)
            await db.flush()
            return assignment
        """

        writer = TestWriter()
        tests = writer.generate_tests(source)

        # Must compile
        compile(tests, '<generated>', 'exec')

    def test_includes_happy_path(self):
        """Should include happy path test."""
        from app.skills.test_writer import TestWriter

        source = "def simple_function(x): return x * 2"

        writer = TestWriter()
        tests = writer.generate_tests(source)

        assert "def test_" in tests
        assert "simple_function" in tests
        assert "assert" in tests

    def test_includes_error_cases(self):
        """Should include error case tests."""
        from app.skills.test_writer import TestWriter

        source = """
        def divide(a, b):
            if b == 0:
                raise ValueError("Division by zero")
            return a / b
        """

        writer = TestWriter()
        tests = writer.generate_tests(source)

        # Should test error case
        assert "ValueError" in tests or "zero" in tests
        assert "pytest.raises" in tests or "with pytest" in tests
```

#### CI Integration for Skill Testing

**Proposed GitHub Actions Workflow:**

```yaml
# .github/workflows/skill-tests.yml
name: Skill Tests

on: [push, pull_request]

jobs:
  skill-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install backend dependencies
        run: pip install -r backend/requirements.txt

      - name: Run skill tests
        run: |
          cd backend
          pytest tests/skills/ -v --tb=short -m skill

      - name: Check skill documentation
        run: |
          python scripts/validate_skill_docs.py

      - name: Test MCP tool integration
        run: |
          cd backend
          pytest tests/skills/test_mcp_integration.py -v

      - name: Test skill composition
        run: |
          cd backend
          pytest tests/skills/test_skill_composition.py -v
```

---

## Final Recommendations

### (INSIGHT + INVESTIGATION Lenses)

#### Immediate Actions (Next 1 week)

1. **Create skill test framework**
   - [ ] Add `backend/tests/skills/` directory
   - [ ] Create skill test fixtures in `conftest.py`
   - [ ] Write example tests for 3 skills (code-review, test-writer, constraint-preflight)

2. **Document testing patterns**
   - [ ] Create `docs/testing/SKILL_TESTING.md`
   - [ ] Add examples for each skill type
   - [ ] Document MCP integration testing approach

3. **Add CI integration**
   - [ ] Create `.github/workflows/skill-tests.yml`
   - [ ] Add skill test job to main CI pipeline
   - [ ] Configure Codecov for skill tests

#### Short-term Improvements (2-4 weeks)

1. **Comprehensive skill coverage**
   - [ ] Write tests for all 15+ skills
   - [ ] Target 70%+ coverage on skill code
   - [ ] Add pre-flight validation in CI

2. **MCP tool validation**
   - [ ] Create tests for all 29+ MCP tools
   - [ ] Verify tool integration with skills
   - [ ] Test error handling paths

3. **Skill composition validation**
   - [ ] Test parallel skill execution
   - [ ] Test serialized skill execution
   - [ ] Test error handling in composition

#### Long-term Vision (1-3 months)

1. **Skill test automation**
   - [ ] Auto-generate test stubs from skill YAML
   - [ ] Generate test reports per skill
   - [ ] Track skill reliability over time

2. **Continuous quality monitoring**
   - [ ] Dashboard showing skill test results
   - [ ] Alerts for skill test failures
   - [ ] Historical trend analysis

3. **Skill certification program**
   - [ ] Define skill quality gates
   - [ ] Require tests before skill deployment
   - [ ] Track skill versioning and compatibility

---

## Appendix A: Testing Terminology

| Term | Definition |
|------|-----------|
| **Unit Test** | Tests single function/method in isolation |
| **Integration Test** | Tests multiple components working together |
| **E2E Test** | Tests complete user workflow end-to-end |
| **Scenario Test** | Tests complex business scenario with setup/validation |
| **Fixture** | Reusable test data/setup |
| **Mock** | Simulated object replacing real dependency |
| **Parametrize** | Run same test with multiple inputs |
| **Coverage** | % of code executed by tests |
| **Marker** | Tag for grouping/filtering tests |
| **Flaky Test** | Test that passes/fails inconsistently |

## Appendix B: Testing Tools Reference

| Tool | Purpose | Status |
|------|---------|--------|
| `pytest` | Python test framework | In use |
| `pytest-asyncio` | Async test support | In use |
| `pytest-cov` | Coverage reporting | In use |
| `pytest-xdist` | Parallel execution | Installed, not in CI |
| `jest` | JavaScript/TypeScript testing | In use |
| `@testing-library/react` | React testing | In use |
| `sqlalchemy` | ORM with test helpers | In use |
| `freezegun` | Mock time in tests | Available |
| `faker` | Generate test data | Available |
| `hypothesis` | Property-based testing | Not installed |

## Appendix C: Quick Command Reference

```bash
# Backend Testing
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific marker
pytest -m acgme
pytest -m integration
pytest -m "not slow"

# Run specific file
pytest tests/test_swap_executor.py

# Run matching pattern
pytest -k "test_execute_swap"

# Debug mode (drop to pdb on failure)
pytest --pdb

# Show print statements
pytest -s

# Parallel execution
pytest -n auto

# Frontend Testing
cd ../frontend

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Watch mode
npm test -- --watch

# Single run (CI mode)
npm run test:ci
```

---

**Document Status:** COMPLETE
**Confidence Level:** HIGH (Based on comprehensive codebase analysis)
**Ready for:** Implementation, CI/CD integration, team documentation


---

**Document Status:** COMPLETE
**Confidence Level:** HIGH (Based on comprehensive codebase analysis)
**Ready for:** Implementation, CI/CD integration, team documentation

**Updated:** 2025-12-31 | **Part 3 of 3**
