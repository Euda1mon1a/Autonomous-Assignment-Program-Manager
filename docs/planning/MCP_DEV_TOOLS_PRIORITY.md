# MCP Development Tools Priority List

> **Goal:** Enable Claude Code to analyze, debug, and refine Python modules
> **Focus:** Development workflow, not production operations

---

## Current State

### What Claude Code CAN Do Now (Without MCP)

| Task | Method | Works? |
|------|--------|--------|
| Read code | `Read` tool | Yes |
| Edit code | `Edit` tool | Yes |
| Run tests | `Bash: pytest` | Yes |
| Check lint | `Bash: ruff` | Yes |
| Git operations | `Bash: git` | Yes |

### What Claude Code CANNOT Do Efficiently

| Task | Current Limitation | MCP Would Enable |
|------|-------------------|------------------|
| Analyze test failures | Parse stdout manually | Structured failure data |
| Debug solver output | Read raw logs | Parsed constraint violations |
| Check module health | Run multiple commands | Single health check |
| Trace code paths | Manual file hopping | Call graph analysis |
| Validate changes | Run suite, parse output | Pre-commit validation |

---

## Priority 1: Test Analysis Tools

### Tool: `run_tests`

**Purpose:** Run pytest with structured output parsing

**Why Needed:**
- Claude Code runs `pytest` but gets raw text output
- Hard to extract failure details, affected tests, coverage
- MCP can return structured JSON

**Implementation:**
```python
@mcp.tool()
async def run_tests_tool(
    path: str = "tests/",
    pattern: str | None = None,
    verbose: bool = True,
    coverage: bool = False,
    fail_fast: bool = False,
) -> TestRunResult:
    """
    Run pytest and return structured results.

    Returns:
        TestRunResult with:
        - passed: int
        - failed: int
        - errors: int
        - skipped: int
        - failures: list[TestFailure] with traceback, assertion details
        - coverage: CoverageReport if requested
        - duration_seconds: float
    """
```

**Effort:** Medium (need to parse pytest output or use pytest hooks)

---

### Tool: `analyze_test_failure`

**Purpose:** Deep analysis of a specific failing test

**Why Needed:**
- When a test fails, Claude needs context
- What was expected vs actual
- Related code paths
- Similar passing tests for comparison

**Implementation:**
```python
@mcp.tool()
async def analyze_test_failure_tool(
    test_path: str,  # e.g., "tests/test_solvers.py::test_greedy_solver"
    include_source: bool = True,
    include_fixtures: bool = True,
) -> TestFailureAnalysis:
    """
    Analyze why a specific test failed.

    Returns:
        TestFailureAnalysis with:
        - error_type: str (AssertionError, TypeError, etc.)
        - assertion_details: dict (expected, actual, diff)
        - source_code: str (the test function)
        - fixture_values: dict (what fixtures provided)
        - related_tests: list (similar tests that passed/failed)
        - suggested_fixes: list[str]
    """
```

**Effort:** High (needs pytest plugin or post-processing)

---

## Priority 2: Solver/Engine Analysis Tools

### Tool: `analyze_solver_run`

**Purpose:** Parse and structure solver output for debugging

**Why Needed:**
- Solvers produce complex output (constraints, objectives, decisions)
- Hard to debug from raw logs
- Need to see which constraints caused issues

**Implementation:**
```python
@mcp.tool()
async def analyze_solver_run_tool(
    solver_type: str,  # greedy, cp_sat, pulp, hybrid
    start_date: str,
    end_date: str,
    dry_run: bool = True,  # Don't save to DB
) -> SolverAnalysis:
    """
    Run solver and return detailed analysis.

    Returns:
        SolverAnalysis with:
        - status: str (optimal, feasible, infeasible, timeout)
        - runtime_seconds: float
        - assignments_made: int
        - constraint_violations: list[ConstraintViolation]
        - objective_breakdown: dict (fairness, coverage, etc.)
        - decision_explanations: dict[block_id -> why_this_template]
        - bottlenecks: list[str] (what limited the solution)
    """
```

**Effort:** Medium (solvers already capture this, need to expose)

---

### Tool: `explain_constraint_violation`

**Purpose:** Explain why a specific constraint was violated

**Why Needed:**
- When solver fails or produces violations, need to understand why
- Need to trace back to specific rules and data

**Implementation:**
```python
@mcp.tool()
async def explain_constraint_violation_tool(
    violation_type: str,  # acgme_80_hour, supervision_ratio, etc.
    person_id: str | None = None,
    date_range: tuple[str, str] | None = None,
) -> ConstraintExplanation:
    """
    Explain why a constraint is violated.

    Returns:
        ConstraintExplanation with:
        - rule_name: str
        - rule_definition: str (plain English)
        - current_value: Any (e.g., 82 hours)
        - threshold: Any (e.g., 80 hours max)
        - contributing_factors: list[str] (which assignments pushed over)
        - fix_options: list[str] (how to resolve)
    """
```

**Effort:** Medium (needs constraint introspection)

---

## Priority 3: Code Quality Tools

### Tool: `check_module_health`

**Purpose:** Quick health check of a Python module

**Why Needed:**
- Before editing, Claude should verify module is healthy
- After editing, verify no regressions
- Catch issues early

**Implementation:**
```python
@mcp.tool()
async def check_module_health_tool(
    module_path: str,  # e.g., "app/scheduling/solvers.py"
) -> ModuleHealth:
    """
    Check health of a Python module.

    Returns:
        ModuleHealth with:
        - imports_ok: bool
        - syntax_ok: bool
        - type_check_ok: bool (mypy)
        - lint_issues: list[LintIssue]
        - test_count: int (tests for this module)
        - test_status: str (passing/failing/unknown)
        - complexity_score: float
        - todo_count: int
    """
```

**Effort:** Low (run ruff, mypy, count tests)

---

### Tool: `find_related_code`

**Purpose:** Find code related to a function/class

**Why Needed:**
- When debugging, need to find all callers/callees
- Find tests that exercise specific code
- Find similar implementations

**Implementation:**
```python
@mcp.tool()
async def find_related_code_tool(
    symbol: str,  # e.g., "SchedulingEngine.solve"
    relation_type: str = "all",  # callers, callees, tests, similar
) -> RelatedCode:
    """
    Find code related to a symbol.

    Returns:
        RelatedCode with:
        - callers: list[CodeLocation] (who calls this)
        - callees: list[CodeLocation] (what this calls)
        - tests: list[str] (tests that exercise this)
        - similar: list[CodeLocation] (similar implementations)
        - dependencies: list[str] (imports this uses)
    """
```

**Effort:** High (needs AST analysis or LSP)

---

## Priority 4: Validation Tools

### Tool: `validate_change`

**Purpose:** Validate a code change before committing

**Why Needed:**
- Pre-commit validation
- Catch issues before pushing
- Ensure tests still pass

**Implementation:**
```python
@mcp.tool()
async def validate_change_tool(
    changed_files: list[str] | None = None,  # If None, use git diff
    run_affected_tests: bool = True,
    run_lint: bool = True,
    run_type_check: bool = True,
) -> ChangeValidation:
    """
    Validate uncommitted changes.

    Returns:
        ChangeValidation with:
        - lint_ok: bool
        - type_check_ok: bool
        - affected_tests: list[str]
        - test_results: TestRunResult
        - ready_to_commit: bool
        - blocking_issues: list[str]
    """
```

**Effort:** Medium (compose existing tools)

---

## Implementation Priority

### Phase 1: Quick Wins (1-2 days)

1. **`check_module_health`** - Compose existing tools (ruff, mypy)
2. **`run_tests`** - Wrap pytest with JSON output parsing
3. **`validate_change`** - Compose lint + type check + tests

### Phase 2: Solver Analysis (3-5 days)

4. **`analyze_solver_run`** - Expose existing solver diagnostics
5. **`explain_constraint_violation`** - Add constraint introspection

### Phase 3: Deep Analysis (5-7 days)

6. **`analyze_test_failure`** - pytest plugin or parsing
7. **`find_related_code`** - AST analysis or LSP integration

---

## What This Enables

### Current Workflow (Without MCP Dev Tools)

```
Claude: Run pytest
[raw text output]
Claude: Parse output manually, grep for errors
Claude: Read test file
Claude: Read source file
Claude: Figure out what's wrong
```

### Improved Workflow (With MCP Dev Tools)

```
Claude: run_tests_tool(pattern="test_solvers")
[structured JSON: 3 failed, here's why]
Claude: analyze_test_failure_tool("test_greedy_solver")
[structured: expected X, got Y, related code paths]
Claude: Fix the issue with context
Claude: validate_change_tool()
[structured: lint ok, tests pass, ready to commit]
```

---

## Connection to Existing MCP Infrastructure

### These Tools Would Use:

- **Existing API client** for backend calls
- **Existing async patterns** for non-blocking
- **Existing error handling** for graceful degradation

### These Tools Would Add:

- **Development-focused** endpoints
- **Structured diagnostics** not available via CLI
- **Cross-cutting analysis** that spans files

---

## Summary

| Tool | Priority | Effort | Value |
|------|----------|--------|-------|
| `check_module_health` | P1 | Low | High |
| `run_tests` | P1 | Medium | High |
| `validate_change` | P1 | Medium | High |
| `analyze_solver_run` | P2 | Medium | High |
| `explain_constraint_violation` | P2 | Medium | Medium |
| `analyze_test_failure` | P3 | High | Medium |
| `find_related_code` | P3 | High | Medium |

**Recommended Start:** Implement `check_module_health` first - low effort, immediate value, proves the pattern.

---

*Priority list for MCP development tools - December 2024*
