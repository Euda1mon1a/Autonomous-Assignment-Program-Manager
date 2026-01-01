---
name: lint-monorepo
description: Unified linting and auto-fix for Python (Ruff) and TypeScript (ESLint) in monorepo. Use when fixing lint errors, running pre-commit checks, or diagnosing persistent code quality issues. Orchestrates auto-fix first, then root-cause analysis.
model_tier: haiku
parallel_hints:
  can_parallel_with: [code-review, test-writer, security-audit]
  must_serialize_with: []
  preferred_batch_size: 10
context_hints:
  max_file_context: 30
  compression_level: 2
  requires_git_context: true
  requires_db_context: false
escalation_triggers:
  - pattern: "breaking.*change"
    reason: "Auto-fix may create breaking changes"
  - pattern: "project-wide.*noqa"
    reason: "Project-wide rule disabling needs human approval"
  - keyword: ["unsafe", "public API"]
    reason: "Unsafe fixes affecting public API need review"
---

***REMOVED*** Lint Monorepo Skill

Holistic linting skill for the Residency Scheduler monorepo. Orchestrates Python (Ruff) and TypeScript (ESLint) linting with intelligent auto-fix and root-cause analysis for persistent issues.

***REMOVED******REMOVED*** When This Skill Activates

- Lint errors reported in CI/CD
- Pre-commit quality checks
- Code review identifies style issues
- `ruff check` or `npm run lint` fails
- Persistent lint errors after auto-fix attempts
- New code needs formatting before commit

***REMOVED******REMOVED*** Monorepo Structure

```
/home/user/Autonomous-Assignment-Program-Manager/
├── backend/          ***REMOVED*** Python 3.11+ (Ruff)
│   ├── app/
│   └── tests/
└── frontend/         ***REMOVED*** TypeScript/Next.js (ESLint)
    ├── src/
    └── __tests__/
```

***REMOVED******REMOVED*** Quick Commands

***REMOVED******REMOVED******REMOVED*** Full Monorepo Lint (Check Only)

```bash
***REMOVED*** Run both in parallel
cd /home/user/Autonomous-Assignment-Program-Manager

***REMOVED*** Backend
cd backend && ruff check app/ tests/ && cd ..

***REMOVED*** Frontend
cd frontend && npm run lint && npm run type-check && cd ..
```

***REMOVED******REMOVED******REMOVED*** Full Monorepo Auto-Fix

```bash
cd /home/user/Autonomous-Assignment-Program-Manager

***REMOVED*** Backend - format first, then fix
cd backend && ruff format app/ tests/ && ruff check app/ tests/ --fix && cd ..

***REMOVED*** Frontend
cd frontend && npm run lint:fix && cd ..
```

***REMOVED******REMOVED*** Unified Linting Workflow

***REMOVED******REMOVED******REMOVED*** Phase 1: Auto-Fix First

Always attempt auto-fix before manual intervention:

```bash
***REMOVED*** Step 1: Python formatting (non-destructive)
cd /home/user/Autonomous-Assignment-Program-Manager/backend
ruff format app/ tests/

***REMOVED*** Step 2: Python lint auto-fix
ruff check app/ tests/ --fix

***REMOVED*** Step 3: TypeScript lint auto-fix
cd /home/user/Autonomous-Assignment-Program-Manager/frontend
npm run lint:fix

***REMOVED*** Step 4: Verify what remains
cd /home/user/Autonomous-Assignment-Program-Manager/backend && ruff check app/ tests/
cd /home/user/Autonomous-Assignment-Program-Manager/frontend && npm run lint
```

***REMOVED******REMOVED******REMOVED*** Phase 2: Triage Remaining Errors

If errors persist after auto-fix, categorize them:

| Category | Python (Ruff) | TypeScript (ESLint) | Action |
|----------|---------------|---------------------|--------|
| **Unsafe fixes** | `--unsafe-fixes` needed | `--fix` didn't apply | Review manually first |
| **Logic errors** | F-codes (F401, F841) | no-unused-vars | Requires code change |
| **Type errors** | Not ruff (use mypy) | @typescript-eslint | Fix types, not lint |
| **Style conflicts** | Formatter vs linter | Prettier vs ESLint | Check config alignment |

***REMOVED******REMOVED******REMOVED*** Phase 3: Root-Cause Analysis

For persistent errors, investigate the root cause:

```bash
***REMOVED*** Python: Show full context
ruff check app/path/to/file.py --show-source --show-fixes

***REMOVED*** Python: Explain the rule
ruff rule <ERROR_CODE>  ***REMOVED*** e.g., ruff rule F401

***REMOVED*** TypeScript: Show rule docs
npx eslint --print-config src/path/to/file.tsx | grep -A5 "rule-name"
```

***REMOVED******REMOVED******REMOVED*** Phase 4: Targeted Fix

Apply fixes based on root cause:

```python
***REMOVED*** Example: F401 - Unused import
***REMOVED*** Root cause: Import was used but function was deleted

***REMOVED*** BAD - Just remove import (might break something)
***REMOVED*** from utils import helper  ***REMOVED*** Removed

***REMOVED*** GOOD - Check if import is re-exported or used elsewhere
grep -r "from.*import.*helper" app/
grep -r "helper" app/
```

***REMOVED******REMOVED*** Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│                    LINT ERROR DETECTED                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: Run auto-fix                                        │
│     ruff check --fix (Python)                                │
│     npm run lint:fix (TypeScript)                            │
│           │                                                  │
│           ▼                                                  │
│  Step 2: Error resolved?                                     │
│     YES → Done, commit changes                               │
│     NO  → Continue                                           │
│           │                                                  │
│           ▼                                                  │
│  Step 3: Is it an unsafe fix?                                │
│     YES → Review the change, then --unsafe-fixes             │
│     NO  → Continue                                           │
│           │                                                  │
│           ▼                                                  │
│  Step 4: Is it a type error (not lint)?                      │
│     YES → Use react-typescript or mypy, not this skill       │
│     NO  → Continue                                           │
│           │                                                  │
│           ▼                                                  │
│  Step 5: Root-cause analysis                                 │
│     - Read the file context                                  │
│     - Check if symbol is used elsewhere                      │
│     - Check if it's a re-export                              │
│     - Apply targeted fix                                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

***REMOVED******REMOVED*** Pre-Commit Checklist

Run before every commit:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager

***REMOVED*** Backend
cd backend
ruff format app/ tests/
ruff check app/ tests/ --fix
ruff check app/ tests/  ***REMOVED*** Verify clean

***REMOVED*** Frontend
cd ../frontend
npm run lint:fix
npm run lint          ***REMOVED*** Verify clean
npm run type-check    ***REMOVED*** Types are separate from lint

***REMOVED*** Return to root
cd ..
```

***REMOVED******REMOVED*** Common Patterns

***REMOVED******REMOVED******REMOVED*** Pattern 1: Unused Import After Refactoring

```python
***REMOVED*** Symptom: F401 after deleting code that used the import

***REMOVED*** Step 1: Check if import is re-exported
grep -l "from.*module import symbol" app/__init__.py app/*/__init__.py

***REMOVED*** Step 2: If re-exported, keep it with noqa
from module import symbol  ***REMOVED*** noqa: F401 (re-exported)

***REMOVED*** Step 3: If not re-exported, safe to remove
```

***REMOVED******REMOVED******REMOVED*** Pattern 2: Unused Variable in Loop

```python
***REMOVED*** Symptom: B007 - Loop variable not used

***REMOVED*** BAD
for item in items:
    do_something_else()

***REMOVED*** GOOD - Use underscore
for _ in items:
    do_something_else()

***REMOVED*** ALSO GOOD - If you need the index
for i, _ in enumerate(items):
    do_something_with_index(i)
```

***REMOVED******REMOVED******REMOVED*** Pattern 3: TypeScript Implicit Any

```typescript
// Symptom: Parameter 'e' implicitly has 'any' type

// BAD
const handleClick = (e) => { ... }

// GOOD
const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => { ... }

// For events, common types:
// - React.ChangeEvent<HTMLInputElement>
// - React.FormEvent<HTMLFormElement>
// - React.KeyboardEvent<HTMLInputElement>
```

***REMOVED******REMOVED******REMOVED*** Pattern 4: SQLAlchemy Boolean Comparison

```python
***REMOVED*** Symptom: E712 comparison to True should be 'if cond is True:' or 'if cond:'

***REMOVED*** This is a FALSE POSITIVE for SQLAlchemy
***REMOVED*** SQLAlchemy requires == True for query building

***REMOVED*** Solution: Add noqa comment
query = select(User).where(User.is_active == True)  ***REMOVED*** noqa: E712
```

***REMOVED******REMOVED*** Unsafe Fixes

Some fixes require `--unsafe-fixes` because they might change behavior:

```bash
***REMOVED*** List what unsafe fixes would do (dry run)
ruff check app/ --unsafe-fixes --diff

***REMOVED*** Apply if you've reviewed
ruff check app/ --unsafe-fixes --fix
```

**Common unsafe fixes:**
- Removing unused imports that might be re-exported
- Removing unused variables that might be used via `locals()`
- Changing mutable default arguments

***REMOVED******REMOVED*** CI/CD Integration

***REMOVED******REMOVED******REMOVED*** GitHub Actions Check

```yaml
***REMOVED*** In .github/workflows/ci.yml
- name: Lint Backend
  run: |
    cd backend
    ruff format --check app/ tests/
    ruff check app/ tests/

- name: Lint Frontend
  run: |
    cd frontend
    npm run lint
    npm run type-check
```

***REMOVED******REMOVED******REMOVED*** Pre-Push Hook

```bash
***REMOVED***!/bin/bash
***REMOVED*** .git/hooks/pre-push

cd backend && ruff check app/ tests/ || exit 1
cd ../frontend && npm run lint || exit 1
```

***REMOVED******REMOVED*** Integration with Other Skills

***REMOVED******REMOVED******REMOVED*** With code-quality-monitor
This skill is invoked by `code-quality-monitor` for lint gate checks:
```
code-quality-monitor detects lint needed
    → invokes lint-monorepo
    → lint-monorepo runs auto-fix
    → returns pass/fail status
```

***REMOVED******REMOVED******REMOVED*** With automated-code-fixer
For complex fixes beyond auto-fix:
1. `lint-monorepo` identifies the error
2. `automated-code-fixer` applies the fix
3. `lint-monorepo` verifies the fix worked

***REMOVED******REMOVED******REMOVED*** With react-typescript
For TypeScript type errors (not ESLint):
- ESLint errors → `lint-monorepo`
- Type errors (TS2xxx) → `react-typescript`

***REMOVED******REMOVED******REMOVED*** With python-testing-patterns
After fixing lint errors, run tests:
```bash
cd backend && pytest -x  ***REMOVED*** Stop on first failure
```

***REMOVED******REMOVED*** Escalation Rules

**Escalate to human when:**

1. Auto-fix creates breaking changes
2. Lint rule conflicts with project requirements
3. Need to add project-wide `noqa` or disable rule
4. CI fails but local passes (environment difference)
5. Unsafe fixes affect public API

**Can fix automatically:**

1. Import sorting (I001)
2. Trailing whitespace
3. Missing newlines
4. Quote style
5. Unused imports (after verifying not re-exported)
6. Line length (via formatting)

***REMOVED******REMOVED*** Configuration Files

| Tool | Config Location |
|------|-----------------|
| Ruff | `backend/pyproject.toml` or `backend/ruff.toml` |
| ESLint | `frontend/.eslintrc.js` or `frontend/eslint.config.js` |
| Prettier | `frontend/.prettierrc` |
| TypeScript | `frontend/tsconfig.json` |

***REMOVED******REMOVED*** References

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [ESLint Documentation](https://eslint.org/docs/latest/)
- See `python.md` for Ruff-specific error codes and fixes
- See `typescript.md` for ESLint/TypeScript patterns
