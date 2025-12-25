---
name: code-quality-monitor
description: Proactive code health monitoring and quality gate enforcement. Use when validating code changes, reviewing PRs, or ensuring code meets quality standards before merging.
---

***REMOVED*** Code Quality Monitor

A proactive health checker that monitors code quality and enforces strict standards.

***REMOVED******REMOVED*** When This Skill Activates

- Before committing changes
- During PR reviews
- When validating code health
- After making multiple edits
- When user asks about code quality

***REMOVED******REMOVED*** Quality Standards

***REMOVED******REMOVED******REMOVED*** Python Backend Standards

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Test Coverage | >= 80% | >= 70% |
| Type Coverage | 100% public APIs | >= 90% |
| Cyclomatic Complexity | <= 10 | <= 15 |
| Function Length | <= 50 lines | <= 100 lines |
| File Length | <= 500 lines | <= 800 lines |

***REMOVED******REMOVED******REMOVED*** TypeScript Frontend Standards

| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Type Safety | No `any` | < 5 `any` uses |
| Test Coverage | >= 75% | >= 60% |
| Component Size | <= 200 lines | <= 300 lines |
| Hook Complexity | <= 5 dependencies | <= 8 dependencies |

***REMOVED******REMOVED*** Health Check Commands

***REMOVED******REMOVED******REMOVED*** Quick Health Check
```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

***REMOVED*** Run all quality checks
pytest --tb=no -q && \
ruff check app/ tests/ && \
black --check app/ tests/ && \
mypy app/ --python-version 3.11 --no-error-summary

echo "Backend health: PASS"
```

***REMOVED******REMOVED******REMOVED*** Comprehensive Health Check
```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

***REMOVED*** Coverage report
pytest --cov=app --cov-report=term-missing --cov-fail-under=70

***REMOVED*** Complexity analysis
radon cc app/ -a -s

***REMOVED*** Security scan
bandit -r app/ -ll

***REMOVED*** Dependency check
pip-audit
```

***REMOVED******REMOVED******REMOVED*** Frontend Health Check
```bash
cd /home/user/Autonomous-Assignment-Program-Manager/frontend

npm run type-check && \
npm run lint && \
npm test -- --coverage --watchAll=false

echo "Frontend health: PASS"
```

***REMOVED******REMOVED*** Quality Gate Rules

***REMOVED******REMOVED******REMOVED*** Gate 1: Must Pass (Blocking)
- [ ] All tests pass
- [ ] No linting errors
- [ ] No type errors
- [ ] No critical security issues

***REMOVED******REMOVED******REMOVED*** Gate 2: Should Pass (Warning)
- [ ] Coverage >= 70%
- [ ] No new complexity issues
- [ ] Documentation updated
- [ ] No TODOs without tickets

***REMOVED******REMOVED******REMOVED*** Gate 3: Nice to Have (Info)
- [ ] Coverage >= 80%
- [ ] All functions documented
- [ ] No magic numbers
- [ ] Consistent naming

***REMOVED******REMOVED*** Monitoring Workflow

***REMOVED******REMOVED******REMOVED*** Pre-Commit Check
Before committing, validate:

```bash
***REMOVED***!/bin/bash
set -e

echo "Running pre-commit checks..."

***REMOVED*** Format
black app/ tests/

***REMOVED*** Lint
ruff check app/ tests/ --fix

***REMOVED*** Type check
mypy app/ --python-version 3.11

***REMOVED*** Quick tests
pytest --tb=no -q --lf

echo "Pre-commit checks: PASS"
```

***REMOVED******REMOVED******REMOVED*** PR Validation Check
For pull request reviews:

```bash
***REMOVED***!/bin/bash
set -e

echo "Running PR validation..."

***REMOVED*** Full test suite with coverage
pytest --cov=app --cov-report=term-missing

***REMOVED*** Security scan
bandit -r app/ -ll

***REMOVED*** Check for common issues
ruff check app/ tests/

***REMOVED*** Type coverage
mypy app/ --python-version 3.11

echo "PR validation: PASS"
```

***REMOVED******REMOVED*** Red Flags to Watch For

***REMOVED******REMOVED******REMOVED*** Immediate Action Required
1. Test coverage dropped below 70%
2. New security vulnerability detected
3. Type errors in public APIs
4. Breaking changes without migration

***REMOVED******REMOVED******REMOVED*** Needs Attention
1. Coverage trending down
2. Increasing complexity metrics
3. Growing file sizes
4. Missing docstrings on new functions

***REMOVED******REMOVED******REMOVED*** Nice to Address
1. Minor style inconsistencies
2. Optimization opportunities
3. Documentation gaps
4. Technical debt

***REMOVED******REMOVED*** Integration Points

***REMOVED******REMOVED******REMOVED*** With lint-monorepo (Primary Linting)
For all linting operations, delegate to the `lint-monorepo` skill:

```
Quality gate check needed
    → Invoke lint-monorepo skill
    → lint-monorepo runs auto-fix workflow
    → Returns pass/fail with details
```

**Linting workflow:**
```bash
***REMOVED*** lint-monorepo handles both Python and TypeScript
***REMOVED*** See .claude/skills/lint-monorepo/ for details

***REMOVED*** Quick lint check
cd /home/user/Autonomous-Assignment-Program-Manager/backend
ruff check app/ tests/

cd /home/user/Autonomous-Assignment-Program-Manager/frontend
npm run lint
```

**For persistent lint errors:** Use `lint-monorepo` root-cause analysis workflow.

***REMOVED******REMOVED******REMOVED*** With automated-code-fixer
When quality issues are detected, the `automated-code-fixer` skill can be triggered to automatically resolve:
- Linting issues (auto-fixable) - coordinates with `lint-monorepo`
- Formatting issues
- Simple type annotation additions
- Import organization

***REMOVED******REMOVED******REMOVED*** With Existing Commands
- `/run-tests` - Full test suite
- `/lint-fix` - Auto-fix linting
- `/health-check` - System health
- `/check-compliance` - ACGME validation

***REMOVED******REMOVED*** Reporting Format

***REMOVED******REMOVED******REMOVED*** Quick Status
```
Code Health: GREEN/YELLOW/RED

Tests: 156 passed, 0 failed
Coverage: 78.2% (target: 80%)
Linting: 0 errors, 3 warnings
Types: 100% coverage
Security: No issues
```

***REMOVED******REMOVED******REMOVED*** Detailed Report
```markdown
***REMOVED******REMOVED*** Code Quality Report

***REMOVED******REMOVED******REMOVED*** Test Results
- Total: 156 tests
- Passed: 156
- Failed: 0
- Skipped: 2

***REMOVED******REMOVED******REMOVED*** Coverage Analysis
- Current: 78.2%
- Target: 80.0%
- Delta: -1.8%
- Uncovered: app/services/new_feature.py (lines 45-67)

***REMOVED******REMOVED******REMOVED*** Linting
- Errors: 0
- Warnings: 3
  - W291: trailing whitespace (3 occurrences)

***REMOVED******REMOVED******REMOVED*** Type Safety
- Checked files: 147
- Errors: 0
- Coverage: 100%

***REMOVED******REMOVED******REMOVED*** Security
- Critical: 0
- High: 0
- Medium: 0
- Low: 0

***REMOVED******REMOVED******REMOVED*** Recommendations
1. Add tests for app/services/new_feature.py
2. Remove trailing whitespace
3. Consider splitting large function in resilience.py
```

***REMOVED******REMOVED*** Escalation Rules

Escalate to human when:
1. Coverage drops below 60%
2. Critical security issue found
3. Multiple interdependent failures
4. Unclear how to improve metrics
5. Architectural concerns detected
