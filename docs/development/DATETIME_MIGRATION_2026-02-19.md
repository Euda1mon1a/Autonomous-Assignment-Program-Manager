# datetime.utcnow() Deprecation Migration

**Date:** 2026-02-19
**PRs:** #1161–#1169 (9 PRs)
**Scope:** Entire `backend/app/` codebase

---

## Why

`datetime.utcnow()` and `datetime.utcfromtimestamp()` are deprecated as of Python 3.12 (PEP 587). They return **naive** datetimes (no timezone info), which cause `TypeError` when compared against timezone-aware datetimes produced by `datetime.now(UTC)`.

The project runs on Python 3.11.12 (pinned via `.python-version` in PR #1166), but the fix uses `datetime.UTC` which is available since 3.11. This future-proofs the codebase for 3.12+ and prevents mixed naive/aware comparison bugs.

## Migration Patterns

### Runtime calls
```python
# Before
now = datetime.utcnow()
expires_at = datetime.utcfromtimestamp(exp)

# After
now = datetime.now(UTC)
expires_at = datetime.fromtimestamp(exp, tz=UTC)
```

### Dataclass defaults
```python
# Before
timestamp: datetime = field(default_factory=datetime.utcnow)

# After (lambda needed — datetime.now(UTC) is a call, not a callable)
timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
```

### Pydantic Field defaults
```python
# Before
timestamp: datetime = Field(default_factory=datetime.utcnow)

# After
timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
```

### SQLAlchemy Column defaults
```python
# Before
created_at = Column(DateTime, default=datetime.utcnow)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# After
created_at = Column(DateTime, default=lambda: datetime.now(UTC))
updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
```

### Import change
```python
# Before
from datetime import datetime, timedelta

# After
from datetime import UTC, datetime, timedelta
```

## PR Breakdown

| PR | Module | Files | Instances | Method |
|----|--------|-------|-----------|--------|
| #1161 | expansion service bug fix | 2 | 1 | Manual |
| #1162 | outbox + mesh | 6 | 21 | Manual |
| #1163 | utcfromtimestamp (auth/security) | 4 | 5 | Manual |
| #1164 | auth + gateway/auth | 10 | ~45 | Manual |
| #1165 | CQRS | 4 | ~34 | Manual |
| #1166 | Python version pin (.python-version) | 1 | — | Manual |
| #1167 | services + remaining modules | ~200 | ~800+ | Agent team |
| #1168 | api/routes + analytics + schemas | ~60 | ~200+ | Agent team |
| #1169 | scheduling | 15 | ~40 | Agent team + manual commit |

**Total:** ~300 files, ~1,270 instances migrated

## PostgreSQL Compatibility

Inserting `timestamptz` (timezone-aware) into a `timestamp` (naive) column is safe in PostgreSQL — it strips the timezone and stores the UTC value. No schema changes required.

## Naive-vs-Aware Guard Pattern

When code compares `datetime.now(UTC)` against a datetime loaded from a naive DB column, use this guard:

```python
retry_at = (
    self.next_retry_at
    if self.next_retry_at.tzinfo
    else self.next_retry_at.replace(tzinfo=UTC)
)
return datetime.now(UTC) >= retry_at
```

This was applied in `outbox/models.py` (PR #1162) for the `should_retry_now` method.

## What Was NOT Changed

- **Test files** (`backend/tests/`) — intentionally excluded to keep PRs focused on production code
- **Migration files** (`alembic/versions/`) — not applicable
- **Frontend** — JavaScript uses different datetime handling

## Merge Order

PRs are independent (each branched from `main`) and can be merged in any order. No inter-PR dependencies. Recommend merging #1166 (Python pin) first as a quick win.

## Verification

After merging all PRs, run:
```bash
grep -rn "datetime.utcnow" backend/app/ --include="*.py" | wc -l
# Expected: 0

grep -rn "utcfromtimestamp" backend/app/ --include="*.py" | wc -l
# Expected: 0
```
