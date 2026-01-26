# Session: Bandit Config + Python 3.11 Setup

**Date:** 2026-01-25
**Branches:** `bandit-config` (pushed), `python311-setup` (in progress)

## Summary

Two main tasks completed/in-progress:
1. Configured Bandit security scanner (done, pushed)
2. Setting up Python 3.11 for local development (in progress)

---

## Completed: Bandit Configuration

**Branch:** `bandit-config`
**Commit:** `733813da`
**Status:** Pushed to origin

### Changes Made

1. **Added `[tool.bandit]` to `backend/pyproject.toml`:**
   ```toml
   [tool.bandit]
   exclude_dirs = ["tests", "venv", "alembic", "benchmarks", "examples", "experimental"]
   targets = ["app"]
   ```

2. **Fixed MD5/SHA1 false positives** (10 locations) with `usedforsecurity=False`:
   - `app/core/cache/keys.py:183`
   - `app/core/service_cache.py:422,454`
   - `app/db/sharding/strategies.py:169,171`
   - `app/features/evaluator.py:185,225`
   - `app/privacy/maskers.py:107`
   - `app/shadow/traffic.py:456`
   - `app/api/routes/backup.py:937`

3. **Fixed Jinja2 XSS risk:**
   - `app/notifications/templates/validators.py:76`
   - Changed `Environment()` to `Environment(autoescape=select_autoescape())`

4. **Added nosec for shell=True:**
   - `app/api/routes/backup.py:851` - `# nosec B602` (pipe required)

### Results
- **High severity:** 12 → 0 ✅
- **Medium severity:** 61 (unchanged, existing patterns)

---

## In Progress: Python 3.11 Setup

**Branch:** `python311-setup`
**Status:** Recreating venv with Python 3.11

### Context

- **Project requires:** Python 3.11+ (`pyproject.toml`)
- **System default:** Python 3.9.6 (`/usr/bin/python3`)
- **Available:** Python 3.11.14 (`/opt/homebrew/bin/python3.11`)

### Why NOT Python 3.14

- Python 3.14 released Oct 2025 (~3 months old)
- PEP 649 (deferred annotation evaluation) can break libraries
- Pydantic has only "initial" support (not full)
- 3.11 is stable (3+ years), all deps fully support it

### Case Conversion Analysis

The camelCase/snake_case conversion is **working as designed**:
- Backend: snake_case (Python/PEP 8)
- Frontend: camelCase (TypeScript)
- Axios interceptor translates between them

**NOT a problem to fix** - this is the correct architecture. Each language uses its own convention.

PascalCase is used for class/component names and is **unaffected by Python version**.

---

## PR Status

| PR | Branch | Status |
|----|--------|--------|
| #766 | cp-sat-canonical | Pushed, Codex P1 fixed |
| #767 | docs security review | Reviewed, docs accurate |
| - | bandit-config | Pushed, awaiting PR creation |
| - | python311-setup | In progress |

---

## Technical Notes

### Bandit Config Location
Bandit automatically reads `[tool.bandit]` from `pyproject.toml` when run from the backend directory.

### usedforsecurity Parameter
Python 3.9+ feature that tells hashlib MD5/SHA1 is being used for non-cryptographic purposes (cache keys, checksums), silencing false positives.

### Stashed Changes
WIP changes from `cp-sat-canonical` stashed: `git stash push -m "WIP: cp-sat-canonical changes"`

---

## Next Steps

1. Wait for venv to finish installing
2. Verify Python 3.11 works
3. Run tests to confirm nothing broke
4. Commit and push `python311-setup` branch
5. Create PRs for both branches
