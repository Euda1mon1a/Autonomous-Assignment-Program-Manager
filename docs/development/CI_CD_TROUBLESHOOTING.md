***REMOVED*** CI/CD Troubleshooting Guide for LLMs and Developers

> **Purpose:** Comprehensive guide for diagnosing and fixing CI/CD failures, with specific guidance for LLMs working in IDE environments.
> **Last Updated:** 2025-12-23

---

***REMOVED******REMOVED*** Table of Contents

1. [Quick Reference](***REMOVED***quick-reference)
2. [Common Ruff Error Codes](***REMOVED***common-ruff-error-codes)
3. [TypeScript Errors in Tests](***REMOVED***typescript-errors-in-tests)
4. [Dependency Resolution Failures](***REMOVED***dependency-resolution-failures)
5. [LLM-Specific Failure Patterns](***REMOVED***llm-specific-failure-patterns)
6. [Pre-CI Checklist](***REMOVED***pre-ci-checklist)
7. [Error Recovery Workflow](***REMOVED***error-recovery-workflow)
8. [Quick Fix Commands](***REMOVED***quick-fix-commands)

---

***REMOVED******REMOVED*** Quick Reference

***REMOVED******REMOVED******REMOVED*** Top 10 Most Common CI Errors

| Error Code | Description | Auto-Fix | Manual Fix |
|------------|-------------|----------|------------|
| **F841** | Unused variable | No | Remove or use variable |
| **B007** | Loop variable not used | No | Use `_` for unused loop vars |
| **E712** | Boolean comparison | Yes | `if x == True:` → `if x:` |
| **F401** | Unused import | Yes | Remove import |
| **SIM102** | Nested if statements | Yes | Combine with `and` |
| **SIM105** | try-except-pass | Yes | Use `contextlib.suppress()` |
| **C401** | Unnecessary generator | Yes | Use set comprehension |
| **E402** | Import not at top | No | Move imports to file top |
| **F821** | Undefined name | No | Add missing import/definition |
| **TS1005** | TypeScript syntax | No | Check file extension (.tsx) |

***REMOVED******REMOVED******REMOVED*** Auto-Fix Success Rate

Based on typical CI failures:
- **~80%** of Ruff errors can be auto-fixed with `ruff check --fix`
- **~20%** require manual intervention (unused variables, undefined names)
- **100%** of TypeScript errors require manual fixes

---

***REMOVED******REMOVED*** Common Ruff Error Codes

***REMOVED******REMOVED******REMOVED*** Variable Hygiene

***REMOVED******REMOVED******REMOVED******REMOVED*** F841: Unused Variable

**Problem:** Variable assigned but never used.

```python
***REMOVED*** BAD - CI will fail
def process_data():
    result = expensive_operation()  ***REMOVED*** F841: assigned but never used
    return True

***REMOVED*** GOOD
def process_data():
    return expensive_operation()  ***REMOVED*** Use return value directly
```

**Common LLM Mistake:** Generating placeholder code that declares variables for "later use" but never implements the usage.

**Fix Strategy:**
1. If variable is needed → Add code that uses it
2. If variable is not needed → Remove the assignment
3. If assignment has side effects → Use `_` prefix: `_unused = func_with_side_effect()`

***REMOVED******REMOVED******REMOVED******REMOVED*** B007: Loop Variable Not Used

**Problem:** Iterating over a collection but not using the loop variable.

```python
***REMOVED*** BAD
for assignment in assignments:  ***REMOVED*** B007: 'assignment' not used
    process_data()

***REMOVED*** GOOD - Use underscore for intentionally unused
for _ in assignments:
    process_data()

***REMOVED*** GOOD - Use enumerate if you need the index
for i, _ in enumerate(assignments):
    process_specific(i)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** E741: Ambiguous Variable Name

**Problem:** Single-letter variable names that look like numbers.

```python
***REMOVED*** BAD
l = [1, 2, 3]  ***REMOVED*** E741: 'l' looks like '1'
O = "value"    ***REMOVED*** E741: 'O' looks like '0'
I = 10         ***REMOVED*** E741: 'I' looks like '1'

***REMOVED*** GOOD
items = [1, 2, 3]
output = "value"
index = 10
```

***REMOVED******REMOVED******REMOVED*** Boolean Comparisons

***REMOVED******REMOVED******REMOVED******REMOVED*** E712: Comparison to True/False

**Problem:** Explicitly comparing to `True` or `False` instead of using truthiness.

```python
***REMOVED*** BAD - SQLAlchemy/ORM exceptions
if user.is_active == True:  ***REMOVED*** E712
    pass

***REMOVED*** GOOD - For regular Python
if user.is_active:
    pass

***REMOVED*** EXCEPTION: SQLAlchemy queries MUST use explicit comparison
query = select(User).where(User.is_active == True)  ***REMOVED*** This is correct!
```

**Important:** In SQLAlchemy filters, `== True` IS required. Add `***REMOVED*** noqa: E712` comment:
```python
query = select(User).where(User.is_active == True)  ***REMOVED*** noqa: E712
```

***REMOVED******REMOVED******REMOVED*** Import Organization

***REMOVED******REMOVED******REMOVED******REMOVED*** F401: Unused Import

**Problem:** Import statement exists but symbol never used.

```python
***REMOVED*** BAD
from typing import Optional, Dict, List  ***REMOVED*** F401: Optional unused
def foo() -> Dict:
    return {}

***REMOVED*** GOOD
from typing import Dict
def foo() -> Dict:
    return {}
```

**Auto-fix:** `ruff check --fix --select F401`

***REMOVED******REMOVED******REMOVED******REMOVED*** E402: Module Import Not at Top

**Problem:** Import statements after non-import code.

```python
***REMOVED*** BAD
import os
print("Starting...")  ***REMOVED*** Non-import code
import sys  ***REMOVED*** E402: import not at top

***REMOVED*** GOOD
import os
import sys

print("Starting...")
```

**Common Cause:** Conditional imports for optional dependencies. Use this pattern:
```python
***REMOVED*** At top of file
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from optional_package import OptionalClass
```

***REMOVED******REMOVED******REMOVED*** Code Simplification

***REMOVED******REMOVED******REMOVED******REMOVED*** SIM102: Nested If Statements

**Problem:** Unnecessarily nested if statements that can be combined.

```python
***REMOVED*** BAD
if condition_a:
    if condition_b:  ***REMOVED*** SIM102: combine with outer if
        do_something()

***REMOVED*** GOOD
if condition_a and condition_b:
    do_something()
```

**Exception:** When the inner if has an else clause:
```python
***REMOVED*** This is fine - cannot be simplified
if condition_a:
    if condition_b:
        do_something()
    else:
        do_other()
```

***REMOVED******REMOVED******REMOVED******REMOVED*** SIM105: Try-Except-Pass

**Problem:** Empty except blocks that silently ignore errors.

```python
***REMOVED*** BAD
try:
    risky_operation()
except Exception:  ***REMOVED*** SIM105: use contextlib.suppress
    pass

***REMOVED*** GOOD
from contextlib import suppress

with suppress(ValueError, TypeError):
    risky_operation()
```

***REMOVED******REMOVED******REMOVED******REMOVED*** SIM108: If-Else to Ternary

**Problem:** Simple if-else that can be a ternary expression.

```python
***REMOVED*** BAD
if condition:
    x = "yes"
else:
    x = "no"

***REMOVED*** GOOD
x = "yes" if condition else "no"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** SIM110: Loop to Any/All

**Problem:** For loop returning boolean that can use `any()` or `all()`.

```python
***REMOVED*** BAD
def has_active(users):
    for user in users:
        if user.is_active:
            return True
    return False

***REMOVED*** GOOD
def has_active(users):
    return any(user.is_active for user in users)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** SIM118: Key in Dict.keys()

**Problem:** Using `.keys()` when checking membership.

```python
***REMOVED*** BAD
if key in my_dict.keys():  ***REMOVED*** SIM118
    pass

***REMOVED*** GOOD
if key in my_dict:
    pass
```

***REMOVED******REMOVED******REMOVED*** Generator/Comprehension Issues

***REMOVED******REMOVED******REMOVED******REMOVED*** C401: Unnecessary Generator

**Problem:** Using generator inside `set()` call.

```python
***REMOVED*** BAD
result = set(x for x in items)  ***REMOVED*** C401: unnecessary generator

***REMOVED*** GOOD
result = {x for x in items}  ***REMOVED*** Set comprehension
```

***REMOVED******REMOVED******REMOVED******REMOVED*** C416: Unnecessary Comprehension

**Problem:** Comprehension that just copies the iterable.

```python
***REMOVED*** BAD
result = [x for x in items]  ***REMOVED*** C416: just copies

***REMOVED*** GOOD
result = list(items)
```

***REMOVED******REMOVED******REMOVED*** Deprecated Patterns

***REMOVED******REMOVED******REMOVED******REMOVED*** UP035: Deprecated Typing Imports

**Problem:** Using `typing.Dict/List/Set` instead of built-in types (Python 3.9+).

```python
***REMOVED*** BAD (Python 3.9+)
from typing import Dict, List, Set

def process(data: Dict[str, List[int]]) -> Set[str]:
    pass

***REMOVED*** GOOD (Python 3.9+)
def process(data: dict[str, list[int]]) -> set[str]:
    pass
```

***REMOVED******REMOVED******REMOVED******REMOVED*** UP028: Yield in For Loop

**Problem:** Using `yield` in a for loop instead of `yield from`.

```python
***REMOVED*** BAD
def get_all():
    for item in items:
        yield item  ***REMOVED*** UP028: use yield from

***REMOVED*** GOOD
def get_all():
    yield from items
```

***REMOVED******REMOVED******REMOVED*** Undefined Names

***REMOVED******REMOVED******REMOVED******REMOVED*** F821: Undefined Name

**Problem:** Using a name that hasn't been imported or defined.

```python
***REMOVED*** BAD
def process():
    return ParameterAdapter()  ***REMOVED*** F821: 'ParameterAdapter' undefined

***REMOVED*** GOOD
from app.adapters import ParameterAdapter

def process():
    return ParameterAdapter()
```

**Common LLM Mistake:** Referencing a class or function that exists in another part of the codebase without importing it.

***REMOVED******REMOVED******REMOVED*** Exception Handling

***REMOVED******REMOVED******REMOVED******REMOVED*** E722: Bare Except

**Problem:** Using `except:` without specifying exception type.

```python
***REMOVED*** BAD
try:
    risky_operation()
except:  ***REMOVED*** E722: bare except catches everything including SystemExit
    pass

***REMOVED*** GOOD
try:
    risky_operation()
except Exception:  ***REMOVED*** Catches most exceptions
    pass

***REMOVED*** BETTER - Be specific
try:
    risky_operation()
except (ValueError, TypeError) as e:
    logger.warning(f"Operation failed: {e}")
```

---

***REMOVED******REMOVED*** TypeScript Errors in Tests

***REMOVED******REMOVED******REMOVED*** TS1005/TS1161: Unterminated Expressions

**Symptom:** Multiple syntax errors like:
```
Error: (55,28): error TS1005: '>' expected.
Error: (55,34): error TS1005: ')' expected.
Error: (55,60): error TS1161: Unterminated regular expression literal.
```

**Root Causes:**

1. **Wrong File Extension**
   ```
   ***REMOVED*** BAD - JSX in .ts file
   __tests__/Component.test.ts  ***REMOVED*** Contains JSX

   ***REMOVED*** GOOD - Use .tsx for JSX
   __tests__/Component.test.tsx
   ```

2. **Generic Type Arrow Confusion**
   ```typescript
   // BAD - In .tsx file, < looks like JSX
   const Component = <T>(props: Props<T>) => { }

   // GOOD - Add trailing comma to disambiguate
   const Component = <T,>(props: Props<T>) => { }
   ```

3. **Regex in Template Literals**
   ```typescript
   // BAD - Division operator misinterpreted
   const pattern = /test/;  // May confuse parser in certain contexts

   // GOOD - Use RegExp constructor in ambiguous contexts
   const pattern = new RegExp('test');
   ```

***REMOVED******REMOVED******REMOVED*** Mock Syntax Issues

**Problem:** TypeScript parser confused by mock definitions.

```typescript
// BAD - May be interpreted as JSX
vi.mock('../hooks', <implementation>);

// GOOD - Use explicit syntax
vi.mock('../hooks', () => ({
  useMyHook: vi.fn().mockReturnValue({})
}));
```

***REMOVED******REMOVED******REMOVED*** Type Assertions in Tests

```typescript
// BAD - Angle bracket assertion looks like JSX
const mock = <MockType>someValue;

// GOOD - Use 'as' keyword
const mock = someValue as MockType;
```

***REMOVED******REMOVED******REMOVED*** Test File Configuration

Ensure `tsconfig.json` includes test files:
```json
{
  "include": [
    "src/**/*",
    "__tests__/**/*",
    "**/*.test.ts",
    "**/*.test.tsx"
  ]
}
```

---

***REMOVED******REMOVED*** Dependency Resolution Failures

***REMOVED******REMOVED******REMOVED*** Resolution Too Deep Error

**Symptom:**
```
× Dependency resolution exceeded maximum depth
╰─> Pip cannot resolve the current dependencies
```

**Root Causes:**

1. **Unbounded Version Constraints**
   ```txt
   ***REMOVED*** BAD - No upper bound creates exponential search
   requests~=2.7
   opentelemetry-instrumentation

   ***REMOVED*** GOOD - Bounded ranges
   requests>=2.32.0,<3.0.0
   opentelemetry-instrumentation>=0.44b0,<0.50
   ```

2. **Transitive Dependency Conflicts**
   - Package A requires `idna>=2.0,<3.0`
   - Package B requires `idna>=3.0`
   - Pip cannot satisfy both

**Solutions:**

1. **Use Dependency Lock Files**
   ```bash
   ***REMOVED*** Install pip-tools
   pip install pip-tools

   ***REMOVED*** Create requirements.in with direct dependencies
   ***REMOVED*** Generate locked requirements.txt
   pip-compile requirements.in -o requirements.txt
   ```

2. **Pin Transitive Dependencies**
   ```txt
   ***REMOVED*** requirements.txt
   ***REMOVED*** Direct dependencies
   fastapi>=0.115.0,<0.116.0

   ***REMOVED*** Pinned transitive (from pip-compile)
   idna==3.6
   charset-normalizer==3.3.2
   ```

3. **Use uv for Faster Resolution**
   ```bash
   ***REMOVED*** Install uv (Rust-based, much faster)
   pip install uv

   ***REMOVED*** Resolve dependencies
   uv pip compile requirements.in -o requirements.txt
   ```

4. **Test Installation in Clean Environment**
   ```bash
   python -m venv test_env
   source test_env/bin/activate
   pip install -r requirements.txt
   python -c "import app; print('Success')"
   deactivate
   rm -rf test_env
   ```

***REMOVED******REMOVED******REMOVED*** OpenTelemetry Specific Issues

The `opentelemetry-instrumentation-*` packages have complex interdependencies.

**Recommended Pinning:**
```txt
***REMOVED*** Pin the core versions
opentelemetry-api>=1.23.0,<1.25.0
opentelemetry-sdk>=1.23.0,<1.25.0
opentelemetry-instrumentation>=0.44b0,<0.46b0

***REMOVED*** Pin instrumentation packages to match
opentelemetry-instrumentation-fastapi>=0.44b0,<0.46b0
opentelemetry-instrumentation-redis>=0.44b0,<0.46b0
```

---

***REMOVED******REMOVED*** LLM-Specific Failure Patterns

***REMOVED******REMOVED******REMOVED*** Why LLMs Fail at CI Checks

***REMOVED******REMOVED******REMOVED******REMOVED*** Pattern 1: Incomplete Context Windows

When editing large files, LLMs may lose track of:
- Import statements at file top
- Variable usage across distant functions
- Type definitions from other files

**Mitigation:**
- Read entire file before editing
- Check imports match usage after edits
- Verify referenced types/classes exist

***REMOVED******REMOVED******REMOVED******REMOVED*** Pattern 2: Template Code Generation

LLMs often generate boilerplate that includes:
- Unused imports from templates
- Placeholder variables never used
- Over-defensive error handling

**Mitigation:**
- Review generated code for unused elements
- Remove placeholder comments and variables
- Simplify exception handling to specific cases

***REMOVED******REMOVED******REMOVED******REMOVED*** Pattern 3: Incremental Changes Without Context

LLMs make local optimizations that break global contracts:
- Remove "unused" variable actually used in callback
- Simplify if statements with side effects
- Refactor imports without checking re-exports

**Mitigation:**
- Search for variable usage before removing
- Check for side effects before simplifying
- Verify exports from `__init__.py` files

***REMOVED******REMOVED******REMOVED******REMOVED*** Pattern 4: Test File Syntax Confusion

LLMs generate test code with:
- Wrong file extensions (.ts vs .tsx)
- JSX syntax in non-JSX files
- Mock patterns that confuse parser

**Mitigation:**
- Always use `.tsx` extension when tests contain JSX
- Use `as` keyword instead of angle bracket assertions
- Follow existing test file patterns in codebase

***REMOVED******REMOVED******REMOVED*** LLM Pre-Edit Checklist

Before modifying any file:

- [ ] Read the entire file first
- [ ] Note all imports at top
- [ ] Identify variables used across functions
- [ ] Check for `__init__.py` exports if modifying imports
- [ ] Understand test file extension requirements

After modifying:

- [ ] Verify all imports are still used
- [ ] Confirm no new undefined names
- [ ] Check variables are used after assignment
- [ ] Run `ruff check` on modified files
- [ ] Run type checker on modified files

---

***REMOVED******REMOVED*** Pre-CI Checklist

Run these commands **before every commit** to catch CI failures early:

***REMOVED******REMOVED******REMOVED*** Backend Validation

```bash
cd backend

***REMOVED*** 1. Auto-fix what's safe
ruff check app/ --fix

***REMOVED*** 2. Format code
ruff format app/

***REMOVED*** 3. Check for remaining issues
ruff check app/ --statistics

***REMOVED*** 4. Type checking
mypy app/ --ignore-missing-imports

***REMOVED*** 5. Run tests
pytest --tb=short

***REMOVED*** 6. Check test coverage
pytest --cov=app --cov-fail-under=70
```

***REMOVED******REMOVED******REMOVED*** Frontend Validation

```bash
cd frontend

***REMOVED*** 1. Fix linting issues
npm run lint:fix

***REMOVED*** 2. Type check
npm run type-check

***REMOVED*** 3. Run tests
npm test -- --run

***REMOVED*** 4. Check coverage
npm run test:coverage
```

***REMOVED******REMOVED******REMOVED*** Dependency Validation

```bash
***REMOVED*** Test that dependencies can be installed
pip install -r requirements.txt --dry-run

***REMOVED*** Check for security vulnerabilities
pip-audit -r requirements.txt
```

***REMOVED******REMOVED******REMOVED*** Quick One-Liner

```bash
***REMOVED*** Backend full check
cd backend && ruff check . --fix && ruff format . && mypy app/ && pytest

***REMOVED*** Frontend full check
cd frontend && npm run lint:fix && npm run type-check && npm test -- --run
```

---

***REMOVED******REMOVED*** Error Recovery Workflow

When CI fails after a commit, follow this workflow:

***REMOVED******REMOVED******REMOVED*** Step 1: Identify Failure Category

```bash
***REMOVED*** Check GitHub Actions logs or run locally:
cd backend && ruff check .        ***REMOVED*** Linting?
cd backend && mypy app/           ***REMOVED*** Type checking?
cd backend && pytest              ***REMOVED*** Tests?
cd frontend && npm run type-check ***REMOVED*** TypeScript?
cd frontend && npm run lint       ***REMOVED*** ESLint?
```

***REMOVED******REMOVED******REMOVED*** Step 2: Reproduce Locally

```bash
***REMOVED*** Checkout the failed commit
git checkout <commit-sha>

***REMOVED*** Run the exact CI command that failed
***REMOVED*** (Copy from GitHub Actions log)
```

***REMOVED******REMOVED******REMOVED*** Step 3: Fix in Batch

Don't fix one error at a time. Use auto-fix for eligible errors:

```bash
***REMOVED*** Fix all auto-fixable Ruff errors
ruff check app/ --fix --unsafe-fixes

***REMOVED*** Fix specific error types
ruff check app/ --select F401,E712 --fix
```

***REMOVED******REMOVED******REMOVED*** Step 4: Verify Complete Fix

```bash
***REMOVED*** Run FULL CI suite locally
cd backend
ruff check app/
mypy app/
pytest

cd frontend
npm run lint
npm run type-check
npm test
```

***REMOVED******REMOVED******REMOVED*** Step 5: Commit Fix

```bash
git add .
git commit -m "fix: resolve CI linting failures

- Remove unused imports (F401)
- Fix boolean comparisons (E712)
- Add missing type annotations"
```

---

***REMOVED******REMOVED*** Quick Fix Commands

***REMOVED******REMOVED******REMOVED*** Ruff Auto-Fix Commands

```bash
***REMOVED*** Fix all auto-fixable issues
ruff check . --fix

***REMOVED*** Fix with unsafe fixes (more aggressive)
ruff check . --fix --unsafe-fixes

***REMOVED*** Fix specific error codes only
ruff check . --select F401,E712,SIM102 --fix

***REMOVED*** Show what would be fixed (dry run)
ruff check . --fix --diff
```

***REMOVED******REMOVED******REMOVED*** Ruff Analysis Commands

```bash
***REMOVED*** Show error statistics
ruff check . --statistics

***REMOVED*** Show errors with source context
ruff check . --show-source

***REMOVED*** Output as JSON for parsing
ruff check . --output-format json
```

***REMOVED******REMOVED******REMOVED*** TypeScript Fix Commands

```bash
***REMOVED*** ESLint auto-fix
npx eslint --fix 'src/**/*.{ts,tsx}'
npx eslint --fix '__tests__/**/*.{ts,tsx}'

***REMOVED*** Prettier formatting
npx prettier --write 'src/**/*.{ts,tsx}'
```

***REMOVED******REMOVED******REMOVED*** Dependency Commands

```bash
***REMOVED*** Check installability
pip install -r requirements.txt --dry-run

***REMOVED*** Compile locked requirements
pip-compile requirements.in -o requirements.txt

***REMOVED*** Upgrade all dependencies
pip-compile requirements.in -o requirements.txt --upgrade

***REMOVED*** Check for conflicts
pip check
```

---

***REMOVED******REMOVED*** Related Documentation

- **[Code Style Guide](code-style.md)** - Formatting standards
- **[Contributing Guide](contributing.md)** - Full development workflow
- **[CI/CD Recommendations](CI_CD_RECOMMENDATIONS.md)** - Pipeline improvements
- **[AI Rules of Engagement](AI_RULES_OF_ENGAGEMENT.md)** - Git and PR workflow
- **[Troubleshooting](../troubleshooting.md)** - Runtime issues

---

***REMOVED******REMOVED*** Appendix: Error Code Quick Reference

***REMOVED******REMOVED******REMOVED*** Ruff Error Families

| Prefix | Category | Description |
|--------|----------|-------------|
| F | Pyflakes | Undefined names, unused imports/vars |
| E | pycodestyle | PEP 8 style errors |
| W | pycodestyle | PEP 8 style warnings |
| C | mccabe/comprehensions | Complexity and comprehension issues |
| B | bugbear | Common bugs and design issues |
| SIM | simplify | Code simplification opportunities |
| UP | pyupgrade | Deprecated patterns for Python version |
| I | isort | Import sorting issues |

***REMOVED******REMOVED******REMOVED*** TypeScript Error Families

| Code | Category | Common Cause |
|------|----------|--------------|
| TS1005 | Syntax | Missing expected token |
| TS1128 | Syntax | Missing declaration/statement |
| TS1161 | Syntax | Unterminated regex/string |
| TS2304 | Type | Cannot find name |
| TS2322 | Type | Type assignment mismatch |
| TS2345 | Type | Argument type mismatch |

---

*This document should be updated whenever new CI failure patterns are identified.*
