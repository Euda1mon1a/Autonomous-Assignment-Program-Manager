***REMOVED*** Quality Gates - Comprehensive Standards & Thresholds

> **Last Updated:** 2025-12-31
> **Purpose:** Define all quality gate requirements, thresholds, and enforcement procedures

---

***REMOVED******REMOVED*** Table of Contents

1. [Overview](***REMOVED***overview)
2. [Code Coverage Thresholds](***REMOVED***code-coverage-thresholds)
3. [Linting Standards](***REMOVED***linting-standards)
4. [Type Checking Requirements](***REMOVED***type-checking-requirements)
5. [Security Standards](***REMOVED***security-standards)
6. [Performance Requirements](***REMOVED***performance-requirements)
7. [Documentation Requirements](***REMOVED***documentation-requirements)
8. [Testing Matrices](***REMOVED***testing-matrices)
9. [Quality Gate Bypass Procedures](***REMOVED***quality-gate-bypass-procedures)
10. [Failure Remediation](***REMOVED***failure-remediation)

---

***REMOVED******REMOVED*** Overview

***REMOVED******REMOVED******REMOVED*** Purpose

Quality gates ensure that all code merged to `main` meets minimum standards for:
- **Reliability**: Tests and type checking
- **Maintainability**: Code style and complexity
- **Security**: Vulnerability scanning and secrets detection
- **Documentation**: API docs, comments, and user-facing changes

***REMOVED******REMOVED******REMOVED*** Architecture

The Quality Gates pipeline runs in 9 phases:

```
Phase 1: Change Detection (efficient filtering)
   ↓
Phase 2: Linting (Ruff, ESLint, formatting)
   ↓
Phase 3: Type Checking (MyPy, TypeScript)
   ↓
Phase 4: Unit Tests & Coverage (pytest, Jest)
   ↓
Phase 5: Common Checks (merge conflicts, debug statements)
   ↓
Phase 6: Security Scanning (Bandit, npm audit, secrets)
   ↓
Phase 7: Build Verification (imports, build output)
   ↓
Phase 8: Documentation (markdown validation, CHANGELOG)
   ↓
Phase 9: Quality Gate Enforcement (final decision)
```

***REMOVED******REMOVED******REMOVED*** Execution

**Triggers:**
- Pull requests to `main`, `master`, `develop`
- Direct pushes to `main` or `master`
- Manual workflow dispatch (`workflow_dispatch`)

**Concurrency:**
- Only one instance per branch/PR
- Earlier runs cancelled if new run starts

---

***REMOVED******REMOVED*** Code Coverage Thresholds

***REMOVED******REMOVED******REMOVED*** Backend (Python)

| Metric | Threshold | Enforcement | Notes |
|--------|-----------|-------------|-------|
| **Line Coverage** | ≥ 80% | Hard gate (blocks merge) | Over all app code |
| **Branch Coverage** | ≥ 70% | Soft gate (warns only) | Decision points in logic |
| **Function Coverage** | ≥ 80% | Hard gate | Ensures functions tested |

**Calculation Method:**
```
coverage = (covered_lines / total_lines) * 100
```

**Example:**
```
✓ PASS:  82% coverage (> 80% threshold)
✗ FAIL:  78% coverage (< 80% threshold)
```

**How to Improve:**
1. Add unit tests for untested functions
2. Test edge cases and error conditions
3. Use `pytest --cov` to identify gaps
4. Add integration tests for complex flows

***REMOVED******REMOVED******REMOVED*** Frontend (TypeScript/React)

| Metric | Threshold | Enforcement | Notes |
|--------|-----------|-------------|-------|
| **Line Coverage** | ≥ 70% | Hard gate (blocks merge) | Over all src code |
| **Branch Coverage** | ≥ 60% | Soft gate (warns only) | Decision points in components |
| **Function Coverage** | ≥ 70% | Hard gate | Component functions |

**Lower threshold rationale:**
- UI components harder to test comprehensively
- Snapshot testing less reliable
- More time investment for diminishing returns

**How to Improve:**
1. Test component rendering with different props
2. Test user interactions (clicks, input)
3. Test conditional rendering
4. Use React Testing Library best practices

***REMOVED******REMOVED******REMOVED*** MCP Server

| Metric | Threshold | Enforcement |
|--------|-----------|-------------|
| **Line Coverage** | ≥ 75% | Hard gate | Tool integration critical |

---

***REMOVED******REMOVED*** Linting Standards

***REMOVED******REMOVED******REMOVED*** Backend (Python) - Ruff

| Rule Category | Enforcement | Details |
|--------------|-------------|---------|
| **Errors** | Hard gate (0 allowed) | `ruff check --exit-code=1` |
| **Warnings** | Soft gate (<10 allowed) | Informational only |
| **Import Order** | Hard gate (0 violations) | `--select I` (isort compatible) |
| **Line Length** | 100 characters max | Enforced by ruff format |
| **Unused Imports** | Hard gate (0 allowed) | `F401` (imported but unused) |
| **Undefined Names** | Hard gate (0 allowed) | `F821` (undefined name) |

**Ruff Configuration (backend/pyproject.toml):**
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",    ***REMOVED*** pycodestyle errors
    "W",    ***REMOVED*** pycodestyle warnings
    "F",    ***REMOVED*** Pyflakes
    "I",    ***REMOVED*** isort imports
    "B",    ***REMOVED*** flake8-bugbear
    "C4",   ***REMOVED*** flake8-comprehensions
    "UP",   ***REMOVED*** pyupgrade
]
ignore = [
    "E501",  ***REMOVED*** line too long (handled by formatter)
]
```

**Running Locally:**
```bash
***REMOVED*** Check for errors only
ruff check backend/ --exit-code=1

***REMOVED*** Auto-fix issues
ruff check backend/ --fix

***REMOVED*** Format code
ruff format backend/
```

***REMOVED******REMOVED******REMOVED*** Frontend (TypeScript/JavaScript) - ESLint

| Rule Category | Enforcement | Details |
|--------------|-------------|---------|
| **Errors** | Hard gate (0 allowed) | `npm run lint` exit code 1 |
| **Warnings** | Soft gate (<15 allowed) | Informational only |
| **Type Violations** | Hard gate (0 allowed) | TypeScript ESLint plugin |
| **React Rules** | Hard gate (0 allowed) | eslint-plugin-react-hooks |
| **Unused Variables** | Hard gate (0 allowed) | No dead code |

**ESLint Configuration (frontend/.eslintrc.json):**
```json
{
  "extends": ["next/core-web-vitals"],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-types": "error",
    "react-hooks/rules-of-hooks": "error",
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

**Running Locally:**
```bash
***REMOVED*** Check for errors
npm run lint

***REMOVED*** Auto-fix issues
npm run lint:fix
```

***REMOVED******REMOVED******REMOVED*** Formatting Standards

| Tool | Language | Standard | Enforcement |
|------|----------|----------|-------------|
| **Ruff Format** | Python | Black-compatible | Pre-commit hook |
| **Prettier** | TypeScript/JSON | Opinionated | Pre-commit hook |

**Key Rules:**
- 2-space indentation (JavaScript/JSON)
- 4-space indentation (Python)
- Single quotes (JavaScript strings)
- Trailing commas in multi-line structures
- No semicolons (JavaScript - Prettier removes them)

---

***REMOVED******REMOVED*** Type Checking Requirements

***REMOVED******REMOVED******REMOVED*** Backend (Python) - MyPy

| Check Type | Enforcement | Details |
|-----------|-------------|---------|
| **Undefined Names** | Hard gate (0 allowed) | `F821` caught by ruff |
| **Type Mismatches** | Soft gate (warns only) | Not yet fully enforced |
| **Missing Annotations** | Soft gate (warns only) | Gradual typing adopted |
| **Protocol Violations** | Soft gate (warns only) | Runtime behavior preserved |

**MyPy Configuration (backend/pyproject.toml):**
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  ***REMOVED*** Gradual typing
ignore_missing_imports = true
```

**Strategy:**
- Currently informational (not blocking)
- Aim to enforce strict mode by Q2 2026
- New code should have type hints
- Existing code gradually updated

**Running Locally:**
```bash
***REMOVED*** Type check only
mypy backend/app/ --ignore-missing-imports

***REMOVED*** With error output
mypy backend/app/ --no-error-summary
```

***REMOVED******REMOVED******REMOVED*** Frontend (TypeScript)

| Check Type | Enforcement | Details |
|-----------|-------------|---------|
| **Type Errors** | Hard gate (0 allowed) | `npx tsc --noEmit` |
| **Unused Variables** | Hard gate (0 allowed) | ESLint coverage |
| **Implicit Any** | Hard gate (0 allowed) | `noImplicitAny: true` |
| **Strict Null Checks** | Hard gate | `strictNullChecks: true` |

**TypeScript Configuration (frontend/tsconfig.json):**
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "esModuleInterop": true
  }
}
```

**Running Locally:**
```bash
***REMOVED*** Type check
npx tsc --noEmit

***REMOVED*** Via npm script
npm run type-check
```

---

***REMOVED******REMOVED*** Security Standards

***REMOVED******REMOVED******REMOVED*** Secret Detection

| Check | Enforcement | Tool | Details |
|-------|-------------|------|---------|
| **Hardcoded Secrets** | Hard gate (blocks merge) | Gitleaks | Prevents credential leaks |
| **API Keys** | Hard gate | Gitleaks | Both public and private keys |
| **Tokens** | Hard gate | Gitleaks | JWT, OAuth, Bearer tokens |
| **Passwords** | Hard gate | Gitleaks | Database and user passwords |

**What Gets Detected:**
- AWS credentials and keys
- GitHub tokens
- SSH private keys
- Database connection strings with passwords
- API tokens and keys
- Bearer tokens
- Encryption keys

**Prevention:**
1. Never commit `.env` files (use `.env.example`)
2. Use environment variables for secrets
3. Use GitHub secrets for CI/CD
4. If accidentally committed:
   - Rotate credentials immediately
   - Use `git filter-branch` or BFG to remove
   - Update commit history

***REMOVED******REMOVED******REMOVED*** Dependency Scanning

| Language | Tool | Enforcement | Severity |
|----------|------|-------------|----------|
| **Python** | pip-audit | Soft gate | CRITICAL, HIGH |
| **Python** | Safety | Soft gate | Known vulnerabilities |
| **Node.js** | npm audit | Soft gate | CRITICAL, HIGH |

**Audit Results:**
- Published as artifacts (visible in Actions tab)
- Non-blocking (warnings only)
- Should be addressed before release
- Regular security updates recommended

**How to Fix:**
```bash
***REMOVED*** Python
pip-audit -r backend/requirements.txt --fix

***REMOVED*** Node.js
npm audit fix
npm audit fix --force  ***REMOVED*** Risky, updates major versions
```

***REMOVED******REMOVED******REMOVED*** Bandit (Python Security)

| Check | Enforcement | Examples |
|-------|-------------|----------|
| **SQL Injection** | Soft gate | Direct SQL queries |
| **Hardcoded SQL** | Soft gate | String-based queries |
| **Weak Crypto** | Soft gate | MD5, DES, random |
| **Insecure Deserialization** | Soft gate | pickle, eval |
| **Shell Injection** | Soft gate | subprocess without list args |

**Running Locally:**
```bash
***REMOVED*** Quick scan (medium/high only)
bandit -r backend/app -ll

***REMOVED*** Full report
bandit -r backend/app -f json
```

---

***REMOVED******REMOVED*** Performance Requirements

***REMOVED******REMOVED******REMOVED*** Build Performance

| Metric | Threshold | Enforcement |
|--------|-----------|-------------|
| **Backend import time** | < 5 seconds | Informational |
| **Frontend build time** | < 60 seconds | Soft gate |
| **Frontend bundle size** | < 500 KB (gzipped) | Soft gate |

***REMOVED******REMOVED******REMOVED*** Test Performance

| Suite | Threshold | Details |
|-------|-----------|---------|
| **Backend unit tests** | < 5 minutes | All tests must complete |
| **Frontend unit tests** | < 3 minutes | Jest suite |
| **Frontend E2E tests** | < 15 minutes | Playwright suite |

---

***REMOVED******REMOVED*** Documentation Requirements

***REMOVED******REMOVED******REMOVED*** Code Documentation

| Requirement | Enforcement | Details |
|------------|-------------|---------|
| **Module docstrings** | Soft gate (warnings) | All modules should have docstrings |
| **Function docstrings** | Soft gate (warnings) | Public functions/methods |
| **Class docstrings** | Soft gate (warnings) | All public classes |
| **Docstring format** | Soft gate (warnings) | Google-style (see CLAUDE.md) |

**Example (Python):**
```python
"""Service for managing schedule assignments."""
from typing import Optional


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
    """
    ***REMOVED*** Implementation
    pass
```

***REMOVED******REMOVED******REMOVED*** CHANGELOG Requirements

| Change Type | CHANGELOG Entry | Example |
|-----------|-----------------|---------|
| **New Features** | `feat:` | `feat: Add schedule export to PDF` |
| **Enhancements** | `feat:` | `feat: Improve performance by 30%` |
| **Bug Fixes** | `fix:` | `fix: Resolve double-booking issue` |
| **Breaking Changes** | Mention in body | `BREAKING CHANGE: Remove old API endpoint` |
| **Deprecations** | Note in entry | `(deprecated in v1.5.0)` |
| **Security Fixes** | Prefix with `security:` | `security: Patch XSS vulnerability` |

**Format:**
```markdown
***REMOVED******REMOVED*** [1.5.0] - 2025-12-31

***REMOVED******REMOVED******REMOVED*** Added
- Schedule export to PDF format
- New ACGME compliance dashboard

***REMOVED******REMOVED******REMOVED*** Fixed
- Double-booking edge case in rotation assignment
- Memory leak in WebSocket handler

***REMOVED******REMOVED******REMOVED*** Security
- Patched XSS vulnerability in search input
- Updated vulnerable dependencies
```

**Requirement:**
- For feature/fix PRs: Update CHANGELOG
- For chore/refactor: Optional but recommended
- For docs-only: Not required

---

***REMOVED******REMOVED*** Testing Matrices

***REMOVED******REMOVED******REMOVED*** Required Tests by Change Type

| Change Type | Unit Tests | Integration | E2E | Security |
|-----------|-----------|-------------|-----|----------|
| **New Feature** | ✓ (80%+) | ✓ (if API) | ✓ (if UI) | ✓ |
| **Bug Fix** | ✓ (80%+) | ✓ (if API) | Optional | ✓ |
| **Refactor** | ✓ (pass) | ✓ (pass) | Optional | ✓ |
| **Chore** | N/A | N/A | N/A | N/A |
| **Docs** | N/A | N/A | N/A | N/A |

***REMOVED******REMOVED******REMOVED*** Test Expectations

**Unit Tests:**
```bash
***REMOVED*** Backend
cd backend
pytest --cov=app --cov-report=term-missing

***REMOVED*** Frontend
cd frontend
npm run test:coverage
```

**Integration Tests:**
- Database-dependent tests
- API endpoint tests
- Cross-service integration

**E2E Tests:**
```bash
cd frontend
npm run test:e2e
```

---

***REMOVED******REMOVED*** Quality Gate Bypass Procedures

***REMOVED******REMOVED******REMOVED*** Emergency Hotfix Bypass

**When:** Critical production bug requires immediate fix

**Process:**
1. Create PR with label `hotfix`
2. Include justification in PR description
3. Require 2 approvals (vs. normal 1)
4. Can bypass non-critical gates only:
   - ✗ Cannot bypass: Linting, type checking, unit tests, security
   - ✓ Can bypass: Code coverage, E2E tests (with justification)

**After Bypass:**
- Must address any warnings within 24 hours
- Document decision in commit message
- Add follow-up task in HUMAN_TODO.md

***REMOVED******REMOVED******REMOVED*** Experimental Feature Bypass

**When:** Testing new patterns or frameworks

**Process:**
1. Create feature branch (not merged to `main`)
2. Create PR to temporary branch (e.g., `experimental/new-system`)
3. Request code review but gates can be more relaxed
4. Must eventually merge to `main` meeting full gates
5. Or delete branch if experiment abandoned

---

***REMOVED******REMOVED*** Failure Remediation

***REMOVED******REMOVED******REMOVED*** Linting Failures

**Error: Too many linting issues**

```bash
***REMOVED*** Auto-fix most issues
ruff check backend/ --fix
ruff format backend/

***REMOVED*** Review remaining issues
ruff check backend/
```

**Common Issues:**
- Unused imports → `ruff check --fix`
- Line too long → `ruff format`
- Unused variables → Manual removal
- Import ordering → `ruff check --select I --fix`

***REMOVED******REMOVED******REMOVED*** Type Checking Failures

**Error: Type checker found errors**

```bash
***REMOVED*** View all type errors
mypy backend/app/

***REMOVED*** Add type hints
***REMOVED*** Example: change function signature to include types
```

**Strategy:**
- Add return type hints
- Add parameter type hints
- Use Union[] for optional types
- Use TypeAlias for complex types

***REMOVED******REMOVED******REMOVED*** Coverage Failures

**Error: Coverage below 80% threshold**

```bash
***REMOVED*** Find uncovered code
pytest --cov=app --cov-report=term-missing backend/

***REMOVED*** Add tests for uncovered lines
***REMOVED*** Edit backend/tests/ to add new test cases
```

**Process:**
1. Identify uncovered functions
2. Write unit tests covering them
3. Test both happy path and error cases
4. Re-run coverage check

***REMOVED******REMOVED******REMOVED*** Test Failures

**Error: One or more tests failed**

```bash
***REMOVED*** Run failing test with verbose output
pytest tests/test_scheduler.py::TestScheduler::test_overlap_detection -v

***REMOVED*** Run with debugging
pytest tests/test_scheduler.py::TestScheduler -v -s
```

**Debug Process:**
1. Read test name and assertion
2. Check test implementation
3. Check code being tested
4. Add debug output (`print()`, `logger.debug()`)
5. Fix code or test

***REMOVED******REMOVED******REMOVED*** Security Scan Failures

**Error: Gitleaks detected secrets**

Immediate action required:
```bash
***REMOVED*** Do NOT add secret to .gitignore (already committed)
***REMOVED*** Rotate the credential immediately

***REMOVED*** Remove secret from git history (if not sensitive data)
git filter-branch --tree-filter 'rm -f .env.production' -- --all

***REMOVED*** Push to update remote (requires force push permissions)
git push origin main --force

***REMOVED*** Or use BFG Repo-Cleaner (simpler, recommended)
***REMOVED*** https://rclone.org/b2/
```

**Prevention:**
- Use `.env.example` as template
- Add real `.env` files to `.gitignore`
- Store secrets in GitHub Secrets
- Use GitHub secret scanning

***REMOVED******REMOVED******REMOVED*** Build Failures

**Error: Build step failed**

```bash
***REMOVED*** Frontend
cd frontend
npm ci  ***REMOVED*** Clean install
npm run build

***REMOVED*** Backend
cd backend
python -m py_compile app/main.py  ***REMOVED*** Check imports
```

**Common Issues:**
- Missing dependencies → `npm ci` / `pip install -r requirements.txt`
- Syntax errors → Fix code
- Missing env variables → Set in workflow
- TypeScript errors → Fix type issues

---

***REMOVED******REMOVED*** Monitoring & Metrics

***REMOVED******REMOVED******REMOVED*** Pipeline Health Dashboard

**View at:** GitHub Actions → Quality Gates workflow

**Key Metrics:**
- Success rate (target: >98%)
- Average runtime (target: <30 min)
- Most common failures
- Trend over time

***REMOVED******REMOVED******REMOVED*** Performance Targets

| Metric | Current | Target | Trend |
|--------|---------|--------|-------|
| Avg Runtime | 28 min | < 25 min | Improving |
| Success Rate | 97% | > 98% | Stable |
| Coverage (Backend) | 82% | ≥ 80% | Improving |
| Coverage (Frontend) | 72% | ≥ 70% | Stable |

***REMOVED******REMOVED******REMOVED*** Monthly Report

- Generated automatically
- Sent to dev team
- Identifies patterns
- Suggests improvements

---

***REMOVED******REMOVED*** Related Documentation

- [CLAUDE.md](../../CLAUDE.md) - Code style and development workflow
- [BRANCH_PROTECTION.md](BRANCH_PROTECTION.md) - Branch protection rules
- [Debugging Workflow Guide](../development/DEBUGGING_WORKFLOW.md)
- [CI/CD Troubleshooting](../development/CI_CD_TROUBLESHOOTING.md)

---

*Last updated: 2025-12-31*
*Maintained by: Development Team*
