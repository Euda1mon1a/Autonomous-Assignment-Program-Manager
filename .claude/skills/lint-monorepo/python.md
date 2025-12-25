# Python Linting Reference (Ruff)

Ruff-specific error codes, patterns, and fixes for the backend Python codebase.

## Ruff Overview

Ruff replaces multiple tools:
- **Flake8** - Style and error checking
- **isort** - Import sorting
- **pyupgrade** - Python version upgrades
- **Bandit** - Security checks (S-codes)

## Quick Reference

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

# Check only
ruff check app/ tests/

# Auto-fix safe issues
ruff check app/ tests/ --fix

# Format code
ruff format app/ tests/

# Show what a rule means
ruff rule F401

# Check specific file with context
ruff check app/services/scheduler.py --show-source

# Preview what fixes would be applied
ruff check app/ --fix --diff
```

## Common Error Codes

### F - Pyflakes (Logic Errors)

| Code | Name | Auto-fix | Example |
|------|------|----------|---------|
| F401 | Unused import | Yes* | `from os import path` (path unused) |
| F402 | Import shadowed | No | `from x import y; y = 1` |
| F403 | Star import | No | `from module import *` |
| F405 | Name from star import | No | Using name from `import *` |
| F601 | Dict key repeated | No | `{"a": 1, "a": 2}` |
| F811 | Redefinition | No | Function defined twice |
| F821 | Undefined name | No | Using variable before assignment |
| F841 | Unused variable | Yes* | `x = 1` (x never used) |

*Marked unsafe - verify before applying

### E - pycodestyle (Style)

| Code | Name | Auto-fix | Example |
|------|------|----------|---------|
| E101 | Mixed tabs/spaces | Yes | Indentation mixing |
| E401 | Multiple imports | Yes | `import os, sys` |
| E501 | Line too long | Yes | >100 chars (our config) |
| E711 | None comparison | Yes | `if x == None:` → `if x is None:` |
| E712 | Bool comparison | Yes | `if x == True:` → `if x:` |
| E713 | Not in test | Yes | `not x in y` → `x not in y` |
| E721 | Type comparison | Yes | `type(x) == int` → `isinstance(x, int)` |
| E722 | Bare except | No | `except:` → `except Exception:` |

### W - pycodestyle Warnings

| Code | Name | Auto-fix | Example |
|------|------|----------|---------|
| W291 | Trailing whitespace | Yes | Spaces at end of line |
| W292 | No newline at EOF | Yes | File doesn't end with newline |
| W293 | Blank line whitespace | Yes | Whitespace on blank line |

### I - isort (Imports)

| Code | Name | Auto-fix | Example |
|------|------|----------|---------|
| I001 | Unsorted imports | Yes | Imports not in order |
| I002 | Missing import | Yes | Required import missing |

### B - Bugbear (Likely Bugs)

| Code | Name | Auto-fix | Example |
|------|------|----------|---------|
| B006 | Mutable default | No | `def f(x=[]):` |
| B007 | Unused loop var | Yes | `for x in items:` (x unused) |
| B008 | Function call default | No | `def f(x=time.time()):` |
| B009 | getattr constant | Yes | `getattr(x, "y")` → `x.y` |
| B010 | setattr constant | Yes | `setattr(x, "y", z)` → `x.y = z` |
| B017 | assertRaises empty | No | `assertRaises(Exception)` |
| B018 | Useless expression | No | `x.y` on its own line |

### S - Bandit (Security)

| Code | Name | Auto-fix | Example |
|------|------|----------|---------|
| S101 | Assert used | No | `assert` in production code |
| S104 | Hardcoded bind | No | `bind("0.0.0.0")` |
| S105 | Hardcoded password | No | `password = "secret"` |
| S106 | Hardcoded password arg | No | `connect(password="secret")` |
| S107 | Hardcoded password default | No | `def f(pwd="secret"):` |
| S110 | Try except pass | No | `except: pass` |
| S301 | Pickle usage | No | `pickle.loads()` |
| S311 | Random for crypto | No | `random.random()` for security |
| S324 | Insecure hash | No | MD5/SHA1 for security |

### UP - pyupgrade (Modern Python)

| Code | Name | Auto-fix | Example |
|------|------|----------|---------|
| UP006 | Use modern type | Yes | `List[int]` → `list[int]` |
| UP007 | Use X \| Y | Yes | `Optional[X]` → `X \| None` |
| UP035 | Deprecated import | Yes | `from typing import Dict` |

### RUF - Ruff-specific

| Code | Name | Auto-fix | Example |
|------|------|----------|---------|
| RUF001 | Ambiguous unicode | No | Confusable characters |
| RUF002 | Ambiguous docstring | No | Docstring unicode issues |
| RUF100 | Unused noqa | Yes | `# noqa` that isn't needed |

## Detailed Fix Patterns

### F401 - Unused Import

```python
# BEFORE
from typing import Optional, List, Dict  # Dict unused

def get_items() -> List[str]:
    return []

# AFTER - Remove unused
from typing import List

def get_items() -> List[str]:
    return []
```

**Check before removing:**
```bash
# Is it re-exported in __init__.py?
grep -r "from.*import.*Dict" app/__init__.py

# Is it used via locals() or globals()?
grep -r "locals()\|globals()" app/
```

**If re-exported, keep with noqa:**
```python
from typing import Dict  # noqa: F401 (re-exported)
```

### F841 - Unused Variable

```python
# BEFORE
result = expensive_calculation()
return True

# AFTER - If result isn't needed
expensive_calculation()  # Side effects only
return True

# OR - If you need to show it's intentionally unused
_ = expensive_calculation()
return True
```

### E712 - Boolean Comparison

```python
# BEFORE
if user.is_active == True:
    process(user)

# AFTER (general Python)
if user.is_active:
    process(user)

# EXCEPTION: SQLAlchemy requires explicit comparison
query = select(User).where(User.is_active == True)  # noqa: E712
```

### E722 - Bare Except

```python
# BEFORE
try:
    risky_operation()
except:
    pass

# AFTER - Specific exception
try:
    risky_operation()
except ValueError:
    pass

# OR - If truly catching all
try:
    risky_operation()
except Exception:
    logger.exception("Operation failed")

# OR - Using contextlib (cleanest)
from contextlib import suppress
with suppress(ValueError, TypeError):
    risky_operation()
```

### B006 - Mutable Default Argument

```python
# BEFORE (BUG!)
def add_item(item, items=[]):
    items.append(item)
    return items

# AFTER
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

# ALSO GOOD - Using dataclass or factory
from dataclasses import dataclass, field

@dataclass
class Container:
    items: list = field(default_factory=list)
```

### B007 - Unused Loop Variable

```python
# BEFORE
for assignment in assignments:
    counter += 1

# AFTER - Underscore convention
for _ in assignments:
    counter += 1

# IF you need enumerate
for i, _ in enumerate(assignments):
    process_index(i)
```

### S105/S106/S107 - Hardcoded Secrets

```python
# BEFORE (SECURITY ISSUE!)
password = "my_secret_password"
db_url = "postgresql://user:password@localhost/db"

# AFTER - Environment variables
import os
password = os.environ["DB_PASSWORD"]
db_url = os.environ["DATABASE_URL"]

# OR - Using pydantic settings
from app.core.config import settings
password = settings.db_password
```

### UP006/UP007 - Modern Type Hints (Python 3.10+)

```python
# BEFORE (Python 3.9 style)
from typing import Optional, List, Dict, Union

def process(
    items: List[str],
    config: Optional[Dict[str, int]] = None,
    value: Union[str, int] = ""
) -> Optional[str]:
    pass

# AFTER (Python 3.10+ style)
def process(
    items: list[str],
    config: dict[str, int] | None = None,
    value: str | int = ""
) -> str | None:
    pass
```

## Project-Specific Patterns

### SQLAlchemy Async Patterns

```python
# Common false positive: E712 with SQLAlchemy
# This is CORRECT for SQLAlchemy - don't "fix" it
result = await db.execute(
    select(Person).where(Person.is_active == True)  # noqa: E712
)

# Unused variable in async context
# Sometimes needed for proper async behavior
async def get_all(db: AsyncSession) -> list[Person]:
    result = await db.execute(select(Person))
    return list(result.scalars().all())  # result is used
```

### FastAPI Dependency Injection

```python
# Unused parameter warning - but it IS used by FastAPI DI
@router.get("/items")
async def list_items(
    db: AsyncSession = Depends(get_db),  # Used by DI system
    current_user: User = Depends(get_current_user),  # Used by DI
) -> list[Item]:
    return await item_service.get_all(db)
```

### Pydantic Models

```python
# Field validators - parameter might look unused
from pydantic import BaseModel, field_validator

class UserCreate(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:  # v is used
        if "@" not in v:
            raise ValueError("Invalid email")
        return v.lower()
```

## Configuration

### pyproject.toml Settings

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # Pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "S",   # flake8-bandit (security)
    "UP",  # pyupgrade
]
ignore = [
    "E712",  # Allow == True for SQLAlchemy
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]  # Allow assert in tests
```

## Troubleshooting

### "Import could not be resolved"

```bash
# Check if package is installed
pip show package_name

# Check virtual environment is active
which python

# Reinstall dependencies
pip install -r requirements.txt
```

### "Auto-fix made code worse"

```bash
# Revert the auto-fix
git checkout -- path/to/file.py

# Run with diff preview first
ruff check path/to/file.py --fix --diff

# Apply only specific rules
ruff check path/to/file.py --fix --fixable I001
```

### "Rule keeps triggering incorrectly"

```python
# Inline ignore for one line
x = something  # noqa: F841

# Ignore specific rule for block
# ruff: noqa: F401
from module import unused_but_needed

# File-level ignore (top of file)
# ruff: noqa: S101
```
